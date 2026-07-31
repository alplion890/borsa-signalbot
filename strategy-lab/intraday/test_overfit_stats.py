"""overfit_stats testleri.

Amac: bir aday portfoyun/modulun exp_R'si, KAC aday taranarak bulundugunu
hesaba katinca hala anlamli mi? Bu dosya o istatistigin dogru davrandigini
sabitler.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from .overfit_stats import (
    align_trials,
    deflated_sharpe_ratio,
    deflated_from_trials,
    expected_max_sharpe,
    probabilistic_sharpe_ratio,
    probability_of_backtest_overfitting,
    sharpe,
)


def _r_series(values, start="2024-01-01", freq="D") -> pd.Series:
    idx = pd.date_range(start, periods=len(values), freq=freq)
    return pd.Series(np.asarray(values, dtype=float), index=idx)


def _noise_trials(n_trials: int, n_obs: int, seed: int) -> dict[str, pd.Series]:
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2024-01-01", periods=n_obs, freq="D")
    return {
        f"t{i}": pd.Series(rng.normal(0.0, 1.0, n_obs), index=idx)
        for i in range(n_trials)
    }


# --- sharpe -----------------------------------------------------------------


def test_sharpe_positive_series() -> None:
    r = _r_series([1.0, -0.5, 1.0, -0.5, 1.0, -0.5])
    assert sharpe(r) > 0


def test_sharpe_zero_variance_is_nan() -> None:
    assert np.isnan(sharpe(_r_series([0.3] * 20)))


def test_sharpe_too_few_observations_is_nan() -> None:
    assert np.isnan(sharpe(_r_series([1.0])))


# --- probabilistic sharpe ---------------------------------------------------


def test_psr_is_a_probability() -> None:
    r = _r_series(np.random.default_rng(0).normal(0.05, 1.0, 300))
    p = probabilistic_sharpe_ratio(r)
    assert 0.0 <= p <= 1.0


def test_psr_grows_with_sample_size() -> None:
    """Ayni pozitif SR, daha cok islem -> daha yuksek guven."""
    small = _r_series([1.5, -1.0] * 30)
    big = _r_series(np.tile(small.to_numpy(), 10))
    assert sharpe(small) > 0
    assert probabilistic_sharpe_ratio(big) > probabilistic_sharpe_ratio(small)


def test_psr_falls_when_benchmark_rises() -> None:
    r = _r_series(np.random.default_rng(3).normal(0.15, 1.0, 400))
    assert probabilistic_sharpe_ratio(r, sr_benchmark=0.30) < probabilistic_sharpe_ratio(r)


# --- expected max sharpe (coklu-karsilastirma esigi) ------------------------


def test_expected_max_sharpe_zero_when_no_dispersion() -> None:
    assert expected_max_sharpe(500, 0.0) == 0.0


def test_expected_max_sharpe_grows_with_trial_count() -> None:
    assert expected_max_sharpe(500, 0.04) > expected_max_sharpe(5, 0.04)


def test_expected_max_sharpe_single_trial_is_zero() -> None:
    assert expected_max_sharpe(1, 0.04) == 0.0


# --- deflated sharpe --------------------------------------------------------


def test_dsr_penalises_larger_search() -> None:
    r = _r_series(np.random.default_rng(11).normal(0.12, 1.0, 400))
    few = deflated_sharpe_ratio(r, n_trials=2, sr_variance=0.02)
    many = deflated_sharpe_ratio(r, n_trials=500, sr_variance=0.02)
    assert many < few


def test_dsr_rejects_best_of_pure_noise() -> None:
    """200 gurultu adayinin en iyisi 'edge' degildir -> DSR dusuk olmali."""
    trials = _noise_trials(200, 250, seed=42)
    out = deflated_from_trials(trials)
    assert out["best"].startswith("t")
    assert out["sharpe"] > 0  # kagitta iyi gorunuyor
    assert out["dsr"] < 0.95  # ama coklu-karsilastirma sonrasi anlamli degil


def test_dsr_keeps_a_real_edge() -> None:
    """Gercek sinyal + gurultu adaylari -> gercek olan gecmeli."""
    trials = _noise_trials(200, 500, seed=5)
    rng = np.random.default_rng(99)
    idx = list(trials.values())[0].index
    trials["gercek"] = pd.Series(rng.normal(0.45, 1.0, len(idx)), index=idx)
    out = deflated_from_trials(trials)
    assert out["best"] == "gercek"
    assert out["dsr"] > 0.95


def test_dsr_is_nan_for_degenerate_input() -> None:
    assert np.isnan(deflated_sharpe_ratio(_r_series([1.0]), n_trials=10, sr_variance=0.02))


# --- PBO (CSCV) -------------------------------------------------------------


def test_pbo_of_pure_noise_is_near_coin_flip() -> None:
    trials = _noise_trials(40, 240, seed=13)
    out = probability_of_backtest_overfitting(align_trials(trials), n_splits=8)
    assert 0.25 <= out["pbo"] <= 0.75


def test_pbo_low_when_one_trial_has_persistent_edge() -> None:
    trials = _noise_trials(40, 240, seed=21)
    idx = list(trials.values())[0].index
    rng = np.random.default_rng(77)
    trials["gercek"] = pd.Series(rng.normal(0.5, 1.0, len(idx)), index=idx)
    out = probability_of_backtest_overfitting(align_trials(trials), n_splits=8)
    assert out["pbo"] < 0.25


def test_pbo_needs_even_split_count() -> None:
    with pytest.raises(ValueError):
        probability_of_backtest_overfitting(align_trials(_noise_trials(5, 100, seed=1)), n_splits=7)


def test_pbo_needs_at_least_two_trials() -> None:
    with pytest.raises(ValueError):
        probability_of_backtest_overfitting(align_trials(_noise_trials(1, 100, seed=1)))


# --- align_trials -----------------------------------------------------------


def test_align_trials_buckets_unaligned_trade_ledgers() -> None:
    """Gercek kullanim: her adayin islem zamanlari farkli. Haftaliga toplanir."""
    a = _r_series([1.0, -1.0, 2.0], start="2024-01-01", freq="D")
    b = _r_series([0.5, 0.5], start="2024-01-08", freq="D")
    m = align_trials({"a": a, "b": b}, freq="W")
    assert list(m.columns) == ["a", "b"]
    assert m.isna().sum().sum() == 0  # islem olmayan hafta 0R, NaN degil
    assert m["a"].sum() == pytest.approx(2.0)
    assert m["b"].sum() == pytest.approx(1.0)


def test_align_trials_rejects_empty_input() -> None:
    with pytest.raises(ValueError):
        align_trials({})
