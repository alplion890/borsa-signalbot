"""Hiyerarsik edge taramasinin zaman ve kombinasyon kontrolleri."""
import pandas as pd

from .hierarchical_edge_lab import (ENTRY_MODES, MACRO_MODES, WEEKLY_MODES,
                                    cash_session_vwap, hourly_ema_trend)


def _bars(index):
    return pd.DataFrame({"open": range(1, len(index) + 1),
                         "high": range(2, len(index) + 2),
                         "low": range(len(index)),
                         "close": range(1, len(index) + 1),
                         "volume": 1.0}, index=index, dtype=float)


def test_search_space_is_precommitted_to_32_candidates():
    assert len(ENTRY_MODES) * len(WEEKLY_MODES) * len(MACRO_MODES) == 32


def test_cash_vwap_starts_at_new_york_open_and_handles_dst():
    # 13:30 UTC yaz saatinde New York 09:30'dur.
    idx = pd.date_range("2026-06-01 13:25", periods=4, freq="5min")
    vwap, window = cash_session_vwap(_bars(idx))
    assert pd.isna(vwap.iloc[0])
    assert pd.notna(vwap.iloc[1])
    assert not window.iloc[1]  # 09:30; giris penceresi 10:00'da baslar.


def test_hourly_trend_is_not_available_before_hour_closes():
    idx = pd.date_range("2026-01-01", periods=80 * 12, freq="5min")
    df = _bars(idx)
    trend = hourly_ema_trend(df)
    # Saat icindeki tum 5m barlar ayni son kapanmis saat degerini gorur.
    hour = trend.loc["2026-01-03 12:00":"2026-01-03 12:55"]
    assert hour.nunique() == 1
