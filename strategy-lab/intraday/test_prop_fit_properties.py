"""Property tests for prop_fit: money/rule invariants checked on generated PnL paths.

Example tests in test_prop_fit.py pin known scenarios; these generate thousands of paths and
assert rules that must hold for ALL of them (a doubled drawdown limit passed all 738 example tests).
"""
import numpy as np
from hypothesis import given, settings, strategies as st

from intraday.prop_fit import Rules, challenge, funded_path

EPS = 1e-9
daily_pnl = st.lists(st.floats(min_value=-0.05, max_value=0.05, allow_nan=False), min_size=1, max_size=60)
funded_pnl = st.lists(st.floats(min_value=-0.03, max_value=0.03, allow_nan=False), min_size=1, max_size=80)
funded_rules = st.builds(
    Rules,
    withdraw_frac=st.sampled_from([0.25, 0.5, 1.0]),
    lock_after_withdraw=st.booleans(),
    funded_trailing=st.booleans(),
    consistency=st.sampled_from([0.2, 0.5, 1e9]),
    min_payout_profit=st.sampled_from([0.0, 0.004]),
    first_payout_min_days=st.sampled_from([0, 3]),
)


# ---------------------------------------------------------------- challenge (phase 1)

def _challenge_reference(daily, rules):
    """Independent re-implementation of the phase-1 rules: first breach wins."""
    bal = peak = 0.0
    for i, x in enumerate(daily[: rules.horizon_days]):
        bal += x
        peak = max(peak, bal) if rules.challenge_trailing else 0.0
        if bal <= peak - rules.static_dd:
            return -1, i + 1
        if bal >= rules.target:
            return 1, i + 1
    return 0, min(len(daily), rules.horizon_days)


@settings(max_examples=300, deadline=None)
@given(daily_pnl, st.booleans())
def test_challenge_matches_rulebook(daily, trailing):
    rules = Rules(challenge_trailing=trailing)
    assert challenge(np.asarray(daily), 0, rules) == _challenge_reference(daily, rules)


@settings(max_examples=300, deadline=None)
@given(daily_pnl)
def test_challenge_never_passes_after_breaching_drawdown(daily):
    rules = Rules()
    outcome, days = challenge(np.asarray(daily), 0, rules)
    path = np.cumsum(daily[:days])
    if outcome == 1:
        assert path.min() > -rules.static_dd, "passed despite hitting the static drawdown floor"
    if outcome == -1:
        assert path[-1] <= -rules.static_dd


# ---------------------------------------------------------------- funded_path (payouts)

def _closed(c, rules):
    c = np.asarray(c, dtype=float)
    return funded_path(c, np.minimum(c, 0.0), np.maximum(c, 0.0), np.ones(len(c), dtype=bool), 0, rules)


# Intraday days: close P&L plus extra dip below / spike above it (worst/best floating P&L).
intraday_days = st.lists(
    st.tuples(st.floats(-0.03, 0.03), st.floats(0.0, 0.03), st.floats(0.0, 0.03)), min_size=1, max_size=80)


def _split(days):
    c = np.array([d[0] for d in days])
    lo = np.minimum(c, 0.0) - np.array([d[1] for d in days])
    hi = np.maximum(c, 0.0) + np.array([d[2] for d in days])
    return c, lo, hi


def _funded_reference(c, rules, lo=None, hi=None):
    """Rulebook walk written independently of funded_path: returns (paid, breached, payouts)."""
    lo = np.minimum(c, 0.0) if lo is None else lo
    hi = np.maximum(c, 0.0) if hi is None else hi
    paid = bal = peak = best = cycle_start = 0.0
    traded_days = cycle_days = payouts = 0
    locked = False
    for x, low, high in list(zip(c, lo, hi))[: rules.horizon_days]:
        floor = 0.0 if locked else (peak if rules.funded_trailing else 0.0) - rules.trail_dd
        if low <= -rules.daily_limit or bal + low <= floor:
            return paid, True, payouts
        if rules.funded_trailing and not locked:
            peak = max(peak, bal + high)
        bal += x
        floor = 0.0 if locked else (peak if rules.funded_trailing else 0.0) - rules.trail_dd
        if bal <= floor:
            return paid, True, payouts
        best, traded_days, cycle_days = max(best, x), traded_days + 1, cycle_days + 1
        cycle_profit, amount = bal - cycle_start, rules.withdraw_frac * bal
        eligible = (cycle_days >= rules.first_payout_min_days and traded_days >= rules.min_trade_days
                    and amount >= rules.min_payout_profit and cycle_profit > 0
                    and best <= rules.consistency * cycle_profit)
        if eligible:
            paid, bal, payouts = paid + amount, bal - amount, payouts + 1
            locked = locked or rules.lock_after_withdraw
            peak = cycle_start = bal
            best, traded_days, cycle_days = 0.0, 0, 0
    return paid, False, payouts


@settings(max_examples=400, deadline=None)
@given(funded_pnl, funded_rules)
def test_funded_matches_rulebook(c, rules):
    paid, breached, n = _closed(c, rules)
    ref_paid, ref_breached, ref_n = _funded_reference(c, rules)
    assert (breached, n) == (ref_breached, ref_n)
    assert abs(paid - ref_paid) < EPS


@settings(max_examples=400, deadline=None)
@given(intraday_days, funded_rules)
def test_funded_intraday_matches_rulebook(days, rules):
    c, lo, hi = _split(days)
    paid, breached, n = funded_path(c, lo, hi, np.ones(len(c), dtype=bool), 0, rules)
    ref_paid, ref_breached, ref_n = _funded_reference(c, rules, lo, hi)
    assert (breached, n) == (ref_breached, ref_n)
    assert abs(paid - ref_paid) < EPS


@settings(max_examples=400, deadline=None)
@given(intraday_days, funded_rules)
def test_funded_intraday_daily_limit_always_breaches(days, rules):
    c, lo, hi = _split(days)
    if any(x <= -rules.daily_limit for x in lo[: rules.horizon_days]):
        _, breached, _ = funded_path(c, lo, hi, np.ones(len(c), dtype=bool), 0, rules)
        assert breached, "an intraday dip beyond the daily loss limit must end the account"


@settings(max_examples=400, deadline=None)
@given(funded_pnl, funded_rules)
def test_funded_never_withdraws_more_than_earned(c, rules):
    # bal never goes below floor >= -trail_dd while alive, so payouts can't exceed earned P&L + buffer
    paid, breached, _ = _closed(c, rules)
    earned = float(np.sum(c[: rules.horizon_days]))
    assert paid >= 0.0
    if not breached:
        assert paid <= earned + rules.trail_dd + EPS


@settings(max_examples=400, deadline=None)
@given(funded_pnl, funded_rules)
def test_funded_payout_count_and_minimum(c, rules):
    paid, _, n = _closed(c, rules)
    assert (paid > 0) == (n > 0) or rules.min_payout_profit == 0.0
    assert paid + EPS >= n * rules.min_payout_profit


@settings(max_examples=400, deadline=None)
@given(funded_pnl, funded_rules)
def test_funded_daily_limit_always_breaches(c, rules):
    if any(x <= -rules.daily_limit for x in c[: rules.horizon_days]):
        _, breached, _ = _closed(c, rules)
        assert breached, "a day beyond the daily loss limit must end the account"


@settings(max_examples=300, deadline=None)
@given(funded_pnl, st.booleans())
def test_funded_locked_full_withdrawal_leaves_no_buffer(c, trailing):
    # lock + 100% withdrawal: after any payout the floor is the initial balance with zero buffer
    rules = Rules(withdraw_frac=1.0, lock_after_withdraw=True, funded_trailing=trailing,
                  consistency=1e9, min_payout_profit=0.0)
    paid, breached, n = _closed(c, rules)
    if n > 0 and not breached:
        assert paid <= float(np.sum(c)) + EPS
