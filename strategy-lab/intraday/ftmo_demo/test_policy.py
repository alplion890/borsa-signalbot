from datetime import datetime, timedelta, timezone

import pytest

from intraday.ftmo_demo.policy import (
    AccountSnapshot,
    HistoryRecord,
    HistoryUnavailable,
    NewsAction,
    NewsCalendar,
    RestrictedEvent,
    RiskRequest,
    check_news,
    consistency_status,
    evaluate_entry,
    history_records_from_mt5,
    payout_eligibility,
    reconstruct_history,
)

UTC = timezone.utc


def _history():
    inception = datetime(2026, 10, 1, tzinfo=UTC)
    rows = [
        HistoryRecord(inception, "deposit", amount=5000),
        HistoryRecord(
            inception + timedelta(hours=1),
            "trade",
            realized_pnl=100,
            commission=-2,
            swap=-1,
            fees=-1,
            entry=1,
        ),
        HistoryRecord(
            inception + timedelta(days=1),
            "trade",
            realized_pnl=300,
            commission=-2,
            swap=0,
            fees=0,
            entry=1,
        ),
        HistoryRecord(
            inception + timedelta(days=2),
            "trade",
            realized_pnl=600,
            commission=-2,
            swap=0,
            fees=0,
            entry=1,
        ),
    ]
    return inception, rows


def test_risk_caps_and_trailing_floors_are_computed_from_account_snapshot():
    now = datetime(2026, 10, 16, 12, tzinfo=UTC)
    snapshot = AccountSnapshot(5200, 5190, now, 5200, 5300)
    denied = evaluate_entry(
        snapshot, RiskRequest(26, symbol="NQ", group="NQ"), group_risk=0
    )
    assert denied.risk_cap == 25
    assert not denied.allowed
    assert "per_trade_risk_exceeds_0_5pct_or_25_usd" in denied.reasons
    assert denied.daily_floor == 5050
    assert denied.max_loss_floor == 4800


def test_risk_uses_aggregate_and_nq_sp_concentration_caps():
    now = datetime(2026, 10, 16, 12, tzinfo=UTC)
    snapshot = AccountSnapshot(5000, 5000, now, 5000, 5000)
    decision = evaluate_entry(
        snapshot, RiskRequest(20, open_risk=40, group="SP"), group_risk=10
    )
    assert not decision.allowed
    assert "nq_sp_combined_risk_exceeds_0_5pct" in decision.reasons
    assert "aggregate_open_risk_exceeds_1pct" in decision.reasons


def test_history_requires_exact_start_anchor_and_balance_reconciliation():
    inception, rows = _history()
    kwargs = dict(
        complete_from=inception,
        complete_through=inception + timedelta(days=3),
        inception=inception,
    )
    with pytest.raises(HistoryUnavailable, match="balance_does_not_match"):
        reconstruct_history(rows, current_balance=6000, **kwargs)
    with pytest.raises(HistoryUnavailable, match="initial_deposit_anchor"):
        reconstruct_history(rows[1:], current_balance=5992, **kwargs)


def test_reconstruction_excludes_cash_flows_from_profit_and_includes_all_trade_costs():
    inception, rows = _history()
    rows.append(HistoryRecord(inception + timedelta(days=3), "deposit", amount=500))
    hist = reconstruct_history(
        rows,
        complete_from=inception,
        complete_through=inception + timedelta(days=4),
        inception=inception,
        current_balance=6492,
    )
    assert hist.net_trading_result == 992
    assert hist.cash_flows == 500
    assert hist.balance_at_end == 6492
    assert hist.closed_balance_high == 5992


def test_mt5_deals_require_complete_anchor_and_all_cost_fields():
    inception, _ = _history()
    deals = [
        {"ticket": 1, "time": inception.timestamp(), "type": 2, "profit": 5000},
        {
            "ticket": 2,
            "time": (inception + timedelta(hours=1)).timestamp(),
            "type": 0,
            "entry": 1,
            "position_id": 9,
            "profit": 10,
            "commission": -1,
            "swap": 0,
            "fee": 0,
            "volume": 1,
            "symbol": "EURUSD",
            "magic": 1,
        },
    ]
    normalized = history_records_from_mt5(
        deals, inception=inception, complete_through=inception + timedelta(days=1)
    )
    assert [record.kind for record in normalized] == ["deposit", "trade"]
    with pytest.raises(HistoryUnavailable, match="missing_required_fields"):
        history_records_from_mt5(
            deals[:1] + [dict(deals[1], commission=None)],
            inception=inception,
            complete_through=inception + timedelta(days=1),
        )


def test_consistency_uses_closed_daily_net_and_payout_waits_full_14_days():
    inception, rows = _history()
    hist = reconstruct_history(
        rows,
        complete_from=inception,
        complete_through=inception + timedelta(days=15),
        inception=inception,
        current_balance=5992,
    )
    status = consistency_status(hist, cycle_start=inception)
    assert status.best_day == 598
    assert not status.eligible
    payout = payout_eligibility(
        hist,
        first_trade_at=inception,
        now=inception + timedelta(days=14),
        cycle_start=inception,
        method="bank",
        history_complete=True,
        account_objectives_met=True,
    )
    assert not payout.eligible
    assert "best_day_share_exceeds_30pct" in payout.reasons
    assert payout.reward == pytest.approx(892.8)


def test_payout_not_eligible_before_exact_14_calendar_days():
    inception, rows = _history()
    # Spread profit over four days, each under 30% of total.
    rows.extend(
        [
            HistoryRecord(
                inception + timedelta(days=3),
                "trade",
                realized_pnl=500,
                commission=0,
                swap=0,
                fees=0,
                entry=1,
            ),
            HistoryRecord(
                inception + timedelta(days=4),
                "trade",
                realized_pnl=500,
                commission=0,
                swap=0,
                fees=0,
                entry=1,
            ),
        ]
    )
    hist = reconstruct_history(
        rows,
        complete_from=inception,
        complete_through=inception + timedelta(days=15),
        inception=inception,
        current_balance=6992,
    )
    payout = payout_eligibility(
        hist,
        first_trade_at=inception,
        now=inception + timedelta(days=14) - timedelta(seconds=1),
        cycle_start=inception,
        method="bank",
        history_complete=True,
        account_objectives_met=True,
    )
    assert not payout.eligible
    assert "first_reward_not_available_before_14_calendar_days" in payout.reasons


def test_news_blocks_entries_and_forbids_execution_in_explicit_window():
    now = datetime(2026, 10, 16, 12, tzinfo=UTC)
    event = RestrictedEvent(
        "USD_CPI_YOY", now + timedelta(minutes=1), frozenset({"EURUSD"})
    )
    calendar = NewsCalendar(
        (event,),
        now - timedelta(minutes=9),
        now - timedelta(hours=1),
        now + timedelta(days=1),
        "https://ftmo.com/en/faq/can-i-trade-news/",
        True,
    )
    result = check_news(calendar, now=now, symbol="EURUSD", action="close")
    assert result.action == NewsAction.FORBID_EXECUTION
    blocked = check_news(calendar, now=now - timedelta(minutes=8), symbol="EURUSD")
    assert blocked.action == NewsAction.BLOCK_ENTRY
    close_soon = check_news(
        calendar, now=now - timedelta(minutes=3), symbol="EURUSD", action="manage_open"
    )
    assert close_soon.action == NewsAction.CLOSE_POSITIONS


def test_news_fails_closed_for_stale_or_uncovered_calendar_and_blocks_preclose():
    now = datetime(2026, 10, 16, 12, tzinfo=UTC)
    stale = NewsCalendar(
        (),
        now - timedelta(hours=7),
        now - timedelta(days=2),
        now - timedelta(days=1),
        "https://ftmo.com/en/faq/can-i-trade-news/",
        True,
    )
    assert check_news(stale, now=now, symbol="NQ").action == NewsAction.BLOCK_UNKNOWN
    current = NewsCalendar(
        (),
        now,
        now - timedelta(hours=1),
        now + timedelta(days=1),
        "https://ftmo.com/en/faq/can-i-trade-news/",
        True,
    )
    decision = check_news(
        current,
        now=now,
        symbol="NQ",
        market_close_at=now + timedelta(minutes=4),
        market_reopens_at=now + timedelta(days=1),
    )
    assert decision.action == NewsAction.BLOCK_ENTRY
    two_hour_close = check_news(
        current,
        now=now,
        symbol="NQ",
        market_close_at=now + timedelta(hours=1),
        market_reopens_at=now + timedelta(hours=4),
    )
    assert two_hour_close.action == NewsAction.BLOCK_ENTRY


def test_unknown_restricted_event_and_missing_market_schedule_fail_closed():
    now = datetime(2026, 10, 16, 12, tzinfo=UTC)
    unknown_event = RestrictedEvent(
        "UNKNOWN_FTMO_EVENT", now + timedelta(minutes=20), frozenset({"US100.CASH"})
    )
    calendar = NewsCalendar(
        (unknown_event,),
        now,
        now - timedelta(hours=1),
        now + timedelta(days=1),
        "https://ftmo.com/en/faq/can-i-trade-news/",
        True,
    )
    assert (
        check_news(calendar, now=now, symbol="US100.cash").action
        == NewsAction.BLOCK_UNKNOWN
    )
    empty = NewsCalendar(
        (),
        now,
        now - timedelta(hours=1),
        now + timedelta(days=1),
        "https://ftmo.com/en/faq/can-i-trade-news/",
        True,
    )
    assert (
        check_news(empty, now=now, symbol="US100.cash").action
        == NewsAction.BLOCK_UNKNOWN
    )
