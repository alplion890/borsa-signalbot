"""Execution cases with predetermined answers, including stop-market gaps."""
import pytest

from . import honest_engine as he
from .test_honest_engine_1m import FREE, OLD, NEW, _frame15, _frame1m, _run


@pytest.mark.parametrize("mode", [OLD, NEW])
@pytest.mark.parametrize("fast", [False, True])
@pytest.mark.parametrize("side", ["long", "short"])
def test_open_position_stop_gap_fills_at_open(mode, fast, side, monkeypatch):
    monkeypatch.setattr(he, "FAST_CORE_AVAILABLE", fast and he.FAST_CORE_AVAILABLE)
    rows = [(100, 100, 100, 100), (100, 100.2, 99.8, 100), (97, 98, 96, 97)]
    if side == "short":
        rows = [(200-o, 200-l, 200-h, 200-c) for o, h, l, c in rows]
    sl, tp = (99, 102) if side == "long" else (101, 98)
    assert _run(_frame15(rows), sl, tp, side=side, fill_mode=mode).iloc[0] == pytest.approx(-3)


@pytest.mark.parametrize("mode", [OLD, NEW])
@pytest.mark.parametrize("side", ["long", "short"])
def test_target_already_marketable_at_open_precedes_later_stop(mode, side):
    rows = [(100, 100, 100, 100), (100, 100.2, 99.8, 100), (103, 104, 98, 100)]
    if side == "short":
        rows = [(200-o, 200-l, 200-h, 200-c) for o, h, l, c in rows]
    sl, tp = (99, 102) if side == "long" else (101, 98)
    # Target is a resting limit: no assumed positive price improvement.
    assert _run(_frame15(rows), sl, tp, side=side, fill_mode=mode).iloc[0] == pytest.approx(2)


@pytest.mark.parametrize("side", ["long", "short"])
def test_gap_inside_ambiguous_parent_bar_uses_first_minute_open(side):
    rows = [(100, 100, 100, 100), (100, 103, 96, 100)]
    minutes = [(100, 100.2, 99.8, 100), (97, 98, 96, 97), (97, 103, 97, 102)]
    if side == "short":
        rows = [(200-o, 200-l, 200-h, 200-c) for o, h, l, c in rows]
        minutes = [(200-o, 200-l, 200-h, 200-c) for o, h, l, c in minutes]
    sl, tp = (99, 102) if side == "long" else (101, 98)
    m1 = _frame1m("2026-01-01 00:15", minutes)
    assert _run(_frame15(rows), sl, tp, side=side, df_1m=m1).iloc[0] == pytest.approx(-3)


def test_missing_minutes_before_target_cannot_prove_target_first():
    df = _frame15([(100, 100, 100, 100), (100, 103, 98, 100)])
    late = _frame1m("2026-01-01 00:17", [(100, 103, 100, 102)])
    assert _run(df, 99, 102, df_1m=late).iloc[0] == pytest.approx(-1)


def test_gap_loss_still_pays_round_trip_cost():
    from .config import Instrument
    costly = Instrument("TEST", "", .001, (0, 24), 1)
    df = _frame15([(100, 100, 100, 100), (100, 100.2, 99.8, 100), (97, 98, 96, 97)])
    for mode in (OLD, NEW):
        assert _run(df, 99, 102, inst=costly, fill_mode=mode).iloc[0] == pytest.approx(-3.2)
