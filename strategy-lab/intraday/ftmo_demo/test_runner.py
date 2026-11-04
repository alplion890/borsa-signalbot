from datetime import datetime, timedelta, timezone
import json
from types import SimpleNamespace as NS

import pandas as pd
import pytest

from intraday.ftmo_demo import runner
from intraday.ftmo_demo import policy
from intraday.ftmo_demo.broker import OrderPlan
from intraday.ftmo_demo.storage import Store, single_process

NOW = datetime(2026, 10, 16, 12, tzinfo=timezone.utc)


def test_enrollment_rejects_other_login_paid_or_unreviewed_evidence():
    config = {"login": 12, "server": "FTMO-Demo"}
    evidence = {
        "login": 12,
        "server": "FTMO-Demo",
        "product": "free_trial",
        "reviewed_by_user": True,
        "source": "https://trader.ftmo.com/account",
        "reference": "Free Trial card",
    }
    runner.verify_authorization(evidence, config)
    for change in (
        {"login": 13},
        {"product": "instant"},
        {"reviewed_by_user": False},
        {"source": "https://evil.test/"},
    ):
        with pytest.raises(ValueError):
            runner.verify_authorization({**evidence, **change}, config)


def test_session_missing_stale_and_final_two_hours_fail_closed():
    data = {
        "validated": True,
        "source": "https://ftmo.com/en/symbols/",
        "generated_at_utc": NOW.isoformat(),
        "symbols": {
            "SP500": [
                {
                    "open": (NOW - timedelta(hours=3)).isoformat(),
                    "close": (NOW + timedelta(hours=4)).isoformat(),
                }
            ]
        },
    }
    assert runner.session_gate(data, "SP500", NOW)[0] == "open"
    assert runner.session_gate(data, "NASDAQ100", NOW)[0] == "closed"
    assert runner.session_gate(data, "SP500", NOW + timedelta(hours=3))[0] == "blocked"
    assert (
        runner.session_gate(data, "SP500", NOW + timedelta(hours=3, minutes=56))[0]
        == "close"
    )
    assert runner.session_gate(data, "SP500", NOW + timedelta(days=2))[0] == "unknown"


def test_audit_survives_restart_and_process_lock_is_exclusive(tmp_path):
    store = Store(tmp_path)
    store.set("intents", {"abc": {"risk": 25}})
    store.event("intent", {"risk": 25}, "abc")
    store.close()
    again = Store(tmp_path)
    assert again.get("intents")["abc"]["risk"] == 25
    assert again.db.execute("SELECT count(*) FROM events").fetchone()[0] == 1
    with single_process(tmp_path):
        with pytest.raises(RuntimeError):
            with single_process(tmp_path):
                pass
    again.close()


def demo(tmp_path, equity=5000):
    config = {
        "login": 12,
        "server": "FTMO-Demo",
        "product": "free_trial",
        "strategy_hash": runner.strategy_hash(),
        "inception": (NOW - timedelta(days=1)).isoformat(),
        "symbols": {key: key for key in runner.MODULES.values()},
        "costs": {
            key: {
                "commission_roundtrip_per_lot": 0,
                "slippage_points": 1,
                "max_spread_points": 5,
            }
            for key in runner.MODULES.values()
        },
    }

    class Client:
        TIMEFRAME_M15 = 15
        ORDER_TYPE_BUY = 0
        ORDER_TYPE_SELL = 1

        def __init__(self):
            self.positions = []

        def positions_get(self):
            return self.positions

        def orders_get(self):
            return ()

        def symbol_info_tick(self, symbol):
            return NS(bid=99.9, ask=100, time=NOW.timestamp())

        def symbol_info(self, symbol):
            return NS(point=0.1, volume_min=0.1)

        def order_calc_profit(self, side, symbol, volume, entry, stop):
            return (stop - entry) * volume * (1 if side == 0 else -1)

    class Broker:
        config = NS(magic=12)

        def __init__(self):
            self.client = Client()
            self.submits = 0
            self.closes = 0
            self.records = {}

        def inspect(self, symbols):
            return {"login": 12, "server": "FTMO-Demo"}

        def reconcile(self, identity):
            return self.records.get(identity, {"status": "not_found"})

        def size_order(self, symbol, side, entry, stop, risk_amount, **kw):
            return OrderPlan(
                symbol,
                side,
                2.0,
                entry,
                stop,
                risk_amount,
                20.0,
                "test",
                kw["cost_reserve"],
                kw.get("take_profit", 0),
            )

        def submit(self, plan, identity):
            self.submits += 1
            raise RuntimeError("simulated network failure after send")

        def close_position(self, ticket):
            self.closes += 1
            return {"closed": ticket}

    b = Broker()
    run = runner.DemoRunner(config, tmp_path, b)
    hist = policy.ReconstructedHistory({}, 0, 0, (), NOW, 5000, 5000, 5000)
    run.context = lambda now: (
        NS(balance=5000, equity=equity),
        [],
        hist,
        policy.AccountSnapshot(5000, equity, now, 5000, 5000),
    )
    calendar = {
        "events": [],
        "generated_at_utc": NOW.isoformat(),
        "coverage_from_utc": (NOW - timedelta(hours=1)).isoformat(),
        "coverage_to_utc": (NOW + timedelta(days=1)).isoformat(),
        "source": "https://ftmo.com/en/faq/can-i-trade-news/",
        "validated": True,
    }
    (tmp_path / "calendar.json").write_text(json.dumps(calendar))
    sessions = {
        "validated": True,
        "source": "https://ftmo.com/en/symbols/",
        "generated_at_utc": NOW.isoformat(),
        "symbols": {
            key: [
                {
                    "open": (NOW - timedelta(hours=1)).isoformat(),
                    "close": (NOW + timedelta(hours=5)).isoformat(),
                }
            ]
            for key in config["symbols"]
        },
    }
    (tmp_path / "sessions.json").write_text(json.dumps(sessions))
    return run, b


def no_signals(monkeypatch):
    frame = pd.DataFrame(
        {"close": [100.0]},
        index=[pd.Timestamp(NOW).tz_localize(None) - pd.Timedelta(minutes=15)],
    )
    monkeypatch.setattr(runner, "closed_bars", lambda *a: frame)
    monkeypatch.setattr(runner, "latest_signal", lambda *a: None)


def test_check_is_emirsiz_and_free_trial_never_payout_ready(tmp_path, monkeypatch):
    run, b = demo(tmp_path)
    no_signals(monkeypatch)
    status = run.cycle(now=NOW)
    assert b.submits == b.closes == 0
    assert status["metrics"]["payout_ready"] is False
    assert len(status["modules"]) == 4
    assert (tmp_path / "status.json").exists()
    run.store.close()


def test_daily_stop_latches_even_if_equity_recovers_until_prague_new_day(
    tmp_path, monkeypatch
):
    run, b = demo(tmp_path, equity=4920)
    no_signals(monkeypatch)
    assert run.cycle(now=NOW)["status"] == "RISK DURDU"
    _, other = demo(tmp_path)
    run.context = lambda now: (
        NS(balance=5000, equity=5000),
        [],
        policy.ReconstructedHistory({}, 0, 0, (), now, 5000, 5000, 5000),
        policy.AccountSnapshot(5000, 5000, now, 5000, 5000),
    )
    assert run.cycle(now=NOW + timedelta(minutes=1))["status"] == "RISK DURDU"
    assert (
        run.store.get("daily_stop") == NOW.astimezone(policy.PRAGUE).date().isoformat()
    )
    run.store.close()


def test_restart_adopts_journaled_fill_and_never_retries_uncertain(tmp_path):
    run, b = demo(tmp_path)
    run.store.set("intents", {"abc": {"id": "abc", "symbol_key": "SP500", "risk": 25}})
    b.records["abc"] = {"status": "confirmed", "record": {"position_ticket": 30}}
    run.recover_intents([NS(ticket=30, identifier=31)])
    assert run.store.get("positions")["30"]["identifier"] == 31
    b.records["abc"] = {"status": "uncertain"}
    with pytest.raises(ValueError, match="Belirsiz emir"):
        run.recover_intents([])
    assert b.submits == 0
    run.store.close()


def test_demo_auto_requires_smoke_and_durable_halt_blocks_restart(tmp_path):
    run, b = demo(tmp_path)
    with pytest.raises(ValueError, match="micro"):
        run.cycle(execute=True, now=NOW)
    run.store.set("smoke_verified", True)
    run.store.set("halt", "unknown send")
    with pytest.raises(ValueError, match="Kalici"):
        run.cycle(execute=True, now=NOW)
    assert b.submits == 0
    run.store.close()


def test_restricted_window_does_not_send_even_for_guard_close(tmp_path):
    run, b = demo(tmp_path)
    run.store.set("positions", {"10": {}})
    event = policy.RestrictedEvent("USD_CPI_YOY", NOW, frozenset({"SP500"}))
    cal = policy.NewsCalendar(
        (event,),
        NOW,
        NOW - timedelta(hours=1),
        NOW + timedelta(hours=1),
        "https://ftmo.com/",
        True,
    )
    run.close_owned(
        [NS(ticket=10, magic=12, symbol="SP500")], [], cal, NOW, "risk", True
    )
    assert b.closes == 0
    run.store.close()


def signal_case(tmp_path, monkeypatch):
    run, broker = demo(tmp_path)
    no_signals(monkeypatch)
    monkeypatch.setattr(runner, "utc_now", lambda: NOW)
    signal = {
        "id": "fresh",
        "module": "SWEEP_CORE_AVOID_MID_VWAP",
        "symbol_key": "NASDAQ100",
        "bar_time": (NOW - timedelta(minutes=15)).isoformat(),
        "direction": 1,
        "entry": 100.0,
        "sl": 90.0,
        "tp": 120.0,
        "version": runner.VERSION,
    }
    monkeypatch.setattr(
        runner,
        "latest_signal",
        lambda module, *a: dict(signal) if module == signal["module"] else None,
    )

    def send(plan, identity):
        # Durable intent exists BEFORE crossing the broker boundary.
        assert run.store.get("intents")[identity]["risk"] > 0
        broker.submits += 1
        position = NS(
            ticket=44,
            identifier=44,
            magic=12,
            symbol=plan.symbol,
            type=0,
            price_open=plan.entry,
            sl=plan.stop,
            volume=plan.volume,
        )
        broker.client.positions.append(position)
        broker.records[identity] = {
            "status": "confirmed",
            "record": {"position_ticket": 44},
        }
        return {"ticket": 44, "status": "confirmed"}

    broker.submit = send
    return run, broker


def test_successful_entry_persists_intent_adopts_position_and_no_duplicate(
    tmp_path, monkeypatch
):
    run, broker = signal_case(tmp_path, monkeypatch)
    run.store.set("smoke_verified", True)
    # A dry-run preview must not consume the executable signal.
    run.cycle(now=NOW)
    run.cycle(execute=True, now=NOW)
    assert broker.submits == 1
    assert run.store.get("positions")["44"]["id"] == "fresh"
    run.cycle(execute=True, now=NOW)
    assert broker.submits == 1
    run.store.close()


def test_micro_min_lot_roundtrip_is_verified_before_auto_permission(
    tmp_path, monkeypatch
):
    run, broker = signal_case(tmp_path, monkeypatch)

    def close(ticket):
        broker.closes += 1
        assert broker.client.positions[0].volume == 0.1
        broker.client.positions.clear()
        return {"closed": ticket}

    broker.close_position = close
    status = run.cycle(execute=True, micro=True, now=NOW)
    assert broker.submits == broker.closes == 1
    assert run.store.get("smoke_verified")["signal_id"] == "fresh"
    assert status["metrics"]["accepted_trades"] == 0
    run.store.close()


def test_ambiguous_send_latches_halt_and_does_not_retry_after_restart(
    tmp_path, monkeypatch
):
    run, broker = signal_case(tmp_path, monkeypatch)
    run.store.set("smoke_verified", True)

    def timeout(plan, identity):
        broker.submits += 1
        raise RuntimeError("unknown send outcome")

    broker.submit = timeout
    with pytest.raises(RuntimeError, match="unknown"):
        run.cycle(execute=True, now=NOW)
    assert run.store.get("halt") == "unknown send outcome"
    with pytest.raises(ValueError, match="Kalici"):
        run.cycle(execute=True, now=NOW)
    assert broker.submits == 1
    run.store.close()


def test_stale_calendar_blocks_guard_close_and_cancel(tmp_path):
    run, broker = demo(tmp_path)
    run.store.set("positions", {"10": {}})
    calendar = policy.NewsCalendar(
        (),
        NOW - timedelta(days=1),
        NOW - timedelta(days=1),
        NOW + timedelta(days=1),
        "https://ftmo.com/",
        True,
    )
    broker.cancel_order = lambda ticket: pytest.fail("stale takvimde iptal gonderildi")
    item = NS(ticket=10, magic=12, symbol="SP500")
    run.close_owned([item], [item], calendar, NOW, "guard", True)
    assert broker.closes == 0
    run.store.close()


def test_real_context_reconstructs_complete_mt5_history_with_costs(tmp_path):
    run, broker = demo(tmp_path)
    inception = runner.timestamp(run.config["inception"])

    class Deal:
        def __init__(self, value):
            self.value = value

        def _asdict(self):
            return self.value

    rows = [
        Deal({"time": inception.timestamp(), "type": 2, "profit": 5000.0, "ticket": 1}),
        Deal(
            {
                "time": (inception + timedelta(hours=1)).timestamp(),
                "type": 0,
                "entry": 1,
                "profit": 12.0,
                "commission": -1.0,
                "swap": -1.0,
                "fee": 0.0,
                "ticket": 2,
            }
        ),
    ]
    broker.client.account_info = lambda: NS(balance=5010.0, equity=5009.0)
    broker.client.history_deals_get = lambda start, end: rows
    # Use the actual implementation, not demo()'s convenient context stub.
    account, _, history, snapshot = runner.DemoRunner.context(run, NOW)
    assert history.balance_at_end == 5010.0
    assert history.net_trading_result == 10.0
    assert snapshot.day_start_balance == 5010.0
    assert account.equity == 5009.0
    run.store.close()


def test_official_usd_event_cannot_omit_us_index_restriction(tmp_path):
    path = tmp_path / "calendar.json"
    path.write_text(
        json.dumps(
            {
                "events": [
                    {
                        "event_id": "USD_CPI_YOY",
                        "timestamp_utc": NOW.isoformat(),
                        "affected_symbols": [],
                    }
                ],
                "generated_at_utc": NOW.isoformat(),
                "coverage_from_utc": NOW.isoformat(),
                "coverage_to_utc": NOW.isoformat(),
                "source": "https://ftmo.com/",
                "validated": True,
            }
        )
    )
    calendar = runner.load_calendar(path)
    assert calendar.events[0].affected_symbols >= {"NASDAQ100", "SP500"}
