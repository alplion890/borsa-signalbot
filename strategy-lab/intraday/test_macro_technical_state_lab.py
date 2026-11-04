"""Makro-teknik durum stratejisinin temel zaman kontrolleri."""
import pandas as pd

from .macro_technical_state_lab import ASSETS, hourly_setup, rolling_vwap


def test_all_four_underlyings_are_tested_independently_of_existing_edges():
    assert {x[0] for x in ASSETS.values()} == {
        "NASDAQ100", "XAUUSD", "EURUSD", "GBPUSD"
    }


def test_rolling_vwap_needs_twenty_closed_bars():
    idx = pd.date_range("2026-01-01", periods=25, freq="1h")
    frame = pd.DataFrame({"open": 1.0, "high": 2.0, "low": 0.5,
                          "close": 1.5, "volume": 10.0}, index=idx)
    out = rolling_vwap(frame)
    assert out.iloc[:19].isna().all()
    assert pd.notna(out.iloc[19])


def test_hourly_setup_is_constant_inside_next_closed_hour():
    idx = pd.date_range("2026-01-01", periods=100 * 12, freq="5min")
    close = pd.Series(range(len(idx)), index=idx, dtype=float) + 100.0
    frame = pd.DataFrame({"open": close - 0.1, "high": close + 0.2,
                          "low": close - 0.2, "close": close, "volume": 10.0})
    long, short = hourly_setup(frame, adx_min=0.0)
    assert long.loc["2026-01-03 12:00":"2026-01-03 12:55"].nunique() == 1
    assert short.loc["2026-01-03 12:00":"2026-01-03 12:55"].nunique() == 1
