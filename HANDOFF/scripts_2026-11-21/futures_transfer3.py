"""Third futures transfer retest: Sweep NQ (T1), Donchian GC N=20 (T2), Sweep RTY (T3).

Prereg: HANDOFF/futures_tasima3_onkayit_2026-11-21.md (commit d4efb82). Engines imported unchanged.
Run from strategy-lab with the vectorbt-lab venv:
  python ../HANDOFF/scripts_2026-11-21/futures_transfer3.py
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
from intraday.config import INSTRUMENTS  # noqa: E402
from intraday.donchian_xau_lab import DonchianCase, build_signals  # noqa: E402
from intraday.honest_engine import simulate_trades  # noqa: E402
from intraday.long_history_ab import _atr_rank, _sweep_build  # noqa: E402

SRC = Path("outputs/databento")
OUT = Path("outputs/intraday/futures_transfer3")
PROFILE = Path("outputs/intraday/mt5_bridge/reality_profile.csv")
COMMISSION_SIDE_USD = 0.61
MNQ_COST_PTS = 0.555                     # measured in futures_cost_retest (bbo-1m + commission)
EVAL0, EVAL1, HOLD1, SPLIT = "2012-01-01", "2026-11-20", "2012-01-01", "2022-01-01"
SEED, REPS = 20261121, 10_000
Q_LO = 0.05 / 3 / 2
PROBE = 1e-4


def load_1m(folder: str, sym: str) -> pd.DataFrame:
    files = sorted((SRC / folder).glob("*.dbn.zst"))
    df = pd.concat(db.DBNStore.from_file(f).to_df() for f in files)
    df = df[df["symbol"] == sym].sort_index()
    df = df[~df.index.duplicated()]
    df.index = df.index.tz_convert("UTC").tz_localize(None)
    return df[["open", "high", "low", "close", "volume", "instrument_id"]]


def back_adjust(m: pd.DataFrame) -> pd.DataFrame:
    """Ratio back-adjust at every instrument_id change between consecutive 1m bars."""
    roll = m["instrument_id"].ne(m["instrument_id"].shift()) & m["instrument_id"].shift().notna()
    ratio = (m["close"] / m["close"].shift()).where(roll, 1.0)
    # factor for bar t = product of ratios of all rolls strictly after t
    factor = ratio[::-1].cumprod()[::-1].shift(-1).fillna(1.0)
    adj = m.copy()
    for c in ("open", "high", "low", "close"):
        adj[c] = m[c] * factor
    adj["raw_close"] = m["close"]
    return adj


def resample(m: pd.DataFrame, rule: str) -> pd.DataFrame:
    r = m.resample(rule, label="left", closed="left")
    out = pd.DataFrame({"open": r["open"].first(), "high": r["high"].max(), "low": r["low"].min(),
                        "close": r["close"].last(), "volume": r["volume"].sum(), "raw_close": r["raw_close"].last()})
    return out.dropna(subset=["close"])


def half_spread_pts(sym: str) -> dict:
    files = sorted((SRC / "bbomicro").glob("*.dbn.zst"))
    q = pd.concat(db.DBNStore.from_file(f).to_df() for f in files)
    q = q[q["symbol"] == sym]
    hs_all = ((q["ask_px_00"] - q["bid_px_00"]) / 2)
    hs_all = hs_all[hs_all > 0]
    ny = q.index.tz_convert("America/New_York")
    mins = ny.hour * 60 + ny.minute
    rth = (mins >= 570) & (mins < 960) & (ny.dayofweek < 5)
    hs = ((q["ask_px_00"] - q["bid_px_00"]) / 2)[rth]
    hs = hs[hs > 0]
    return {"median_rth": float(hs.median()), "median_all": float(hs_all.median()), "n": int(len(hs)),
            "from": str(q.index.min().date()), "to": str(q.index.max().date())}


def sweep_r(df: pd.DataFrame, inst) -> pd.Series:
    le, se, lsl, ltp, ssl, stp = _sweep_build(df)
    rank = _atr_rank(df)
    parts = []
    for mask, max_rr in ((rank < 0.33, 4.0), ((rank >= 0.33) & (rank < 0.67), 6.0), (rank >= 0.67, 8.0)):
        r = simulate_trades(df, le & mask, se & mask, lsl, ltp, ssl, stp, inst,
                            min_rr=2.0, max_rr=max_rr, max_hold=480)
        if len(r):
            parts.append(r)
    return pd.concat(parts).sort_index() if parts else pd.Series(dtype=float)


def donchian_r(df: pd.DataFrame, inst) -> pd.Series:
    le, se, lsl, ltp, ssl, stp = build_signals(df, DonchianCase(20))
    return simulate_trades(df, le, se, lsl, ltp, ssl, stp, inst, min_rr=1.99, max_rr=2.0, max_hold=200)


def boot_ci(x: np.ndarray) -> list[float]:
    rng = np.random.default_rng(SEED)
    m = x[rng.integers(0, len(x), size=(REPS, len(x)))].mean(axis=1)
    return np.quantile(m, [Q_LO, 1 - Q_LO]).tolist()


def summarize(r: pd.Series) -> dict:
    ev = r[(r.index >= EVAL0) & (r.index < EVAL1)]
    ho = r[r.index < HOLD1]
    return {"n": int(len(ev)), "mean_R": float(ev.mean()), "ci_bonf": boot_ci(ev.to_numpy()),
            "2012-21": float(ev[ev.index < SPLIT].mean()), "2022+": float(ev[ev.index >= SPLIT].mean()),
            "holdout_mean_R": float(ho.mean()) if len(ho) else None, "holdout_n": int(len(ho))}


def run(name: str, df: pd.DataFrame, cfd_key: str, cost_pts: float, maven: float, fn) -> dict:
    base = INSTRUMENTS[cfd_key]
    r0 = fn(df, dataclasses.replace(base, cost_per_side=0.0))
    r1 = fn(df, dataclasses.replace(base, cost_per_side=PROBE))
    rm = fn(df, dataclasses.replace(base, cost_per_side=maven))
    if not (r0.index.equals(r1.index) and r0.index.equals(rm.index)):
        raise RuntimeError(f"{name}: trade set changes with cost; points conversion invalid")
    entry_raw = df["raw_close"].reindex(r0.index).to_numpy()
    per_frac = ((r0 - r1) / PROBE).to_numpy()          # = 2 * entry_adj / risk
    out = {"trades_total": int(len(r0))}
    for label, pts in (("zero", 0.0), ("central", cost_pts), ("pessimistic", 2 * cost_pts)):
        out[label] = summarize(r0 - per_frac * pts / entry_raw)
    out["maven_cfd"] = summarize(rm)
    c = out["central"]
    out["PASS"] = bool(c["ci_bonf"][0] > 0 and c["2012-21"] > 0 and c["2022+"] > 0
                       and out["pessimistic"]["mean_R"] > 0)
    return out


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    prof = pd.read_csv(PROFILE).set_index("symbol")["real_cost_per_side_central"]
    res = {"commission_side_usd": COMMISSION_SIDE_USD, "mnq_cost_pts": MNQ_COST_PTS}
    cost = {"NQ": MNQ_COST_PTS}
    for micro, root, mult in (("MGC", "GC", 10.0), ("M2K", "RTY", 5.0)):
        hs = half_spread_pts(f"{micro}.c.0")
        res[f"spread_{micro}"] = hs
        cost[root] = hs["median_rth"] + COMMISSION_SIDE_USD / mult
        res[f"cost_side_pts_{micro}"] = cost[root]
    nq = resample(back_adjust(load_1m("nq1m", "NQ.c.0")), "15min")
    res["T1_SWEEP_NQ"] = run("T1", nq, "NASDAQ100", cost["NQ"], float(prof["NASDAQ100"]), sweep_r)
    gc = resample(back_adjust(load_1m("gc1h", "GC.v.0")), "1h")   # prereg EK: volume-ranked 1h
    res["T2_DONCHIAN_GC"] = run("T2", gc, "XAUUSD", cost["GC"], float(prof["XAUUSD"]), donchian_r)
    rty = resample(back_adjust(load_1m("rty1m", "RTY.c.0")), "15min")
    us2000 = "US2000" if "US2000" in INSTRUMENTS else "NASDAQ100"
    res["T3_SWEEP_RTY"] = run("T3", rty, us2000, cost["RTY"], float(prof["US2000"]), sweep_r)
    (OUT / "result.json").write_text(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
