"""Lab simulator must equal honest_engine with empty masks; masks behave."""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import sweep_prop_lab as lab
from .config import INSTRUMENTS
from .honest_engine import simulate_trades


def _frame(n=600, seed=3):
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2026-01-05", periods=n, freq="15min")
    close = 100 + np.cumsum(rng.normal(0, 0.3, n))
    high = close + rng.uniform(0.05, 0.6, n); low = close - rng.uniform(0.05, 0.6, n)
    df = pd.DataFrame({"open": np.r_[close[0], close[:-1]], "high": high, "low": low,
                       "close": close, "volume": 1.0}, index=idx)
    le = pd.Series(rng.random(n) < 0.03, index=idx); se = pd.Series(rng.random(n) < 0.03, index=idx)
    lsl = df.low - 0.5; ltp = df.close + 2.0; ssl = df.high + 0.5; stp = df.close - 2.0
    return df, le, se, lsl, ltp, ssl, stp


def test_empty_masks_match_engine_exactly():
    df, *sig = _frame()
    inst = INSTRUMENTS["NASDAQ100"]
    ref = simulate_trades(df, *sig, inst, min_rr=2.0, max_rr=8.0, max_hold=40)
    got = lab.simulate(df, *sig, inst, 2.0, 8.0, 40)
    assert ref.index.equals(got.index) and np.allclose(ref, got)


def test_no_entry_mask_blocks_and_force_exit_closes_early():
    df, *sig = _frame()
    inst = INSTRUMENTS["NASDAQ100"]
    allblock = pd.Series(True, index=df.index)
    assert lab.simulate(df, *sig, inst, 2.0, 8.0, 40, no_entry=allblock).empty
    base = lab.simulate(df, *sig, inst, 2.0, 8.0, 40)
    forced = lab.simulate(df, *sig, inst, 2.0, 8.0, 40, force_exit=allblock)
    assert len(forced) >= len(base)  # exiting every bar frees the slot sooner


def test_prop_masks_friday_late_and_news_window():
    idx = pd.DatetimeIndex(["2026-11-06 19:45", "2026-11-06 20:00", "2026-11-06 13:15",
                            "2026-11-06 13:30", "2026-11-05 13:15"])
    no_entry, friday = lab.prop_masks(idx)
    assert list(friday) == [False, True, False, False, False]
    # 13:15 bar closes 13:30 UTC = NFP 08:30 ET on 2026-11-06 -> blocked
    assert bool(no_entry.iloc[2]) and not bool(no_entry.iloc[3]) and not bool(no_entry.iloc[4])
