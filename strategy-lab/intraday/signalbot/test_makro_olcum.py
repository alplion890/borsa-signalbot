"""Macro measurement: numbers only, no direction, no adjectives."""
from __future__ import annotations

import datetime as dt
import json

import pandas as pd

from . import makro_olcum as mo

UTC = dt.timezone.utc
T0 = dt.datetime(2026, 11, 6, 13, 30, tzinfo=UTC)  # NFP 08:30 ET

RAW = [
    {"title": "Non-Farm Employment Change", "country": "USD", "impact": "High",
     "date": "2026-11-06T08:30:00-05:00", "forecast": "65K", "previous": "29K",
     "actual": "120K"},
    {"title": "Unemployment Rate", "country": "USD", "impact": "High",
     "date": "2026-11-06T08:30:00-05:00", "forecast": "4.2%", "previous": "4.2%"},
    {"title": "German Factory Orders", "country": "EUR", "impact": "High",
     "date": "2026-11-06T02:00:00-05:00", "forecast": "1.0%", "previous": "0.5%"},
    {"title": "Crude Oil Inventories", "country": "USD", "impact": "Medium",
     "date": "2026-11-06T10:30:00-05:00", "forecast": "", "previous": ""},
]


def _bars(start_close: float, end_close: float) -> pd.DataFrame:
    idx = pd.date_range("2026-11-06 12:00", "2026-11-06 15:55", freq="5min", tz="UTC")
    close = pd.Series(start_close, index=idx)
    close[idx >= pd.Timestamp("2026-11-06 13:30", tz="UTC")] = end_close
    return pd.DataFrame({"open": close, "high": close, "low": close,
                         "close": close, "volume": 1.0}, index=idx)


def test_parse_number_with_units():
    assert mo.parse_number("65K") == (65.0, "K")
    assert mo.parse_number("-0.3%") == (-0.3, "%")
    assert mo.parse_number("1.25B") == (1.25, "B")
    assert mo.parse_number("") is None
    assert mo.parse_number(None) is None


def test_surprise_needs_same_unit():
    assert mo.surprise("120K", "65K") == "+55K"
    assert mo.surprise("4.3%", "4.2%") == "+0.1%"
    assert mo.surprise("4.3%", "65K") is None
    assert mo.surprise(None, "65K") is None


def test_only_usd_high_impact_events():
    events = mo.usd_high_events(RAW)
    assert [e["title"] for e in events] == ["Non-Farm Employment Change",
                                            "Unemployment Rate"]
    assert events[0]["time_utc"] == T0
    assert events[1]["actual"] is None


def test_reaction_uses_bar_closed_before_event_and_at_offset():
    frame = _bars(100.0, 101.0)
    assert round(mo.reaction_pct(frame, T0, 15), 4) == 1.0
    # data not yet covering t0+60 -> no number, never a guess
    assert mo.reaction_pct(frame[frame.index < "2026-11-06 14:00"], T0, 60) is None


def test_yield_change_in_basis_points():
    frame = _bars(4.689, 4.739)
    assert round(mo.change_bp(frame, T0, 15), 1) == 5.0


def _fetchers(calls):
    def bars(name):
        calls.append(name)
        return {"NQ": _bars(25000, 25100), "XAU": _bars(4000, 3990),
                "ZT": _bars(102.0, 101.9), "Y5": _bars(4.689, 4.739)}[name]
    return bars


def test_run_sends_pre_and_post_once_and_records(tmp_path):
    state = tmp_path / "makro.json"
    sent, calls = [], []
    common = dict(state_path=state, fetch_calendar=lambda: RAW,
                  fetch_bars=_fetchers(calls), send=sent.append)

    mo.run(now=T0 - dt.timedelta(minutes=30), **common)
    assert len(sent) == 2 and "beklenti 65K" in sent[0] and "onceki 29K" in sent[0]

    mo.run(now=T0 + dt.timedelta(minutes=16), **common)
    post = [m for m in sent if "+15 dk" in m]
    assert len(post) == 2
    nfp = next(m for m in post if "Non-Farm" in m)
    assert "gerceklesen 120K" in nfp and "surpriz +55K" in nfp
    assert "NQ +0.40%" in nfp and "XAU -0.25%" in nfp and "5Y getiri +5.0 bp" in nfp
    unemp = next(m for m in post if "Unemployment" in m)
    assert "gerceklesen kaynakta yok" in unemp

    before = len(sent)
    mo.run(now=T0 + dt.timedelta(minutes=20), **common)
    assert len(sent) == before  # no duplicates

    records = json.loads(state.read_text(encoding="utf-8"))["records"]
    assert {r["offset_min"] for r in records} == {15}
    assert records[0]["nq_pct"] is not None


def test_stale_events_are_not_announced(tmp_path):
    sent = []
    mo.run(now=T0 + dt.timedelta(hours=5), state_path=tmp_path / "s.json",
           fetch_calendar=lambda: RAW, fetch_bars=_fetchers([]), send=sent.append)
    assert sent == []


def test_messages_carry_no_direction_words(tmp_path):
    sent = []
    common = dict(state_path=tmp_path / "s.json", fetch_calendar=lambda: RAW,
                  fetch_bars=_fetchers([]), send=sent.append)
    mo.run(now=T0 - dt.timedelta(minutes=30), **common)
    mo.run(now=T0 + dt.timedelta(minutes=61), **common)
    text = " ".join(sent).lower()
    for word in ("sahin", "guvercin", "guclu", "zayif", "long", "short",
                 "al ", "sat ", "yukselis", "dusus", "beklentiyi asti"):
        assert word not in text


def test_calendar_is_fetched_at_most_hourly(tmp_path):
    state = tmp_path / "s.json"
    count = []

    def cal():
        count.append(1)
        return RAW

    for minutes in (0, 20, 50):
        mo.run(now=T0 - dt.timedelta(hours=3) + dt.timedelta(minutes=minutes),
               state_path=state, fetch_calendar=cal,
               fetch_bars=_fetchers([]), send=lambda m: None)
    assert len(count) == 1


def test_calendar_failure_does_not_crash(tmp_path):
    def broken():
        raise RuntimeError("ff down")

    out = mo.run(now=T0, state_path=tmp_path / "s.json", fetch_calendar=broken,
                 fetch_bars=_fetchers([]), send=lambda m: None)
    assert out == []
