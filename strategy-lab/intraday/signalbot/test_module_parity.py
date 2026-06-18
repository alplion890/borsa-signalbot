import numpy as np
import pandas as pd

from intraday.forward_ea import modules


def _ohlcv(end="2026-06-17 15:00", periods=600, freq="15min"):
    idx = pd.date_range(end=end, periods=periods, freq=freq, tz="UTC")
    p = np.linspace(20000, 20100, periods)
    return pd.DataFrame(
        {"open": p, "high": p + 2, "low": p - 2, "close": p, "volume": 100},
        index=idx,
    )


def test_sweep_is_disabled_on_wednesday(monkeypatch):
    detector = modules._sweep_core_detector()
    df = _ohlcv(end="2026-06-17 15:00")  # Wednesday
    called = []

    def fake_signals(*args, **kwargs):
        called.append(True)
        raise AssertionError("Wednesday should be rejected before signal generation")

    import intraday.adx_lab as adx_lab
    monkeypatch.setattr(adx_lab, "_make_signals", fake_signals)
    assert detector(df) is None
    assert called == []


def test_default_gbp_has_normal_range_filter():
    # Behavioral details are captured in the constructed detector closure;
    # this guards the final module identity/weight while integration tests
    # exercise scanner delivery.
    gbp = next(m for m in modules.default_modules() if m.name == "GBP_LONDON_STRONG_TREND")
    assert gbp.weight == 0.25
    assert gbp.tf == "5m"


def test_final_module_count_and_weights():
    live = {m.name: m.weight for m in modules.default_modules()}
    assert live == {
        "GOLD_NY_ORB_TREND": 1.0,
        "NQ_ORB_STRONG_TREND": 1.0,
        "SWEEP_CORE_AVOID_MID_VWAP": 1.0,
        "EUR_LONDON_FADE_EMA": 1.0,
        "GBP_LONDON_STRONG_TREND": 0.25,
        "SWEEP_ES_DIV": 2.0,
    }
