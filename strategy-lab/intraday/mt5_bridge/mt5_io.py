"""MetaTrader5 baglanti + veri adaptoru.

Bu modul tek sorumluluk tasir: MT5 terminaline baglanip OHLCV ve tick verisini
pandas formatinda dondurmek. Strateji mantigi YOK.

Kullanim:
    from intraday.mt5_bridge import mt5_io
    with mt5_io.session():
        df = mt5_io.ohlcv("XAUUSD", "5m", days=120)
        ticks = mt5_io.ticks("XAUUSD", days=3)
"""
from __future__ import annotations

import contextlib
import subprocess
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

try:
    import MetaTrader5 as mt5
except ModuleNotFoundError as exc:  # pragma: no cover
    raise ModuleNotFoundError(
        "MetaTrader5 paketi gerekli: pip install MetaTrader5 (yalnizca Windows)"
    ) from exc


# Ic strateji anahtari -> bu broker'daki MT5 sembol adi.
# Not: NASDAQ100/SP500 CFD; XAUUSD/EURUSD spot FX/metal. BTC spot YOK.
SYMBOL_MAP: dict[str, str] = {
    "NASDAQ100": "US100",   # MavenTrade broker: Ind&Com3 Market\US100 (eski "USTEC" bu broker'da yok)
    "SP500": "US500",
    "XAUUSD": "XAUUSD",
    "EURUSD": "EURUSD",
    "GBPUSD": "GBPUSD",
    "BTCUSDT": "BTCUSD",    # MavenTrade broker: Cryptocurrencies\BTCUSD (CFD; tick_volume var)
}

# Bu broker'da spot karsiligi olmayan modul sembolleri.
UNAVAILABLE: dict[str, str] = {}

_TF = {
    "1m": "TIMEFRAME_M1",
    "5m": "TIMEFRAME_M5",
    "15m": "TIMEFRAME_M15",
    "1H": "TIMEFRAME_H1",
    "4H": "TIMEFRAME_H4",
    "1D": "TIMEFRAME_D1",
}


class MT5Error(RuntimeError):
    pass


_TERMINAL_IMAGES = ("terminal64.exe", "terminal.exe")


def _terminal_running() -> bool:
    """MT5 terminali su an calisiyor mu? (tasklist ile, ek bagimlilik yok)

    NEDEN GEREKLI: `mt5.initialize()` argumansiz cagrildiginda terminal
    kapaliysa ONU KENDISI BASLATIR (MT5 Python API'sinin belgelenmis
    davranisi). Forward EA Task Scheduler'dan 5 dakikada bir kostugu icin
    bu, kullanici MT5'i kapatsa bile terminalin surekli geri acilmasina yol
    aciyordu -- 2026-08'de kullanici sikayeti oldu ve gorev devre disi
    birakilmisti (yani veri toplama tamamen durmustu).

    Tespit edilemezse (tasklist yok/patladi) True doner: yanlis pozitif
    anlasilir bir baglanti hatasi verir, yanlis negatif ise botu sessizce
    oldururdu. Sessiz olum bu repoda tekrar eden hata -- kacinilir.
    """
    for image in _TERMINAL_IMAGES:
        try:
            proc = subprocess.run(
                ["tasklist", "/FI", f"IMAGENAME eq {image}", "/NH"],
                capture_output=True, text=True, timeout=10,
            )
        except (OSError, subprocess.SubprocessError):
            return True  # tespit edemedik -> engelleme
        if image.lower() in (proc.stdout or "").lower():
            return True
    return False


def initialize() -> None:
    """Calisan terminale baglan. Terminal kapaliysa ACMADAN hata firlat."""
    if not _terminal_running():
        raise MT5Error(
            "MT5 terminali kapali. Bilerek ACILMADI -- forward EA terminali "
            "kendiliginden baslatmaz. MetaTrader 5'i elle ac ve Maven hesabina "
            "giris yap; bir sonraki 5 dakikalik tetiklemede kaldigi yerden devam eder."
        )
    if not mt5.initialize():
        code, msg = mt5.last_error()
        raise MT5Error(
            f"MT5 baglanamadi ({code}: {msg}). MetaTrader 5 terminalini ac ve "
            f"hesabin girili oldugundan emin ol."
        )


def shutdown() -> None:
    mt5.shutdown()


@contextlib.contextmanager
def session():
    """`with mt5_io.session():` icinde baglanti garanti acik/kapatilir."""
    initialize()
    try:
        yield
    finally:
        shutdown()


def account() -> dict:
    ai = mt5.account_info()
    ti = mt5.terminal_info()
    if ai is None or ti is None:
        raise MT5Error("Hesap/terminal bilgisi alinamadi.")
    return {
        "login": ai.login,
        "broker": ai.company,
        "server": ai.server,
        "balance": ai.balance,
        "currency": ai.currency,
        "connected": ti.connected,
    }


def resolve(symbol_key: str) -> str:
    """Ic anahtari MT5 sembol adina cevir, sembolu Market Watch'a ekle."""
    if symbol_key in UNAVAILABLE:
        raise MT5Error(f"{symbol_key}: {UNAVAILABLE[symbol_key]}")
    name = SYMBOL_MAP.get(symbol_key, symbol_key)
    if not mt5.symbol_select(name, True):
        raise MT5Error(f"Sembol secilemedi: {name} (broker'da yok olabilir)")
    return name


def symbol_meta(symbol_key: str) -> dict:
    name = resolve(symbol_key)
    info = mt5.symbol_info(name)
    tick = mt5.symbol_info_tick(name)
    return {
        "key": symbol_key,
        "name": name,
        "digits": info.digits,
        "point": info.point,
        "spread_points": info.spread,
        "bid": getattr(tick, "bid", None),
        "ask": getattr(tick, "ask", None),
        "path": info.path,
    }


def ohlcv(symbol_key: str, tf: str = "5m", days: int = 120) -> pd.DataFrame:
    """OHLCV bar verisi. UTC index, tz-naive, data.py cache formatiyla uyumlu."""
    if tf not in _TF:
        raise MT5Error(f"Desteklenmeyen TF: {tf}")
    name = resolve(symbol_key)
    timeframe = getattr(mt5, _TF[tf])
    end = datetime.now()
    start = end - timedelta(days=days)
    rates = mt5.copy_rates_range(name, timeframe, start, end)
    if rates is None or len(rates) == 0:
        raise MT5Error(f"{name} {tf}: bar verisi gelmedi (broker gecmisi sig olabilir).")
    df = pd.DataFrame(rates)
    df["timestamp"] = pd.to_datetime(df["time"], unit="s")
    df = df.set_index("timestamp")
    df = df.rename(columns={"tick_volume": "volume"})
    return df[["open", "high", "low", "close", "volume"]].astype(float).sort_index()


def ticks(symbol_key: str, days: int = 3, limit: int = 500_000) -> pd.DataFrame:
    """Tick verisi (bid/ask). Spread/slippage olcumu icin."""
    name = resolve(symbol_key)
    start = datetime.now() - timedelta(days=days)
    raw = mt5.copy_ticks_from(name, start, limit, mt5.COPY_TICKS_ALL)
    if raw is None or len(raw) == 0:
        raise MT5Error(f"{name}: tick verisi gelmedi.")
    df = pd.DataFrame(raw)
    df["timestamp"] = pd.to_datetime(df["time_msc"], unit="ms")
    df = df.set_index("timestamp")
    df = df[(df["bid"] > 0) & (df["ask"] > 0)].copy()
    df["mid"] = (df["bid"] + df["ask"]) / 2.0
    df["spread_ratio"] = (df["ask"] - df["bid"]) / df["mid"]
    return df[["bid", "ask", "mid", "spread_ratio"]].sort_index()


def history_start(symbol_key: str, tf: str = "1D") -> pd.Timestamp | None:
    """Broker bu sembol icin veriye nereden basliyor (sig-geçmiş tespiti)."""
    try:
        df = ohlcv(symbol_key, tf, days=4000)
    except MT5Error:
        return None
    return df.index.min() if len(df) else None
