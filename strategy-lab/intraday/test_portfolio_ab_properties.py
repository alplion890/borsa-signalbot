"""Property tests for portfolio_ab's Monte-Carlo cores.

The vectorised simulators draw from an rng; a recording rng captures every draw so each path's
trades can be replayed through an independent rulebook. Rule numbers are the pre-registered spec
values (docs/superpowers/specs/2026-08-14-portfoy-kompozisyonu-design.md) and must not drift.
"""
import numpy as np
from hypothesis import given, settings, strategies as st

from intraday.portfolio_ab import challenge_equity_after, simulate_challenge, simulate_funded

CH_RISK, CH_RISK_AFTER_WIN, CH_TARGET, CH_STOP = 0.015, 0.03, 0.04, -0.08
FU_RISK, FU_DAILY_LOSS, FU_TRAILING_DD = 0.005, 0.04, 0.08

r_pool = st.lists(st.floats(-3.0, 3.0, allow_nan=False), min_size=1, max_size=8)


class RecordingRng:
    def __init__(self, seed):
        self._rng = np.random.default_rng(seed)
        self.calls = []

    def integers(self, high, size):
        out = self._rng.integers(high, size=size)
        self.calls.append(("i", out))
        return out

    def poisson(self, lam, size):
        out = self._rng.poisson(lam, size=size)
        self.calls.append(("p", out))
        return out


def _challenge_reference(r_seq):
    """Spec: 1.5% risk, 3% after a winning trade; +4% pass, -8% stop. Returns (passed, equity)."""
    eq, prev_win = 1.0, False
    for r in r_seq:
        eq *= 1.0 + (CH_RISK_AFTER_WIN if prev_win else CH_RISK) * r
        prev_win = r > 0
        if eq >= 1.0 + CH_TARGET:
            return True, eq
        if eq <= 1.0 + CH_STOP:
            return False, eq
    return False, eq


@settings(max_examples=200, deadline=None)
@given(st.lists(st.floats(-3.0, 3.0, allow_nan=False), max_size=30))
def test_challenge_equity_follows_risk_rule(r_seq):
    eq, prev_win = 1.0, False
    for r in r_seq:
        eq *= 1.0 + (CH_RISK_AFTER_WIN if prev_win else CH_RISK) * r
        prev_win = r > 0
    assert abs(challenge_equity_after(np.array(r_seq)) - eq) < 1e-9


@settings(max_examples=150, deadline=None)
@given(r_pool, st.integers(0, 10_000))
def test_simulate_challenge_matches_rulebook(R, seed):
    R = np.array(R)
    rng = RecordingRng(seed)
    passed = simulate_challenge(R, 16, rng)
    draws = np.array([idx for kind, idx in rng.calls if kind == "i"])  # steps x paths
    for p in range(16):
        assert passed[p] == _challenge_reference(R[draws[:, p]])[0]


def _funded_reference(days):
    """Spec: a day at or below -4% ends the account; 8% below the running peak ends it."""
    eq = peak = 1.0
    for d in days:
        if d <= -FU_DAILY_LOSS:
            return False
        eq += d
        peak = max(peak, eq)
        if peak - eq >= FU_TRAILING_DD:
            return False
    return True


def _replay_days(calls, R, n_paths):
    days, counts, k = [], None, 0
    for kind, arr in calls:
        if kind == "p":
            counts, k = arr, 0
            days.append(np.zeros(n_paths))
        else:
            k += 1
            days[-1] += np.where(counts >= k, R[arr] * FU_RISK, 0.0)
    return np.array(days)  # days x paths


@settings(max_examples=150, deadline=None)
@given(st.lists(st.floats(-10.0, 10.0, allow_nan=False), min_size=1, max_size=8),
       st.floats(0.3, 3.0), st.integers(0, 10_000))
def test_simulate_funded_matches_rulebook(R, trades_per_day, seed):
    R, n_paths = np.array(R), 16
    rng = RecordingRng(seed)
    alive = simulate_funded(R, trades_per_day, 40, n_paths, rng)
    days = _replay_days(rng.calls, R, n_paths)
    for p in range(n_paths):
        assert alive[p] == _funded_reference(days[:, p])
