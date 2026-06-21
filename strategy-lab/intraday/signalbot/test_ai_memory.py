import datetime as dt

import pandas as pd

from intraday.signalbot import ai_memory


def _record(now, direction="long"):
    idea = {
        "symbol": "XAUUSD",
        "direction": direction,
        "setup": "liquidity sweep reclaim",
        "confidence": 82,
        "entry_low": 99.8,
        "entry_high": 100.2,
        "stop": 99.0 if direction == "long" else 101.0,
        "target": 102.0 if direction == "long" else 98.0,
        "rr": 2.0,
    }
    return ai_memory.make_record(
        idea, now=now, market_context={"trade_risk": "normal"}
    )


def test_settle_target_after_entry():
    now = dt.datetime(2026, 6, 18, 14, 0, tzinfo=dt.timezone.utc)
    idx = pd.date_range(now + dt.timedelta(minutes=15), periods=3, freq="15min", tz="UTC")
    frame = pd.DataFrame({
        "open": [100.3, 100.5, 101.5],
        "high": [100.5, 101.0, 102.2],
        "low": [99.9, 100.1, 101.0],
        "close": [100.2, 100.8, 102.0],
        "volume": [10, 10, 10],
    }, index=idx)
    records = [_record(now)]

    changed = ai_memory.settle(records, {"XAUUSD": frame}, now + dt.timedelta(hours=1))

    assert changed >= 1
    assert records[0]["outcome"] == "target"
    assert records[0]["result_r"] == 2.0
    assert records[0]["mfe_r"] >= 2.0


def test_same_bar_stop_and_target_is_ambiguous():
    now = dt.datetime(2026, 6, 18, 14, 0, tzinfo=dt.timezone.utc)
    idx = pd.date_range(now + dt.timedelta(minutes=15), periods=1, freq="15min", tz="UTC")
    frame = pd.DataFrame({
        "open": [100.0], "high": [102.2], "low": [98.8],
        "close": [100.5], "volume": [10],
    }, index=idx)
    records = [_record(now)]

    ai_memory.settle(records, {"XAUUSD": frame}, now + dt.timedelta(minutes=30))

    assert records[0]["outcome"] == "ambiguous"
    assert records[0]["result_r"] is None


def test_summary_groups_measured_results():
    now = dt.datetime(2026, 6, 18, 14, 0, tzinfo=dt.timezone.utc)
    winner = _record(now)
    loser = _record(now + dt.timedelta(minutes=1))
    winner.update({"outcome": "target", "result_r": 2.0, "mfe_r": 2.1})
    loser.update({"outcome": "stop", "result_r": -1.0, "mfe_r": 0.3})

    result = ai_memory.summary([winner, loser])

    assert result["resolved_samples"] == 2
    assert result["patterns"][0]["samples"] == 2
    assert result["patterns"][0]["avg_r"] == 0.5
    assert result["win_rate"] == 0.5
    assert result["wins"] == 1
    assert result["losses"] == 1


def test_report_contains_recent_trade_results(tmp_path):
    now = dt.datetime(2026, 6, 18, 14, 0, tzinfo=dt.timezone.utc)
    winner = _record(now)
    winner.update({"outcome": "target", "result_r": 2.0, "mfe_r": 2.2})
    path = tmp_path / "ledger.jsonl"
    ai_memory.save([winner], path)

    text = ai_memory.report(path)

    assert "Win rate 100.0%" in text
    assert "Ortalama R +2.000" in text
    assert "liquidity sweep reclaim" in text
