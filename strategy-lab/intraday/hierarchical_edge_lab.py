"""NQ icin haftalik -> gunluk -> 1s -> 5d hiyerarsik edge taramasi.

Yalniz 16 onceden tanimli hipotez dener. 2012-2021 kesif, 2022-2026 OOS'tur.
Canli sistemi degistirmez.
"""
from __future__ import annotations

import json
from itertools import product
from pathlib import Path

import numpy as np
import pandas as pd

from .config import INSTRUMENTS
from .cross_asset_positioning_ab import (_daily_context, _macro_sources,
                                          _positioning_sources)
from .history_fetch import load_history
from .honest_engine import simulate_trades
from .indicators import atr, ema
from .macro_context_ab import _summary
from .overfit_stats import (align_trials, deflated_from_trials,
                            probability_of_backtest_overfitting)

OUT = (Path(__file__).resolve().parent.parent / "outputs" / "intraday" /
       "hierarchical_edge_lab")
ENTRY_MODES = ("vwap_reclaim", "ema20_reclaim", "vwap_hold", "ema20_hold")
WEEKLY_MODES = ("none", "oi", "cot", "cot_oi")
MACRO_MODES = ("none", "not_against")


def cash_session_vwap(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """New York 09:30-16:00 VWAP ve 10:00-15:30 giris penceresi."""
    utc = pd.DatetimeIndex(df.index).tz_localize("UTC")
    ny = utc.tz_convert("America/New_York")
    minute = ny.hour * 60 + ny.minute
    cash = (minute >= 9 * 60 + 30) & (minute < 16 * 60)
    entry_window = (minute >= 10 * 60) & (minute < 15 * 60 + 30)
    day = pd.Index(ny.date)
    typical = (df["high"] + df["low"] + df["close"]) / 3.0
    volume = df["volume"].clip(lower=1e-9)
    pv = (typical * volume).where(cash).groupby(day).cumsum()
    cv = volume.where(cash).groupby(day).cumsum()
    return pv / cv, pd.Series(entry_window, index=df.index)


def hourly_ema_trend(df: pd.DataFrame) -> pd.Series:
    """Yalniz kapanmis 1 saatlik barlardan +1/-1/0 trend."""
    hourly = df.resample("1h", closed="left", label="right").agg({
        "open": "first", "high": "max", "low": "min", "close": "last",
        "volume": "sum",
    }).dropna()
    fast, slow = ema(hourly["close"], 20), ema(hourly["close"], 50)
    trend = pd.Series(0, index=hourly.index, dtype=int)
    trend[(hourly["close"] > fast) & (fast > slow)] = 1
    trend[(hourly["close"] < fast) & (fast < slow)] = -1
    return trend.reindex(df.index, method="ffill").fillna(0).astype(int)


def asof_weekly(index: pd.DatetimeIndex, positioning: pd.DataFrame,
                market: str = "nq") -> pd.DataFrame:
    part = positioning.loc[positioning["market"] == market,
                           ["available_date", "oi_change", "cot_change"]].copy()
    part["available_at"] = pd.to_datetime(part.pop("available_date"), utc=True)
    bars = pd.DataFrame({"timestamp": pd.to_datetime(index, utc=True)})
    out = pd.merge_asof(bars, part.sort_values("available_at"),
                        left_on="timestamp", right_on="available_at",
                        direction="backward")
    out.index = index
    return out.drop(columns=["timestamp", "available_at"])


def build_features(df: pd.DataFrame, refresh: bool = False) -> dict[str, pd.Series]:
    vwap, session = cash_session_vwap(df)
    ema20 = ema(df["close"], 20)
    htf = hourly_ema_trend(df)
    bullish = df["close"] > df["open"]
    bearish = df["close"] < df["open"]
    entries = {
        "vwap_reclaim": (
            (df["close"].shift(1) <= vwap.shift(1)) & (df["close"] > vwap) & bullish,
            (df["close"].shift(1) >= vwap.shift(1)) & (df["close"] < vwap) & bearish,
        ),
        "ema20_reclaim": (
            (df["close"].shift(1) <= ema20.shift(1)) & (df["close"] > ema20) & bullish,
            (df["close"].shift(1) >= ema20.shift(1)) & (df["close"] < ema20) & bearish,
        ),
        "vwap_hold": (
            (df["close"].shift(1) > vwap.shift(1)) & (df["low"] <= vwap) &
            (df["close"] > vwap) & bullish,
            (df["close"].shift(1) < vwap.shift(1)) & (df["high"] >= vwap) &
            (df["close"] < vwap) & bearish,
        ),
        "ema20_hold": (
            (df["close"].shift(1) > ema20.shift(1)) & (df["low"] <= ema20) &
            (df["close"] > ema20) & bullish,
            (df["close"].shift(1) < ema20.shift(1)) & (df["high"] >= ema20) &
            (df["close"] < ema20) & bearish,
        ),
    }
    positioning = _positioning_sources(refresh, 2026)
    weekly = asof_weekly(df.index, positioning)
    sources = _macro_sources(refresh)
    dates = pd.DatetimeIndex(df.index.normalize().unique())
    macro_daily = _daily_context("NQ_ORB", dates, sources)
    macro = macro_daily.reindex(df.index.normalize()).set_axis(df.index)
    return {"vwap": vwap, "session": session, "ema20": ema20, "htf": htf,
            "entries": entries, "weekly": weekly, "macro": macro}


def candidate_masks(features: dict, entry_mode: str, weekly_mode: str,
                    macro_mode: str) -> tuple[pd.Series, pd.Series]:
    weekly, macro = features["weekly"], features["macro"]
    base_long, base_short = features["entries"][entry_mode]
    coverage = (features["session"] & weekly[["oi_change", "cot_change"]]
                .notna().all(axis=1) & macro["valid"].fillna(False))
    long = coverage & base_long & (features["htf"] == 1)
    short = coverage & base_short & (features["htf"] == -1)
    if weekly_mode in {"oi", "cot_oi"}:
        long &= weekly["oi_change"] >= 0
        short &= weekly["oi_change"] >= 0
    if weekly_mode in {"cot", "cot_oi"}:
        long &= weekly["cot_change"] >= 0
        short &= weekly["cot_change"] <= 0
    if macro_mode == "not_against":
        long &= macro["score"] >= 0
        short &= macro["score"] <= 0
    return long, short


def _run_candidate(df: pd.DataFrame, long: pd.Series, short: pd.Series) -> pd.Series:
    risk = atr(df, 14)
    price = df["close"]
    return simulate_trades(
        df, long, short,
        price - risk, price + 1.5 * risk,
        price + risk, price - 1.5 * risk,
        INSTRUMENTS["NASDAQ100"], min_rr=1.49, max_rr=1.5, max_hold=24,
    )


def run(refresh: bool = False) -> dict:
    OUT.mkdir(parents=True, exist_ok=True)
    df = load_history("NASDAQ100", "5m", start_year=2012)
    features = build_features(df, refresh)
    trials: dict[str, pd.Series] = {}
    for entry_mode, weekly_mode, macro_mode in product(
            ENTRY_MODES, WEEKLY_MODES, MACRO_MODES):
        name = f"{entry_mode}__{weekly_mode}__{macro_mode}"
        trials[name] = _run_candidate(
            df, *candidate_masks(features, entry_mode, weekly_mode, macro_mode)
        )

    discovery = {k: v[v.index.year <= 2021] for k, v in trials.items()}
    oos = {k: v[v.index.year >= 2022] for k, v in trials.items()}
    rows = []
    for name in trials:
        rows.append({"candidate": name,
                     **{f"is_{k}": v for k, v in _summary(discovery[name]).items()},
                     **{f"oos_{k}": v for k, v in _summary(oos[name]).items()},
                     **{f"full_{k}": v for k, v in _summary(trials[name]).items()}})
        trials[name].rename("R").to_csv(OUT / f"trades_{name}.csv",
                                         index_label="entry_utc")
    table = pd.DataFrame(rows).sort_values(
        ["is_haftalik_SR", "is_toplam_R"], ascending=False
    )
    table.to_csv(OUT / "candidates.csv", index=False)
    report = {
        "design": {
            "trials": len(trials), "discovery": "2012-2021", "oos": "2022-2026",
            "entry": list(ENTRY_MODES), "weekly": list(WEEKLY_MODES),
            "macro": list(MACRO_MODES), "hourly": "EMA20/EMA50 aligned",
            "exit": "1 ATR stop, 1.5 ATR target, 24x5m max hold",
        },
        "discovery_multiple_test": deflated_from_trials(discovery),
        "pbo": probability_of_backtest_overfitting(align_trials(discovery)),
        "candidates": table.replace({np.nan: None}).to_dict(orient="records"),
    }
    (OUT / "report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False),
                                      encoding="utf-8")
    return report


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, ensure_ascii=False))
