"""Short-lived Finnhub WebSocket client for live price enrichment.

Finnhub is optional. Missing credentials, unsupported symbols, closed markets,
or connection errors return no quote and never suppress a strategy signal.
"""
from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass

_DEFAULT_SYMBOLS = {
    "XAUUSD": "OANDA:XAU_USD",
    "NASDAQ100": "OANDA:NAS100_USD",
    "SP500": "OANDA:SPX500_USD",
    "EURUSD": "OANDA:EUR_USD",
    "GBPUSD": "OANDA:GBP_USD",
    "BTC": "BINANCE:BTCUSDT",
}


@dataclass(frozen=True)
class LiveQuote:
    symbol_key: str
    provider_symbol: str
    price: float
    timestamp_ms: int


def provider_symbol(symbol_key: str) -> str:
    env_name = f"FINNHUB_SYMBOL_{symbol_key}"
    return os.environ.get(env_name, _DEFAULT_SYMBOLS[symbol_key])


def collect_quotes(symbol_keys: set[str], *, api_key: str | None = None,
                   timeout_seconds: float = 7.0) -> dict[str, LiveQuote]:
    """Collect the newest trade/price update for each requested symbol."""
    token = api_key or os.environ.get("FINNHUB_API_KEY")
    if not token or not symbol_keys:
        return {}

    import websocket

    reverse = {provider_symbol(key): key for key in symbol_keys}
    ws = None
    quotes: dict[str, LiveQuote] = {}
    try:
        ws = websocket.create_connection(
            f"wss://ws.finnhub.io?token={token}",
            timeout=min(timeout_seconds, 5.0),
        )
        for symbol in reverse:
            ws.send(json.dumps({"type": "subscribe", "symbol": symbol}))

        deadline = time.monotonic() + timeout_seconds
        while time.monotonic() < deadline and len(quotes) < len(reverse):
            ws.settimeout(max(0.2, deadline - time.monotonic()))
            try:
                payload = json.loads(ws.recv())
            except TimeoutError:
                break
            if payload.get("type") != "trade":
                continue
            for item in payload.get("data", []):
                symbol = item.get("s")
                key = reverse.get(symbol)
                if key is None:
                    continue
                price = float(item.get("p", 0.0))
                timestamp = int(item.get("t", 0))
                if price <= 0:
                    continue
                current = quotes.get(key)
                if current is None or timestamp >= current.timestamp_ms:
                    quotes[key] = LiveQuote(key, symbol, price, timestamp)
    except Exception as exc:
        print(f"Finnhub canli fiyat alinamadi: {type(exc).__name__}: {exc}")
    finally:
        if ws is not None:
            try:
                ws.close()
            except Exception:
                pass
    return quotes
