"""Internetten bilinen strateji ailelerini bizim honest engine ile tekrar test.

Seed stratejiler:
  1. Opening Range Breakout (ORB): ilk 5/15/30/60 dk range, breakout entry.
     Kaynak aile: ORB, index futures/stocks icin yaygin mekanik sistem.
  2. London Breakout: Asya/Londra-oncesi range, Londra acilis breakout.
     Kaynak aile: EURUSD/GBPUSD icin yaygin FX session breakout sistemi.

Amaç: "sifirdan icat" yerine populer/backtest edilmis fikirleri alip ayni veri,
ayni maliyet ve ayni muhafazakar fill modeliyle elemek.

Calistir:
    python -m intraday.internet_seed_strategies
"""
from __future__ import annotations

import sys
import warnings
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from . import data
from .config import INSTRUMENTS, ATR_LEN
from .honest_engine import metrics, oos_metrics, simulate_trades
from .indicators import atr, ema
try:
    from .walkforward import _folds
except ModuleNotFoundError:
    _folds = None

OUT = Path(__file__).resolve().parent.parent / "outputs" / "intraday"
OUT.mkdir(parents=True, exist_ok=True)


@dataclass(frozen=True)
class ORBCase:
    symbol: str
    open_hour: float
    range_minutes: int
    trade_end_hour: float
    entry_mode: str       # close | retest
    trend_filter: str     # none | ema | vwap
    rr: float
    sl_mode: str          # other_side | half_range | atr
    atr_mult: float
    max_hold: int


@dataclass(frozen=True)
class LondonCase:
    symbol: str
    range_start: float
    range_end: float
    trade_end: float
    trend_filter: str     # none | ema
    rr: float
    sl_mode: str          # other_side | half_range | atr
    atr_mult: float
    max_hold: int


def _hour_float(index: pd.DatetimeIndex) -> np.ndarray:
    return index.hour.to_numpy() + index.minute.to_numpy() / 60.0


def _daily_vwap(df: pd.DataFrame) -> pd.Series:
    hlc3 = (df["high"] + df["low"] + df["close"]) / 3
    day = pd.Index(df.index.date)
    vol = df["volume"].clip(lower=1e-9)
    return (hlc3 * vol).groupby(day).cumsum() / vol.groupby(day).cumsum()


def _range_by_clock(df: pd.DataFrame, start_h: float, end_h: float) -> tuple[pd.Series, pd.Series]:
    h = _hour_float(df.index)
    if start_h <= end_h:
        mask = (h >= start_h) & (h < end_h)
    else:
        mask = (h >= start_h) | (h < end_h)
    day = pd.Index(df.index.date)
    hi = df["high"].where(mask).groupby(day).transform("max").ffill()
    lo = df["low"].where(mask).groupby(day).transform("min").ffill()
    return hi, lo


def _one_signal_per_day(raw: pd.Series) -> pd.Series:
    """Gunun ilk True barini birak (vektorize, gunluk cumsum==1)."""
    r = raw.fillna(False).astype(bool)
    day = pd.Index(r.index.date)
    first = r & (r.groupby(day).cumsum() == 1)
    return first


def _build_orb(df: pd.DataFrame, case: ORBCase) -> tuple:
    h = _hour_float(df.index)
    range_end = case.open_hour + case.range_minutes / 60.0
    or_hi, or_lo = _range_by_clock(df, case.open_hour, range_end)
    trade_window = (h >= range_end) & (h < case.trade_end_hour)
    a = atr(df, ATR_LEN)
    vwap = _daily_vwap(df)
    e20 = ema(df["close"], 20)
    e50 = ema(df["close"], 50)

    long_raw = trade_window & (df["close"] > or_hi) & (df["close"].shift(1) <= or_hi.shift(1))
    short_raw = trade_window & (df["close"] < or_lo) & (df["close"].shift(1) >= or_lo.shift(1))

    if case.entry_mode == "retest":
        broke_up = (df["close"] > or_hi).groupby(pd.Index(df.index.date)).cummax()
        broke_dn = (df["close"] < or_lo).groupby(pd.Index(df.index.date)).cummax()
        long_raw = trade_window & broke_up & (df["low"] <= or_hi) & (df["close"] > or_hi)
        short_raw = trade_window & broke_dn & (df["high"] >= or_lo) & (df["close"] < or_lo)

    if case.trend_filter == "ema":
        long_raw &= e20 > e50
        short_raw &= e20 < e50
    elif case.trend_filter == "vwap":
        long_raw &= df["close"] > vwap
        short_raw &= df["close"] < vwap

    le = _one_signal_per_day(long_raw)
    se = _one_signal_per_day(short_raw & ~le)
    entry = df["close"]
    rng = (or_hi - or_lo).clip(lower=1e-9)

    if case.sl_mode == "other_side":
        long_sl = or_lo.where(le)
        short_sl = or_hi.where(se)
    elif case.sl_mode == "half_range":
        long_sl = (entry - 0.5 * rng).where(le)
        short_sl = (entry + 0.5 * rng).where(se)
    else:
        long_sl = (entry - case.atr_mult * a).where(le)
        short_sl = (entry + case.atr_mult * a).where(se)

    long_risk = entry - long_sl
    short_risk = short_sl - entry
    long_tp = (entry + case.rr * long_risk).where(le)
    short_tp = (entry - case.rr * short_risk).where(se)
    return le, se, long_sl, long_tp, short_sl, short_tp


def _build_london(df: pd.DataFrame, case: LondonCase) -> tuple:
    h = _hour_float(df.index)
    hi, lo = _range_by_clock(df, case.range_start, case.range_end)
    trade_window = (h >= case.range_end) & (h < case.trade_end)
    a = atr(df, ATR_LEN)
    e20 = ema(df["close"], 20)
    e50 = ema(df["close"], 50)

    long_raw = trade_window & (df["close"] > hi) & (df["close"].shift(1) <= hi.shift(1))
    short_raw = trade_window & (df["close"] < lo) & (df["close"].shift(1) >= lo.shift(1))
    if case.trend_filter == "ema":
        long_raw &= e20 > e50
        short_raw &= e20 < e50

    le = _one_signal_per_day(long_raw)
    se = _one_signal_per_day(short_raw & ~le)
    entry = df["close"]
    rng = (hi - lo).clip(lower=1e-9)

    if case.sl_mode == "other_side":
        long_sl = lo.where(le)
        short_sl = hi.where(se)
    elif case.sl_mode == "half_range":
        long_sl = (entry - 0.5 * rng).where(le)
        short_sl = (entry + 0.5 * rng).where(se)
    else:
        long_sl = (entry - case.atr_mult * a).where(le)
        short_sl = (entry + case.atr_mult * a).where(se)

    long_risk = entry - long_sl
    short_risk = short_sl - entry
    long_tp = (entry + case.rr * long_risk).where(le)
    short_tp = (entry - case.rr * short_risk).where(se)
    return le, se, long_sl, long_tp, short_sl, short_tp


def run_orb(case: ORBCase, days: int = 1080) -> tuple[dict, pd.Series]:
    df = data.load_ohlcv(case.symbol, "5m", days)
    sig = _build_orb(df, case)
    r = simulate_trades(
        df, *sig, INSTRUMENTS[case.symbol],
        min_rr=max(1.0, case.rr - 0.01), max_rr=case.rr, max_hold=case.max_hold
    )
    return _row("orb", case.symbol, case, df, r), r


def run_london(case: LondonCase, days: int = 1080) -> tuple[dict, pd.Series]:
    df = data.load_ohlcv(case.symbol, "5m", days)
    sig = _build_london(df, case)
    r = simulate_trades(
        df, *sig, INSTRUMENTS[case.symbol],
        min_rr=max(1.0, case.rr - 0.01), max_rr=case.rr, max_hold=case.max_hold
    )
    return _row("london_breakout", case.symbol, case, df, r), r


def _row(kind: str, symbol: str, case, df: pd.DataFrame, r: pd.Series) -> dict:
    m = metrics(r)
    folds = _folds(df.index) if _folds is not None else []
    o = oos_metrics(r, folds) if folds else {"oos_exp_r": np.nan, "pos_folds": "0/0", "total_R": float(r.sum())}
    weeks = max((df.index[-1] - df.index[0]).days / 7, 1e-9)
    d = {"kind": kind, "symbol": symbol, **case.__dict__}
    d.update({
        "trades": m["trades"],
        "trades_per_week": round(m["trades"] / weeks, 3),
        "exp_r": m["exp_r"],
        "win_rate": m["win_rate"],
        "pf": m["pf"],
        "oos_exp_r": o.get("oos_exp_r"),
        "pos_folds": o.get("pos_folds"),
        "total_R": o.get("total_R"),
        "score": _score(m, o, m["trades"] / weeks),
        "data_start": str(df.index[0]),
        "data_end": str(df.index[-1]),
    })
    return d


def _score(m: dict, o: dict, tpw: float) -> float:
    exp = float(m["exp_r"]) if pd.notna(m["exp_r"]) else -9
    oos = float(o.get("oos_exp_r", np.nan)) if pd.notna(o.get("oos_exp_r", np.nan)) else -9
    pf = float(m["pf"]) if np.isfinite(float(m["pf"])) else 3.0
    freq_target = -abs(tpw - 5.0) * 0.08
    return round(exp * 1.0 + oos * 1.5 + min(pf, 3.0) * 0.3 + freq_target, 4)


def orb_cases(symbol: str = "NASDAQ100") -> list[ORBCase]:
    cases = []
    for open_h in (13.5, 14.5):
        for mins in (5, 15, 30, 60):
            for entry in ("close", "retest"):
                for trend in ("none", "ema", "vwap"):
                    for rr in (1.0, 1.2, 1.5, 2.0):
                        for sl in ("other_side", "half_range", "atr"):
                            for hold in (12, 24, 48):
                                cases.append(ORBCase(symbol, open_h, mins, 20.5, entry, trend, rr, sl, 1.0, hold))
    return cases


def london_cases(symbol: str) -> list[LondonCase]:
    cases = []
    for r0, r1, tend in ((0.0, 7.0, 11.0), (2.0, 7.0, 11.0), (0.0, 8.0, 12.0), (6.0, 8.0, 12.0)):
        for trend in ("none", "ema"):
            for rr in (1.0, 1.2, 1.5, 2.0):
                for sl in ("other_side", "half_range", "atr"):
                    for hold in (12, 24, 48):
                        cases.append(LondonCase(symbol, r0, r1, tend, trend, rr, sl, 1.0, hold))
    return cases


def main(days: int = 1080) -> None:
    print(f"\n{'='*104}")
    print("  INTERNET SEED STRATEGIES | ORB + London Breakout | honest_engine")
    print(f"  days={days}")
    print(f"{'='*104}\n")

    rows = []
    for case in orb_cases("NASDAQ100"):
        row, _ = run_orb(case, days)
        rows.append(row)
    for symbol in ("EURUSD", "GBPUSD"):
        for case in london_cases(symbol):
            row, _ = run_london(case, days)
            rows.append(row)

    res = pd.DataFrame(rows).sort_values("score", ascending=False)
    out = OUT / "internet_seed_strategies_results.csv"
    res.to_csv(out, index=False)

    print(f"  CSV: {out}")
    cols = [
        "kind", "symbol", "trades", "trades_per_week", "exp_r", "win_rate",
        "pf", "oos_exp_r", "pos_folds", "total_R", "score",
    ]
    print(f"\n{'-'*104}")
    print("  TOP 30 OVERALL")
    print(f"{'-'*104}")
    print(res.head(30)[cols].to_string(index=False))

    print(f"\n{'-'*104}")
    print("  TOP BY SYMBOL")
    print(f"{'-'*104}")
    for symbol in ("NASDAQ100", "EURUSD", "GBPUSD"):
        sub = res[res["symbol"] == symbol].head(12)
        print(f"\n{symbol}")
        print(sub[cols + ["open_hour", "range_minutes", "range_start", "range_end", "entry_mode", "trend_filter", "rr", "sl_mode", "max_hold"]].to_string(index=False))

    freq_ok = res[
        (res["trades_per_week"] >= 4)
        & (res["trades_per_week"] <= 7)
        & (res["exp_r"] > 0)
        & (res["oos_exp_r"] > 0)
        & (res["pf"] > 1.05)
    ]
    print(f"\n{'='*104}")
    print(f"  Haftada 4-7 trade + pozitif OOS ön eleme: {len(freq_ok)} case")
    if not freq_ok.empty:
        print(freq_ok.head(30).to_string(index=False))
    print(f"{'='*104}\n")


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("--days", type=int, default=1080)
    args = p.parse_args()
    main(args.days)
