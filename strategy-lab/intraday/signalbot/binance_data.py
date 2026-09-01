"""Binance public klines -> mt5_io sekli. Key gerekmez."""
from __future__ import annotations
import pandas as pd
import requests

# "1d": trend katmani gunluk bar istiyor (telefon brifingi, 2026-09-01).
# Eksikligi KeyError veriyordu ve BTC listede "VERI YOK" olarak kaliyordu.
_TF_BINANCE = {"5m": "5m", "15m": "15m", "1H": "1h", "1d": "1d"}
_BASES = (
    "https://data-api.binance.vision/api/v3/klines",
    "https://api.binance.com/api/v3/klines",
)


def _get(symbol: str, interval: str, limit: int) -> list:
    last_error = None
    for base in _BASES:
        try:
            r = requests.get(base, params={"symbol": symbol, "interval": interval,
                                          "limit": limit}, timeout=15)
            r.raise_for_status()
            return r.json()
        except requests.RequestException as exc:
            last_error = exc
    raise last_error


def klines(symbol: str, tf: str, days: int = 60) -> pd.DataFrame:
    per_day = {"5m": 288, "15m": 96, "1H": 24, "1d": 1}[tf]
    limit = min(1000, max(200, per_day * days))
    rows = _get(symbol, _TF_BINANCE[tf], limit)
    df = pd.DataFrame(rows, columns=[
        "ot", "open", "high", "low", "close", "volume",
        "ct", "qv", "n", "tb", "tq", "ig"])
    idx = pd.to_datetime(df["ot"], unit="ms", utc=True)
    out = df[["open", "high", "low", "close", "volume"]].astype(float)
    return out.set_axis(pd.DatetimeIndex(idx)).sort_index()
