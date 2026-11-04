"""COT/OI/funding A/B deneyinin zaman hizalama kontrolleri."""
from __future__ import annotations

import pandas as pd

from .positioning_context_ab import _asof_features


def test_cot_tuesday_report_is_not_visible_before_following_monday():
    bars = pd.DatetimeIndex([
        "2026-01-09 18:00+00:00",  # Friday before conservative availability
        "2026-01-12 13:00+00:00",  # Monday
    ])
    cot = pd.DataFrame({
        "available_date": pd.to_datetime(["2026-01-12"]),
        "oi_change": [100.0], "lev_net_change": [20.0],
        "asset_net_change": [30.0],
    })
    funding = pd.DataFrame({
        "available_at": pd.to_datetime(["2026-01-01"], utc=True),
        "funding_3d": [0.0001],
    })
    result = _asof_features(bars, cot, funding)
    assert pd.isna(result.iloc[0]["oi_change"])
    assert result.iloc[1]["oi_change"] == 100.0


def test_funding_uses_only_last_published_observation():
    bars = pd.DatetimeIndex(["2026-01-12 07:59+00:00", "2026-01-12 08:01+00:00"])
    cot = pd.DataFrame({
        "available_date": pd.to_datetime(["2026-01-01"]),
        "oi_change": [1.0], "lev_net_change": [1.0], "asset_net_change": [1.0],
    })
    funding = pd.DataFrame({
        "available_at": pd.to_datetime([
            "2026-01-12 00:00+00:00", "2026-01-12 08:00+00:00"
        ]),
        "funding_3d": [-0.001, 0.002],
    })
    result = _asof_features(bars, cot, funding)
    assert result.iloc[0]["funding_3d"] == -0.001
    assert result.iloc[1]["funding_3d"] == 0.002


def test_funding_accepts_mixed_iso_precision():
    bars = pd.DatetimeIndex(["2026-01-12 08:01+00:00"])
    cot = pd.DataFrame({
        "available_date": pd.to_datetime(["2026-01-01"]),
        "oi_change": [1.0], "lev_net_change": [1.0], "asset_net_change": [1.0],
    })
    funding = pd.DataFrame({
        "available_at": ["2026-01-12 00:00:00+00:00",
                         "2026-01-12 08:00:00.001000+00:00"],
        "funding_3d": [-0.001, 0.002],
    })
    result = _asof_features(bars, cot, funding)
    assert result.iloc[0]["funding_3d"] == 0.002
