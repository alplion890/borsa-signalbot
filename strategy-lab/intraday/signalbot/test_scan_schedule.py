import datetime as dt
from intraday.signalbot.scan_schedule import is_open, TR


def at(day, hour, minute=0):
    return dt.datetime.fromisoformat(f'{day}T{hour:02}:{minute:02}').replace(tzinfo=TR)


def test_entire_day_includes_ema_and_late_us_session():
    assert not is_open(at('2026-10-01', 8, 55))
    assert is_open(at('2026-10-01', 9))
    assert is_open(at('2026-10-01', 16, 35))
    assert is_open(at('2026-10-01', 20, 5))
    assert is_open(at('2026-10-01', 22, 55))
    assert not is_open(at('2026-10-01', 23))


def test_winter_dst_holiday_and_early_close():
    assert is_open(at('2026-12-01', 23, 55))
    assert not is_open(at('2026-12-02', 0))
    assert not is_open(at('2026-11-26', 16, 35))
    assert is_open(at('2026-11-27', 20, 55))
    assert not is_open(at('2026-11-27', 21))
    assert not is_open(at('2026-10-03', 16, 35))
