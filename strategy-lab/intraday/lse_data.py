"""London Strategic Edge (LSE) masaustu terminali veri adaptoru.

Terminalin localhost API'sini kullanir; API anahtari bu projeye yazilmaz.
Canli kullanimda LSE yalniz yedektir ve bayat bar fail-closed edilir.
Gecmis indirmeler yillik Parquet parcalari olarak tutulur.
"""
from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen

import pandas as pd


BASE_URL = os.environ.get("LSE_TERMINAL_URL", "http://127.0.0.1:7799").rstrip("/")
COLUMNS = ["open", "high", "low", "close", "volume"]
HISTORY_CACHE = (
    Path(__file__).resolve().parent.parent
    / "outputs" / "intraday" / "cache" / "lse"
)

SYMBOLS = {
    "NASDAQ100": ("NQ.F", "futures", 2016),
    "EURUSD": ("EUR/USD", "fx", 2009),
    "GBPUSD": ("GBP/USD", "fx", 2009),
}

_TF_DELTA = {
    "1m": pd.Timedelta(minutes=1),
    "5m": pd.Timedelta(minutes=5),
    "15m": pd.Timedelta(minutes=15),
    "1H": pd.Timedelta(hours=1),
    "4H": pd.Timedelta(hours=4),
    "1d": pd.Timedelta(days=1),
}


class LSEDataError(RuntimeError):
    """LSE terminaline veya verisine guvenli sekilde erisilemedi."""


def _get_json(path: str, params: dict, timeout: float = 30.0) -> dict:
    url = f"{BASE_URL}{path}?{urlencode(params)}"
    try:
        with urlopen(url, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise LSEDataError(f"LSE terminal API erisimi basarisiz: {exc}") from exc


def _normalize(candles: list[list]) -> pd.DataFrame:
    if not candles:
        return pd.DataFrame(columns=COLUMNS, dtype=float)
    frame = pd.DataFrame(candles, columns=["timestamp", *COLUMNS])
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], unit="s", utc=True)
    frame = frame.set_index("timestamp")[COLUMNS].astype(float).sort_index()
    frame = frame[~frame.index.duplicated(keep="last")]
    frame.attrs.update({"source": "lse-terminal", "expected_delay_minutes": 0})
    return frame


def _normalize_rows(rows: list[dict]) -> pd.DataFrame:
    if not rows:
        return pd.DataFrame(columns=COLUMNS, dtype=float)
    frame = pd.DataFrame(rows)
    timestamp = "timestamp" if "timestamp" in frame else "time"
    if timestamp not in frame:
        raise LSEDataError("LSE uzak API timestamp kolonu dondurmedi")
    missing = set(COLUMNS) - set(frame.columns)
    if missing:
        raise LSEDataError(f"LSE uzak API eksik kolonlar: {sorted(missing)}")
    frame[timestamp] = pd.to_datetime(frame[timestamp], utc=True)
    frame = frame.set_index(timestamp)[COLUMNS].astype(float).sort_index()
    frame = frame[~frame.index.duplicated(keep="last")]
    frame.attrs.update({"source": "lse-cloud", "expected_delay_minutes": 0})
    return frame


def candles(
    symbol_key: str,
    tf: str = "15m",
    *,
    limit: int = 5000,
    start: str | pd.Timestamp | None = None,
    end: str | pd.Timestamp | None = None,
    getter: Callable[[str, dict, float], dict] = _get_json,
) -> pd.DataFrame:
    """LSE'den UTC OHLCV al; terminal kapaliysa acik hata ver."""
    if symbol_key not in SYMBOLS:
        raise ValueError(f"LSE sembol eslemesi yok: {symbol_key}")
    if tf not in _TF_DELTA:
        raise ValueError(f"LSE zaman dilimi desteklenmiyor: {tf}")
    lse_symbol = SYMBOLS[symbol_key][0]
    params: dict[str, object] = {
        "provider": "lse",
        "symbol": lse_symbol,
        "timeframe": tf.lower(),
        "limit": min(max(int(limit), 1), 5000),
    }
    if start is not None:
        params["start"] = pd.Timestamp(start).isoformat()
    if end is not None:
        params["end"] = pd.Timestamp(end).isoformat()
    payload = getter("/api/candles", params, 30.0)
    return _normalize(payload.get("candles", []))


def remote_ohlcv(
    symbol_key: str,
    tf: str = "15m",
    days: int = 60,
    *,
    client_factory=None,
) -> pd.DataFrame:
    """GitHub Actions icin resmi LSE SDK/uzak vault uzerinden mum al."""
    if symbol_key not in SYMBOLS:
        raise ValueError(f"LSE sembol eslemesi yok: {symbol_key}")
    if client_factory is None:
        try:
            from lse import LSE
        except ModuleNotFoundError as exc:
            raise LSEDataError("lse-data paketi kurulu degil") from exc
        client_factory = LSE
    end = pd.Timestamp.now(tz="UTC")
    start = end - pd.Timedelta(days=days)
    try:
        client = client_factory()
        rows = client.candles(
            SYMBOLS[symbol_key][0], tf.lower(), start=start.isoformat(),
            end=end.isoformat(), limit=5000, order="asc",
        )
    except Exception as exc:
        raise LSEDataError(f"LSE uzak API basarisiz: {exc}") from exc
    return _normalize_rows(rows)


def ohlcv(symbol_key: str, tf: str = "15m", days: int = 60) -> pd.DataFrame:
    """Bulutta uzak LSE'yi, PC'de acik masaustu terminalini kullan."""
    if os.environ.get("LSE_API_KEY"):
        return remote_ohlcv(symbol_key, tf, days)
    end = pd.Timestamp.now(tz="UTC")
    start = end - pd.Timedelta(days=days)
    return candles(symbol_key, tf, start=start, end=end, limit=5000)


def _is_fresh(
    frame: pd.DataFrame,
    tf: str,
    now: datetime | pd.Timestamp,
    *,
    max_age_minutes: float,
    min_rows: int,
) -> tuple[bool, str]:
    if frame is None or len(frame) < min_rows:
        return False, f"yetersiz bar ({0 if frame is None else len(frame)})"
    index = pd.DatetimeIndex(frame.index)
    index = index.tz_localize("UTC") if index.tz is None else index.tz_convert("UTC")
    now_ts = pd.Timestamp(now)
    now_ts = now_ts.tz_localize("UTC") if now_ts.tzinfo is None else now_ts.tz_convert("UTC")
    closed = index[index + _TF_DELTA[tf] <= now_ts]
    if len(closed) == 0:
        return False, "tamamlanmis bar yok"
    age = (now_ts - (closed[-1] + _TF_DELTA[tf])).total_seconds() / 60
    if age > max_age_minutes:
        return False, f"son kapanmis bar {age:.0f} dakika eski"
    return True, "guncel"


def ohlcv_with_backup(
    symbol_key: str,
    tf: str,
    days: int,
    *,
    now: datetime | pd.Timestamp | None = None,
    primary: Callable[[str, str, int], pd.DataFrame] | None = None,
    backup: Callable[[str, str, int], pd.DataFrame] | None = None,
    max_age_minutes: float = 45,
    min_rows: int = 1,
) -> pd.DataFrame:
    """Birincil veri bozuk/bayatsa LSE'ye gec; iki kaynak da bayatsa dur."""
    if primary is None:
        from .signalbot import free_data

        primary = free_data.ohlcv
    backup = backup or ohlcv
    now = now or datetime.now(timezone.utc)
    errors: list[str] = []
    for name, fetch in (("birincil", primary), ("LSE yedek", backup)):
        try:
            frame = fetch(symbol_key, tf, days)
            ok, reason = _is_fresh(
                frame, tf, now,
                max_age_minutes=max_age_minutes,
                min_rows=min_rows,
            )
            if ok:
                frame.attrs["fallback_role"] = name
                return frame
            errors.append(f"{name}: {reason}")
        except Exception as exc:
            errors.append(f"{name}: {type(exc).__name__}: {exc}")
    raise LSEDataError("; ".join(errors))


def fetch_range(
    symbol_key: str,
    tf: str,
    start: pd.Timestamp,
    end: pd.Timestamp,
    *,
    fetch_page: Callable[..., pd.DataFrame] = candles,
    pause_seconds: float = 0.05,
) -> pd.DataFrame:
    """5000 bar API sinirini sayfalayarak tarih araligi indirir."""
    cursor = pd.Timestamp(start)
    end_ts = pd.Timestamp(end)
    parts: list[pd.DataFrame] = []
    while cursor < end_ts:
        page = fetch_page(symbol_key, tf, limit=5000, start=cursor, end=end_ts)
        if page.empty:
            break
        parts.append(page)
        next_cursor = pd.Timestamp(page.index[-1]) + _TF_DELTA[tf]
        if next_cursor <= cursor:
            raise LSEDataError("LSE sayfalama ilerlemedi")
        cursor = next_cursor
        if len(page) < 5000:
            break
        if pause_seconds:
            time.sleep(pause_seconds)
    if not parts:
        return pd.DataFrame(columns=COLUMNS, dtype=float)
    out = pd.concat(parts).sort_index()
    return out[~out.index.duplicated(keep="last")][COLUMNS].astype(float)


def download_history(
    symbol_key: str,
    tf: str,
    start_year: int,
    end_year: int,
    *,
    cache_dir: Path = HISTORY_CACHE,
    fetcher: Callable[..., pd.DataFrame] = fetch_range,
    on_progress: Callable[[str], None] | None = None,
) -> list[Path]:
    """Yillik, sikistirilmis ve atomik Parquet arsivi olusturur."""
    if symbol_key not in SYMBOLS:
        raise ValueError(f"LSE sembol eslemesi yok: {symbol_key}")
    first_year = SYMBOLS[symbol_key][2]
    cache_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    now = pd.Timestamp.now(tz="UTC")
    for year in range(max(start_year, first_year), end_year + 1):
        target = cache_dir / f"{symbol_key}_{tf}_{year}.parquet"
        if target.exists() and year < now.year:
            if on_progress:
                on_progress(f"{symbol_key} {year}: mevcut, atlandi")
            continue
        start = pd.Timestamp(year=year, month=1, day=1, tz="UTC")
        end = min(pd.Timestamp(year=year + 1, month=1, day=1, tz="UTC"), now)
        frame = fetcher(symbol_key, tf, start, end)
        if frame.empty:
            if on_progress:
                on_progress(f"{symbol_key} {year}: veri yok")
            continue
        temp = target.with_suffix(".parquet.part")
        try:
            frame.to_parquet(temp, compression="zstd")
            os.replace(temp, target)
        finally:
            if temp.exists():
                temp.unlink()
        written.append(target)
        if on_progress:
            on_progress(
                f"{symbol_key} {year}: {len(frame):,} bar, "
                f"{target.stat().st_size / 1024 / 1024:.2f} MB"
            )
    return written


def load_history(
    symbol_key: str,
    tf: str = "15m",
    *,
    cache_dir: Path = HISTORY_CACHE,
) -> pd.DataFrame:
    paths = sorted(cache_dir.glob(f"{symbol_key}_{tf}_*.parquet"))
    if not paths:
        raise FileNotFoundError(f"LSE gecmisi yok: {symbol_key} {tf} ({cache_dir})")
    frame = pd.concat(pd.read_parquet(path) for path in paths).sort_index()
    frame = frame[~frame.index.duplicated(keep="last")]
    index = pd.DatetimeIndex(frame.index)
    frame.index = index.tz_localize("UTC") if index.tz is None else index.tz_convert("UTC")
    return frame[COLUMNS].astype(float)

