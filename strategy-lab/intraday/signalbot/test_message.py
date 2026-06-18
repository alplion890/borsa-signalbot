from intraday.signalbot.message import format_signal
from intraday.signalbot.risk import Tier


def test_live_gold_message():
    msg = format_signal(
        tier=Tier.LIVE,
        module="GOLD_NY_ORB_TREND",
        symbol_key="XAUUSD",
        direction=1,
        entry=4225,
        sl=4214,
        tp=4247,
        lot=0.5,
        risk_usd=75.0,
        trt_time="16:42"
    )
    assert "long" in msg
    assert "4225" in msg
    assert "4214" in msg
    assert "4247" in msg
    assert msg.count("|") == 0
    assert "retest" in msg.lower()


def test_paper_eur_message():
    msg = format_signal(
        tier=Tier.PAPER,
        module="EUR_LONDON_FADE_EMA",
        symbol_key="EURUSD",
        direction=-1,
        entry=1.0950,
        sl=1.0960,
        tp=1.0930,
        lot=0.1,
        risk_usd=50.0,
        trt_time="10:15"
    )
    assert "paper" in msg.lower()
    assert ("teyit" in msg.lower()) or ("kontrol" in msg.lower())
