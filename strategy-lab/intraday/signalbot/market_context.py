"""Ucretsiz haber ve ekonomik takvim baglami.

Oncelik mevcut Finnhub anahtaridir. Ucretsiz plan endpointleri sinirlarsa
resmi Fed RSS, BLS iCalendar ve BEA RSS kaynaklari kullanilir. Her hata bos
baglama doner; AI scout'un teknik taramasini durdurmaz.
"""
from __future__ import annotations

import datetime as dt
import email.utils
import os
import re
import xml.etree.ElementTree as ET
from typing import Any

import requests

FINNHUB_NEWS_URL = "https://finnhub.io/api/v1/news"
FINNHUB_CALENDAR_URL = "https://finnhub.io/api/v1/calendar/economic"
FED_RSS_URL = "https://www.federalreserve.gov/feeds/press_monetary.xml"
BLS_ICS_URL = "https://www.bls.gov/schedule/news_release/bls.ics"
BEA_RSS_URL = "https://apps.bea.gov/rss/rss.xml"

_KEYWORDS = {
    "fed", "fomc", "powell", "rate", "rates", "inflation", "cpi", "pce",
    "payroll", "employment", "unemployment", "jobs", "gdp", "treasury",
    "yield", "dollar", "gold", "oil", "tariff", "sanction", "war",
    "bitcoin", "crypto", "sec", "ecb", "boe", "euro", "sterling",
}
_HIGH_IMPACT = {
    "consumer price", "cpi", "employment situation", "nonfarm", "payroll",
    "fomc", "federal funds", "interest rate", "pce", "gross domestic product",
    "gdp", "producer price", "ppi", "retail sales", "job openings", "jolts",
    "unemployment", "powell", "monetary policy",
}


def _utc(value: dt.datetime) -> dt.datetime:
    return value if value.tzinfo else value.replace(tzinfo=dt.timezone.utc)


def _parse_datetime(value: Any) -> dt.datetime | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return dt.datetime.fromtimestamp(float(value), tz=dt.timezone.utc)
    text = str(value).strip()
    if not text:
        return None
    try:
        parsed = dt.datetime.fromisoformat(text.replace("Z", "+00:00"))
        return _utc(parsed).astimezone(dt.timezone.utc)
    except ValueError:
        pass
    try:
        parsed = email.utils.parsedate_to_datetime(text)
        return _utc(parsed).astimezone(dt.timezone.utc)
    except (TypeError, ValueError):
        return None


def _relevant(text: str) -> bool:
    lower = text.lower()
    return any(word in lower for word in _KEYWORDS)


def _high_impact(text: str, impact: Any = "") -> bool:
    impact_text = str(impact).lower()
    return impact_text in {"3", "high"} or any(word in text.lower() for word in _HIGH_IMPACT)


def _get_json(url: str, *, params: dict[str, Any], timeout: float = 8.0) -> Any:
    response = requests.get(
        url, params=params, timeout=timeout,
        headers={"User-Agent": "borsa-signalbot/1.0"},
    )
    response.raise_for_status()
    return response.json()


def _finnhub_news(now: dt.datetime, api_key: str) -> list[dict[str, Any]]:
    data = _get_json(FINNHUB_NEWS_URL, params={"category": "general", "token": api_key})
    if not isinstance(data, list):
        return []
    cutoff = now - dt.timedelta(hours=24)
    result = []
    for item in data:
        if not isinstance(item, dict):
            continue
        published = _parse_datetime(item.get("datetime"))
        headline = str(item.get("headline", "")).strip()
        summary = str(item.get("summary", "")).strip()
        if not headline or published is None or published < cutoff:
            continue
        if not _relevant(f"{headline} {summary}"):
            continue
        result.append({
            "published_utc": published.isoformat(),
            "headline": headline[:180],
            "source": str(item.get("source", "Finnhub"))[:50],
        })
    return sorted(result, key=lambda x: x["published_utc"], reverse=True)[:8]


def _finnhub_calendar(now: dt.datetime, api_key: str) -> list[dict[str, Any]]:
    start = (now - dt.timedelta(days=1)).date().isoformat()
    end = (now + dt.timedelta(days=2)).date().isoformat()
    data = _get_json(
        FINNHUB_CALENDAR_URL,
        params={"from": start, "to": end, "token": api_key},
    )
    rows = data.get("economicCalendar", []) if isinstance(data, dict) else []
    result = []
    for item in rows:
        if not isinstance(item, dict):
            continue
        event = str(item.get("event", "")).strip()
        country = str(item.get("country", "")).upper()
        event_time = _parse_datetime(item.get("time") or item.get("date"))
        if not event or event_time is None or country not in {"US", "EU", "GB"}:
            continue
        minutes = (event_time - now).total_seconds() / 60
        if not -90 <= minutes <= 36 * 60 or not _high_impact(event, item.get("impact")):
            continue
        result.append({
            "time_utc": event_time.isoformat(),
            "minutes_until": round(minutes),
            "country": country,
            "event": event[:140],
            "impact": str(item.get("impact", "high"))[:20],
            "actual": item.get("actual"),
            "estimate": item.get("estimate"),
            "previous": item.get("prev"),
        })
    return sorted(result, key=lambda x: x["time_utc"])[:12]


def _rss_items(url: str, now: dt.datetime) -> list[dict[str, Any]]:
    response = requests.get(url, timeout=8, headers={"User-Agent": "borsa-signalbot/1.0"})
    response.raise_for_status()
    root = ET.fromstring(response.content)
    cutoff = now - dt.timedelta(hours=36)
    result = []
    for item in root.findall(".//item"):
        title = (item.findtext("title") or "").strip()
        published = _parse_datetime(item.findtext("pubDate"))
        if not title or published is None or published < cutoff or not _relevant(title):
            continue
        result.append({
            "published_utc": published.isoformat(),
            "headline": title[:180],
            "source": "Federal Reserve" if "federalreserve" in url else "BEA",
        })
    return result


def _unfold_ics(text: str) -> list[str]:
    return re.sub(r"\r?\n[ \t]", "", text).splitlines()


def _parse_ics_time(value: str) -> dt.datetime | None:
    value = value.strip()
    for fmt in ("%Y%m%dT%H%M%SZ", "%Y%m%dT%H%M%S", "%Y%m%d"):
        try:
            parsed = dt.datetime.strptime(value, fmt)
            # BLS takvimi ET saatleriyle yayinlanir; Z yoksa America/New_York.
            if value.endswith("Z"):
                return parsed.replace(tzinfo=dt.timezone.utc)
            try:
                from zoneinfo import ZoneInfo
                return parsed.replace(tzinfo=ZoneInfo("America/New_York")).astimezone(
                    dt.timezone.utc
                )
            except Exception:
                return parsed.replace(tzinfo=dt.timezone.utc)
        except ValueError:
            continue
    return None


def _bls_calendar(now: dt.datetime) -> list[dict[str, Any]]:
    response = requests.get(
        BLS_ICS_URL, timeout=8, headers={"User-Agent": "borsa-signalbot/1.0"}
    )
    response.raise_for_status()
    events: list[dict[str, str]] = []
    current: dict[str, str] | None = None
    for line in _unfold_ics(response.text):
        if line == "BEGIN:VEVENT":
            current = {}
        elif line == "END:VEVENT" and current is not None:
            events.append(current)
            current = None
        elif current is not None and ":" in line:
            key, value = line.split(":", 1)
            current[key.split(";", 1)[0]] = value
    result = []
    for event in events:
        title = event.get("SUMMARY", "")
        event_time = _parse_ics_time(event.get("DTSTART", ""))
        if not title or event_time is None or not _high_impact(title):
            continue
        minutes = (event_time - now).total_seconds() / 60
        if -90 <= minutes <= 36 * 60:
            result.append({
                "time_utc": event_time.isoformat(),
                "minutes_until": round(minutes),
                "country": "US",
                "event": title[:140],
                "impact": "high",
            })
    return sorted(result, key=lambda x: x["time_utc"])[:12]


def collect(now: dt.datetime, *, api_key: str | None = None) -> dict[str, Any]:
    """Kisa, dedupe edilmis ve prompta hazir piyasa baglami."""
    now = _utc(now).astimezone(dt.timezone.utc)
    token = api_key or os.environ.get("FINNHUB_API_KEY")
    news: list[dict[str, Any]] = []
    calendar: list[dict[str, Any]] = []
    sources: list[str] = []

    if token:
        try:
            news = _finnhub_news(now, token)
            if news:
                sources.append("Finnhub news")
        except Exception as exc:
            print(f"AI haber Finnhub hatasi: {type(exc).__name__}: {exc}")
        # Finnhub free plan bu endpointte 403 donuyor. Varsayilan olarak resmi,
        # ucretsiz BLS takvimi kullan; sadece acikca etkinlestirilirse dene.
        if os.environ.get("FINNHUB_CALENDAR_ENABLED", "").lower() in {"1", "true", "yes"}:
            try:
                calendar = _finnhub_calendar(now, token)
                if calendar:
                    sources.append("Finnhub calendar")
            except Exception as exc:
                print(f"AI takvim Finnhub hatasi: {type(exc).__name__}: {exc}")

    if not news:
        for url in (FED_RSS_URL, BEA_RSS_URL):
            try:
                news.extend(_rss_items(url, now))
            except Exception as exc:
                print(f"AI resmi RSS hatasi: {type(exc).__name__}: {exc}")
        if news:
            sources.append("Fed/BEA RSS")

    if not calendar:
        try:
            calendar = _bls_calendar(now)
            if calendar:
                sources.append("BLS calendar")
        except Exception as exc:
            print(f"AI BLS takvim hatasi: {type(exc).__name__}: {exc}")

    seen: set[str] = set()
    deduped_news = []
    for item in sorted(news, key=lambda x: x["published_utc"], reverse=True):
        key = re.sub(r"\W+", " ", item["headline"].lower()).strip()
        if key in seen:
            continue
        seen.add(key)
        deduped_news.append(item)

    imminent = [
        event for event in calendar
        if -15 <= int(event.get("minutes_until", 99999)) <= 60
    ]
    return {
        "sources": sources,
        "recent_news": deduped_news[:8],
        "economic_calendar": calendar[:12],
        "imminent_high_impact_count": len(imminent),
        "trade_risk": "high" if imminent else "normal",
    }
