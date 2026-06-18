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


def test_get_falls_back_to_market_data_domain(monkeypatch):
    calls = []

    class _Response:
        def __init__(self, ok):
            self.ok = ok

        def raise_for_status(self):
            if not self.ok:
                import requests
                raise requests.HTTPError("451")

        def json(self):
            return _SAMPLE

    def fake_get(url, **kwargs):
        calls.append(url)
        return _Response(ok=len(calls) == 1)

    monkeypatch.setattr(binance_data.requests, "get", fake_get)
    assert binance_data._get("BTCUSDT", "1h", 200) == _SAMPLE
    assert calls[0].startswith("https://data-api.binance.vision")
