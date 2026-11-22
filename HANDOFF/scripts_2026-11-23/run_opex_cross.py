"""Round 5 — Part 1: Opex intraday pinning (O1_NQ, O1_ES + 5A ref), Cross-asset IBS (X1) & Donchian 1h (X2).

Prereg: HANDOFF/futures_tur5_onkayit_2026-11-23.md (commit 1df1cd7).
Run from strategy-lab with vectorbt-lab venv:
  python ../HANDOFF/scripts_2026-11-23/run_opex_cross.py
"""
from __future__ import annotations

import dataclasses
import json
import sys
from pathlib import Path

import databento as db
import numpy as np
import pandas as pd

sys.path.insert(0, ".")
sys.path.insert(0, "../HANDOFF/scripts_2026-11-21")
from intraday.config import INSTRUMENTS  # noqa: E402
from intraday.donchian_xau_lab import DonchianCase, build_signals  # noqa: E402
from intraday.honest_engine import simulate_trades  # noqa: E402
from intraday.kaynak_adaylari import nyse_days, third_friday  # noqa: E402
from intraday.seffaf_adaylari import resample_nq_daily, simulate_b7  # noqa: E402
from futures_cost_retest import load_1m  # noqa: E402
from futures_transfer3 import back_adjust  # noqa: E402

SRC = Path("outputs/databento")
OUT = Path("outputs/intraday/futures_round5")
COMMISSION_SIDE_USD = 0.61
COST_INDEX = {"NQ.c.0": 0.555, "ES.c.0": 0.247}
MULT = {"CL": 1000.0, "ZN": 1000.0, "6E": 125000.0, "MCL": 100.0, "M6E": 12500.0}
EVAL0, EVAL1, HOLD1, SPLIT = "2012-01-01", "2026-11-20", "2012-01-01", "2022-01-01"
SEED, REPS = 20261123, 10_000
N_TESTS = 11
Q_LO = 0.05 / N_TESTS / 2.0
PROBE = 1e-4


def boot_ci(x: np.ndarray) -> list[float]:
    if len(x) < 10:
        return [float("nan"), float("nan")]
    rng = np.random.default_rng(SEED)
    m = x[rng.integers(0, len(x), size=(REPS, len(x)))].mean(axis=1)
    return np.quantile(m, [Q_LO, 1.0 - Q_LO]).tolist()


def summarize(s: pd.Series, scale: float) -> dict:
    s = s.dropna().sort_index()
    ev = s[(s.index >= EVAL0) & (s.index < EVAL1)]
    ho = s[s.index < HOLD1]
    lo, hi = boot_ci(ev.to_numpy())
    pre = ev[ev.index < SPLIT]
    post = ev[ev.index >= SPLIT]
    return {
        "n": int(len(ev)),
        "mean": float(ev.mean() * scale) if len(ev) else float("nan"),
        "ci_bonf": [float(lo * scale), float(hi * scale)],
        "2012-21": float(pre.mean() * scale) if len(pre) else float("nan"),
        "2022+": float(post.mean() * scale) if len(post) else float("nan"),
        "holdout_mean": float(ho.mean() * scale) if len(ho) else None,
        "holdout_n": int(len(ho)),
    }


def check_pass(res: dict) -> bool:
    c = res["central"]
    p = res["pessimistic"]
    if np.isnan(c["ci_bonf"][0]) or np.isnan(c["2012-21"]) or np.isnan(c["2022+"]):
        return False
    return bool(c["ci_bonf"][0] > 0 and c["2012-21"] > 0 and c["2022+"] > 0 and p["mean"] > 0)


# -------------------- BBOX SPREAD MEASUREMENT --------------------

def measure_bbox() -> dict:
    files = sorted((SRC / "bbox").glob("*.dbn.zst"))
    q = pd.concat(db.DBNStore.from_file(f).to_df() for f in files)
    ny = q.index.tz_convert("America/New_York")
    mins = ny.hour * 60 + ny.minute
    rth_mask = (mins >= 570) & (mins < 960) & (ny.dayofweek < 5)
    out = {}
    for sym in ("CL.c.0", "ZN.c.0", "6E.c.0", "MCL.c.0", "M6E.c.0"):
        sub = q[q["symbol"] == sym]
        if sub.empty:
            out[sym] = {"n": 0, "error": "empty"}
            continue
        hs_all = (sub["ask_px_00"] - sub["bid_px_00"]) / 2.0
        hs_all = hs_all[hs_all > 0]
        sub_rth = sub[rth_mask[q["symbol"] == sym]]
        hs_rth = (sub_rth["ask_px_00"] - sub_rth["bid_px_00"]) / 2.0
        hs_rth = hs_rth[hs_rth > 0]
        root = sym.split(".")[0]
        med = float(hs_rth.median()) if len(hs_rth) else float(hs_all.median())
        comm_pts = COMMISSION_SIDE_USD / MULT[root]
        out[sym] = {
            "n_rth": int(len(hs_rth)),
            "half_spread_rth": med,
            "half_spread_all": float(hs_all.median()) if len(hs_all) else None,
            "comm_pts": comm_pts,
            "cost_side_pts": med + comm_pts,
            "from": str(sub.index.min().date()),
            "to": str(sub.index.max().date()),
        }
    return out


# -------------------- O1: OPEX 3RD FRIDAY PINNING (5B) + 5A REF --------------------

def opex_dates_in(dates: pd.DatetimeIndex) -> set[pd.Timestamp]:
    """3rd Friday of each month, or previous trading day if holiday."""
    tr_days = nyse_days(str(dates.min().date()), str(dates.max().date()))
    tr_set = set(tr_days)
    out = set()
    months = pd.date_range(dates.min().replace(day=1), dates.max(), freq="MS")
    for m in months:
        tf = third_friday(m)
        d = tf
        while d not in tr_set and d >= m:
            d -= pd.Timedelta(days=1)
        if d in tr_set:
            out.add(d)
    return out


def run_o1_symbol(sym: str) -> dict:
    m = load_1m(sym)
    ny = m.tz_convert("America/New_York")
    mins = ny.index.hour * 60 + ny.index.minute
    rth = ny[(mins >= 570) & (mins < 960) & (ny.index.dayofweek < 5)].copy()
    rth["date"] = rth.index.normalize().tz_localize(None)
    rth["hm"] = rth.index.strftime("%H:%M")

    # Daily summary for morning move and roll detection
    day_iid = rth.groupby("date")["instrument_id"].agg(["first", "last"])
    roll_days = set(day_iid.index[day_iid["first"].ne(day_iid["last"]) | day_iid["last"].ne(day_iid["last"].shift())])

    # Build morning return series (09:30 open -> 10:59 close) for all complete days
    morn_rows = []
    grouped = {d: g for d, g in rth.groupby("date", sort=True)}
    all_dates = sorted(grouped.keys())
    for d in all_dates:
        g = grouped[d]
        if len(g) < 350:  # skip half-days / severely incomplete
            continue
        g_hm = g.set_index("hm")
        if "09:30" not in g_hm.index or "10:59" not in g_hm.index or "11:00" not in g_hm.index or "15:55" not in g_hm.index:
            continue
        p0930 = float(g_hm.loc["09:30", "open"])
        p1059 = float(g_hm.loc["10:59", "close"])
        morn_rows.append({"date": d, "r_morn": p1059 / p0930 - 1.0, "p0930": p0930})

    morn_df = pd.DataFrame(morn_rows).set_index("date")
    morn_df["sigma20"] = morn_df["r_morn"].rolling(20).std().shift(1)
    opex_set = opex_dates_in(morn_df.index)

    trades = []
    for d, row in morn_df.iterrows():
        if d not in opex_set or d in roll_days or np.isnan(row["sigma20"]) or row["sigma20"] <= 0:
            continue
        if abs(row["r_morn"]) < 1.0 * row["sigma20"]:
            continue
        g = grouped[d]
        morn_part = g[(g["hm"] >= "09:30") & (g["hm"] <= "10:59")]
        aft_part = g[(g["hm"] >= "11:00") & (g["hm"] <= "15:55")]
        if morn_part.empty or aft_part.empty:
            continue
        direction = -1 if row["r_morn"] > 0 else 1
        entry = float(aft_part.iloc[0]["open"])
        buf = 0.5 * row["sigma20"] * row["p0930"]
        stop = (float(morn_part["high"].max()) + buf) if direction == -1 else (float(morn_part["low"].min()) - buf)

        exit_px = None
        reason = "close_1555"
        for _, bar in aft_part.iterrows():
            if direction == 1 and bar["low"] <= stop:
                exit_px = min(float(bar["open"]), stop)
                reason = "stop"
                break
            if direction == -1 and bar["high"] >= stop:
                exit_px = max(float(bar["open"]), stop)
                reason = "stop"
                break
        if exit_px is None:
            exit_px = float(aft_part.iloc[-1]["close"])
        trades.append({
            "date": d, "dir": direction, "entry": entry, "exit": exit_px,
            "gross": direction * (exit_px / entry - 1.0), "reason": reason,
        })

    tdf = pd.DataFrame(trades).set_index("date")
    pts = COST_INDEX[sym]
    res = {"trades_total": int(len(tdf)), "stop_rate": float((tdf["reason"] == "stop").mean()) if len(tdf) else 0.0}
    for lab, k in (("zero", 0.0), ("central", 1.0), ("pessimistic", 2.0)):
        ratio = tdf["exit"] / tdf["entry"]
        frac = k * pts / tdf["entry"]
        net = tdf["dir"] * (ratio - 1.0) - frac * (1.0 + ratio)
        res[lab] = summarize(net, 1e4)
    res["PASS"] = check_pass(res)

    # Reference 5A: Opex week long (prev Friday 15:55 -> 3rd Friday 15:55, same instrument_id)
    cl_rows = []
    for d in all_dates:
        g = grouped[d]
        g_hm = g.set_index("hm")
        if "15:55" in g_hm.index:
            cl_rows.append({"date": d, "close": float(g_hm.loc["15:55", "close"]), "iid": int(g_hm.loc["15:55", "instrument_id"])})
    cdf = pd.DataFrame(cl_rows).set_index("date")
    wk = cdf.groupby(cdf.index.to_period("W-FRI")).last()
    wk.index = wk.index.end_time.normalize()
    same_iid = wk["iid"].eq(wk["iid"].shift(1))
    wret = (wk["close"] / wk["close"].shift(1) - 1.0).where(same_iid)
    is_oe = pd.Series([third_friday(d) == d for d in wret.index], index=wret.index)
    w_ev = wret[(wret.index >= EVAL0) & (wret.index < EVAL1)].dropna()
    oe_ev = w_ev[is_oe.reindex(w_ev.index).fillna(False)]
    oth_ev = w_ev[~is_oe.reindex(w_ev.index).fillna(False)]
    res["REF_5A_opex_week"] = {
        "n_oe": int(len(oe_ev)),
        "oe_mean_bp_gross": float(oe_ev.mean() * 1e4),
        "other_mean_bp_gross": float(oth_ev.mean() * 1e4),
        "diff_bp": float((oe_ev.mean() - oth_ev.mean()) * 1e4),
        "oe_2012_21": float(oe_ev[oe_ev.index < SPLIT].mean() * 1e4),
        "oe_2022+": float(oe_ev[oe_ev.index >= SPLIT].mean() * 1e4),
    }
    return res


# -------------------- X1 (IBS) & X2 (DONCHIAN 1H) ON CL / ZN / 6E --------------------

def load_x1h(sym: str) -> pd.DataFrame:
    files = sorted((SRC / "x1h").glob("*.dbn.zst"))
    df = pd.concat(db.DBNStore.from_file(f).to_df() for f in files)
    df = df[df["symbol"] == sym].sort_index()
    df = df[~df.index.duplicated()]
    return df[["open", "high", "low", "close", "volume", "instrument_id"]]


def run_x1_ibs(root: str, h1: pd.DataFrame, cost_pts: float) -> dict:
    # Build NY RTH (09:30-16:00) daily bars from 1h (hours 09..15 NY)
    ny = h1.tz_convert("America/New_York")
    rth = ny[(ny.index.hour >= 9) & (ny.index.hour < 16) & (ny.index.dayofweek < 5)].copy()
    rth["_date"] = rth.index.normalize().tz_localize(None)
    daily = rth.groupby("_date").agg({
        "open": "first", "high": "max", "low": "min", "close": "last", "instrument_id": "last",
    }).dropna()
    daily.index = pd.DatetimeIndex(daily.index, name="date")

    rolls = set(daily.index[daily["instrument_id"].ne(daily["instrument_id"].shift())][1:])
    roll_ts = pd.to_datetime(sorted(rolls))
    tr = simulate_b7(daily[["open", "high", "low", "close"]])
    ent, ext = pd.to_datetime(tr["entry_time"]), pd.to_datetime(tr["exit_time"])
    spans = np.array([((roll_ts > a) & (roll_ts <= b)).any() for a, b in zip(ent, ext)])
    tr = tr[~spans].copy()
    idx = pd.to_datetime(tr["entry_time"])
    gross = pd.Series(tr["gross"].to_numpy(), idx)
    entry = pd.Series(tr["entry"].to_numpy(), idx)
    exit_p = pd.Series(tr["exit"].to_numpy(), idx)
    ratio = exit_p / entry

    res = {"trades_total": int(len(tr)), "dropped_roll_span": int(spans.sum())}
    for lab, k in (("zero", 0.0), ("central", 1.0), ("pessimistic", 2.0)):
        frac = k * cost_pts / entry
        net = (ratio - 1.0) - frac * (1.0 + ratio)
        res[lab] = summarize(net, 1e4)
    res["PASS"] = check_pass(res)
    return res


def run_x2_donchian(root: str, h1: pd.DataFrame, cost_pts: float) -> dict:
    df_utc = h1.copy()
    df_utc.index = df_utc.index.tz_convert("UTC").tz_localize(None)
    adj = back_adjust(df_utc)
    base = INSTRUMENTS["XAUUSD"]

    def _run_sim(cost_frac: float) -> pd.Series:
        inst = dataclasses.replace(base, cost_per_side=cost_frac)
        le, se, lsl, ltp, ssl, stp = build_signals(adj, DonchianCase(20))
        return simulate_trades(adj, le, se, lsl, ltp, ssl, stp, inst, min_rr=1.99, max_rr=2.0, max_hold=200)

    r0 = _run_sim(0.0)
    r1 = _run_sim(PROBE)
    if not r0.index.equals(r1.index):
        raise RuntimeError(f"X2_{root}: trade set changes with cost")
    entry_raw = adj["raw_close"].reindex(r0.index).to_numpy()
    per_frac = ((r0 - r1) / PROBE).to_numpy()

    res = {"trades_total": int(len(r0))}
    for lab, pts in (("zero", 0.0), ("central", cost_pts), ("pessimistic", 2.0 * cost_pts)):
        r_net = pd.Series(r0.to_numpy() - per_frac * pts / entry_raw, index=r0.index)
        res[lab] = summarize(r_net, 1.0)
    res["PASS"] = check_pass(res)
    return res


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    bbox = measure_bbox()
    res: dict = {"bbox_costs": bbox, "bonferroni_n": N_TESTS}

    for sym in ("NQ.c.0", "ES.c.0"):
        k = sym[:2]
        res[f"O1_{k}"] = run_o1_symbol(sym)

    for root in ("CL", "ZN", "6E"):
        h1 = load_x1h(f"{root}.v.0")
        c_pts = bbox[f"{root}.c.0"]["cost_side_pts"]
        res[f"X1_{root}"] = run_x1_ibs(root, h1, c_pts)
        res[f"X2_{root}"] = run_x2_donchian(root, h1, c_pts)

    (OUT / "opex_cross_result.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
    for k, v in res.items():
        if k in ("bbox_costs", "bonferroni_n"):
            continue
        c = v["central"]
        p = v["pessimistic"]
        z = v["zero"]
        print(
            f"{k:8s} n={c['n']:4d} zero={z['mean']:+7.3f} cen={c['mean']:+7.3f} "
            f"CI=[{c['ci_bonf'][0]:+7.3f},{c['ci_bonf'][1]:+7.3f}] "
            f"12-21={c['2012-21']:+7.3f} 22+={c['2022+']:+7.3f} 2x={p['mean']:+7.3f} "
            f"hold={c['holdout_mean']} PASS={v['PASS']}"
        )


if __name__ == "__main__":
    main()
