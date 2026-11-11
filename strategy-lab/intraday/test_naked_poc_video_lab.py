"""Naked-POC first touch: D filter, single use, confirmation, stop/target geometry."""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import naked_poc_video_lab as lab


def _two_days(drop_to: float = 1.0950) -> pd.DataFrame:
    """Day 1 balances around 1.1000 (POC mid-range); day 2 rallies then falls back onto it."""
    d1 = pd.date_range("2026-03-02 00:00", periods=96, freq="15min")
    d2 = pd.date_range("2026-03-03 00:00", periods=96, freq="15min")
    rng = np.random.default_rng(0)
    c1 = 1.1000 + rng.normal(0, 0.0003, 96)
    c1[:5] = 1.0960; c1[-5:] = 1.1040          # extremes away from the middle
    c2 = np.r_[np.linspace(1.1060, 1.1150, 40), np.linspace(1.1150, 1.1010, 30), np.full(26, np.nan)]
    c2[69] = 1.0995                             # touch bar
    c2[70:] = np.linspace(1.1012, 1.1150, 26)   # close-back rally
    c = np.r_[c1, c2]
    o = np.r_[c[0], c[:-1]]
    h = np.maximum(o, c) + 0.0002
    l = np.minimum(o, c) - 0.0002
    v = np.r_[np.where(np.abs(c1 - 1.1) < 0.0005, 50.0, 5.0), np.full(96, 5.0)]
    return pd.DataFrame({"open": o, "high": h, "low": l, "close": c, "volume": v}, index=d1.append(d2))


def test_d_shape_level_found_mid_range():
    df = _two_days()
    lv = lab.d_shaped_levels(df)
    assert lv and abs(lv[0].poc - 1.1000) < 0.0010


def test_first_touch_long_with_confirmation_and_geometry():
    df = _two_days()
    sig = lab.signals(df, 1.5)
    assert sig["le"].sum() == 1 and sig["se"].sum() == 0
    j = int(np.flatnonzero(sig["le"].to_numpy())[0])
    entry, sl, tp = df["close"].iloc[j], sig["lsl"].iloc[j], sig["ltp"].iloc[j]
    assert sl < entry and np.isclose(tp - entry, 1.5 * (entry - sl))


def test_level_used_only_once():
    df = _two_days()
    df2 = pd.concat([df, df.iloc[96:].set_axis(df.index[96:] + pd.Timedelta(days=1))])
    sig = lab.signals(df2, 1.5)
    lv = lab.d_shaped_levels(df2)
    assert sig["le"].sum() + sig["se"].sum() <= len(lv)
