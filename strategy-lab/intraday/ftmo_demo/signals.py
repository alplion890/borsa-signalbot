"""Frozen existing Sweep detectors, with broker-only M15 data."""

from __future__ import annotations

import hashlib
import math
from pathlib import Path

import pandas as pd

MODULES = {
    "SWEEP_CORE_AVOID_MID_VWAP": "NASDAQ100",
    "CAND_SWEEP_JAP225": "JAP225",
    "CAND_SWEEP_SP500": "SP500",
    "CAND_SWEEP_UK100": "UK100",
}
VERSION = "ftmo-sweep-news-exit-v1"


def strategy_hash():
    root = Path(__file__).resolve().parents[1]
    digest = hashlib.sha256()
    for name in [
        "forward_ea/modules.py",
        "adx_lab.py",
        "indicators.py",
        "ftmo_demo/signals.py",
    ]:
        digest.update(name.encode())
        digest.update((root / name).read_bytes())
    return digest.hexdigest()


def closed_bars(client, symbol, now):
    rates = client.copy_rates_from_pos(symbol, client.TIMEFRAME_M15, 0, 4000)
    if rates is None or len(rates) < 521:
        raise ValueError(f"{symbol}: en az 521 FTMO bari gerekli")
    frame = pd.DataFrame(rates)
    frame.index = pd.to_datetime(frame.pop("time"), unit="s", utc=True).dt.tz_localize(
        None
    )
    if not frame.index.is_monotonic_increasing or frame.index.has_duplicates:
        raise ValueError("Bar zamanlari sirali ve tekil olmali")
    cutoff = pd.Timestamp(now).tz_convert("UTC").tz_localize(None)
    frame = frame.loc[frame.index + pd.Timedelta(minutes=15) <= cutoff]
    if len(frame) < 520 or frame[["open", "high", "low", "close"]].isna().any().any():
        raise ValueError("Yetersiz veya eksik kapanmis bar")
    return frame


def latest_signal(module, frame, now):
    from ..forward_ea.modules import _sweep_core_detector

    age = (
        pd.Timestamp(now).tz_convert("UTC").tz_localize(None)
        - frame.index[-1]
        - pd.Timedelta(minutes=15)
    ).total_seconds()
    if not 0 <= age <= 120:
        return None
    signal = _sweep_core_detector(adx_thresh=25.0, min_rr=2.0, skip_wednesday=True)(
        frame
    )
    if signal is None:
        return None
    if not all(
        math.isfinite(v) and v > 0 for v in [signal.entry, signal.sl, signal.tp]
    ):
        raise ValueError("Gecersiz sinyal seviyesi")
    timestamp = frame.index[-1].tz_localize("UTC").isoformat()
    identity = hashlib.sha256(f"{VERSION}|{module}|{timestamp}".encode()).hexdigest()[
        :24
    ]
    return {
        "id": identity,
        "module": module,
        "symbol_key": MODULES[module],
        "bar_time": timestamp,
        "direction": signal.direction,
        "entry": signal.entry,
        "sl": signal.sl,
        "tp": signal.tp,
        "version": VERSION,
        "strategy_hash": strategy_hash(),
    }
