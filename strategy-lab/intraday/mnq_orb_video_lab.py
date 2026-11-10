"""Instagram '$20K/month' MNQ ORB test: 9:15-9:30 NY range, 15m close break, 0.5R target.

Preregistration: HANDOFF/mnq_orb_15m_halfR_video_onkayit_2026-11-10.md (committed before run).
Uses sweep_prop_lab.simulate (honest_engine parity) with a force-exit mask for 16:00 ET flat.

    python -m intraday.mnq_orb_video_lab
"""
from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import numpy as np
import pandas as pd

from .config import INSTRUMENTS
from .data import load_ohlcv
from .data_quality import clean
from .history_fetch import load_history
from .honest_engine import metrics
from .sweep_prop_lab import simulate

OUT = Path(__file__).resolve().parent.parent / "outputs" / "intraday" / "mnq_orb_video"
TARGET_R = 0.5
RANGE_BAR = "09:15"
FIRST_ENTRY, LAST_ENTRY = "09:30", "15:45"
FLAT_FROM = "15:45"     # bar opening 15:45 closes at 16:00 ET
MAX_HOLD = 480


def _et_clock(idx: pd.DatetimeIndex) -> tuple[pd.Index, pd.Index]:
    et = idx.tz_localize("UTC").tz_convert("America/New_York")
    return pd.Index(et.date), pd.Index(et.strftime("%H:%M"))


def signals(df: pd.DataFrame) -> dict:
    """First 15m close outside the 9:15 ET bar range, one per ET day."""
    day, hm = _et_clock(df.index)
    n = len(df)
    le, se = np.zeros(n, bool), np.zeros(n, bool)
    close, high, low = (df[c].to_numpy(dtype=float) for c in ("close", "high", "low"))
    lsl, ssl = np.full(n, np.nan), np.full(n, np.nan)
    ltp, stp = np.full(n, np.nan), np.full(n, np.nan)
    hm_arr, day_arr = hm.to_numpy(), day.to_numpy()
    rng = {d: i for i, (d, t) in enumerate(zip(day_arr, hm_arr)) if t == RANGE_BAR}
    window = (hm_arr >= FIRST_ENTRY) & (hm_arr <= LAST_ENTRY)
    taken: set = set()
    for i in np.flatnonzero(window):
        d = day_arr[i]
        if d in taken or d not in rng:
            continue
        r = rng[d]
        rh, rl = high[r], low[r]
        if close[i] > rh:
            le[i] = True
            lsl[i] = low[i]
            ltp[i] = close[i] + TARGET_R * (close[i] - low[i])
            taken.add(d)
        elif close[i] < rl:
            se[i] = True
            ssl[i] = high[i]
            stp[i] = close[i] - TARGET_R * (high[i] - close[i])
            taken.add(d)
    s = lambda a: pd.Series(a, index=df.index)
    flat = s((hm_arr >= FLAT_FROM) | (np.r_[day_arr[1:] != day_arr[:-1], True]))
    return {"le": s(le), "se": s(se), "lsl": s(lsl), "ltp": s(ltp), "ssl": s(ssl), "stp": s(stp),
            "flat": flat}


def run(df: pd.DataFrame, sig: dict, cost_mult: float = 1.0, eod: bool = True,
        side: str = "both") -> pd.Series:
    base = INSTRUMENTS["NASDAQ100"]
    inst = replace(base, cost_per_side=base.cost_per_side * cost_mult)
    le, se = sig["le"], sig["se"]
    if side == "long":
        se = se & False
    elif side == "short":
        le = le & False
    return simulate(df, le, se, sig["lsl"], sig["ltp"], sig["ssl"], sig["stp"], inst,
                    0.01, 20.0, MAX_HOLD, force_exit=sig["flat"] if eod else None)


def _row(name: str, df: pd.DataFrame, sig: dict) -> dict:
    r1 = run(df, sig)
    mid = df.index[0] + (df.index[-1] - df.index[0]) / 2
    half = lambda x: round(float(x.mean()), 3) if len(x) else float("nan")
    m = metrics(r1)
    row = {"data": name, "start": str(df.index[0].date()), "end": str(df.index[-1].date()),
           "n": m["trades"], "exp_r": m["exp_r"], "wr": m["win_rate"], "pf": m["pf"],
           "avg_win": m["avg_win"], "avg_loss": m["avg_loss"], "sum_r": round(float(r1.sum()), 1),
           "exp_r_2x": metrics(run(df, sig, 2.0))["exp_r"],
           "exp_r_0x": metrics(run(df, sig, 0.0))["exp_r"],
           "wr_0x": metrics(run(df, sig, 0.0))["win_rate"],
           "exp_r_no_eod": metrics(run(df, sig, eod=False))["exp_r"],
           "half1": half(r1[r1.index < mid]), "half2": half(r1[r1.index >= mid]),
           "long_exp_r": metrics(run(df, sig, side="long"))["exp_r"],
           "short_exp_r": metrics(run(df, sig, side="short"))["exp_r"]}
    yearly = r1.groupby(r1.index.year).agg(["count", "mean"]).round(3)
    row["yearly"] = {int(y): [int(c), float(v)] for y, (c, v) in yearly.iterrows()}
    row["candidate"] = bool(row["n"] >= 30 and row["exp_r"] > 0 and row["exp_r_2x"] > 0
                            and row["half1"] > 0 and row["half2"] > 0)
    return row


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    prim = load_ohlcv("NASDAQ100", "15m", 1825)
    long = clean(load_history("NASDAQ100", "15m", start_year=2012))
    rows = [_row("primary_2021_2026", prim, signals(prim)), _row("long_2012_plus", long, signals(long))]
    verdict = "ADAY" if rows[0]["candidate"] else "ELENDI"
    (OUT / "result_2026-11-10.json").write_text(json.dumps({"verdict": verdict, "rows": rows}, indent=1),
                                               encoding="utf8")
    for r in rows:
        print({k: v for k, v in r.items() if k != "yearly"})
        print("  yillik:", r["yearly"])
    print("KARAR (on-kayit):", verdict)


if __name__ == "__main__":
    main()
