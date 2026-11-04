"""Genis makro oyununun sabit iliski ve cogunluk testleri."""
from __future__ import annotations

import pandas as pd

from .cross_asset_positioning_ab import _daily_context


def test_nq_requires_true_majority_when_six_features_exist():
    days = pd.date_range("2026-01-01", periods=12, freq="B")
    trade = pd.DatetimeIndex([days[-1]])
    # Gecikmeli 5 gunluk degisim: uc destek, uc karsi -> skor 0, islem gecmez.
    sources = {}
    for name in ("dxy", "dgs2", "dgs10"):
        sources[name] = pd.Series(range(12), index=days, dtype=float)
    for name in ("real", "breakeven"):
        sources[name] = pd.Series(range(11, -1, -1), index=days, dtype=float)
    sources["es"] = pd.Series(range(12), index=days, dtype=float)
    result = _daily_context("SWEEP_CORE", trade, sources)
    assert result.iloc[0]["score"] == 0
    assert not result.iloc[0]["long_ok"]
    assert not result.iloc[0]["short_ok"]


def test_gold_expected_relations_can_form_long_majority():
    days = pd.date_range("2026-01-01", periods=12, freq="B")
    trade = pd.DatetimeIndex([days[-1]])
    down = pd.Series(range(11, -1, -1), index=days, dtype=float)
    up = pd.Series(range(12), index=days, dtype=float)
    sources = {"dxy": down, "dgs10": down, "real": down,
               "breakeven": up, "eur": up}
    result = _daily_context("GOLD_ORB", trade, sources)
    assert result.iloc[0]["score"] == 5
    assert result.iloc[0]["long_ok"]
