"""Bedava veri adaptoru — mt5_io.ohlcv ile AYNI sekil dondurur.

Donus: DatetimeIndex(UTC), sutunlar open/high/low/close/volume (float).
Boylece forward_ea/modules.py dedektorleri degismeden calisir.
"""
from __future__ import annotations
import pandas as pd
from .symbols import resolve, Source

_TF_YF = {"5m": "5m", "15m": "15m", "1H": "60m"}


def _yf_download(ticker: str, interval: str, period: str) -> pd.DataFrame:
    import yfinance as yf
    return yf.download(ticker, interval=interval, period=period,
                       progress=False, auto_adjust=False)


def _normalize(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    if isinstance(df.columns, pd.MultiIndex):
        df = df.copy()
        df.columns = df.columns.get_level_values(0)
    df = df.rename(columns=str.lower)[["open", "high", "low", "close", "volume"]]
    idx = pd.DatetimeIndex(df.index)
    idx = idx.tz_localize("UTC") if idx.tz is None else idx.tz_convert("UTC")
    df = df.set_axis(idx).astype(float)
    return df[~df.index.duplicated(keep="last")].sort_index()


def _period_for(days: int) -> str:
    return f"{max(1, min(days, 59))}d"


def ohlcv(symbol_key: str, tf: str, days: int = 60) -> pd.DataFrame:
    spec = resolve(symbol_key)
    if spec.source is Source.YFINANCE:
        raw = _yf_download(spec.ticker, _TF_YF[tf], _period_for(days))
        frame = _normalize(raw)
        frame.attrs.update(
            {
                "source": "yfinance",
                "expected_delay_minutes": spec.expected_delay_minutes,
            }
        )
        return frame
    if spec.source is Source.BINANCE:
        from .binance_data import klines
        frame = klines(spec.ticker, tf, days)
        frame.attrs.update({"source": "binance", "expected_delay_minutes": 0})
        return frame
    raise ValueError(f"desteklenmeyen kaynak: {spec.source}")


def source_of(frame: pd.DataFrame) -> str:
    return str(frame.attrs.get("source", "unknown"))


def expected_delay(frame: pd.DataFrame, fallback: int = 0) -> int:
    return int(frame.attrs.get("expected_delay_minutes", fallback))
