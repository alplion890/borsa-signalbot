import datetime as dt

import numpy as np
import pandas as pd

from intraday.signalbot import ai_scout


def _df(now, periods=240):
    idx = pd.date_range(end=now - dt.timedelta(minutes=15), periods=periods,
                        freq="15min", tz="UTC")
    base = np.linspace(98.0, 100.0, periods)
    return pd.DataFrame(
        {
            "open": base - 0.1,
            "high": base + 0.7,
            "low": base - 0.7,
            "close": base,
            "volume": np.linspace(100, 150, periods),
        },
        index=idx,
    )


def test_build_snapshot_is_compact_and_numeric():
    now = dt.datetime(2026, 6, 18, 14, 0, tzinfo=dt.timezone.utc)
    snapshot = ai_scout.build_snapshot("XAUUSD", _df(now), now, live_price=100.2)

    assert snapshot["symbol"] == "XAUUSD"
    assert snapshot["live_price"] == 100.2
    assert snapshot["atr14"] > 0
    assert len(snapshot["last_bars"]) == 8
    assert snapshot["data_age_minutes"] == 15


def test_validate_idea_rejects_wrong_side_stop():
    now = dt.datetime(2026, 6, 18, 14, 0, tzinfo=dt.timezone.utc)
    snapshot = ai_scout.build_snapshot("XAUUSD", _df(now), now)
    raw = {
        "symbol": "XAUUSD",
        "status": "opportunity",
        "direction": "long",
        "confidence": 90,
        "setup": "reclaim",
        "entry_low": 99.8,
        "entry_high": 100.2,
        "stop": 101,
        "target": 104,
    }

    assert ai_scout.validate_idea(raw, {"XAUUSD": snapshot}) is None


def test_validate_idea_downgrades_low_rr_to_watch():
    now = dt.datetime(2026, 6, 18, 14, 0, tzinfo=dt.timezone.utc)
    snapshot = ai_scout.build_snapshot("XAUUSD", _df(now), now)
    raw = {
        "symbol": "XAUUSD",
        "status": "opportunity",
        "direction": "long",
        "confidence": 82,
        "setup": "vwap reclaim",
        "entry_low": 99.8,
        "entry_high": 100.2,
        "stop": 99,
        "target": 101,
        "reason": "trend",
        "invalidation": "vwap kaybi",
        "risk_flags": [],
    }

    idea = ai_scout.validate_idea(raw, {"XAUUSD": snapshot})
    assert idea is not None
    assert idea["status"] == "watch"


def test_run_sends_confirmed_opportunity_to_same_telegram(monkeypatch, tmp_path):
    now = dt.datetime(2026, 6, 18, 14, 0, tzinfo=dt.timezone.utc)
    monkeypatch.setattr(ai_scout.free_data, "ohlcv", lambda *a, **k: _df(now))
    monkeypatch.setattr(ai_scout.finnhub_live, "collect_quotes", lambda *a, **k: {})
    monkeypatch.setattr(
        ai_scout.market_context, "collect",
        lambda *a, **k: {
            "recent_news": [], "economic_calendar": [],
            "trade_risk": "normal", "imminent_high_impact_count": 0,
        },
    )
    sent = []
    monkeypatch.setattr(ai_scout.telegram_notify, "send", sent.append)

    raw = {
        "symbol": "XAUUSD",
        "status": "opportunity",
        "direction": "long",
        "confidence": 82,
        "setup": "liquidity sweep reclaim",
        "entry_low": 99.8,
        "entry_high": 100.2,
        "stop": 98,
        "target": 104,
        "reason": "VWAP ustunde reclaim",
        "invalidation": "98 alti kapanis",
        "risk_flags": ["veri gecikmesi"],
    }
    calls = []

    def fake_call(**kwargs):
        calls.append(kwargs["model"])
        return ai_scout.ModelReply({"ideas": [raw]}, 0.001)

    monkeypatch.setattr(ai_scout, "_call_deepseek", fake_call)
    messages = ai_scout.run(
        now=now, state_path=tmp_path / "ai.json", api_key="test-key"
    )

    assert calls == [ai_scout.FLASH_MODEL, ai_scout.PRO_MODEL]
    assert len(messages) == 1
    assert sent == messages
    assert messages[0].startswith("AI FIRSAT Gold long")
    assert (tmp_path / "ai.json").exists()
    assert (tmp_path / "ai_ledger.jsonl").exists()


def test_missing_api_key_is_noop(monkeypatch, tmp_path):
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    assert ai_scout.run(state_path=tmp_path / "ai.json") == []
    assert not (tmp_path / "ai.json").exists()


def test_high_impact_calendar_downgrades_macro_opportunity(monkeypatch, tmp_path):
    now = dt.datetime(2026, 6, 18, 14, 0, tzinfo=dt.timezone.utc)
    monkeypatch.setattr(ai_scout, "_active_symbols", lambda *a: ["XAUUSD"])
    monkeypatch.setattr(ai_scout.free_data, "ohlcv", lambda *a, **k: _df(now))
    monkeypatch.setattr(ai_scout.finnhub_live, "collect_quotes", lambda *a, **k: {})
    monkeypatch.setattr(
        ai_scout.market_context, "collect",
        lambda *a, **k: {
            "recent_news": [{"headline": "US CPI ahead"}],
            "economic_calendar": [{"event": "CPI", "minutes_until": 30}],
            "trade_risk": "high",
            "imminent_high_impact_count": 1,
        },
    )
    raw = {
        "symbol": "XAUUSD", "status": "opportunity", "direction": "long",
        "confidence": 85, "setup": "reclaim", "entry_low": 99.8,
        "entry_high": 100.2, "stop": 98, "target": 104,
        "reason": "trend", "invalidation": "98 alti", "risk_flags": [],
    }
    calls = []

    def fake_call(**kwargs):
        calls.append(kwargs["model"])
        return ai_scout.ModelReply({"ideas": [raw]}, 0.001)

    monkeypatch.setattr(ai_scout, "_call_deepseek", fake_call)
    messages = ai_scout.run(
        now=now, state_path=tmp_path / "ai.json", api_key="test-key", dry_run=True
    )

    assert calls == [ai_scout.FLASH_MODEL]
    assert messages[0].startswith("AI IZLE")
    assert "yuksek etkili veri" in messages[0]
    assert (tmp_path / "ai_ledger.jsonl").read_text(encoding="utf-8") == ""
