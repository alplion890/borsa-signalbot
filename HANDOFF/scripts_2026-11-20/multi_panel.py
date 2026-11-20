"""Build daily panels for untested-family tests (no parameters chosen here).

- Close snapshot: last bar at/before 21:00 UTC on each weekday (one common clock for all markets -> no cross-sectional look-ahead).
- US index intraday legs for overnight MR: NY 16:00 close -> NY 09:30 open (overnight), NY 09:30 -> 16:00 (day), DST-aware.
Data: Dukascopy cache via history_fetch.load_history + data_quality.clean; BTC from Binance 1h cache.
Output: outputs/intraday/untested_families/{close.csv, us_legs.csv}
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, ".")
from intraday.data_quality import clean  # noqa: E402
from intraday.history_fetch import load_history  # noqa: E402

OUT = Path("outputs/intraday/untested_families")
SYMS = {"AUDUSD": "5m", "EURUSD": "5m", "GBPUSD": "5m", "USDCAD": "5m", "USDCHF": "5m", "USDJPY": "5m",
        "XAUUSD": "5m", "NASDAQ100": "15m", "SP500": "15m", "US30": "5m", "US2000": "5m",
        "UK100": "5m", "FRA40": "5m", "JAP225": "5m"}
US = ["NASDAQ100", "SP500", "US30", "US2000"]
NY = "America/New_York"


def snap_close(df: pd.DataFrame) -> pd.Series:
    x = df["close"]
    day = x.index.normalize()
    keep = x.index.hour < 21
    s = x[keep].groupby(day[keep]).last()
    return s[s.index.dayofweek < 5]


def ny_legs(df: pd.DataFrame) -> pd.DataFrame:
    idx = df.index.tz_localize("UTC").tz_convert(NY)
    o = pd.Series(df["open"].to_numpy(), index=idx)
    c = pd.Series(df["close"].to_numpy(), index=idx)
    d = idx.normalize()
    mins = idx.hour * 60 + idx.minute
    open_px = o[mins == 9 * 60 + 30].groupby(d[mins == 9 * 60 + 30]).first()
    sess = (mins >= 9 * 60 + 30) & (mins < 16 * 60)
    close_px = c[sess].groupby(d[sess]).last()
    t = pd.DataFrame({"open": open_px, "close": close_px}).dropna()
    t["overnight"] = t["open"] / t["close"].shift(1) - 1
    t["day"] = t["close"] / t["open"] - 1
    t.index = t.index.tz_localize(None)
    return t.dropna()


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    closes, legs = {}, {}
    for s, tf in SYMS.items():
        df = clean(load_history(s, tf, start_year=2012))
        closes[s] = snap_close(df)
        if s in US:
            legs[s] = ny_legs(df)
        print(s, tf, closes[s].index.min().date(), closes[s].index.max().date(), len(closes[s]))
    b = pd.read_csv("outputs/intraday/cache/binance/BTCUSDT_1h.csv", parse_dates=["ts"]).set_index("ts")
    closes["BTCUSD"] = snap_close(b.rename(columns=str.lower))
    print("BTCUSD", closes["BTCUSD"].index.min().date(), len(closes["BTCUSD"]))
    pd.DataFrame(closes).sort_index().to_csv(OUT / "close.csv")
    pd.concat({k: v[["overnight", "day"]] for k, v in legs.items()}, axis=1).to_csv(OUT / "us_legs.csv")


if __name__ == "__main__":
    main()
