import datetime as dt

import numpy as np
import pandas as pd

from intraday.forward_ea.modules import LiveModule, Signal
from intraday.signalbot import signal_scan


def _df(now):
    idx = pd.date_range(end=now, periods=600, freq="5min", tz="UTC")
    p = np.linspace(4200, 4225, len(idx))
    return pd.DataFrame(
        {"open": p, "high": p + 1, "low": p - 1, "close": p, "volume": 10},
        index=idx,
    )


def test_sends_every_distinct_setup_and_dedupes_same_bar(monkeypatch, tmp_path):
    now = dt.datetime(2026, 6, 18, 13, 42, tzinfo=dt.timezone.utc)
    modules = [
        LiveModule("GOLD_NY_ORB_TREND", "XAUUSD", "5m", 1.0, 48,
                   lambda df: Signal(1, 4225, 4214, 4247)),
        LiveModule("NQ_ORB_STRONG_TREND", "NASDAQ100", "5m", 1.0, 48,
                   lambda df: Signal(-1, 22000, 22020, 21970)),
    ]
    monkeypatch.setattr(signal_scan, "_load_modules", lambda: modules)
    monkeypatch.setattr(signal_scan.free_data, "ohlcv", lambda *a, **k: _df(now))
    monkeypatch.setattr(signal_scan.sessions, "is_active", lambda *a, **k: True)
    monkeypatch.setattr(signal_scan.finnhub_live, "collect_quotes", lambda *a, **k: {})
    sent = []
    monkeypatch.setattr(signal_scan.telegram_notify, "send", sent.append)
    state = tmp_path / "state.json"

    first = signal_scan.run(now=now, state_path=state)
    second = signal_scan.run(now=now, state_path=state)

    assert len(first) == 2
    assert len(sent) == 2
    assert second == []


def test_stale_bar_is_not_sent(monkeypatch, tmp_path):
    now = dt.datetime(2026, 6, 18, 13, 42, tzinfo=dt.timezone.utc)
    mod = LiveModule("GOLD_NY_ORB_TREND", "XAUUSD", "5m", 1.0, 48,
                     lambda df: Signal(1, 4225, 4214, 4247))
    monkeypatch.setattr(signal_scan, "_load_modules", lambda: [mod])
    stale = _df(now - dt.timedelta(hours=2))
    monkeypatch.setattr(signal_scan.free_data, "ohlcv", lambda *a, **k: stale)
    monkeypatch.setattr(signal_scan.sessions, "is_active", lambda *a, **k: True)
    monkeypatch.setattr(signal_scan.finnhub_live, "collect_quotes", lambda *a, **k: {})
    sent = []
    monkeypatch.setattr(signal_scan.telegram_notify, "send", sent.append)

    assert signal_scan.run(now=now, state_path=tmp_path / "state.json") == []
    assert sent == []


def test_dry_run_does_not_persist_dedupe_state(monkeypatch, tmp_path):
    now = dt.datetime(2026, 6, 18, 13, 42, tzinfo=dt.timezone.utc)
    mod = LiveModule("GOLD_NY_ORB_TREND", "XAUUSD", "5m", 1.0, 48,
                     lambda df: Signal(1, 4225, 4214, 4247))
    monkeypatch.setattr(signal_scan, "_load_modules", lambda: [mod])
    monkeypatch.setattr(signal_scan.free_data, "ohlcv", lambda *a, **k: _df(now))
    monkeypatch.setattr(signal_scan.sessions, "is_active", lambda *a, **k: True)
    monkeypatch.setattr(signal_scan.finnhub_live, "collect_quotes", lambda *a, **k: {})
    state = tmp_path / "state.json"

    assert len(signal_scan.run(now=now, state_path=state, dry_run=True)) == 1
    assert not state.exists()
