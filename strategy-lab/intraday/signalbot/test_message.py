from intraday.signalbot.message import format_signal
from intraday.signalbot.finnhub_live import LiveQuote
from intraday.signalbot.risk import Tier
from intraday.signalbot.risk import risk_plan


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


def test_delayed_futures_message_has_live_price_guard():
    msg = format_signal(
        tier=Tier.LIVE,
        module="GOLD_NY_ORB_TREND",
        symbol_key="XAUUSD",
        direction=1,
        entry=3000,
        sl=2990,
        tp=3010,
        lot=0.07,
        risk_usd=75,
        trt_time="16 45",
        expected_delay_minutes=10,
    )
    assert "10 dakika onceki" in msg
    assert "Finnhub canli fiyat gelmedi" in msg
    assert "Maven" in msg


def test_live_quote_is_compared_in_r_units():
    msg = format_signal(
        tier=Tier.LIVE,
        module="GOLD_NY_ORB_TREND",
        symbol_key="XAUUSD",
        direction=1,
        entry=3000,
        sl=2990,
        tp=3010,
        lot=0.07,
        risk_usd=75,
        trt_time="16 45",
        signal_age_minutes=15,
        live_quote=LiveQuote("XAUUSD", "OANDA:XAU_USD", 3003, 1781800000000),
    )
    assert "15 dakika onceki" in msg
    assert "Finnhub anlik fiyat 3003" in msg
    assert "+0.30R" in msg
    assert "long yonune ilerlemis" in msg


def test_funded_message_contains_locked_stops_and_consistency():
    plan = risk_plan(
        phase="bnpl_funded", balance=5000, module_name="GOLD_NY_ORB_TREND",
        module_weight=1.0, symbol_key="XAUUSD", entry=3000, sl=2990,
    )
    msg = format_signal(
        tier=Tier.LIVE, module="GOLD_NY_ORB_TREND", symbol_key="XAUUSD",
        direction=1, entry=3000, sl=2990, tp=3015,
        lot=plan.normal_lot, risk_usd=plan.normal_usd,
        risk_plan=plan, trt_time="16 45",
    )
    assert "Funded kilidi" in msg
    assert "Kazanc sonrasi risk artirma" in msg
    assert "Gun kari yuzde 0.5" in msg
    assert "yuzde 18" in msg
    assert "yuzde 2.5 kar tamponu" in msg


def test_funded_paper_message_forces_zero_real_risk():
    plan = risk_plan(
        phase="bnpl_funded", balance=5000, module_name="SWEEP_ES_DIV",
        module_weight=2.0, symbol_key="NASDAQ100", entry=20000, sl=19950,
    )
    msg = format_signal(
        tier=Tier.PAPER, module="SWEEP_ES_DIV", symbol_key="NASDAQ100",
        direction=1, entry=20000, sl=19950, tp=20100,
        lot=plan.normal_lot, risk_usd=plan.normal_usd,
        risk_plan=plan, trt_time="16 45",
    )
    assert "gercek risk sifir" in msg
    assert "Sadece izle" in msg
