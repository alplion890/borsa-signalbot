"""Known answers for the independent execution reference."""
import numpy as np
import pandas as pd
import pytest

from .config import Instrument
from .execution_audit import reference_trades
from .honest_engine import simulate_trades, FILL_BAR_SL_FIRST, FILL_1M_THEN_SL_FIRST


def test_reference_reports_gap_price_time_and_cost():
    idx = pd.date_range("2026-01-01", periods=3, freq="15min")
    df = pd.DataFrame({"open": [100, 100, 97], "high": [100, 100.2, 98],
                       "low": [100, 99.8, 96], "close": [100, 100, 97]}, index=idx)
    signals = [pd.Series(x, index=idx) for x in
               ([True, False, False], [False]*3, [99]*3, [102]*3, [np.nan]*3, [np.nan]*3)]
    for mode in (FILL_BAR_SL_FIRST, FILL_1M_THEN_SL_FIRST):
        rows = reference_trades(df, signals, Instrument("TEST", "", .001, (0,24), 1), .5, 10, 50, mode)
        assert len(rows) == 1
        assert rows[0]["exit"] == 97
        assert rows[0]["exit_time"] == idx[2].isoformat()
        assert rows[0]["reason"] == "stop_gap"
        assert rows[0]["r"] == pytest.approx(-3.2)


@pytest.mark.parametrize("mode", [FILL_BAR_SL_FIRST, FILL_1M_THEN_SL_FIRST])
def test_state_machine_matches_engine_on_seeded_gapped_market(mode):
    rng = np.random.default_rng(20261025)
    n = 1500
    closes = 100 + rng.normal(0, .4, n).cumsum()
    opens = np.r_[closes[0], closes[:-1]] + rng.normal(0, .7, n)
    idx = pd.date_range("2026-01-01", periods=n, freq="15min")
    df = pd.DataFrame({"open": opens, "close": closes,
                       "high": np.maximum(opens, closes) + .3,
                       "low": np.minimum(opens, closes) - .3}, index=idx)
    le = rng.random(n) < .05
    se = (rng.random(n) < .05) & ~le
    signals = [pd.Series(x, index=idx) for x in (le, se, closes-1, closes+2, closes+1, closes-2)]
    inst = Instrument("TEST", "", .00009, (0,24), 1)
    ref = reference_trades(df, signals, inst, 1., 6., 20, mode)
    actual = simulate_trades(df, *signals, inst, min_rr=1., max_rr=6., max_hold=20, fill_mode=mode)
    assert list(actual.index) == [pd.Timestamp(r["signal_time"]) for r in ref]
    np.testing.assert_allclose(actual, [r["r"] for r in ref], rtol=0, atol=1e-10)
