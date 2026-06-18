import datetime as dt
from intraday.signalbot.sessions import to_trt, is_active


def test_to_trt_converts_correctly():
    utc_dt = dt.datetime(2026, 6, 18, 13, 42, tzinfo=dt.timezone.utc)
    result = to_trt(utc_dt)
    assert result == "16 42"


def test_is_active_btc_absorption_always_true():
    utc_dt = dt.datetime(2026, 6, 18, 3, 0, tzinfo=dt.timezone.utc)
    assert is_active("BTC_ABSORPTION", utc_dt) is True


def test_is_active_gold_ny_orb_at_3_utc_is_false():
    utc_dt = dt.datetime(2026, 6, 18, 3, 0, tzinfo=dt.timezone.utc)
    assert is_active("GOLD_NY_ORB_TREND", utc_dt) is False
