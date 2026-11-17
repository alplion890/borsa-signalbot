import numpy as np
import pandas as pd

from intraday.kaynak_adaylari import boot_bounds, judge, nyse_days, third_friday


def test_nyse_days_match_known_year_counts():
    assert len(nyse_days("2022-01-01", "2022-12-31")) == 251
    assert len(nyse_days("2024-01-01", "2024-12-31")) == 252
    d = nyse_days("2021-12-30", "2022-01-04")
    assert pd.Timestamp("2021-12-31") in d  # Jan 1 2022 is Saturday: NYSE open on Fri Dec 31
    assert pd.Timestamp("2024-03-29") not in nyse_days("2024-03-25", "2024-04-01")  # Good Friday


def test_third_friday():
    assert third_friday(pd.Timestamp("2026-11-03")) == pd.Timestamp("2026-11-20")
    assert third_friday(pd.Timestamp("2024-03-15")) == pd.Timestamp("2024-03-15")


def test_judge_fails_zero_edge_and_passes_clear_edge():
    idx = pd.bdate_range("2015-01-01", periods=2000)
    rng = np.random.default_rng(0)
    noise = pd.Series(rng.normal(0, 0.001, len(idx)), index=idx)
    assert judge(noise - noise.mean(), 0.0001, 1, 5)["PASS"] is False
    assert judge(noise - noise.mean() + 0.002, 0.0001, 1, 5)["PASS"] is True
    assert judge(noise, None, 1, 5)["PASS"] is None


def test_boot_bounds_brackets_mean():
    x = np.random.default_rng(1).normal(0.001, 0.01, 500)
    lo, hi = boot_bounds(x, 0.025, 5)
    assert lo < x.mean() * 1e4 < hi
