"""Seans pencereleri UTC tabanli. TRT gosterim = UTC+3 (sabit, DST yok)."""
from __future__ import annotations
import datetime as dt

# (utc_start_hour, utc_end_hour) — yaz referansi; DST toleransi icin genis.
_WINDOWS = {
    "GOLD_NY_ORB_TREND": (13, 16),
    "NQ_ORB_STRONG_TREND": (13, 17),
    "SWEEP_CORE_AVOID_MID_VWAP": (13, 21),
    "SWEEP_ES_DIV": (13, 21),
    "EUR_LONDON_FADE_EMA": (7, 11),
    "GBP_LONDON_STRONG_TREND": (7, 11),
    "BTCUSDT_OF_ABSORPTION": None,  # 7/24
}


def to_trt(utc: dt.datetime) -> str:
    trt = utc.astimezone(dt.timezone(dt.timedelta(hours=3)))
    return f"{trt.hour:02d} {trt.minute:02d}"


def is_active(module_name: str, utc: dt.datetime) -> bool:
    win = _WINDOWS.get(module_name, None)
    if win is None:
        return True
    start, end = win
    return start <= utc.hour < end
