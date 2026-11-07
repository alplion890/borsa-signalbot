"""Indicator formulas and the dip -> cross -> flip sequence of the video lab."""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import rsiband_st_video_lab as lab


def _df(n=400, seed=1):
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2026-01-01", periods=n, freq="1h")
    c = 100 + np.cumsum(rng.normal(0, 0.5, n))
    o = np.r_[c[0], c[:-1]]
    h = np.maximum(o, c) + rng.uniform(0.05, 0.5, n)
    l = np.minimum(o, c) - rng.uniform(0.05, 0.5, n)
    return pd.DataFrame({"open": o, "high": h, "low": l, "close": c, "volume": 1.0}, index=idx)


def test_heikin_ashi_recursion():
    df = _df(10)
    ha = lab.heikin_ashi(df)
    assert np.isclose(ha["close"].iloc[3], df.iloc[3][["open", "high", "low", "close"]].mean())
    assert np.isclose(ha["open"].iloc[3], (ha["open"].iloc[2] + ha["close"].iloc[2]) / 2)
    assert (ha["high"] >= ha[["open", "close"]].max(axis=1)).all()


def test_rsi_bands_bracket_price():
    """Bands sit above/below price most of the time and never cross each other."""
    df = _df(300)
    ub, lb = lab.rsi_bands(df["close"], 12, 70, 30)
    c = df["close"].iloc[50:]
    assert (ub.iloc[50:] > lb.iloc[50:]).all()
    assert ((c < ub.iloc[50:]) & (c > lb.iloc[50:])).mean() > 0.8


def test_sequence_requires_order_and_resets():
    n = 20
    arm = np.zeros(n, bool); cross = np.zeros(n, bool); tdi = np.zeros(n, bool); flip = np.zeros(n, bool)
    arm[2] = True; cross[4] = True; flip[6] = True; flip[8] = True
    s = lab._sequence(arm, cross, tdi, flip, need_tdi=False)
    assert s[6] and not s[8]              # only first flip after the cross
    assert not lab._sequence(arm, cross, tdi, flip, need_tdi=True)[6]
    arm2 = np.zeros(n, bool); arm2[2] = True
    cross2 = np.zeros(n, bool)
    assert not lab._sequence(arm2, cross2, tdi, flip, False).any()   # no cross -> no signal


def test_sequence_expires():
    n = 60
    arm = np.zeros(n, bool); cross = np.zeros(n, bool); flip = np.zeros(n, bool)
    arm[0] = True; cross[1] = True; flip[lab.ARM_BARS + 5] = True
    assert not lab._sequence(arm, cross, np.zeros(n, bool), flip, False).any()


def test_build_runs_and_signals_are_bool():
    df = _df(800)
    sig = lab.build(df)
    le, se = sig["A"]
    assert le.dtype == bool and se.dtype == bool
    assert not (le & se).any()
    r = lab.run_one(df, "BTCUSDT", sig, "A", 0.5)
    assert r.notna().all()
