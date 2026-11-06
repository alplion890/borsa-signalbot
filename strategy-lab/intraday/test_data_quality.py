"""Frozen-day detection: flat filler days and implausibly narrow days."""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import data_quality as dq


def _days(n_days=80, seed=1):
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2026-01-05", periods=n_days * 96, freq="15min")
    close = 100 + np.cumsum(rng.normal(0, 0.2, len(idx)))
    df = pd.DataFrame({"open": close, "high": close + 0.3, "low": close - 0.3,
                       "close": close, "volume": 1.0}, index=idx)
    return df


def test_flat_filler_day_is_frozen():
    df = _days()
    day = df.index.normalize() == pd.Timestamp("2026-03-10")
    df.loc[day, ["open", "high", "low", "close"]] = 101.0
    assert pd.Timestamp("2026-03-10").date() in dq.frozen_days(df)


def test_narrow_oscillating_day_is_frozen():
    df = _days()
    day = df.index.normalize() == pd.Timestamp("2026-03-12")
    k = int(day.sum())
    base = 100 + np.tile([0.0, 0.01], k // 2)
    df.loc[day, "open"] = base; df.loc[day, "close"] = base[::-1]
    df.loc[day, "high"] = base + 0.02; df.loc[day, "low"] = base - 0.02
    assert pd.Timestamp("2026-03-12").date() in dq.frozen_days(df)


def test_normal_days_are_kept_and_clean_drops_only_frozen():
    df = _days()
    day = df.index.normalize() == pd.Timestamp("2026-03-10")
    df.loc[day, ["open", "high", "low", "close"]] = 101.0
    frozen = dq.frozen_days(df)
    assert frozen == {pd.Timestamp("2026-03-10").date()}
    clean = dq.clean(df)
    assert len(clean) == len(df) - int(day.sum())
    assert not (clean.index.normalize() == pd.Timestamp("2026-03-10")).any()
