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
        "setup_family": "liquidity_sweep",
        "session": "new_york",
        "structure_level": 99.5,
        "entry_low": 99.8,
        "entry_high": 100.2,
        "stop": 101,
        "target": 104,
    }

    assert ai_scout.validate_idea(raw, {"XAUUSD": snapshot}) is None


def test_validate_idea_rejects_below_two_rr():
    now = dt.datetime(2026, 6, 18, 14, 0, tzinfo=dt.timezone.utc)
    snapshot = ai_scout.build_snapshot("XAUUSD", _df(now), now)
    raw = {
        "symbol": "XAUUSD",
        "status": "opportunity",
        "direction": "long",
        "confidence": 82,
        "setup": "vwap reclaim",
        "setup_family": "trend_pullback",
        "session": "new_york",
        "structure_level": 99.5,
        "entry_low": 99.8,
        "entry_high": 100.2,
        "stop": 99,
        "target": 101,
        "reason": "trend",
        "invalidation": "vwap kaybi",
        "evidence": ["trend", "location", "trigger"],
        "risk_flags": [],
    }

    idea = ai_scout.validate_idea(raw, {"XAUUSD": snapshot})
    assert idea is None


def test_validate_idea_rejects_stale_market_data():
    now = dt.datetime(2026, 6, 18, 14, 0, tzinfo=dt.timezone.utc)
    snapshot = ai_scout.build_snapshot("XAUUSD", _df(now), now)
    snapshot["data_age_minutes"] = 46
    raw = {
        "symbol": "XAUUSD", "status": "opportunity", "direction": "long",
        "confidence": 90, "setup": "sweep reclaim",
        "setup_family": "liquidity_sweep", "session": "asia",
        "structure_level": 99.5, "entry_low": 99.8, "entry_high": 100.2,
        "stop": 98, "target": 104,
        "reason": "structured trade", "invalidation": "98 alti",
        "evidence": ["trend regime", "liquidity sweep", "reclaim trigger"],
        "risk_flags": [],
    }

    assert ai_scout.validate_idea(raw, {"XAUUSD": snapshot}) is None


def test_session_is_derived_from_clock_not_model_label():
    now = dt.datetime(2026, 6, 18, 14, 0, tzinfo=dt.timezone.utc)
    snapshot = ai_scout.build_snapshot("XAUUSD", _df(now), now)
    raw = {
        "symbol": "XAUUSD", "status": "opportunity", "direction": "long",
        "confidence": 90, "setup": "sweep reclaim",
        "setup_family": "liquidity_sweep", "session": "asia",
        "structure_level": 99.5, "entry_low": 99.8, "entry_high": 100.2,
        "stop": 98, "target": 104,
        "reason": "structured trade", "invalidation": "98 alti",
        "evidence": ["trend regime", "liquidity sweep", "reclaim trigger"],
        "risk_flags": [],
    }

    idea = ai_scout.validate_idea(raw, {"XAUUSD": snapshot})
    assert idea is not None
    assert idea["session"] == "new_york"


def test_duplicate_evidence_does_not_count_as_three_categories():
    now = dt.datetime(2026, 6, 18, 14, 0, tzinfo=dt.timezone.utc)
    snapshot = ai_scout.build_snapshot("XAUUSD", _df(now), now)
    raw = {
        "symbol": "XAUUSD", "status": "opportunity", "direction": "long",
        "confidence": 90, "setup": "vwap reclaim",
        "setup_family": "trend_pullback", "session": "new_york",
        "structure_level": 99.5, "entry_low": 99.8, "entry_high": 100.2,
        "stop": 98, "target": 104,
        "reason": "vwap", "invalidation": "98 alti",
        "evidence": ["vwap reclaim", "vwap reclaim", "vwap reclaim"],
        "risk_flags": [],
    }

    assert ai_scout.validate_idea(raw, {"XAUUSD": snapshot}) is None


def test_multiple_candidates_use_one_batched_pro_call(monkeypatch, tmp_path):
    now = dt.datetime(2026, 6, 18, 14, 0, tzinfo=dt.timezone.utc)
    monkeypatch.setattr(ai_scout, "_active_symbols", lambda *a: ["XAUUSD", "SP500"])
    monkeypatch.setattr(ai_scout.free_data, "ohlcv", lambda *a, **k: _df(now))
    monkeypatch.setattr(ai_scout.finnhub_live, "collect_quotes", lambda *a, **k: {})
    monkeypatch.setattr(
        ai_scout.market_context, "collect",
        lambda *a, **k: {
            "recent_news": [], "economic_calendar": [],
            "trade_risk": "normal", "imminent_high_impact_count": 0,
        },
    )
    base = {
        "status": "opportunity", "direction": "long", "confidence": 85,
        "setup": "sweep reclaim", "setup_family": "liquidity_sweep",
        "session": "asia", "structure_level": 99.5,
        "entry_low": 99.8, "entry_high": 100.2, "stop": 98, "target": 104,
        "reason": "structured trade", "invalidation": "98 alti",
        "evidence": ["trend regime", "liquidity sweep", "reclaim trigger"],
        "risk_flags": [],
    }
    raw = [{**base, "symbol": "XAUUSD"}, {**base, "symbol": "SP500"}]
    calls = []

    def fake_call(**kwargs):
        calls.append(kwargs["model"])
        return ai_scout.ModelReply({"ideas": raw}, 0.001)

    monkeypatch.setattr(ai_scout, "_call_deepseek", fake_call)
    monkeypatch.setattr(ai_scout.telegram_notify, "send", lambda text: None)

    messages = ai_scout.run(now=now, state_path=tmp_path / "ai.json", api_key="key")

    assert calls == [ai_scout.FLASH_MODEL, ai_scout.PRO_MODEL]
    assert len(messages) == 2


def test_pro_cannot_replace_candidate_with_opposite_trade(monkeypatch, tmp_path):
    now = dt.datetime(2026, 6, 18, 14, 0, tzinfo=dt.timezone.utc)
    monkeypatch.setattr(ai_scout, "_active_symbols", lambda *a: ["XAUUSD"])
    monkeypatch.setattr(ai_scout.free_data, "ohlcv", lambda *a, **k: _df(now))
    monkeypatch.setattr(ai_scout.finnhub_live, "collect_quotes", lambda *a, **k: {})
    monkeypatch.setattr(
        ai_scout.market_context, "collect",
        lambda *a, **k: {
            "recent_news": [], "economic_calendar": [],
            "trade_risk": "normal", "imminent_high_impact_count": 0,
        },
    )
    long_idea = {
        "symbol": "XAUUSD", "status": "opportunity", "direction": "long",
        "confidence": 85, "setup": "sweep reclaim",
        "setup_family": "liquidity_sweep", "session": "new_york",
        "structure_level": 99.5, "entry_low": 99.8, "entry_high": 100.2,
        "stop": 98, "target": 104, "reason": "structured trade",
        "invalidation": "98 alti",
        "evidence": ["trend regime", "liquidity sweep", "reclaim trigger"],
        "risk_flags": [],
    }
    short_idea = {
        **long_idea, "direction": "short", "stop": 102, "target": 96,
        "setup": "failed breakout", "setup_family": "failed_breakout",
    }
    replies = iter((long_idea, short_idea))
    monkeypatch.setattr(
        ai_scout, "_call_deepseek",
        lambda **kwargs: ai_scout.ModelReply({"ideas": [next(replies)]}, 0.001),
    )
    sent = []
    monkeypatch.setattr(ai_scout.telegram_notify, "send", sent.append)

    messages = ai_scout.run(now=now, state_path=tmp_path / "ai.json", api_key="key")

    assert messages == []
    assert sent == []
    assert "pro_rejected" in (
        tmp_path / "ai_audit.jsonl"
    ).read_text(encoding="utf-8")


def test_pro_api_error_keeps_flash_cost_state_and_does_not_crash(monkeypatch, tmp_path):
    now = dt.datetime(2026, 6, 18, 14, 0, tzinfo=dt.timezone.utc)
    monkeypatch.setattr(ai_scout, "_active_symbols", lambda *a: ["XAUUSD"])
    monkeypatch.setattr(ai_scout.free_data, "ohlcv", lambda *a, **k: _df(now))
    monkeypatch.setattr(ai_scout.finnhub_live, "collect_quotes", lambda *a, **k: {})
    monkeypatch.setattr(
        ai_scout.market_context, "collect",
        lambda *a, **k: {
            "recent_news": [], "economic_calendar": [],
            "trade_risk": "normal", "imminent_high_impact_count": 0,
        },
    )
    raw = {
        "symbol": "XAUUSD", "status": "opportunity", "direction": "long",
        "confidence": 85, "setup": "sweep reclaim",
        "setup_family": "liquidity_sweep", "session": "new_york",
        "structure_level": 99.5, "entry_low": 99.8, "entry_high": 100.2,
        "stop": 98, "target": 104, "reason": "structured trade",
        "invalidation": "98 alti",
        "evidence": ["trend regime", "liquidity sweep", "reclaim trigger"],
        "risk_flags": [],
    }
    calls = 0

    def fake_call(**kwargs):
        nonlocal calls
        calls += 1
        if calls == 1:
            return ai_scout.ModelReply({"ideas": [raw]}, 0.001)
        raise TimeoutError("pro timeout")

    monkeypatch.setattr(ai_scout, "_call_deepseek", fake_call)
    state_path = tmp_path / "ai.json"

    assert ai_scout.run(now=now, state_path=state_path, api_key="key") == []
    state = __import__("json").loads(state_path.read_text(encoding="utf-8"))
    assert state["spent_usd"] == 0.001
    assert state["calls"] == 1
    assert state["last_run_utc"] == now.isoformat()
    assert "pro_api_error" in (
        tmp_path / "ai_audit.jsonl"
    ).read_text(encoding="utf-8")


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
        "setup_family": "liquidity_sweep",
        "session": "new_york",
        "structure_level": 99.5,
        "entry_low": 99.8,
        "entry_high": 100.2,
        "stop": 98,
        "target": 104,
        "reason": "VWAP ustunde reclaim",
        "invalidation": "98 alti kapanis",
        "evidence": ["trend regime", "liquidity sweep", "reclaim trigger"],
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
        "setup_family": "liquidity_sweep",
        "session": "new_york", "structure_level": 99.5,
        "entry_high": 100.2, "stop": 98, "target": 104,
        "reason": "trend", "invalidation": "98 alti",
        "evidence": ["trend regime", "liquidity sweep", "reclaim trigger"],
        "risk_flags": [],
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
    assert messages == []
    assert (tmp_path / "ai_ledger.jsonl").read_text(encoding="utf-8") == ""


def test_same_open_structure_is_suppressed_but_new_atr_structure_is_allowed(
        monkeypatch, tmp_path):
    now = dt.datetime(2026, 6, 18, 14, 0, tzinfo=dt.timezone.utc)
    monkeypatch.setattr(ai_scout, "_active_symbols", lambda *a: ["XAUUSD"])
    monkeypatch.setattr(ai_scout.free_data, "ohlcv", lambda *a, **k: _df(now))
    monkeypatch.setattr(ai_scout.finnhub_live, "collect_quotes", lambda *a, **k: {})
    monkeypatch.setattr(
        ai_scout.market_context, "collect",
        lambda *a, **k: {
            "recent_news": [], "economic_calendar": [],
            "trade_risk": "normal", "imminent_high_impact_count": 0,
        },
    )
    raw = {
        "symbol": "XAUUSD", "status": "opportunity", "direction": "long",
        "confidence": 85, "setup": "sweep reclaim", "entry_low": 99.8,
        "setup_family": "liquidity_sweep",
        "session": "new_york", "structure_level": 99.5,
        "entry_high": 100.2, "stop": 98, "target": 104,
        "reason": "structured asymmetric trade", "invalidation": "98 alti",
        "evidence": ["trend regime", "liquidity sweep", "reclaim trigger"],
        "risk_flags": [],
    }
    monkeypatch.setattr(
        ai_scout, "_call_deepseek",
        lambda **kwargs: ai_scout.ModelReply({"ideas": [raw]}, 0.001),
    )
    sent = []
    monkeypatch.setattr(ai_scout.telegram_notify, "send", sent.append)
    state = tmp_path / "ai.json"

    first = ai_scout.run(now=now, state_path=state, api_key="key")
    second = ai_scout.run(
        now=now + dt.timedelta(minutes=10), state_path=state, api_key="key"
    )
    moved = {
        **raw,
        "entry_low": 101.4,
        "entry_high": 101.6,
        "stop": 99.4,
        "target": 106.0,
    }
    monkeypatch.setattr(
        ai_scout, "_call_deepseek",
        lambda **kwargs: ai_scout.ModelReply({"ideas": [moved]}, 0.001),
    )
    third = ai_scout.run(
        now=now + dt.timedelta(minutes=20), state_path=state, api_key="key"
    )

    assert len(first) == 1
    assert second == []
    assert len(third) == 1
    assert len(sent) == 2
    assert "same_open_structure" in (
        tmp_path / "ai_audit.jsonl"
    ).read_text(encoding="utf-8")
