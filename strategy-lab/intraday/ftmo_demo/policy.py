"""Pure FTMO Instant demo risk, history, payout and news policy calculations.

This module never places, modifies, or closes an order. Callers must provide
authoritative account/history/calendar snapshots and act on returned reasons.

Example::

    snapshot = AccountSnapshot(balance, equity, observed_at, day_start_balance, closed_high)
    decision = evaluate_entry(snapshot, RiskRequest(stop_risk=12.5, costs=1.0))
    if decision.allowed:
        # The caller still owns all order execution and authorization.
        ...
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from math import isfinite
from enum import Enum
from typing import Iterable, Mapping, Sequence
from zoneinfo import ZoneInfo

PRAGUE = ZoneInfo("Europe/Prague")
UTC = timezone.utc
INITIAL_CAPITAL = 5_000.0
REWARD_RATIO = 0.90
KNOWN_RESTRICTED_EVENT_IDS = frozenset(
    {
        "USD_FED_FUNDS_RATE",
        "USD_NFP",
        "USD_UNEMPLOYMENT_RATE_WAGES",
        "USD_ADVANCE_GDP",
        "USD_FOMC_MINUTES",
        "USD_CPI_YOY",
        "EUR_MAIN_REFINANCING_RATE",
        "GBP_OFFICIAL_BANK_RATE_MPC_VOTES",
        "GBP_CPI_YOY",
        "CAD_OVERNIGHT_RATE_BOC_STATEMENT",
        "CAD_CPI_MM",
        "CAD_EMPLOYMENT_UNEMPLOYMENT",
        "AUD_CASH_RATE_RBA_STATEMENT",
        "AUD_EMPLOYMENT_UNEMPLOYMENT",
        "AUD_CPI_MM",
        "AUD_CPI_YOY",
        "AUD_GDP_QQ",
        "NZD_OFFICIAL_CASH_RATE_RBNZ_STATEMENT",
        "NZD_EMPLOYMENT_UNEMPLOYMENT",
        "NZD_CPI_QQ",
        "NZD_GDP_QQ",
        "CHF_SNB_POLICY_RATE",
        "CRUDE_OIL_INVENTORIES",
    }
)

__all__ = [
    "INITIAL_CAPITAL",
    "REWARD_RATIO",
    "KNOWN_RESTRICTED_EVENT_IDS",
    "HistoryUnavailable",
    "AccountSnapshot",
    "RiskRequest",
    "RiskDecision",
    "evaluate_entry",
    "HistoryRecord",
    "ReconstructedHistory",
    "reconstruct_history",
    "history_records_from_mt5",
    "ConsistencyStatus",
    "consistency_status",
    "PayoutEligibility",
    "payout_eligibility",
    "NewsAction",
    "RestrictedEvent",
    "NewsCalendar",
    "NewsDecision",
    "check_news",
]


class HistoryUnavailable(ValueError):
    """Raised when records cannot safely establish a complete account history."""


@dataclass(frozen=True)
class AccountSnapshot:
    balance: float
    equity: float
    observed_at: datetime
    day_start_balance: float
    closed_balance_high: float
    initial_capital: float = INITIAL_CAPITAL


@dataclass(frozen=True)
class RiskRequest:
    stop_risk: float
    costs: float = 0.0
    open_risk: float = 0.0
    open_costs: float = 0.0
    symbol: str = ""
    group: str = ""


@dataclass(frozen=True)
class RiskDecision:
    allowed: bool
    reasons: tuple[str, ...]
    risk_cap: float
    daily_floor: float
    max_loss_floor: float
    aggregate_risk_after: float
    daily_risk_after: float


def evaluate_entry(
    snapshot: AccountSnapshot,
    request: RiskRequest,
    *,
    daily_net_pnl: float = 0.0,
    group_risk: float = 0.0,
) -> RiskDecision:
    """Evaluate a proposed trade against internal and FTMO account limits."""
    reasons: list[str] = []
    risk_cap = min(max(0.0, min(snapshot.balance, snapshot.equity)) * 0.005, 25.0)
    daily_floor = snapshot.day_start_balance - snapshot.initial_capital * 0.03
    max_loss_floor = (
        max(snapshot.initial_capital, snapshot.closed_balance_high)
        - snapshot.initial_capital * 0.10
    )
    new_costed_risk = request.stop_risk + request.costs
    aggregate_after = request.open_risk + request.open_costs + new_costed_risk
    daily_after = max(0.0, -(daily_net_pnl)) + aggregate_after

    if snapshot.observed_at.tzinfo is None:
        reasons.append("account_time_must_be_timezone_aware")
    if snapshot.initial_capital != INITIAL_CAPITAL:
        reasons.append("policy_is_scoped_to_5000_usd_account")
    numeric_inputs = (
        snapshot.balance,
        snapshot.equity,
        snapshot.day_start_balance,
        snapshot.closed_balance_high,
        request.stop_risk,
        request.costs,
        request.open_risk,
        request.open_costs,
        daily_net_pnl,
        group_risk,
        snapshot.initial_capital,
    )
    if any(not isfinite(value) for value in numeric_inputs):
        reasons.append("non_finite_numeric_input")
    if (
        min(
            (
                snapshot.balance,
                snapshot.equity,
                snapshot.day_start_balance,
                snapshot.closed_balance_high,
                request.stop_risk,
                request.costs,
                request.open_risk,
                request.open_costs,
                group_risk,
                snapshot.initial_capital,
            )
        )
        < 0
    ):
        reasons.append("invalid_negative_input")
    if request.stop_risk <= 0:
        reasons.append("stop_risk_required")
    if new_costed_risk > risk_cap:
        reasons.append("per_trade_risk_exceeds_0_5pct_or_25_usd")
    if aggregate_after > snapshot.initial_capital * 0.01:
        reasons.append("aggregate_open_risk_exceeds_1pct")
    if (
        request.group.upper() in {"NQ", "SP", "NQ_SP", "NQ/SP"}
        and group_risk + new_costed_risk > snapshot.initial_capital * 0.005
    ):
        reasons.append("nq_sp_combined_risk_exceeds_0_5pct")
    if daily_after > snapshot.initial_capital * 0.015:
        reasons.append("internal_daily_risk_exceeds_1_5pct")
    headroom = min(snapshot.equity - daily_floor, snapshot.equity - max_loss_floor)
    if headroom - 50.0 < aggregate_after:
        reasons.append(
            "firm_floor_buffer_50_usd_does_not_cover_aggregate_risk_and_costs"
        )
    if snapshot.equity < daily_floor:
        reasons.append("ftmo_max_daily_loss_breached")
    if snapshot.equity < max_loss_floor:
        reasons.append("ftmo_max_loss_breached")
    return RiskDecision(
        not reasons,
        tuple(dict.fromkeys(reasons)),
        risk_cap,
        daily_floor,
        max_loss_floor,
        aggregate_after,
        daily_after,
    )


@dataclass(frozen=True)
class HistoryRecord:
    timestamp: datetime
    kind: str  # trade, deposit, withdrawal
    amount: float = 0.0  # cash movement for deposit/withdrawal
    realized_pnl: float | None = None  # trade gross realized P/L
    commission: float | None = None
    swap: float | None = None
    fees: float | None = None
    entry: int | None = None
    ticket: int | str | None = None


@dataclass(frozen=True)
class ReconstructedHistory:
    daily_net: Mapping[date, float]
    cash_flows: float
    net_trading_result: float
    records: tuple[HistoryRecord, ...]
    complete_through: datetime
    balance_at_end: float
    closed_balance_high: float
    day_start_balance: float


def _cycle_daily_net(
    history: ReconstructedHistory, cycle_start: datetime
) -> dict[date, float]:
    if cycle_start.tzinfo is None:
        raise HistoryUnavailable("cycle_start_must_be_timezone_aware")
    start_utc = cycle_start.astimezone(UTC)
    end_utc = history.complete_through.astimezone(UTC)
    daily: dict[date, float] = defaultdict(float)
    for row in history.records:
        if row.kind.lower() != "trade" or row.timestamp.astimezone(UTC) < start_utc:
            continue
        if row.timestamp.astimezone(UTC) > end_utc:
            continue
        if any(
            value is None or not isfinite(float(value))
            for value in (row.realized_pnl, row.commission, row.swap, row.fees)
        ):
            raise HistoryUnavailable("trade_history_missing_or_non_finite_cost_data")
        net = (
            float(row.realized_pnl)
            + float(row.commission)
            + float(row.swap)
            + float(row.fees)
        )
        daily[row.timestamp.astimezone(PRAGUE).date()] += net
    return dict(daily)


def reconstruct_history(
    records: Iterable[HistoryRecord],
    *,
    complete_from: datetime,
    complete_through: datetime,
    inception: datetime,
    current_balance: float,
    opening_balance: float = INITIAL_CAPITAL,
) -> ReconstructedHistory:
    """Rebuild closed daily P/L after commission, swap and fees.

    Cash movements are tracked separately and never counted as trading profit.
    Caller must attest the exported history's coverage interval.
    """
    if any(t.tzinfo is None for t in (complete_from, complete_through, inception)):
        raise HistoryUnavailable("history_coverage_must_be_timezone_aware")
    rows = tuple(records)
    if (
        complete_from > complete_through
        or complete_from != inception
        or opening_balance != INITIAL_CAPITAL
    ):
        raise HistoryUnavailable("invalid_history_coverage")
    if any(row.timestamp.tzinfo is None for row in rows) or not isfinite(
        current_balance
    ):
        raise HistoryUnavailable("invalid_history_timestamp_or_platform_balance")
    ordered = sorted(rows, key=lambda row: row.timestamp)
    if not ordered or not any(
        r.kind.lower() == "deposit"
        and abs(r.amount - opening_balance) < 0.01
        and r.timestamp == inception
        for r in ordered
    ):
        raise HistoryUnavailable("missing_exact_initial_deposit_anchor")
    daily: dict[date, float] = defaultdict(float)
    cash_flows = 0.0
    net_total = 0.0
    balance = opening_balance
    high = opening_balance
    observed_day = complete_through.astimezone(PRAGUE).date()
    day_start_balance = opening_balance
    boundary = datetime.combine(observed_day, time.min, tzinfo=PRAGUE)
    for row in ordered:
        if row.timestamp.tzinfo is None or not (
            complete_from <= row.timestamp <= complete_through
        ):
            raise HistoryUnavailable("record_outside_or_without_coverage_timestamp")
        kind = row.kind.lower()
        if kind in {"deposit", "withdrawal"}:
            if not isfinite(row.amount):
                raise HistoryUnavailable("non_finite_cash_movement")
            is_initial_anchor = (
                kind == "deposit"
                and abs(row.amount - opening_balance) < 0.01
                and row.timestamp == inception
            )
            if not is_initial_anchor:
                cash_flows += row.amount if kind == "deposit" else -abs(row.amount)
                movement = row.amount if kind == "deposit" else -abs(row.amount)
                balance += movement
        elif kind == "trade":
            values = (row.realized_pnl, row.commission, row.swap, row.fees)
            if any(value is None for value in values):
                raise HistoryUnavailable(
                    "trade_history_missing_pnl_commission_swap_or_fees"
                )
            if any(not isfinite(float(value)) for value in values if value is not None):
                raise HistoryUnavailable("non_finite_trade_history_value")
            if row.entry not in (None, 0, 1, 2):
                raise HistoryUnavailable("unsupported_mt5_deal_entry")
            net = (
                float(row.realized_pnl)
                + float(row.commission)
                + float(row.swap)
                + float(row.fees)
            )
            local_day = row.timestamp.astimezone(PRAGUE).date()
            daily[local_day] += net
            net_total += net
            balance += net
        else:
            raise HistoryUnavailable(f"unknown_history_record_kind:{row.kind}")
        if kind == "trade":
            high = max(high, balance)
        if row.timestamp.astimezone(PRAGUE) < boundary:
            day_start_balance = balance
    if current_balance is not None and abs(balance - current_balance) > 0.01:
        raise HistoryUnavailable(
            "reconstructed_balance_does_not_match_platform_balance"
        )
    if inception.astimezone(PRAGUE).date() > observed_day:
        raise HistoryUnavailable("inception_after_observed_day")
    if (
        inception.astimezone(PRAGUE).date() == observed_day
        and inception.astimezone(PRAGUE) >= boundary
    ):
        day_start_balance = opening_balance
    return ReconstructedHistory(
        dict(daily),
        cash_flows,
        net_total,
        rows,
        complete_through,
        balance,
        high,
        day_start_balance,
    )


def history_records_from_mt5(
    deals: Sequence[Mapping[str, object]],
    *,
    inception: datetime,
    complete_through: datetime,
) -> tuple[HistoryRecord, ...]:
    """Normalize MT5 deal-history dictionaries; balances are explicit cash records."""
    out: list[HistoryRecord] = []
    for deal in deals:
        try:
            ts = datetime.fromtimestamp(float(deal["time"]), tz=UTC)
            kind_code = int(deal["type"])
            if kind_code == 2:  # MT5 DEAL_TYPE_BALANCE
                amount = float(deal.get("profit", 0.0))
                kind = "deposit" if amount >= 0 else "withdrawal"
                out.append(HistoryRecord(ts, kind, amount=abs(amount)))
            elif kind_code in (0, 1):  # MT5 DEAL_TYPE_BUY / DEAL_TYPE_SELL
                if any(
                    name not in deal or deal[name] is None
                    for name in ("entry", "profit", "commission", "swap", "fee")
                ):
                    raise HistoryUnavailable("mt5_trade_deal_missing_required_fields")
                entry = int(deal["entry"])
                out.append(
                    HistoryRecord(
                        ts,
                        "trade",
                        realized_pnl=float(deal["profit"]),
                        commission=float(deal["commission"]),
                        swap=float(deal["swap"]),
                        fees=float(deal["fee"]),
                        entry=entry,
                        ticket=deal.get("ticket"),  # type: ignore[arg-type]
                    )
                )
            else:
                raise HistoryUnavailable(f"unsupported_mt5_deal_type:{kind_code}")
        except (KeyError, TypeError, ValueError, OverflowError) as exc:
            if isinstance(exc, HistoryUnavailable):
                raise
            raise HistoryUnavailable("malformed_mt5_deal_history") from exc
    if not any(
        r.kind == "deposit"
        and abs(r.amount - INITIAL_CAPITAL) < 0.01
        and r.timestamp == inception
        for r in out
    ):
        raise HistoryUnavailable("missing_exact_initial_deposit_anchor")
    if any(r.timestamp < inception or r.timestamp > complete_through for r in out):
        raise HistoryUnavailable("mt5_deal_outside_declared_history_coverage")
    return tuple(out)


@dataclass(frozen=True)
class ConsistencyStatus:
    eligible: bool
    best_day: float
    total_profit: float
    ratio: float | None
    reason: str


def consistency_status(
    history: ReconstructedHistory,
    *,
    cycle_start: datetime,
    max_best_day_share: float = 0.30,
) -> ConsistencyStatus:
    values = list(_cycle_daily_net(history, cycle_start).values())
    total = sum(values)
    best = max(values, default=0.0)
    if total <= 0:
        return ConsistencyStatus(
            False, best, total, None, "cycle_net_profit_must_be_positive"
        )
    ratio = best / total
    eligible = ratio <= max_best_day_share
    return ConsistencyStatus(
        eligible,
        best,
        total,
        ratio,
        "eligible" if eligible else "best_day_share_exceeds_30pct",
    )


@dataclass(frozen=True)
class PayoutEligibility:
    eligible: bool
    gross_profit: float
    reward: float
    reasons: tuple[str, ...]


def payout_eligibility(
    history: ReconstructedHistory,
    *,
    first_trade_at: datetime,
    now: datetime,
    cycle_start: datetime,
    method: str,
    history_complete: bool,
    account_objectives_met: bool,
    positions_flat: bool = False,
) -> PayoutEligibility:
    reasons: list[str] = []
    if not history_complete:
        reasons.append("history_incomplete")
    if any(value.tzinfo is None for value in (first_trade_at, now, cycle_start)):
        reasons.append("payout_times_must_be_timezone_aware")
        gross = 0.0
    else:
        if now.astimezone(UTC) < first_trade_at.astimezone(UTC) + timedelta(days=14):
            reasons.append("first_reward_not_available_before_14_calendar_days")
        gross = sum(_cycle_daily_net(history, cycle_start).values())
        status = consistency_status(history, cycle_start=cycle_start)
        if not status.eligible:
            reasons.append(status.reason)
    if not account_objectives_met:
        reasons.append("account_objectives_not_met")
    if not positions_flat:
        reasons.append("close_all_positions_and_pending_orders_before_claim")
    if gross <= 0:
        reasons.append("positive_closed_cycle_profit_required")
    method_key = method.lower().replace(" ", "_")
    if method_key in {"crypto", "cryptocurrency"}:
        minimum = 50.0
    elif method_key in {
        "bank",
        "bank_wire",
        "wire",
        "visa",
        "visa_direct",
        "mastercard",
        "mastercard_send",
        "instant_transfer",
    }:
        minimum = 20.0
    elif method_key == "skrill":
        minimum = 0.0
    else:
        minimum = 0.0
        reasons.append("unsupported_or_unknown_payout_method")
    if gross < minimum:
        reasons.append(f"minimum_closed_profit_{minimum:g}_usd_for_{method_key}")
    return PayoutEligibility(
        not reasons, gross, gross * REWARD_RATIO, tuple(dict.fromkeys(reasons))
    )


class NewsAction(str, Enum):
    ALLOW = "allow"
    BLOCK_ENTRY = "block_entry"
    FORBID_EXECUTION = "forbid_execution"
    BLOCK_UNKNOWN = "block_unknown_calendar"
    CLOSE_POSITIONS = "close_positions"


@dataclass(frozen=True)
class RestrictedEvent:
    event_id: str
    timestamp_utc: datetime
    affected_symbols: frozenset[str]


@dataclass(frozen=True)
class NewsCalendar:
    events: tuple[RestrictedEvent, ...]
    generated_at_utc: datetime
    coverage_from_utc: datetime
    coverage_to_utc: datetime
    source: str
    validated: bool


@dataclass(frozen=True)
class NewsDecision:
    action: NewsAction
    reason: str
    event_id: str | None = None


def check_news(
    calendar: NewsCalendar,
    *,
    now: datetime,
    symbol: str,
    action: str = "entry",
    market_close_at: datetime | None = None,
    market_reopens_at: datetime | None = None,
    maximum_age: timedelta = timedelta(hours=6),
) -> NewsDecision:
    """Check supplied official restricted-event data; no event direction is inferred."""
    if now.tzinfo is None:
        return NewsDecision(NewsAction.BLOCK_UNKNOWN, "now_must_be_timezone_aware")
    if (
        not calendar.validated
        or not calendar.source.startswith("https://ftmo.com/")
        or any(
            t.tzinfo is None
            for t in (
                calendar.generated_at_utc,
                calendar.coverage_from_utc,
                calendar.coverage_to_utc,
            )
        )
    ):
        return NewsDecision(
            NewsAction.BLOCK_UNKNOWN, "unvalidated_or_nonofficial_calendar"
        )
    instant = now.astimezone(UTC)
    generated = calendar.generated_at_utc.astimezone(UTC)
    if (
        instant - generated > maximum_age
        or generated > instant + timedelta(minutes=1)
        or not calendar.coverage_from_utc.astimezone(UTC)
        <= instant
        <= calendar.coverage_to_utc.astimezone(UTC)
    ):
        return NewsDecision(
            NewsAction.BLOCK_UNKNOWN, "stale_or_incomplete_calendar_coverage"
        )
    symbol_key = symbol.upper()
    decisions: list[NewsDecision] = []
    for event in calendar.events:
        if event.timestamp_utc.tzinfo is None:
            return NewsDecision(
                NewsAction.BLOCK_UNKNOWN,
                "event_timestamp_not_utc_aware",
                event.event_id,
            )
        if symbol_key not in {s.upper() for s in event.affected_symbols}:
            continue
        if event.event_id not in KNOWN_RESTRICTED_EVENT_IDS:
            decisions.append(
                NewsDecision(
                    NewsAction.BLOCK_UNKNOWN,
                    "unknown_restricted_event_identifier",
                    event.event_id,
                )
            )
            continue
        delta = (event.timestamp_utc.astimezone(UTC) - instant).total_seconds()
        if -120 <= delta <= 120:
            decisions.append(
                NewsDecision(
                    NewsAction.FORBID_EXECUTION,
                    "execution_restricted_within_2_minutes_before_or_after_event",
                    event.event_id,
                )
            )
            continue
        if action.lower() in {"manage_open", "maintain"} and 120 < delta <= 300:
            decisions.append(
                NewsDecision(
                    NewsAction.CLOSE_POSITIONS,
                    "close_positions_5_to_2_minutes_before_restricted_event",
                    event.event_id,
                )
            )
            continue
        if (
            action.lower() in {"entry", "open", "place_pending"}
            and -300 <= delta <= 600
        ):
            decisions.append(
                NewsDecision(
                    NewsAction.BLOCK_ENTRY,
                    "entry_blocked_10_minutes_before_until_5_minutes_after_event",
                    event.event_id,
                )
            )
    if decisions:
        rank = {
            NewsAction.FORBID_EXECUTION: 0,
            NewsAction.CLOSE_POSITIONS: 1,
            NewsAction.BLOCK_ENTRY: 2,
            NewsAction.BLOCK_UNKNOWN: 3,
        }
        return min(decisions, key=lambda decision: rank[decision.action])
    if (
        action.lower() in {"entry", "open", "place_pending"}
        and market_close_at is not None
    ):
        if market_close_at.tzinfo is None:
            return NewsDecision(
                NewsAction.BLOCK_UNKNOWN, "market_close_time_not_timezone_aware"
            )
        close_delta = market_close_at.astimezone(UTC) - instant
        if timedelta(0) <= close_delta <= timedelta(hours=2):
            if market_reopens_at is None or market_reopens_at.tzinfo is None:
                return NewsDecision(
                    NewsAction.BLOCK_UNKNOWN,
                    "market_reopen_schedule_missing_near_close",
                )
            closed_for = market_reopens_at.astimezone(UTC) - market_close_at.astimezone(
                UTC
            )
            if closed_for >= timedelta(hours=2):
                return NewsDecision(
                    NewsAction.BLOCK_ENTRY,
                    "entry_blocked_within_2_hours_of_market_close_before_2h_closure",
                )
        if timedelta(0) <= close_delta <= timedelta(minutes=5):
            return NewsDecision(
                NewsAction.BLOCK_ENTRY, "entry_blocked_within_5_minutes_of_market_close"
            )
    elif action.lower() in {"entry", "open", "place_pending"}:
        return NewsDecision(NewsAction.BLOCK_UNKNOWN, "market_close_schedule_missing")
    return NewsDecision(NewsAction.ALLOW, "no_matching_restricted_event")
