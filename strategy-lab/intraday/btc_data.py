"""Binance BTC verisi + order flow deltası (ÜCRETSIZ, gerçek agresör tarafı).

Binance kline'ları her mumda 'taker buy base volume' içerir (index 9).
delta = taker_buy - taker_sell = 2*taker_buy - toplam_hacim
Bu, gerçek footprint/CVD'nin mum-bazlı (tick'siz) özetidir — yüksek HTF
order flow için doğru ve yeterli.
"""
from __future__ import annotations

import time
from pathlib import Path

import pandas as pd
import requests

CACHE = Path(__file__).resolve().parent.parent / "outputs" / "intraday" / "cache"
CACHE.mkdir(parents=True, exist_ok=True)

_BASE = "https://api.binance.com/api/v3/klines"
_MS = {"5m": 300_000, "15m": 900_000, "1h": 3_600_000, "4h": 14_400_000}


def load_btc(interval: str = "4h", days: int = 1080, symbol: str = "BTCUSDT") -> pd.DataFrame:
    """OHLCV + delta + cvd döner (UTC index, tz-naive)."""
    cached = CACHE / f"{symbol}_{interval}_{days}d_of.csv"
    if cached.exists():
        df = pd.read_csv(cached, parse_dates=["timestamp"]).set_index("timestamp")
        return df.sort_index()

    step = _MS[interval]
    end = int(time.time() * 1000)
    start = end - days * 86_400_000
    rows = []
    cur = start
    while cur < end:
        r = requests.get(
            _BASE,
            params={"symbol": symbol, "interval": interval, "startTime": cur, "limit": 1000},
            timeout=30,
        )
        r.raise_for_status()
        batch = r.json()
        if not batch:
            break
        rows.extend(batch)
        cur = batch[-1][0] + step
        if len(batch) < 1000:
            break
        time.sleep(0.25)

    df = pd.DataFrame(
        rows,
        columns=[
            "open_time", "open", "high", "low", "close", "volume",
            "close_time", "qav", "trades", "taker_buy_base", "taker_buy_quote", "ignore",
        ],
    )
    for c in ("open", "high", "low", "close", "volume", "taker_buy_base"):
        df[c] = df[c].astype(float)
    df["timestamp"] = pd.to_datetime(df["open_time"], unit="ms", utc=True).dt.tz_convert(None)
    df = df.drop_duplicates("timestamp").set_index("timestamp").sort_index()

    # Order flow: mum başına net agresör deltası ve kümülatif (CVD)
    df["delta"] = 2 * df["taker_buy_base"] - df["volume"]
    df["cvd"] = df["delta"].cumsum()
    out = df[["open", "high", "low", "close", "volume", "delta", "cvd"]]
    out.to_csv(cached)
    return out
