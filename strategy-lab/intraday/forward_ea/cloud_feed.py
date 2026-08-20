"""Bulut kosucusunun veri kaynagi — MT5 yok, bedava feed'ler.

Neden ayri bir tablo: signalbot'un `symbols.py`'si SADECE Telegram'a cikan
canli portfoyu tanir. Forward EA bunun ustune adaylari da olcer (US30,
JAP225, UK100...). O anahtarlari signalbot tablosuna eklemek, signalbot'un
davranisini (parity olcumu, sembol dongueleri) bu isle ilgisiz sekilde
degistirirdi. Bu yuzden: once signalbot tablosuna bak, yoksa buradaki
ek tabloya. Normalizasyon yine tek yerden (`free_data.ohlcv_spec`).

VADELI/SPOT NOTU: cogu anahtar vadeli kontrata bakar (NQ=F, ES=F...).
MT5 CFD'siyle arasinda baz farki vardir -- olculdu, NASDAQ'ta gurultu
p95 = 0.074R (bkz [[Borsa - Feed Parity yfinance vs MT5]]). Bu yuzden bulut
defteri MT5 defterinin YERINE gecmez, YANINDA durur.
"""
from __future__ import annotations

import pandas as pd

from ..signalbot.free_data import ohlcv_spec as _free_ohlcv
from ..signalbot.symbols import Source, SymbolSpec
from ..signalbot.symbols import resolve as _signalbot_resolve

# signalbot tablosunda olmayan, yalnizca forward EA adaylarinin kullandigi
# semboller. Ticker secimi: intraday veri veren en yakin vadeli kontrat.
_EXTRA: dict[str, SymbolSpec] = {
    "US30":    SymbolSpec(Source.YFINANCE, "YM=F", 10, False),
    "US2000":  SymbolSpec(Source.YFINANCE, "RTY=F", 10, False),
    "UK100":   SymbolSpec(Source.YFINANCE, "^FTSE", 15, False),
    "FRA40":   SymbolSpec(Source.YFINANCE, "^FCHI", 15, False),
    "JAP225":  SymbolSpec(Source.YFINANCE, "NIY=F", 10, False),
    # INSTRUMENTS anahtari "BTCUSDT"; signalbot ayni sembole "BTC" diyor.
    # Ikisi de ayni Binance serisine gitmeli, yoksa maliyet KeyError verir
    # ve sinyal sessizce duser (2026-08-06'da tam olarak bu oldu).
    "BTCUSDT": SymbolSpec(Source.BINANCE, "BTCUSDT"),
}


def resolve(symbol_key: str) -> SymbolSpec:
    try:
        return _signalbot_resolve(symbol_key)
    except KeyError:
        pass
    if symbol_key in _EXTRA:
        return _EXTRA[symbol_key]
    raise KeyError(f"bulut feed'i tanimsiz symbol_key: {symbol_key}")


def supports(symbol_key: str) -> bool:
    try:
        resolve(symbol_key)
    except KeyError:
        return False
    return True


def source_of(symbol_key: str) -> str:
    return resolve(symbol_key).source.value


def ohlcv(symbol_key: str, tf: str, days: int = 60) -> pd.DataFrame:
    """Bar cerceve — mt5_io sozlesmesi: UTC index, tz-NAIVE.

    yfinance ve Binance ikisi de tz-AWARE dondurur. Naive'e indirmek burada
    ZORUNLU: karisik tz defter yazimini patlatir ve hata `_save_state` icinde
    oldugu icin o dongudeki TUM modullerin kaydi kaybolur.
    """
    frame = _free_ohlcv(resolve(symbol_key), tf, days)
    if len(frame) and frame.index.tz is not None:
        frame = frame.tz_convert("UTC").tz_localize(None)
    return frame
