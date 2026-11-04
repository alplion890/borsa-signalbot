from __future__ import annotations

import time
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest

from intraday.ftmo_demo.broker import (
    BrokerError,
    FTMOConfig,
    FTMOBroker,
    UncertainExecution,
    read_only_inspect,
)


class FakeMT5:
    ACCOUNT_TRADE_MODE_DEMO = 0
    ACCOUNT_TRADE_MODE_REAL = 2
    ORDER_TYPE_BUY = 0
    ORDER_TYPE_SELL = 1
    TRADE_ACTION_DEAL = 1
    TRADE_ACTION_REMOVE = 8
    ORDER_TIME_GTC = 0
    ORDER_FILLING_FOK = 0
    ORDER_FILLING_IOC = 1
    ORDER_FILLING_RETURN = 2
    SYMBOL_FILLING_FOK = 1
    SYMBOL_FILLING_IOC = 2
    SYMBOL_TRADE_EXECUTION_MARKET = 2
    TRADE_RETCODE_DONE = 10009
    TRADE_RETCODE_DONE_PARTIAL = 10010

    def __init__(self, path: Path, *, trade_mode=0, sl=99.0, send_exception=False):
        self.path = str(path.parent)
        self.account = SimpleNamespace(
            login=123,
            name="FTMO Free Trial",
            server="FTMO-Demo",
            company="FTMO Global Markets",
            trade_mode=trade_mode,
            currency="USD",
            balance=10000,
            equity=10000,
            trade_allowed=True,
        )
        self.terminal = SimpleNamespace(
            path=self.path, connected=True, trade_allowed=True, tradeapi_disabled=False
        )
        self.info = SimpleNamespace(
            visible=True,
            digits=2,
            point=0.01,
            volume_min=0.01,
            volume_step=0.01,
            volume_max=100.0,
            trade_stops_level=0,
            filling_mode=1,
            trade_exemode=2,
        )
        self.tick = SimpleNamespace(bid=100.0, ask=100.1, time=int(time.time()))
        self.positions = []
        self.orders = []
        self.deals = []
        self.checks = []
        self.requests = []
        self.send_exception = send_exception
        self.send_retcode = self.TRADE_RETCODE_DONE
        self.position_sl = sl
        self.initialize_calls = []

    def initialize(self, **kwargs):
        self.initialize_calls.append(kwargs)
        return True

    def shutdown(self):
        return None

    def terminal_info(self):
        return self.terminal

    def account_info(self):
        return self.account

    def symbol_info(self, symbol):
        return self.info

    def symbol_info_tick(self, symbol):
        return self.tick

    def symbol_select(self, symbol, select):
        return True

    def order_calc_profit(self, kind, symbol, volume, entry, close):
        delta = close - entry
        return (delta if kind == self.ORDER_TYPE_BUY else -delta) * 100 * volume

    def positions_get(self, symbol=None):
        return tuple(p for p in self.positions if symbol is None or p.symbol == symbol)

    def orders_get(self):
        return tuple(self.orders)

    def history_deals_get(self, start, end):
        return tuple(self.deals)

    def order_check(self, request):
        self.checks.append(dict(request))
        return SimpleNamespace(retcode=0)

    def order_send(self, request):
        self.requests.append(dict(request))
        if self.send_exception:
            raise TimeoutError("simulated timeout")
        if request.get("position"):
            self.positions = [
                p for p in self.positions if p.ticket != request["position"]
            ]
        elif request.get("action") == self.TRADE_ACTION_DEAL:
            self.positions.append(
                SimpleNamespace(
                    symbol=request["symbol"],
                    magic=request["magic"],
                    comment=request["comment"],
                    ticket=77,
                    volume=request["volume"],
                    sl=self.position_sl,
                    tp=request.get("tp", 0),
                    type=request["type"],
                    price_open=request["price"],
                )
            )
        return SimpleNamespace(
            retcode=self.send_retcode,
            order=77,
            deal=88,
            volume=request.get("volume", 0),
        )

    def last_error(self):
        return (-6, "authorization failed")


@pytest.fixture
def setup(tmp_path):
    terminal = tmp_path / "terminal64.exe"
    terminal.write_bytes(b"stub")
    client = FakeMT5(terminal)
    config = FTMOConfig(
        terminal,
        123,
        "FTMO-Demo",
        "free_trial",
        execution_enabled=True,
        approved_free_trial_login=123,
        approved_free_trial_server="FTMO-Demo",
    )
    broker = FTMOBroker(
        config,
        client=client,
        state_path=tmp_path / "state.json",
        process_checker=lambda _: True,
    )
    broker.connect()
    return broker, client


def test_only_explicit_free_trial_product_is_accepted(tmp_path):
    with pytest.raises(ValueError, match="free_trial"):
        FTMOConfig(tmp_path / "terminal64.exe", 1, "FTMO-Demo", "challenge")


def test_unknown_position_query_blocks_send(setup):
    broker, client = setup
    plan = broker.size_order("XAUUSD", "buy", 100.1, 99, 25, signal_id="query-fail")
    client.positions_get = lambda **kwargs: None
    with pytest.raises(BrokerError, match="listesi okunamadi"):
        broker.submit(plan, "query-fail")
    assert not client.requests


def test_connect_rejects_real_mode_even_when_server_is_ftmo(tmp_path):
    terminal = tmp_path / "terminal64.exe"
    terminal.write_bytes(b"stub")
    client = FakeMT5(terminal, trade_mode=FakeMT5.ACCOUNT_TRADE_MODE_REAL)
    broker = FTMOBroker(
        FTMOConfig(terminal, 123, "FTMO-Demo", "free_trial"),
        client=client,
        process_checker=lambda _: True,
    )
    with pytest.raises(BrokerError, match="demo"):
        broker.connect()


def test_size_uses_mt5_profit_and_rounds_down_with_cost_reserve(setup):
    broker, _ = setup
    plan = broker.size_order(
        "XAUUSD",
        "buy",
        100,
        99,
        50,
        cost_reserve=10,
        signal_id="case-a",
        take_profit=102,
    )
    assert plan.volume == pytest.approx(0.4)
    assert plan.estimated_stop_loss == pytest.approx(40)
    assert plan.comment == broker._comment("case-a")
    assert plan.take_profit == 102


def test_submit_checks_risk_tp_and_persists_duplicate_guard(setup):
    broker, client = setup
    plan = broker.size_order(
        "XAUUSD", "buy", 100.1, 99, 50, signal_id="one", take_profit=102
    )
    result = broker.submit(plan, "one")
    assert result["status"] == "confirmed"
    assert client.checks[0]["sl"] == 99
    assert client.checks[0]["tp"] == 102
    assert client.checks[0]["volume"] <= 0.5
    with pytest.raises(BrokerError, match="signal_id"):
        broker.submit(plan, "one")
    assert len(client.requests) == 1


def test_partial_fill_is_accepted_only_after_sl_and_risk_confirmation(setup):
    broker, client = setup
    client.send_retcode = client.TRADE_RETCODE_DONE_PARTIAL
    plan = broker.size_order("XAUUSD", "buy", 100.1, 99, 50, signal_id="partial")
    result = broker.submit(plan, "partial")
    assert result["status"] == "confirmed"
    assert result["fill_status"] == "partial"


def test_execution_is_disabled_by_default(tmp_path):
    terminal = tmp_path / "terminal64.exe"
    terminal.write_bytes(b"stub")
    client = FakeMT5(terminal)
    broker = FTMOBroker(
        FTMOConfig(terminal, 123, "FTMO-Demo", "free_trial"),
        client=client,
        state_path=tmp_path / "state.json",
        process_checker=lambda _: True,
    )
    broker.connect()
    plan = broker.size_order("XAUUSD", "buy", 100.1, 99, 50, signal_id="disabled")
    with pytest.raises(BrokerError, match="Emir yürütme kapalı"):
        broker.submit(plan, "disabled")
    assert not client.checks and not client.requests


def test_demo_without_user_approved_free_trial_identity_cannot_execute(tmp_path):
    terminal = tmp_path / "terminal64.exe"
    terminal.write_bytes(b"stub")
    client = FakeMT5(terminal)
    broker = FTMOBroker(
        FTMOConfig(terminal, 123, "FTMO-Demo", "free_trial", execution_enabled=True),
        client=client,
        state_path=tmp_path / "state.json",
        process_checker=lambda _: True,
    )
    broker.connect()
    assert broker.inspect()["account_name"] == "FTMO Free Trial"
    plan = broker.size_order("XAUUSD", "buy", 100.1, 99, 50, signal_id="unapproved")
    with pytest.raises(BrokerError, match="kullanıcı onaylı"):
        broker.submit(plan, "unapproved")
    assert not client.checks and not client.requests


def test_uncertain_send_survives_restart_without_blind_retry(tmp_path):
    terminal = tmp_path / "terminal64.exe"
    terminal.write_bytes(b"stub")
    state = tmp_path / "state.json"
    client = FakeMT5(terminal, send_exception=True)
    config = FTMOConfig(
        terminal,
        123,
        "FTMO-Demo",
        "free_trial",
        execution_enabled=True,
        approved_free_trial_login=123,
        approved_free_trial_server="FTMO-Demo",
    )
    first = FTMOBroker(
        config, client=client, state_path=state, process_checker=lambda _: True
    )
    first.connect()
    plan = first.size_order("XAUUSD", "buy", 100.1, 99, 50, signal_id="timeout")
    with pytest.raises(UncertainExecution):
        first.submit(plan, "timeout")
    second = FTMOBroker(
        config, client=client, state_path=state, process_checker=lambda _: True
    )
    second.connect()
    with pytest.raises(BrokerError, match="reconcile"):
        second.submit(plan, "timeout")
    assert second.reconcile("timeout")["status"] == "uncertain"
    assert len(client.requests) == 1


def test_foreign_position_blocks_new_order(setup):
    broker, client = setup
    client.positions.append(SimpleNamespace(symbol="EURUSD", magic=55, ticket=1))
    plan = broker.size_order("XAUUSD", "buy", 100, 99, 50, signal_id="foreign")
    with pytest.raises(BrokerError, match="foreign"):
        broker.submit(plan, "foreign")
    assert not client.requests


def test_missing_broker_stop_triggers_emergency_close_and_halt(setup):
    broker, client = setup
    client.position_sl = 0
    plan = broker.size_order("XAUUSD", "buy", 100.1, 99, 50, signal_id="no-sl")
    with pytest.raises(BrokerError, match="SL"):
        broker.submit(plan, "no-sl")
    assert len(client.requests) == 2  # entry, then exact-ticket emergency close
    with pytest.raises(BrokerError, match="kilidi"):
        broker.size_order("XAUUSD", "buy", 100.1, 99, 50)


def test_readonly_inspect_never_sends_orders(tmp_path):
    terminal = tmp_path / "terminal64.exe"
    terminal.write_bytes(b"stub")
    client = FakeMT5(terminal)
    result = read_only_inspect(
        terminal, ("XAUUSD",), client=client, process_checker=lambda _: True
    )
    assert result["login"] == 123
    assert result["symbols"]["XAUUSD"]["ask"] == 100.1
    assert not client.requests and not client.checks


def test_close_position_is_exact_ticket_cleanup_even_when_entries_are_halted(setup):
    broker, client = setup
    client.positions.append(
        SimpleNamespace(
            symbol="XAUUSD",
            magic=broker.config.magic,
            ticket=901,
            volume=0.1,
            type=client.ORDER_TYPE_BUY,
            comment="ours",
            sl=99.0,
        )
    )
    broker._halt_reason = "entry halt"
    assert broker.close_position(901)["status"] == "close_sent"
    assert client.requests[-1]["position"] == 901
    assert not client.positions


def test_close_position_refuses_account_switch_even_during_halt(setup):
    broker, client = setup
    client.positions.append(
        SimpleNamespace(
            symbol="XAUUSD",
            magic=broker.config.magic,
            ticket=902,
            volume=0.1,
            type=client.ORDER_TYPE_BUY,
            comment="ours",
            sl=99.0,
        )
    )
    client.account.login = 999
    broker._halt_reason = "entry halt"
    with pytest.raises(BrokerError, match="login/server"):
        broker.close_position(902)
    assert not client.requests


def test_daily_request_cap_is_reserved_before_check_or_send(setup):
    broker, client = setup
    state = broker._load_state()
    day_key = "_daily_requests_" + datetime.now(timezone.utc).date().isoformat()
    state[day_key] = 1499
    broker._save_state(state)
    plan = broker.size_order("XAUUSD", "buy", 100.1, 99, 50, signal_id="cap")
    with pytest.raises(BrokerError, match="request"):
        broker.submit(plan, "cap")
    assert not client.checks and not client.requests
