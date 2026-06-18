"""Dukascopy veri yükleyici + CSV cache.

Tick->bar toplanmış OHLCV verisini dukascopy_python ile çeker.
Hafta sonu/seans boşlukları dukascopy tarafından zaten dışlanır.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

try:
    import dukascopy_python as dk
    import dukascopy_python.instruments as inst
except ModuleNotFoundError:  # cache varsa veri indirmeden calisabiliriz
    dk = None
    inst = None

from .config import Instrument, INSTRUMENTS, LOOKBACK_DAYS

CACHE = Path(__file__).resolve().parent.parent / "outputs" / "intraday" / "cache"
CACHE.mkdir(parents=True, exist_ok=True)

if dk is not None:
    _INTERVALS = {
        "5m":  dk.INTERVAL_MIN_5,
        "15m": dk.INTERVAL_MIN_15,
        "1H":  dk.INTERVAL_HOUR_1,
        "4H":  dk.INTERVAL_HOUR_4,
    }
else:
    _INTERVALS = {"5m": "5m", "15m": "15m", "1H": "1H", "4H": "4H"}


def _duka_const(name: str):
    if inst is None:
        raise ModuleNotFoundError("dukascopy_python gerekli: cache yoksa veri indirilemez")
    try:
        return getattr(inst, name)
    except AttributeError as exc:  # pragma: no cover - konfig hatası
        raise ValueError(f"Bilinmeyen dukascopy sembolü: {name}") from exc


def load_ohlcv(symbol: str, tf: str = "15m", days: int = LOOKBACK_DAYS) -> pd.DataFrame:
    """Tek enstrüman + zaman dilimi için OHLCV döner (UTC index, tz-naive)."""
    if symbol not in INSTRUMENTS:
        raise ValueError(f"Tanımsız enstrüman: {symbol}")
    if tf not in _INTERVALS:
        raise ValueError(f"Desteklenmeyen zaman dilimi: {tf}")

    instrument: Instrument = INSTRUMENTS[symbol]
    cached = CACHE / f"{symbol}_{tf}_{days}d.csv"
    if cached.exists():
        df = pd.read_csv(cached, parse_dates=["timestamp"]).set_index("timestamp")
        return df[["open", "high", "low", "close", "volume"]].astype(float).sort_index()

    if dk is None:
        raise ModuleNotFoundError(
            f"dukascopy_python kurulu degil ve cache bulunamadi: {cached}"
        )

    end = datetime.utcnow()
    start = end - timedelta(days=days)
    # BID tarafı: tutarlı, gerçekçi giriş referansı; maliyeti ayrıca uyguluyoruz.
    df = dk.fetch(
        _duka_const(instrument.duka),
        _INTERVALS[tf],
        dk.OFFER_SIDE_BID,
        start,
        end,
    )
    if df is None or df.empty:
        raise RuntimeError(f"{symbol} {tf} için veri gelmedi")

    df = df.copy()
    df.index = pd.to_datetime(df.index, utc=True).tz_convert(None)
    df.index.name = "timestamp"
    df = df[["open", "high", "low", "close", "volume"]].astype(float).sort_index()
    df = df[~df.index.duplicated(keep="first")]
    df.to_csv(cached)
    return df


def load_all(symbol: str, days: int = LOOKBACK_DAYS) -> dict[str, pd.DataFrame]:
    """15m + 1H + 4H veriyi birlikte döner."""
    return {tf: load_ohlcv(symbol, tf, days) for tf in ("15m", "1H", "4H")}
