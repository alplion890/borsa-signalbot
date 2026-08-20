"""Bulut feed'i sozlesmesi.

Iki sey burada kirilirsa defter sessizce bosalir (ikisi de daha once oldu):
  1. Bilinmeyen sembol -> sinyal uretilir ama kayit dusmez.
  2. tz-aware index -> defter yazimi patlar, O DONGUDEKI tum moduller kaybolur.
"""
from __future__ import annotations

import pandas as pd
import pytest

from . import cloud_feed
from .modules import forward_test_modules


def _frame(tz: str | None) -> pd.DataFrame:
    idx = pd.date_range("2026-08-01", periods=3, freq="15min", tz=tz)
    return pd.DataFrame(
        {"open": 1.0, "high": 2.0, "low": 0.5, "close": 1.5, "volume": 10.0},
        index=idx,
    )


def test_her_forward_modulunun_sembolu_cozulur():
    eksik = sorted({m.symbol_key for m in forward_test_modules()
                    if not cloud_feed.supports(m.symbol_key)})
    assert eksik == [], f"bulut feed'i olmayan semboller: {eksik}"


def test_bilinmeyen_sembol_sessizce_gecmez():
    with pytest.raises(KeyError):
        cloud_feed.resolve("YOK_BOYLE_BIR_SEY")


def test_tz_aware_feed_naive_uible_indirilir(monkeypatch):
    monkeypatch.setattr(cloud_feed, "_free_ohlcv", lambda *a, **k: _frame("UTC"))
    out = cloud_feed.ohlcv("NASDAQ100", "15m", days=5)
    assert out.index.tz is None


def test_naive_feed_bozulmadan_gecer(monkeypatch):
    monkeypatch.setattr(cloud_feed, "_free_ohlcv", lambda *a, **k: _frame(None))
    out = cloud_feed.ohlcv("NASDAQ100", "15m", days=5)
    assert out.index.tz is None
    assert list(out.columns) == ["open", "high", "low", "close", "volume"]


def test_kaynak_adi_raporlanir(monkeypatch):
    monkeypatch.setattr(cloud_feed, "_free_ohlcv", lambda *a, **k: _frame("UTC"))
    assert cloud_feed.source_of("NASDAQ100") == "yfinance"
    assert cloud_feed.source_of("BTCUSDT") == "binance"
