from contextlib import nullcontext
import json
import pytest
from unittest.mock import Mock

from .test_feed_routing import live_runner


def test_paper_refresh_without_notifications_never_executes_orders(monkeypatch):
    book = Mock()
    monkeypatch.setattr(live_runner, "_load_state", lambda: {})
    monkeypatch.setattr(live_runner, "_book_from_state", lambda _: book)
    book.open_positions = []
    monkeypatch.setattr(live_runner, "forward_test_modules", lambda: [])
    monkeypatch.setattr(live_runner, "retired_position_managers", lambda _: [])
    monkeypatch.setattr(live_runner.mt5_io, "session", lambda: nullcontext())
    monkeypatch.setattr(live_runner.mt5_io, "account", lambda: {"broker":"Maven", "server":"Maven-test", "connected":True})
    monkeypatch.setattr(live_runner, "_dashboard", Mock())
    cycle, save, executor = Mock(return_value=[object()]), Mock(), Mock()
    monkeypatch.setattr(live_runner, "_cycle", cycle)
    monkeypatch.setattr(live_runner, "_save_state", save)
    monkeypatch.setattr(live_runner, "OrderExecutor", executor)
    from . import notify
    sender = Mock()
    monkeypatch.setattr(notify, "notify_new_positions", sender)
    live_runner.run_once(warmup_days=1, live=False, notify=False)
    save.assert_called_once()
    executor.assert_not_called()
    sender.assert_not_called()
    assert cycle.call_args.args[-1] == 1


def test_local_state_has_measurement_timestamp(monkeypatch, tmp_path):
    from .positions import Book
    target = tmp_path / "state.json"
    monkeypatch.setattr(live_runner, "STATE_JSON", target)
    monkeypatch.setattr(live_runner, "LEDGER_CSV", tmp_path / "ledger.csv")
    live_runner._save_state(Book(), {})
    assert json.loads(target.read_text())["updated_at"].endswith("+00:00")


def test_wrong_broker_cannot_advance_forward_or_execute(monkeypatch):
    book=Mock()
    book.open_positions=[]
    monkeypatch.setattr(live_runner,"_load_state",lambda:{})
    monkeypatch.setattr(live_runner,"_book_from_state",lambda _:book)
    monkeypatch.setattr(live_runner,"forward_test_modules",lambda:[])
    monkeypatch.setattr(live_runner,"retired_position_managers",lambda _:[])
    monkeypatch.setattr(live_runner.mt5_io,"session",lambda:nullcontext())
    monkeypatch.setattr(live_runner.mt5_io,"account",lambda:{"broker":"Other", "server":"Other", "connected":True})
    cycle,save,executor=Mock(),Mock(),Mock()
    monkeypatch.setattr(live_runner,"_cycle",cycle)
    monkeypatch.setattr(live_runner,"_save_state",save)
    monkeypatch.setattr(live_runner,"OrderExecutor",executor)
    with pytest.raises(Exception,match="Maven"):
        live_runner.run_once(notify=False)
    cycle.assert_not_called()
    save.assert_not_called()
    executor.assert_not_called()
