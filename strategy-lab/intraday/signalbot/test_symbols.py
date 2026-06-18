import pytest
from intraday.signalbot.symbols import resolve, Source


def test_resolve_xauusd():
    spec = resolve("XAUUSD")
    assert spec.source == Source.YFINANCE
    assert spec.ticker == "GC=F"


def test_resolve_btc():
    spec = resolve("BTC")
    assert spec.source == Source.BINANCE
    assert spec.ticker == "BTCUSDT"


def test_resolve_unknown_raises():
    with pytest.raises(KeyError):
        resolve("DOGECOIN")
