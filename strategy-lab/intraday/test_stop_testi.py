import numpy as np
import pandas as pd
import pytest

from intraday.stop_testi import Path5, adverse, apply_stop, first_stop


def test_first_stop_long_touch_gap_and_none() -> None:
    o = np.array([100.0, 99.0, 97.0])
    h = np.array([101.0, 99.5, 98.0])
    l = np.array([99.0, 98.5, 96.0])
    assert first_stop(o, h, l, 1, 98.0) == pytest.approx(97.0)  # bar 2 opens below stop -> gap fill at open
    assert first_stop(o, h, l, 1, 98.6) == pytest.approx(98.6)  # bar 1 low touches stop
    assert first_stop(o, h, l, 1, 95.0) is None


def test_first_stop_short_mirror() -> None:
    o = np.array([100.0, 103.0])
    h = np.array([101.0, 104.0])
    l = np.array([99.0, 102.0])
    assert first_stop(o, h, l, -1, 102.0) == pytest.approx(103.0)  # gap above stop -> open
    assert first_stop(o, h, l, -1, 100.5) == pytest.approx(100.5)
    assert adverse(o, h, l, -1, 100.0) == pytest.approx(4.0)


def test_apply_stop_only_uses_bars_inside_trade_window() -> None:
    idx = pd.date_range("2024-01-01 00:00", periods=4, freq="1h")
    path = Path5(pd.DataFrame({"open": [100, 100, 100, 100.0], "high": [101, 101, 101, 101.0],
                               "low": [99, 99, 90, 99.0]}, index=idx))
    tr = pd.DataFrame(dict(entry_ts=[idx[0]], exit_ts=[idx[2]], direction=[1], entry=[100.0],
                           exit=[100.5], atr=[2.0], nights=[0]))
    out = apply_stop(path, tr, 1.0)  # stop 98; bar 2 (low 90) is at exit time -> excluded
    assert not out["stopped"].iloc[0]
    assert out["gross"].iloc[0] == pytest.approx(0.005)
    out2 = apply_stop(path, tr.assign(exit_ts=[idx[3]]), 1.0)
    assert out2["stopped"].iloc[0]
    assert out2["gross"].iloc[0] == pytest.approx(-0.02)
    assert apply_stop(path, tr, None)["mae_atr"].iloc[0] == pytest.approx(0.5)
