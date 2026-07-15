"""forward_ea.notify testleri."""
from __future__ import annotations

import datetime as dt

import pandas as pd

from intraday.forward_ea.notify import notify_new_positions, build_message
from intraday.forward_ea.positions import PaperPosition


def _pos(module: str, symbol: str, minutes_ago: float,
         entry: float = 20000.0, sl: float = 20050.0, tp: float = 19900.0,
         weight: float = 1.0) -> PaperPosition:
    now = dt.datetime.now(dt.timezone.utc)
    return PaperPosition(
        module=module, symbol=symbol, direction=-1,
        entry_time=pd.Timestamp(now - dt.timedelta(minutes=minutes_ago)),
        entry=entry, sl=sl, tp=tp, weight=weight,
        max_hold_bars=48, cost_per_side=0.0001,
    )


def test_fresh_live_position_sends_message_with_card():
    outbox: list[str] = []
    sent = notify_new_positions(
        [_pos("NQ_ORB_STRONG_TREND", "NASDAQ100", minutes_ago=5)],
        send_fn=outbox.append,
    )
    assert len(sent) == 1 and len(outbox) == 1
    assert "MAVEN EMIR KARTI" in outbox[0]
    assert "US100" in outbox[0]
    assert "SELL" in outbox[0]


def test_stale_backfill_position_is_skipped():
    outbox: list[str] = []
    sent = notify_new_positions(
        [_pos("NQ_ORB_STRONG_TREND", "NASDAQ100", minutes_ago=120)],
        send_fn=outbox.append,
    )
    assert sent == [] and outbox == []


def test_paper_module_message_has_no_card():
    now = dt.datetime.now(dt.timezone.utc)
    msg = build_message(
        _pos("EUR_LONDON_FADE_EMA", "EURUSD", minutes_ago=3,
             entry=1.095, sl=1.096, tp=1.093), now,
    )
    assert "paper" in msg.lower()
    assert "MAVEN EMIR KARTI" not in msg


def test_send_failure_does_not_raise():
    def boom(_msg: str) -> None:
        raise RuntimeError("env eksik")

    sent = notify_new_positions(
        [_pos("NQ_ORB_STRONG_TREND", "NASDAQ100", minutes_ago=5)],
        send_fn=boom,
    )
    assert len(sent) == 1  # mesaj uretildi, hata donguyu kirmadi
