from intraday.signalbot import binance_data

_SAMPLE = [
    [1781800000000, "100", "110", "90", "105", "12.5", 0, 0, 0, 0, 0, 0],
    [1781803600000, "105", "115", "95", "108", "9.0", 0, 0, 0, 0, 0, 0],
]


def test_klines_normalized(monkeypatch):
    monkeypatch.setattr(binance_data, "_get", lambda *a, **k: _SAMPLE)
    df = binance_data.klines("BTCUSDT", "1H", days=1)
    assert list(df.columns) == ["open", "high", "low", "close", "volume"]
    assert str(df.index.tz) == "UTC"
    assert float(df["close"].iloc[-1]) == 108.0
