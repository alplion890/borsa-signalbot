"""Frozen-day detection for the Dukascopy history cache (2026-11-06).

Found while testing Sweep: the worst long-history trade (-22.46R, 2013-02-25)
sat on bars that oscillated inside a ~2 point band for hours on a day the real
Nasdaq moved sharply. The cache also holds weekend/holiday filler days with
O=H=L=C. Such days are dropped from a CLEAN copy; the raw cache is untouched.

Rule (fixed before re-running any strategy):
- a day is frozen if >= FLAT_SHARE of its bars are flat (O=H=L=C), or
- its high-low range is < NARROW_RATIO x the median daily range of the
  previous MEDIAN_DAYS days (min 20 days of history).
"""
from __future__ import annotations

import datetime as dt

import pandas as pd

FLAT_SHARE = 0.80
NARROW_RATIO = 0.25
MEDIAN_DAYS = 60


def daily_table(df: pd.DataFrame) -> pd.DataFrame:
    day = pd.Index(df.index.date, name="day")
    flat = (df["open"] == df["high"]) & (df["high"] == df["low"]) & (df["low"] == df["close"])
    g = df.assign(flat=flat.to_numpy()).groupby(day)
    t = g.agg(h=("high", "max"), l=("low", "min"), c=("close", "last"),
              bars=("close", "size"), flat_share=("flat", "mean"))
    t["rng"] = (t["h"] - t["l"]) / t["c"]
    t["ref"] = t["rng"].rolling(MEDIAN_DAYS, min_periods=20).median().shift(1)
    return t


def frozen_days(df: pd.DataFrame) -> set[dt.date]:
    t = daily_table(df)
    narrow = t["ref"].notna() & (t["rng"] < NARROW_RATIO * t["ref"])
    flat = t["flat_share"] >= FLAT_SHARE
    return set(t.index[narrow | flat])


def clean(df: pd.DataFrame) -> pd.DataFrame:
    bad = frozen_days(df)
    if not bad:
        return df
    keep = ~pd.Index(df.index.date).isin(bad)
    return df[keep]
