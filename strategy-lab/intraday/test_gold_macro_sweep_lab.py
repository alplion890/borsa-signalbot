"""Gold makro-sweep adaylarinin kapsam ve seviye testleri."""
import pandas as pd

from .gold_macro_sweep_lab import CONTEXTS, ENTRIES, london_range_levels


def test_search_space_is_precommitted_to_ten_candidates():
    assert len(CONTEXTS) * len(ENTRIES) == 10


def test_london_range_uses_only_0700_to_1300_utc():
    idx = pd.date_range("2026-01-05 06:55", "2026-01-05 13:05", freq="5min")
    frame = pd.DataFrame({"open": 1.0, "high": 2.0, "low": 1.0,
                          "close": 1.5, "volume": 1.0}, index=idx)
    frame.loc["2026-01-05 06:55", "high"] = 99.0
    frame.loc["2026-01-05 13:00", "high"] = 88.0
    high, _ = london_range_levels(frame)
    assert high.loc["2026-01-05 13:05"] == 2.0
