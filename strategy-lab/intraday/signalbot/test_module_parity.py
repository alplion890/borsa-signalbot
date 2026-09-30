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


def test_final_module_count_and_weights():
    """Modul kumesini KILITLER -- sessiz ekleme/cikarma burada patlar.

    2026-08-28: GOLD_NY_ORB_TREND cikarildi (emekli).
    2026-09-11: NQ_ORB_STRONG_TREND negatif forward sonucuyla cikarildi.
    Bu satiri guncellemek kasitli bir karardi; gerekceler modules.py ve
    test_live_whitelist icinde kilitlidir.
    Listeyi degistiren herkes ayni seyi yapmali: once gerekce, sonra satir.
    """
    live = {m.name: m.weight for m in modules.default_modules()}
    assert live == {
        "SWEEP_CORE_AVOID_MID_VWAP": 1.0,
    }
