import json

from intraday.signalbot import finnhub_live


class _Socket:
    def __init__(self):
        self.sent = []
        self.responses = [
            json.dumps(
                {
                    "type": "trade",
                    "data": [
                        {"s": "OANDA:XAU_USD", "p": 3012.5, "t": 1781800000000, "v": 0}
                    ],
                }
            )
        ]

    def send(self, message):
        self.sent.append(json.loads(message))

    def recv(self):
        return self.responses.pop(0)

    def settimeout(self, timeout):
        pass

    def close(self):
        pass


def test_missing_key_returns_empty(monkeypatch):
    monkeypatch.delenv("FINNHUB_API_KEY", raising=False)
    assert finnhub_live.collect_quotes({"XAUUSD"}) == {}


def test_collects_websocket_quote(monkeypatch):
    socket = _Socket()
    monkeypatch.setattr("websocket.create_connection", lambda *a, **k: socket)
    quotes = finnhub_live.collect_quotes({"XAUUSD"}, api_key="test")
    assert quotes["XAUUSD"].price == 3012.5
    assert socket.sent == [{"type": "subscribe", "symbol": "OANDA:XAU_USD"}]
