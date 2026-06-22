import pytest
from intraday.signalbot.symbols import resolve, Source


def test_resolve_xauusd():
    spec = resolve("XAUUSD")
    assert spec.source == Source.YFINANCE
    assert spec.ticker == "GC=F"
    assert spec.expected_delay_minutes == 10
    assert spec.live_quote_compatible is False


def test_resolve_btc():
    spec = resolve("BTC")
    assert spec.source == Source.BINANCE
    assert spec.ticker == "BTCUSDT"
    assert spec.live_quote_compatible is True


def test_resolve_unknown_raises():
    with pytest.raises(KeyError):
        resolve("DOGECOIN")
