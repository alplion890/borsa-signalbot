"""Gold: makro rejim + 1s trend + 5d likidite sweep edge aramasi.

Iki onceden tanimli giris ailesi:
1) onceki gun high/low sweep ve geri alis,
2) 07:00-13:00 UTC Londra araligi sweep ve NY penceresinde geri alis.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from .config import INSTRUMENTS
from .cross_asset_positioning_ab import (_daily_context, _macro_sources,
                                          _positioning_sources)
from .hierarchical_edge_lab import asof_weekly
from .history_fetch import load_history
from .honest_engine import simulate_trades
from .indicators import atr, prev_day_levels
from .macro_context_ab import _summary
from .macro_technical_state_lab import hourly_setup
from .overfit_stats import (align_trials, deflated_from_trials,
                            probability_of_backtest_overfitting)

OUT = (Path(__file__).resolve().parent.parent / "outputs" / "intraday" /
       "gold_macro_sweep_lab")
CONTEXTS = ("technical", "dxy", "macro", "macro_cot", "macro_cot_oi")
ENTRIES = ("previous_day_sweep", "london_range_sweep")


def london_range_levels(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    hour = df.index.hour + df.index.minute / 60.0
    in_range = (hour >= 7.0) & (hour < 13.0)
    day = pd.Index(df.index.date)
    high = df["high"].where(in_range).groupby(day).transform("max")
    low = df["low"].where(in_range).groupby(day).transform("min")
    return high, low


def sweep_signals(df: pd.DataFrame, mode: str) -> tuple[pd.Series, pd.Series]:
    hour = df.index.hour + df.index.minute / 60.0
    if mode == "previous_day_sweep":
        high, low = prev_day_levels(df)
        window = (hour >= 7.0) & (hour < 20.0)
    elif mode == "london_range_sweep":
        high, low = london_range_levels(df)
        window = (hour >= 13.0) & (hour < 20.0)
    else:
        raise ValueError(mode)
    long_raw = (window & (df["low"] < low) & (df["close"] > low) &
                (df["low"].shift(1) >= low.shift(1)))
    short_raw = (window & (df["high"] > high) & (df["close"] < high) &
                 (df["high"].shift(1) <= high.shift(1)))
    # Ayni gunde yalniz ilk teyitli sweep; sonradan tekrar tekrar girme yok.
    any_raw = long_raw | short_raw
    first = any_raw.groupby(pd.Index(df.index.date)).cumsum() == 1
    return long_raw & first, short_raw & first


def _simulate(df: pd.DataFrame, long: pd.Series, short: pd.Series) -> pd.Series:
    a = atr(df, 14)
    entry = df["close"]
    long_sl = df["low"] - 0.10 * a
    short_sl = df["high"] + 0.10 * a
    long_risk = entry - long_sl
    short_risk = short_sl - entry
    return simulate_trades(
        df, long, short,
        long_sl, entry + 2.0 * long_risk,
        short_sl, entry - 2.0 * short_risk,
        INSTRUMENTS["XAUUSD"], min_rr=1.99, max_rr=2.0, max_hold=48,
    )


def run(refresh: bool = False) -> dict:
    OUT.mkdir(parents=True, exist_ok=True)
    df = load_history("XAUUSD", "5m", start_year=2012)
    sources = _macro_sources(refresh)
    positioning = _positioning_sources(refresh, 2026)
    weekly = asof_weekly(df.index, positioning, "gold")
    dates = pd.DatetimeIndex(df.index.normalize().unique())
    daily = _daily_context("GOLD_ORB", dates, sources)
    macro = daily.reindex(df.index.normalize()).set_axis(df.index)
    setup_l, setup_s = hourly_setup(df, adx_min=25.0)
    valid = (weekly[["oi_change", "cot_change"]].notna().all(axis=1) &
             macro["valid"].fillna(False))
    dxy_l, dxy_s = macro["dxy"] <= 0, macro["dxy"] >= 0
    macro_l, macro_s = macro["score"] > 0, macro["score"] < 0
    cot_l, cot_s = weekly["cot_change"] >= 0, weekly["cot_change"] <= 0
    oi = weekly["oi_change"] >= 0
    trials: dict[str, pd.Series] = {}
    for entry_mode in ENTRIES:
        trigger_l, trigger_s = sweep_signals(df, entry_mode)
        base_l = valid & setup_l & trigger_l
        base_s = valid & setup_s & trigger_s
        masks = {
            "technical": (base_l, base_s),
            "dxy": (base_l & dxy_l, base_s & dxy_s),
            "macro": (base_l & macro_l, base_s & macro_s),
            "macro_cot": (base_l & macro_l & cot_l,
                          base_s & macro_s & cot_s),
            "macro_cot_oi": (base_l & macro_l & cot_l & oi,
                             base_s & macro_s & cot_s & oi),
        }
        for context, (lm, sm) in masks.items():
            trials[f"{entry_mode}__{context}"] = _simulate(df, lm, sm)

    discovery = {k: v[v.index.year <= 2021] for k, v in trials.items()}
    rows = []
    for name, result in trials.items():
        is_r = result[result.index.year <= 2021]
        oos_r = result[result.index.year >= 2022]
        rows.append({"candidate": name,
                     **{f"is_{k}": v for k, v in _summary(is_r).items()},
                     **{f"oos_{k}": v for k, v in _summary(oos_r).items()},
                     **{f"full_{k}": v for k, v in _summary(result).items()}})
        result.rename("R").to_csv(OUT / f"trades_{name}.csv", index_label="entry_utc")
    table = pd.DataFrame(rows).sort_values(
        ["is_haftalik_SR", "is_toplam_R"], ascending=False
    )
    table.to_csv(OUT / "candidates.csv", index=False)
    report = {
        "design": {
            "entries": list(ENTRIES), "contexts": list(CONTEXTS),
            "trials": len(trials), "discovery": "2012-2021", "oos": "2022-2026",
            "hourly": "closed 1h EMA20 and rolling VWAP20 alignment, ADX>25",
            "exit": "sweep extreme + 0.1 ATR stop, 2R target, 4h max hold",
        },
        "discovery_multiple_test": deflated_from_trials(discovery),
        "pbo": probability_of_backtest_overfitting(align_trials(discovery)),
        "candidates": table.to_dict(orient="records"),
    }
    (OUT / "report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False, default=str), encoding="utf-8"
    )
    return report


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, ensure_ascii=False, default=str))
