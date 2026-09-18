import datetime as dt

import pandas as pd

from intraday.signalbot import mobile_watch


NOW = dt.datetime(2026, 9, 18, 15, 45, tzinfo=dt.timezone.utc)


def _bars():
    index = pd.date_range(end=NOW - dt.timedelta(minutes=15), periods=15 * 96,
                          freq="15min", tz="UTC")
    frame = pd.DataFrame({"open": 100.0, "high": 101.0, "low": 99.0,
                          "close": 100.0, "volume": 20.0}, index=index)
    frame.loc[index[-1], "close"] = 101.0
    return frame


def test_watch_sends_once_per_day_and_level(tmp_path):
    sent = []
    state = tmp_path / "watch.json"
    fetch = lambda *args, **kwargs: _bars()

    first = mobile_watch.run(now=NOW, state_path=state, fetch=fetch, send=sent.append)
    second = mobile_watch.run(now=NOW, state_path=state, fetch=fetch, send=sent.append)

    assert first is not None and "IZLEME" in first
    assert "Mekanik LIVE sinyali degildir" in first
    assert second is None
    assert len(sent) == 1


def test_watch_rejects_stale_bar_and_closed_window(tmp_path):
    sent = []
    stale = _bars().iloc[:-4]
    assert mobile_watch.run(now=NOW, state_path=tmp_path / "a.json",
                            fetch=lambda *a, **kw: stale, send=sent.append) is None
    before = NOW - dt.timedelta(hours=1)
    assert mobile_watch.run(now=before, state_path=tmp_path / "b.json",
                            fetch=lambda *a, **kw: _bars(), send=sent.append) is None
    assert sent == []


def test_watch_vwap_reclaim_with_volume_without_level_contact():
    frame = _bars()
    ny_dates = frame.index.tz_convert(mobile_watch.NY).date
    previous = ny_dates == dt.date(2026, 9, 17)
    frame.loc[previous, "high"] = 130.0
    frame.loc[previous, "low"] = 70.0
    frame.loc[frame.index[-1], "close"] = 100.5
    frame.loc[frame.index[-1], "volume"] = 50.0

    item = mobile_watch.candidate(frame, NOW)

    assert item is not None
    assert "vwap" in item["key"]
    assert item["volume_ratio"] == 2.5


def test_failed_delivery_does_not_dedupe_future_attempt(tmp_path):
    state = tmp_path / "watch.json"

    def fail(_message):
        raise RuntimeError("telegram failed")

    try:
        mobile_watch.run(now=NOW, state_path=state,
                         fetch=lambda *a, **kw: _bars(), send=fail)
    except RuntimeError:
        pass
    else:
        raise AssertionError("delivery failure should propagate")

    assert not state.exists()
