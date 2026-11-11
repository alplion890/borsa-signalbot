"""Livestream 'prop firm system' test: first touch of a D-shaped naked daily POC on FX minors.

Preregistration: HANDOFF/naked_poc_minor_video_onkayit_2026-11-11.md (committed before run).
Tests only the key-level half; the closed synthetic-footprint confirmation cannot be reproduced.

    python -m intraday.naked_poc_video_lab
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from .config import INSTRUMENTS, Instrument
from .data import CACHE
from .honest_engine import metrics, simulate_trades
from .indicators import atr, calc_volume_profile_for_day

OUT = Path(__file__).resolve().parent.parent / "outputs" / "intraday" / "naked_poc_video"

MIN_DAY_BARS = 48
D_LOW, D_HIGH = 0.25, 0.75
VALID_DAYS = 20
CONFIRM_BARS = 4
STOP_ATR = 0.1
TARGETS = (1.5, 1.0)
PRIMARY_TARGET = 1.5
MAX_HOLD = 192

# Cost per side. EURJPY/GBPJPY from config; the rest are preregistered assumptions.
COST_ASSUMED = {"EURGBP": 0.00010, "AUDCAD": 0.00013, "NZDJPY": 0.00012,
                "AUDNZD": 0.00015, "EURNZD": 0.00015, "GBPNZD": 0.00018}
PAIRS = ("EURGBP", "AUDNZD", "AUDCAD", "EURNZD", "GBPNZD", "NZDJPY", "EURJPY", "GBPJPY")


@dataclass(frozen=True)
class Level:
    day_end: pd.Timestamp     # first bar after the profile day may touch it
    poc: float


def instrument(sym: str, cost_mult: float = 1.0) -> Instrument:
    if sym in INSTRUMENTS:
        base = INSTRUMENTS[sym]
        return Instrument(base.key, base.duka, base.cost_per_side * cost_mult, base.session_utc, base.pip)
    return Instrument(sym, "", COST_ASSUMED[sym] * cost_mult, (0, 24), 0.0001)


def load(sym: str) -> pd.DataFrame:
    """Maven MT5 M15 export (broker server time, tick volume); see preregistration deviation note."""
    df = pd.read_csv(CACHE / f"{sym}_15m_maven.csv", parse_dates=["timestamp"]).set_index("timestamp")
    return df[["open", "high", "low", "close", "volume"]].astype(float).sort_index()


def d_shaped_levels(df: pd.DataFrame) -> list[Level]:
    """Daily POCs whose location sits in the middle half of the day's range."""
    out = []
    for _, g in df.groupby(df.index.date):
        if len(g) < MIN_DAY_BARS:
            continue
        _, _, poc = calc_volume_profile_for_day(g)
        lo, hi = g["low"].min(), g["high"].max()
        if not np.isfinite(poc) or hi <= lo:
            continue
        pos = (poc - lo) / (hi - lo)
        if D_LOW <= pos <= D_HIGH:
            out.append(Level(g.index[-1], float(poc)))
    return out


def signals(df: pd.DataFrame, target_r: float) -> dict:
    """First touch of each naked level, then a close-back confirmation within CONFIRM_BARS."""
    n = len(df)
    idx = df.index
    o_high, o_low, o_close = (df[c].to_numpy(dtype=float) for c in ("high", "low", "close"))
    a = atr(df, 14).to_numpy()
    le, se = np.zeros(n, bool), np.zeros(n, bool)
    lsl, ltp, ssl, stp = (np.full(n, np.nan) for _ in range(4))
    pos_of = {t: k for k, t in enumerate(idx)}
    for lv in d_shaped_levels(df):
        start = pos_of[lv.day_end] + 1
        if start >= n:
            continue
        stop_at = idx[start] + pd.Timedelta(days=VALID_DAYS * 7 / 5)
        end = min(n, int(np.searchsorted(idx.to_numpy(), stop_at.to_datetime64())))
        seg = np.flatnonzero((o_low[start:end] <= lv.poc) & (o_high[start:end] >= lv.poc))
        if not len(seg):
            continue
        i = start + int(seg[0])
        if i < 1 or not np.isfinite(a[i]):
            continue
        long_side = o_close[i - 1] > lv.poc
        for j in range(i, min(i + CONFIRM_BARS + 1, n)):
            if j < 1:
                continue
            if long_side and o_close[j] > lv.poc and o_close[j] > o_high[j - 1]:
                sl = o_low[i:j + 1].min() - STOP_ATR * a[j]
                if sl < o_close[j] and not (le[j] or se[j]):
                    le[j], lsl[j] = True, sl
                    ltp[j] = o_close[j] + target_r * (o_close[j] - sl)
                break
            if not long_side and o_close[j] < lv.poc and o_close[j] < o_low[j - 1]:
                sl = o_high[i:j + 1].max() + STOP_ATR * a[j]
                if sl > o_close[j] and not (le[j] or se[j]):
                    se[j], ssl[j] = True, sl
                    stp[j] = o_close[j] - target_r * (sl - o_close[j])
                break
    s = lambda x: pd.Series(x, index=idx)
    return {"le": s(le), "se": s(se), "lsl": s(lsl), "ltp": s(ltp), "ssl": s(ssl), "stp": s(stp)}


def run(df: pd.DataFrame, sig: dict, sym: str, cost_mult: float = 1.0) -> pd.Series:
    return simulate_trades(df, sig["le"], sig["se"], sig["lsl"], sig["ltp"], sig["ssl"], sig["stp"],
                           instrument(sym, cost_mult), min_rr=0.5, max_rr=20.0, max_hold=MAX_HOLD)


def _halves(r: pd.Series, t0: pd.Timestamp, t1: pd.Timestamp) -> tuple[float, float]:
    mid = t0 + (t1 - t0) / 2
    f = lambda x: round(float(x.mean()), 3) if len(x) else float("nan")
    return f(r[r.index < mid]), f(r[r.index >= mid])


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    rows, pooled = [], {t: {1.0: [], 2.0: [], 0.0: []} for t in TARGETS}
    t0, t1 = None, None
    for sym in PAIRS:
        df = load(sym)
        t0 = df.index[0] if t0 is None else min(t0, df.index[0])
        t1 = df.index[-1] if t1 is None else max(t1, df.index[-1])
        for tr in TARGETS:
            sig = signals(df, tr)
            res = {cm: run(df, sig, sym, cm) for cm in (1.0, 2.0, 0.0)}
            for cm, r in res.items():
                pooled[tr][cm].append(r)
            m = metrics(res[1.0])
            h1, h2 = _halves(res[1.0], df.index[0], df.index[-1])
            rows.append({"sym": sym, "target": tr, "n": m["trades"], "exp_r": m["exp_r"], "wr": m["win_rate"],
                         "pf": m["pf"], "exp_r_2x": metrics(res[2.0])["exp_r"],
                         "exp_r_0x": metrics(res[0.0])["exp_r"], "wr_0x": metrics(res[0.0])["win_rate"],
                         "half1": h1, "half2": h2,
                         "long_n": int(sig["le"].sum()), "short_n": int(sig["se"].sum())})
    res_df = pd.DataFrame(rows)
    summary = {}
    for tr in TARGETS:
        r1 = pd.concat(pooled[tr][1.0]).sort_index()
        m = metrics(r1)
        h1, h2 = _halves(r1, t0, t1)
        pos = int((res_df[res_df.target == tr].exp_r > 0).sum())
        summary[tr] = {"n": m["trades"], "exp_r": m["exp_r"], "wr": m["win_rate"], "pf": m["pf"],
                       "exp_r_2x": metrics(pd.concat(pooled[tr][2.0]))["exp_r"],
                       "exp_r_0x": metrics(pd.concat(pooled[tr][0.0]))["exp_r"],
                       "wr_0x": metrics(pd.concat(pooled[tr][0.0]))["win_rate"],
                       "half1": h1, "half2": h2, "pairs_positive": f"{pos}/{len(PAIRS)}"}
    p = summary[PRIMARY_TARGET]
    cand = (p["n"] >= 30 and p["exp_r"] > 0 and p["exp_r_2x"] > 0 and p["half1"] > 0 and p["half2"] > 0
            and int(p["pairs_positive"].split("/")[0]) >= 5)
    verdict = "SEVIYE ADAY" if cand else "SEVIYE ELENDI"
    res_df.to_csv(OUT / "result_2026-11-11.csv", index=False)
    (OUT / "result_2026-11-11.json").write_text(json.dumps(
        {"verdict": verdict, "pooled": {str(k): v for k, v in summary.items()}, "rows": rows}, indent=1),
        encoding="utf8")
    with pd.option_context("display.width", 220, "display.max_columns", 20):
        print(res_df.to_string(index=False))
    for tr, v in summary.items():
        print(f"BIRLESIK {tr}R:", v)
    print("KARAR (on-kayit):", verdict)


if __name__ == "__main__":
    main()
