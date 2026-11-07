"""14-day execution trial (prereg HANDOFF/icra_denemesi_14gun_onkayit_2026-11-07.md).

XAU Donchian N20 1H is measured on Maven as a candidate AND, only during the
trial window, alerted on Telegram. Other candidates stay silent.
"""
from __future__ import annotations

import datetime as dt

import numpy as np
import pandas as pd

from . import modules, notify
from .positions import PaperPosition

UTC = dt.timezone.utc


def _frame(breakout: float) -> pd.DataFrame:
    idx = pd.date_range("2026-11-09", periods=260, freq="1h")
    close = pd.Series(4000.0 + np.sin(np.arange(260)) * 2, index=idx)
    close.iloc[-1] = breakout
    return pd.DataFrame({"open": close, "high": close + 1, "low": close - 1,
                         "close": close, "volume": 1.0}, index=idx)


def test_donchian_long_on_close_above_prior_20_high():
    df = _frame(4010.0)
    sig = modules.donchian_detector(20, 2.0)(df)
    upper = df["high"].iloc[-21:-1].max(); lower = df["low"].iloc[-21:-1].min()
    assert sig is not None and sig.direction == 1
    assert sig.sl == lower
    assert sig.tp == 4010.0 + 2.0 * (4010.0 - lower)
    assert upper < 4010.0


def test_donchian_short_and_no_signal_inside_channel():
    assert modules.donchian_detector(20, 2.0)(_frame(3990.0)).direction == -1
    assert modules.donchian_detector(20, 2.0)(_frame(4000.5)) is None


def test_registered_as_candidate_1h_200_bars():
    mod = {m.name: m for m in modules.candidate_modules()}["CAND_DONCHIAN_XAU_1H"]
    assert (mod.symbol_key, mod.tf, mod.weight, mod.max_hold_bars) == ("XAUUSD", "1H", 0.0, 200)


def _pos(module: str, when: dt.datetime) -> PaperPosition:
    return PaperPosition(module=module, symbol="XAUUSD", direction=1,
                         entry_time=pd.Timestamp(when).tz_convert(None), entry=4010.0,
                         sl=3995.0, tp=4040.0, weight=0.0, max_hold_bars=200,
                         cost_per_side=0.00012)


def test_trial_candidate_is_alerted_inside_window_only():
    now = dt.datetime(2026, 11, 12, 10, 3, tzinfo=UTC)
    sent = notify.notify_new_positions(
        [_pos("CAND_DONCHIAN_XAU_1H", now - dt.timedelta(minutes=3))], now=now,
        send_fn=lambda m: None)
    assert len(sent) == 1 and "XAUUSD" in sent[0] and "4040" in sent[0]
    assert "ICRA DENEMESI" in sent[0]
    later = dt.datetime(2026, 11, 23, 10, 3, tzinfo=UTC)
    assert notify.notify_new_positions(
        [_pos("CAND_DONCHIAN_XAU_1H", later - dt.timedelta(minutes=3))], now=later,
        send_fn=lambda m: None) == []


def test_other_candidates_stay_silent_during_trial():
    now = dt.datetime(2026, 11, 12, 10, 3, tzinfo=UTC)
    assert notify.notify_new_positions(
        [_pos("CAND_SWEEP_SP500", now - dt.timedelta(minutes=3))], now=now,
        send_fn=lambda m: None) == []
