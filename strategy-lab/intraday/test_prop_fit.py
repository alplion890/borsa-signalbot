import numpy as np

from intraday.prop_fit import Rules, funded_path


def _closed(c, rules, traded=None):
    c = np.asarray(c, dtype=float)
    t = np.ones(len(c), dtype=bool) if traded is None else np.asarray(traded)
    return funded_path(c, np.minimum(c, 0.0), np.maximum(c, 0.0), t, 0, rules)


NO_CONS = dict(consistency=1e9, min_payout_profit=0.0)


def test_lock_after_full_withdrawal_breaches_on_next_loss():
    # +1% day -> full withdrawal -> floor locks at initial balance -> any loss breaches
    paid, breached, n = _closed([0.01, -0.001], Rules(**NO_CONS))
    assert n == 1 and breached and abs(paid - 0.01) < 1e-12


def test_no_lock_keeps_trailing_buffer_after_withdrawal():
    paid, breached, n = _closed([0.01, -0.001], Rules(lock_after_withdraw=False, **NO_CONS))
    assert n == 1 and not breached


def test_partial_withdrawal_leaves_buffer_above_locked_floor():
    # withdraw 50% of 1% -> 0.5% buffer survives a -0.4% day, breaches on further -0.2%
    _, breached, _ = _closed([0.01, -0.004], Rules(withdraw_frac=0.5, **NO_CONS))
    assert not breached
    _, breached, _ = _closed([0.01, -0.004, -0.002], Rules(withdraw_frac=0.5, **NO_CONS))
    assert breached


def test_consistency_uses_cycle_profit_not_retained_buffer():
    # after first payout (50% kept as buffer) the next cycle's best day is judged vs cycle profit only
    r = Rules(withdraw_frac=0.5, consistency=0.5, min_payout_profit=0.0)
    paid, breached, n = _closed([0.01, 0.01, 0.002], r)
    assert n == 1  # day 3 cycle profit 0.002, best 0.002 > 0.5 * 0.002 -> no second payout yet
    assert not breached


def test_daily_limit_on_intraday_low():
    c = np.array([0.01])
    _, breached, _ = funded_path(c, np.array([-0.05]), np.array([0.02]), np.array([True]), 0, Rules())
    assert breached


def test_waiting_period_and_min_days_respected():
    r = Rules(first_payout_min_days=3, lock_after_withdraw=False, **NO_CONS)
    _, _, n = _closed([0.01, 0.01], r)
    assert n == 0
    _, _, n = _closed([0.01, 0.01, 0.01], r)
    assert n == 1
