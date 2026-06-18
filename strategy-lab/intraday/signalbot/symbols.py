"""symbol_key -> bedava veri kaynagi eslemesi. Tek degisiklik noktasi."""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum


class Source(str, Enum):
    YFINANCE = "yfinance"
    BINANCE = "binance"


@dataclass(frozen=True)
class SymbolSpec:
    source: Source
    ticker: str
    expected_delay_minutes: int = 0


_MAP: dict[str, SymbolSpec] = {
    "XAUUSD":    SymbolSpec(Source.YFINANCE, "GC=F", 10),
    "NASDAQ100": SymbolSpec(Source.YFINANCE, "NQ=F", 10),
    "SP500":     SymbolSpec(Source.YFINANCE, "ES=F", 10),
    "EURUSD":    SymbolSpec(Source.YFINANCE, "EURUSD=X"),
    "GBPUSD":    SymbolSpec(Source.YFINANCE, "GBPUSD=X"),
    "BTC":       SymbolSpec(Source.BINANCE, "BTCUSDT"),
}


def resolve(symbol_key: str) -> SymbolSpec:
    if symbol_key not in _MAP:
        raise KeyError(f"bilinmeyen symbol_key: {symbol_key}")
    return _MAP[symbol_key]
