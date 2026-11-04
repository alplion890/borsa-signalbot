"""Daytime observation schedule, independent of strategy entry windows."""
from __future__ import annotations

import datetime as dt
from zoneinfo import ZoneInfo

TR = ZoneInfo('Europe/Istanbul')
NY = ZoneInfo('America/New_York')


def is_open(now: dt.datetime | None = None) -> bool:
    now = now or dt.datetime.now(dt.timezone.utc)
    if now.tzinfo is None:
        raise ValueError('now must be timezone aware')
    local = now.astimezone(TR)
    ny = now.astimezone(NY)
    if local.weekday() >= 5 or local.time() < dt.time(9):
        return False
    # Reuse the existing pinned calendar instead of maintaining a second copy.
    from ..forward_ea.telegram_brief import _NYSE_KAPALI, _NYSE_ERKEN_KAPANIS
    if ny.year not in {2026, 2027, 2028} or ny.date().isoformat() in _NYSE_KAPALI:
        return False
    close = dt.time(13) if ny.date().isoformat() in _NYSE_ERKEN_KAPANIS else dt.time(16)
    return ny.weekday() < 5 and ny.time() < close


def main() -> None:
    active = is_open()
    print('open' if active else 'closed')
    raise SystemExit(0 if active else 1)


if __name__ == '__main__':
    main()
