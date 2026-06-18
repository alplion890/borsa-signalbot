"""BTCUSDT 1H CVD/session-liquidity absorption live detector."""
from __future__ import annotations

import numpy as np
import pandas as pd

from ..forward_ea.modules import LiveModule, Signal
from ..indicators import atr, ema


def detect(df: pd.DataFrame, lookback: int = 12, rr: float = 2.0,
           atr_mult: float = 1.0) -> Signal | None:
    if len(df) < 220:
        return None
    spread = (df["high"] - df["low"]).replace(0.0, np.nan)
    delta = (df["volume"] * (df["close"] - df["open"]) / spread).fillna(0.0)
    rlo = df["low"].rolling(lookback).min().shift(1)
    rhi = df["high"].rolling(lookback).max().shift(1)
    trend = ema(df["close"], 200)
    a = atr(df, 14)
    i = -1

    swept_low = df["low"].iloc[i] < rlo.iloc[i] and df["close"].iloc[i] > rlo.iloc[i]
    swept_high = df["high"].iloc[i] > rhi.iloc[i] and df["close"].iloc[i] < rhi.iloc[i]
    entry = float(df["close"].iloc[i])
    if swept_low and delta.iloc[i] > 0 and entry > trend.iloc[i]:
        sl = float(df["low"].iloc[i] - a.iloc[i] * atr_mult)
        risk = entry - sl
        return Signal(1, entry, sl, entry + rr * risk) if risk > 0 else None
    if swept_high and delta.iloc[i] < 0 and entry < trend.iloc[i]:
        sl = float(df["high"].iloc[i] + a.iloc[i] * atr_mult)
        risk = sl - entry
        return Signal(-1, entry, sl, entry - rr * risk) if risk > 0 else None
    return None


def module() -> LiveModule:
    return LiveModule(
        "BTCUSDT_OF_ABSORPTION",
        "BTC",
        "1H",
        0.11,
        96,
        detect,
    )
