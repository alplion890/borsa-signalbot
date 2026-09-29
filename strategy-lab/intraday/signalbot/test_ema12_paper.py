import datetime as dt
import json

import pandas as pd

from intraday.signalbot import ema12_paper


OPEN = pd.Timestamp("2026-09-29 13:30:00+00:00")  # 09:30 New York (EDT)
OBSERVED = dt.datetime(2026, 9, 29, 13, 47, tzinfo=dt.timezone.utc)


def _bars():
    idx = pd.date_range("2026-09-28 00:00+00:00", periods=700, freq="5min")
    frame = pd.DataFrame({"open": 100.0, "high": 100.5, "low": 99.5,
                          "close": 100.0, "volume": 10.0}, index=idx)
    frame.loc[OPEN, ["open", "high", "low", "close"]] = [100, 103, 99, 102]
    frame.loc[frame.index > OPEN, ["open", "high", "low", "close"]] = [104, 104.5, 103.5, 104]
    frame.attrs["source"] = "yfinance"
    return frame


def test_signal_and_six_hour_result_match_fixed_rule():
    frame = _bars()
    item = ema12_paper.signal(frame, OBSERVED)
    assert item is not None
    assert item["direction"] == "LONG"
    assert item["entry_proxy"] == 102
    assert item["stop_proxy"] == 98
    assert ema12_paper.settle(item, frame, OBSERVED) is None
    result = ema12_paper.settle(item, frame,
                                dt.datetime(2026, 9, 29, 20, 0, tzinfo=dt.timezone.utc))
    assert result["status"] == "closed"
    assert result["exit_reason"] == "6 saat"
    assert result["net_r"] == 0.49541


def test_local_sends_once_cloud_suppresses_then_falls_back(tmp_path):
    frame = _bars()
    messages = []
    path = tmp_path / "paper.json"
    fetch = lambda *args, **kwargs: frame
    ema12_paper.run(now=OBSERVED, state_path=path, fetch=fetch,
                    send=messages.append, suppress_alert=True)
    assert messages == []
    assert json.loads(path.read_text())["signals"]["2026-09-29"]["alert_sent"] is False
    ema12_paper.run(now=OBSERVED + dt.timedelta(minutes=5), state_path=path,
                    fetch=fetch, send=messages.append)
    ema12_paper.run(now=OBSERVED + dt.timedelta(minutes=5), state_path=path,
                    fetch=fetch, send=messages.append)
    assert len(messages) == 1
    assert "PAPER FORWARD" in messages[0]
    assert "emir acma cagrisi" in messages[0]


def test_result_is_recorded_once_without_local_result_message(tmp_path):
    frame = _bars()
    messages = []
    path = tmp_path / "paper.json"
    fetch = lambda *args, **kwargs: frame
    ema12_paper.run(now=OBSERVED, state_path=path, fetch=fetch, send=messages.append)
    late = dt.datetime(2026, 9, 29, 20, 0, tzinfo=dt.timezone.utc)
    ema12_paper.run(now=late, state_path=path, fetch=fetch, send=messages.append,
                    suppress_result=True)
    assert len(messages) == 1
    assert json.loads(path.read_text())["signals"]["2026-09-29"]["status"] == "closed"
    ema12_paper.run(now=late, state_path=path, fetch=fetch, send=messages.append)
    assert len(messages) == 1
