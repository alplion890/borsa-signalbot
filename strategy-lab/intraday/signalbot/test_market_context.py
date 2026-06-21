import datetime as dt

from intraday.signalbot import market_context


class _Response:
    def __init__(self, *, data=None, text="", content=b""):
        self._data = data
        self.text = text
        self.content = content

    def raise_for_status(self):
        return None

    def json(self):
        return self._data


def test_collect_uses_finnhub_news_and_calendar(monkeypatch):
    now = dt.datetime(2026, 6, 18, 14, 0, tzinfo=dt.timezone.utc)

    def fake_get(url, **kwargs):
        if url == market_context.FINNHUB_NEWS_URL:
            return _Response(data=[{
                "datetime": int(now.timestamp()),
                "headline": "Fed rate decision moves dollar and gold",
                "summary": "Powell speaks",
                "source": "Test",
            }])
        return _Response(data={"economicCalendar": [{
            "time": (now + dt.timedelta(minutes=30)).isoformat(),
            "country": "US",
            "event": "Consumer Price Index CPI",
            "impact": "high",
            "estimate": 2.8,
            "prev": 2.7,
        }]})

    monkeypatch.setattr(market_context.requests, "get", fake_get)
    result = market_context.collect(now, api_key="key")

    assert len(result["recent_news"]) == 1
    assert len(result["economic_calendar"]) == 1
    assert result["trade_risk"] == "high"
    assert result["imminent_high_impact_count"] == 1


def test_bls_ics_parser_marks_upcoming_high_impact(monkeypatch):
    now = dt.datetime(2026, 6, 18, 12, 0, tzinfo=dt.timezone.utc)
    ics = """BEGIN:VCALENDAR
BEGIN:VEVENT
DTSTART:20260618T123000Z
SUMMARY:Consumer Price Index
END:VEVENT
END:VCALENDAR
"""
    monkeypatch.setattr(
        market_context.requests, "get",
        lambda *a, **k: _Response(text=ics),
    )

    events = market_context._bls_calendar(now)
    assert events[0]["minutes_until"] == 30
    assert events[0]["impact"] == "high"
