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
    def matching_frame(symbol_key, *args, **kwargs):
        frame = _df(now)
        frame.loc[:, "close"] = 4225.0 if symbol_key == "XAUUSD" else 22000.0
        return frame

    monkeypatch.setattr(signal_scan.free_data, "ohlcv", matching_frame)
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


def test_delayed_bar_is_still_sent(monkeypatch, tmp_path):
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

    messages = signal_scan.run(now=now, state_path=tmp_path / "state.json")
    assert len(messages) == 1
    assert len(sent) == 1
    assert "onceki kapanmis mumdan" in messages[0]


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


def test_structural_revision_of_same_setup_is_not_sent_twice(monkeypatch, tmp_path):
    now = dt.datetime(2026, 6, 18, 15, 1, tzinfo=dt.timezone.utc)
    calls = {"count": 0}

    def detector(df):
        calls["count"] += 1
        if calls["count"] == 1:
            return Signal(-1, 30607.8, 30762.2, 30376.0)
        return Signal(-1, 30580.5, 30762.2, 30307.9)

    mod = LiveModule(
        "NQ_ORB_STRONG_TREND", "NASDAQ100", "5m", 1.0, 48, detector
    )
    monkeypatch.setattr(signal_scan, "_load_modules", lambda: [mod])
    monkeypatch.setattr(signal_scan.sessions, "is_active", lambda *a, **k: True)
    monkeypatch.setattr(signal_scan.finnhub_live, "collect_quotes", lambda *a, **k: {})
    sent = []
    monkeypatch.setattr(signal_scan.telegram_notify, "send", sent.append)
    state = tmp_path / "state.json"

    first_df = _df(now)
    first_df.loc[:, "close"] = 30600.0
    second_df = _df(now + dt.timedelta(minutes=10))
    second_df.loc[:, "close"] = 30590.0
    frames = iter([first_df, second_df])
    monkeypatch.setattr(signal_scan.free_data, "ohlcv", lambda *a, **k: next(frames))

    first = signal_scan.run(now=now, state_path=state)
    second = signal_scan.run(now=now + dt.timedelta(minutes=10), state_path=state)

    assert len(first) == 1
    assert second == []
    assert len(sent) == 1


def test_signal_more_than_half_r_from_latest_close_is_suppressed(
    monkeypatch, tmp_path
):
    now = dt.datetime(2026, 6, 18, 15, 1, tzinfo=dt.timezone.utc)
    mod = LiveModule(
        "NQ_ORB_STRONG_TREND",
        "NASDAQ100",
        "5m",
        1.0,
        48,
        lambda df: Signal(-1, 30607.8, 30762.2, 30376.0),
    )
    frame = _df(now)
    frame.loc[:, "close"] = 30427.6
    monkeypatch.setattr(signal_scan, "_load_modules", lambda: [mod])
    monkeypatch.setattr(signal_scan.free_data, "ohlcv", lambda *a, **k: frame)
    monkeypatch.setattr(signal_scan.sessions, "is_active", lambda *a, **k: True)
    quote_calls = []
    monkeypatch.setattr(
        signal_scan.finnhub_live,
        "collect_quotes",
        lambda keys: quote_calls.append(keys) or {},
    )
    sent = []
    monkeypatch.setattr(signal_scan.telegram_notify, "send", sent.append)

    messages = signal_scan.run(now=now, state_path=tmp_path / "state.json")

    assert messages == []
    assert sent == []
    assert quote_calls == [set()]


def test_futures_proxy_quote_is_not_requested(monkeypatch, tmp_path):
    now = dt.datetime(2026, 6, 18, 15, 1, tzinfo=dt.timezone.utc)
    mod = LiveModule(
        "NQ_ORB_STRONG_TREND",
        "NASDAQ100",
        "5m",
        1.0,
        48,
        lambda df: Signal(-1, 30600, 30750, 30300),
    )
    frame = _df(now)
    frame.loc[:, "close"] = 30590.0
    monkeypatch.setattr(signal_scan, "_load_modules", lambda: [mod])
    monkeypatch.setattr(signal_scan.free_data, "ohlcv", lambda *a, **k: frame)
    monkeypatch.setattr(signal_scan.sessions, "is_active", lambda *a, **k: True)
    requested = []
    monkeypatch.setattr(
        signal_scan.finnhub_live,
        "collect_quotes",
        lambda keys: requested.append(keys) or {},
    )
    monkeypatch.setattr(signal_scan.telegram_notify, "send", lambda message: None)

    messages = signal_scan.run(now=now, state_path=tmp_path / "state.json")

    assert requested == [set()]
    assert len(messages) == 1
    assert "uyumsuz CFD/spot fiyat proxy'si" in messages[0]
