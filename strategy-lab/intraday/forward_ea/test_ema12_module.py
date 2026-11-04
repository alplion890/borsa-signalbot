"""EMA12 first-5m PAPER rule, measured on Maven bars by the forward EA."""
from __future__ import annotations

import pandas as pd

from .modules import candidate_modules, ema12_first5m_detector


def _frame(last_close: float, end: str = "2026-11-04 14:30") -> pd.DataFrame:
    # Maven bars are naive UTC; 14:30 UTC = 09:30 New York in November (EST).
    idx = pd.date_range(end=end, periods=240, freq="5min")
    close = pd.Series(100.0, index=idx)
    close.iloc[-1] = last_close
    return pd.DataFrame({"open": close, "high": close + 1.0, "low": close - 1.0,
                         "close": close, "volume": 1.0}, index=idx)


def test_long_when_first_candle_closes_above_ema12():
    sig = ema12_first5m_detector(_frame(101.0))
    assert sig is not None and sig.direction == 1
    assert sig.entry == 101.0
    assert sig.sl == 99.0            # entry - candle range (2.0)


def test_short_when_first_candle_closes_below_ema12():
    sig = ema12_first5m_detector(_frame(99.0))
    assert sig is not None and sig.direction == -1
    assert sig.sl == 101.0


def test_ignores_other_bars_and_weekends():
    assert ema12_first5m_detector(_frame(101.0, end="2026-11-04 14:35")) is None
    assert ema12_first5m_detector(_frame(101.0, end="2026-11-07 14:30")) is None  # Saturday


def test_dst_summer_open_is_13_30_utc():
    assert ema12_first5m_detector(_frame(101.0, end="2026-07-01 13:30")) is not None


def test_registered_as_paper_candidate_with_six_hour_exit():
    mod = {m.name: m for m in candidate_modules()}["CAND_EMA12_FIRST5M"]
    assert (mod.symbol_key, mod.tf, mod.max_hold_bars, mod.weight) == \
        ("NASDAQ100", "5m", 72, 0.0)
