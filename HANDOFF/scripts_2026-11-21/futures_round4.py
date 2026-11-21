"""Round 4: real-volume rules B1/B2 on NQ and ES, and asset-class-neutral carry A1 on 23 futures.

Prereg: HANDOFF/futures_hacim_carry_onkayit_2026-11-21.md (commit 4348418).
Run from strategy-lab with the vectorbt-lab venv:
  python ../HANDOFF/scripts_2026-11-21/futures_round4.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import databento as db
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from futures_cost_retest import load_1m  # noqa: E402

SRC = Path("outputs/databento")
OUT = Path("outputs/intraday/futures_round4")
COST_PTS = {"NQ.c.0": 0.555, "ES.c.0": 0.247}
EVAL0, EVAL1, HOLD1, SPLIT = "2012-01-01", "2026-11-20", "2012-01-01", "2022-01-01"
SEED, REPS = 20261121, 10_000
Q_LO = 0.05 / 5 / 2
CLASSES = {"eq": ["ES", "NQ", "YM", "RTY"], "rates": ["ZN", "ZB", "ZF", "ZT"],
           "fx": ["6E", "6B", "6J", "6A", "6C", "6S"],
           "cmdty": ["CL", "BZ", "GC", "SI", "HG", "NG", "ZC", "ZS", "ZW"]}


# ---------------------------------------------------------------- B1 / B2
def rth_bars(m: pd.DataFrame, minutes: int) -> pd.DataFrame:
    """NY-time RTH bars (09:30-16:00) of given size; drops roll days and incomplete sessions."""
    ny = m.tz_convert("America/New_York") if m.index.tz is not None else m
    t = ny.index.hour * 60 + ny.index.minute
    ny = ny[(t >= 570) & (t < 960) & (ny.index.dayofweek < 5)]
    r = ny.resample(f"{minutes}min", label="left", closed="left")
    b = pd.DataFrame({"open": r["open"].first(), "high": r["high"].max(), "low": r["low"].min(),
                      "close": r["close"].last(), "volume": r["volume"].sum(),
                      "iid": r["instrument_id"].last()}).dropna(subset=["close"])
    b["date"] = b.index.strftime("%Y-%m-%d")
    b["slot"] = b.index.strftime("%H:%M")
    per_day = b.groupby("date")["close"].transform("size")
    b = b[per_day == 390 // minutes]
    day_iid = b.groupby("date")["iid"].last()
    rolls = set(day_iid.index[day_iid.ne(day_iid.shift())][1:])
    b["roll_day"] = b["date"].isin(rolls)
    return b


def slot_features(b: pd.DataFrame) -> pd.DataFrame:
    b = b.copy()
    b["ret"] = b["close"] / b["open"] - 1
    vol = b.pivot(index="date", columns="slot", values="volume")
    ret = b.pivot(index="date", columns="slot", values="ret")
    rvol = vol / vol.rolling(20).median().shift(1)
    sig = ret.rolling(20).std().shift(1)
    b["rvol"] = [rvol.at[d, s] for d, s in zip(b["date"], b["slot"])]
    b["sigma"] = [sig.at[d, s] for d, s in zip(b["date"], b["slot"])]
    return b


def simulate_rule(b: pd.DataFrame, rule: str) -> pd.DataFrame:
    rows = []
    for date, day in b.groupby("date", sort=True):
        if day["roll_day"].iat[0]:
            continue
        day = day.reset_index(drop=True)
        for i in range(len(day)):
            x = day.loc[i]
            if rule == "B1":
                if not ("09:45" <= x.slot <= "14:15") or not (x.rvol > 2.5 and abs(x.ret) > 0.75 * x.sigma):
                    continue
                rng = x.high - x.low
                if rng <= 0:
                    continue
                pos = (x.close - x.low) / rng
                d = 1 if pos >= 0.75 else (-1 if pos <= 0.25 else 0)
                if d == 0:
                    continue
                stop_dist, hold = 2.0 * rng, 4
            else:
                if not ("09:30" <= x.slot <= "14:00") or not (abs(x.ret) > 1.5 * x.sigma and x.rvol < 0.85):
                    continue
                d = -int(np.sign(x.ret))
                stop_dist, hold = 1.5 * abs(x.close - x.open), 1
                if stop_dist <= 0:
                    continue
            entry = x.close
            stop = entry - d * stop_dist
            exit_px = None
            for j in range(i + 1, i + 1 + hold):
                y = day.loc[j]
                if d == 1 and y.low <= stop:
                    exit_px = min(y.open, stop)
                elif d == -1 and y.high >= stop:
                    exit_px = max(y.open, stop)
                if exit_px is not None:
                    break
            if exit_px is None:
                exit_px = day.loc[i + hold, "close"]
            rows.append({"date": date, "dir": d, "entry": entry, "exit": float(exit_px)})
            break
    return pd.DataFrame(rows)


def boot_ci(x: np.ndarray, block: int = 1) -> list[float]:
    rng = np.random.default_rng(SEED)
    n = len(x)
    st = rng.integers(0, n, size=(REPS, (n + block - 1) // block))
    ix = ((st[:, :, None] + np.arange(block)) % n).reshape(REPS, -1)[:, :n]
    return np.quantile(x[ix].mean(axis=1), [Q_LO, 1 - Q_LO]).tolist()


def summarize(x: pd.Series, scale: float, block: int = 1) -> dict:
    ev = x[(x.index >= EVAL0) & (x.index < EVAL1)]
    ho = x[x.index < HOLD1]
    lo, hi = boot_ci(ev.to_numpy(), block) if len(ev) > 20 else (np.nan, np.nan)
    return {"n": int(len(ev)), "mean": float(ev.mean() * scale), "ci_bonf": [lo * scale, hi * scale],
            "2012-21": float(ev[ev.index < SPLIT].mean() * scale), "2022+": float(ev[ev.index >= SPLIT].mean() * scale),
            "holdout_mean": float(ho.mean() * scale) if len(ho) else None, "holdout_n": int(len(ho))}


def judge(res: dict) -> bool:
    c = res["central"]
    return bool(c["ci_bonf"][0] > 0 and c["2012-21"] > 0 and c["2022+"] > 0 and res["pessimistic"]["mean"] > 0)


def run_intraday(sym: str) -> dict:
    m = load_1m(sym)
    out = {}
    for rule, minutes in (("B1", 15), ("B2", 30)):
        b = slot_features(rth_bars(m, minutes))
        t = simulate_rule(b, rule).set_index("date")
        ratio = t["exit"] / t["entry"]
        res = {"trades": int(len(t)), "long_share": float((t["dir"] > 0).mean())}
        for label, k in (("zero", 0.0), ("central", 1.0), ("pessimistic", 2.0)):
            frac = k * COST_PTS[sym] / t["entry"]
            res[label] = summarize(t["dir"] * (ratio - 1) - frac * (1 + ratio), 1e4)
        res["PASS"] = judge(res)
        out[rule] = res
    return out


# ---------------------------------------------------------------- A1 carry
def load_daily(pattern: str, folder: str) -> pd.DataFrame:
    files = sorted((SRC / folder).rglob(pattern))
    return pd.concat(db.DBNStore.from_file(f).to_df() for f in files)


def carry_panel() -> dict[str, pd.DataFrame]:
    dv = load_daily("*.dbn.zst", "vdaily")             # prereg EK: volume-ranked v.0 / v.1
    d0 = dv[dv["symbol"].str.endswith(".v.0")]
    d1 = dv[dv["symbol"].str.endswith(".v.1")]
    defs = load_daily("*definition*.dbn.zst", "daily").drop_duplicates("instrument_id", keep="last")
    exp = defs.set_index("instrument_id")["expiration"].dt.tz_localize(None).dt.normalize()
    tick = defs.set_index("instrument_id")["min_price_increment"]
    panel = {}
    for name, df in (("P0", d0), ("P1", d1)):
        df = df.assign(root=df["symbol"].str.split(".").str[0], day=df.index.tz_localize(None).normalize())
        panel[name] = df.pivot_table(index="day", columns="root", values="close", aggfunc="last")
        panel["I" + name[1]] = df.pivot_table(index="day", columns="root", values="instrument_id", aggfunc="last")
    idx = panel["P0"].index
    for k in ("P1", "I1"):
        panel[k] = panel[k].reindex(idx)
    panel["E0"] = panel["I0"].apply(lambda s: s.map(exp))
    panel["E1"] = panel["I1"].apply(lambda s: s.map(exp))
    panel["TICK"] = panel["I0"].apply(lambda s: s.map(tick))
    return panel


def carry_returns(p: dict[str, pd.DataFrame]) -> tuple[pd.DataFrame, pd.DataFrame]:
    p0, p1, i0, i1 = p["P0"], p["P1"], p["I0"], p["I1"]
    same = i0.eq(i0.shift())
    rolled = i0.ne(i0.shift()) & i1.shift().eq(i0)
    r = (p0 / p0.shift() - 1).where(same, np.nan)
    r = r.where(~rolled, p0 / p1.shift() - 1)
    roll_flag = i0.ne(i0.shift()) & i0.shift().notna()
    return r.fillna(0.0), roll_flag


def run_carry() -> dict:
    p = carry_panel()
    r, roll_flag = carry_returns(p)
    dd = (p["E1"] - p["E0"]).apply(lambda s: s.dt.days)
    carry = (p["P0"] - p["P1"]) / p["P1"] * 365 / dd.where(dd != 0)   # prereg EK: negative gap kept
    sigma = r.rolling(60).std() * np.sqrt(252)
    s = carry / sigma
    cls = {root: c for c, roots in CLASSES.items() for root in roots}
    month_ends = r.groupby(r.index.to_period("M")).apply(lambda g: g.index.max()).tolist()
    cost_frac = (p["TICK"] / p["P0"]).ffill()
    rows, prev_w = [], pd.Series(dtype=float)
    for t0, t1 in zip(month_ends[:-1], month_ends[1:]):
        st = s.loc[t0].dropna()
        st = st[np.isfinite(st)]
        if len(st) < 10:
            continue
        st_dm = st - st.groupby(st.index.map(cls)).transform("mean")
        longs = st_dm[st_dm > 0].nlargest(5).index
        shorts = st_dm[st_dm < 0].nsmallest(5).index
        inv = 1 / sigma.loc[t0]
        w = pd.Series(0.0, index=st.index)
        if len(longs):
            w[longs] = 0.5 * inv[longs] / inv[longs].sum()
        if len(shorts):
            w[shorts] = -0.5 * inv[shorts] / inv[shorts].sum()
        window = r.loc[(r.index > t0) & (r.index <= t1), w.index]
        gross = float(((1 + window).prod() - 1).mul(w).sum())
        turnover = w.sub(prev_w.reindex(w.index).fillna(0.0)).abs()
        n_rolls = roll_flag.loc[(roll_flag.index > t0) & (roll_flag.index <= t1), w.index].sum()
        cf = cost_frac.loc[t0, w.index].fillna(cost_frac.loc[t0].median())
        cost = float((turnover * cf).sum() + (2 * n_rolls * w.abs() * cf).sum())
        rows.append({"month": str(t1.date()), "gross": gross, "cost": cost, "n_long": len(longs),
                     "n_short": len(shorts)})
        prev_w = w
    m = pd.DataFrame(rows).set_index("month")
    res = {"months": int(len(m))}
    for label, k in (("zero", 0.0), ("central", 1.0), ("pessimistic", 2.0)):
        net = m["gross"] - k * m["cost"]
        res[label] = summarize(net, 1e4, block=3)
        ev = net[(net.index >= EVAL0) & (net.index < EVAL1)]
        res[label]["ann_sr"] = float(ev.mean() / ev.std() * np.sqrt(12))
    res["PASS"] = judge(res)
    res["label"] = "cost not measured: 1 tick per side lower bound"
    return res


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    res = {"A1_CARRY": run_carry()}
    for sym in ("NQ.c.0", "ES.c.0"):
        res[sym] = run_intraday(sym)
    (OUT / "result.json").write_text(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
