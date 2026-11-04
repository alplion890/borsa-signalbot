"""Tum edge hiyerarsisinin sabit kapsam kontrolleri."""
from .cross_asset_positioning_ab import MODULES


def test_all_five_historical_edges_are_included():
    assert set(MODULES) == {
        "SWEEP_CORE", "NQ_ORB", "GOLD_ORB", "EUR_LONDON", "GBP_LONDON"
    }
