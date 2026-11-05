"""Macro event measurement for the cloud bot: numbers only, never a thesis.

Decision 2026-11-05 ([[Borsa - Tek Kaynak ve Bulut Rolu Karari 2026-11-05]]):
the cloud bot no longer measures trades. For each USD high-impact release it
reports, without adjectives or direction:

- before (<=60 min): expectation and previous value,
- +15 and +60 min: actual (if the source has it), surprise vs expectation,
  NQ and XAU % change, 2Y Treasury futures (ZT=F) % change and the 5Y yield
  change in basis points (the hawkish/dovish read, as a number).

Calendar: Forex Factory weekly JSON (public, unofficial, fetched at most
hourly). Finnhub's calendar is not on the free plan (HTTP 403, 2026-11-05).
Missing values stay missing; nothing is filled in.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
from pathlib import Path
from typing import Callable
from zoneinfo import ZoneInfo

import pandas as pd

from . import telegram_notify

UTC = dt.timezone.utc
TR = ZoneInfo("Europe/Istanbul")
CALENDAR_URL = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"
STATE_PATH = Path(os.environ.get("MAKRO_OLCUM_STATE_PATH", ".signalbot/makro_olcum.json"))
CALENDAR_TTL = dt.timedelta(minutes=60)
PRE_WINDOW = dt.timedelta(minutes=60)
OFFSETS = (15, 60)
STALE_AFTER = dt.timedelta(minutes=120)  # post message only while still fresh
BAR = pd.Timedelta(minutes=5)

# name -> (yfinance ticker or free_data symbol key, kind)
SERIES = {"NQ": ("NASDAQ100", "key"), "XAU": ("XAUUSD", "key"),
          "ZT": ("ZT=F", "ticker"), "Y5": ("^FVX", "ticker")}

_NUM = re.compile(r"^\s*([+-]?\d+(?:\.\d+)?)\s*([A-Za-z%]*)\s*$")


def parse_number(text: str | None) -> tuple[float, str] | None:
    if not text:
        return None
    match = _NUM.match(str(text))
    if not match:
        return None
    return float(match.group(1)), match.group(2)


def surprise(actual: str | None, forecast: str | None) -> str | None:
    a, f = parse_number(actual), parse_number(forecast)
    if a is None or f is None or a[1] != f[1]:
        return None
    diff = round(a[0] - f[0], 6)
    return f"{diff:+g}{a[1]}"


def usd_high_events(raw: list[dict]) -> list[dict]:
    events = []
    for item in raw:
        if item.get("country") != "USD" or item.get("impact") != "High":
            continue
        try:
            when = dt.datetime.fromisoformat(str(item["date"])).astimezone(UTC)
        except (KeyError, ValueError):
            continue
        title = str(item.get("title", "")).strip()
        events.append({
            "key": f"{when.isoformat()}|{title}",
            "title": title,
            "time_utc": when,
            "forecast": item.get("forecast") or None,
            "previous": item.get("previous") or None,
            "actual": item.get("actual") or None,
        })
    return sorted(events, key=lambda e: e["time_utc"])


def _close_at(frame: pd.DataFrame, moment: dt.datetime) -> float | None:
    """Close of the last bar that had closed by `moment`; None if data stops earlier."""
    if frame is None or frame.empty:
        return None
    closes = frame.index + BAR
    stamp = pd.Timestamp(moment)
    if closes.max() < stamp:
        return None
    done = frame[closes <= stamp]
    return None if done.empty else float(done["close"].iloc[-1])


def reaction_pct(frame: pd.DataFrame, t0: dt.datetime, minutes: int) -> float | None:
    before = _close_at(frame, t0)
    after = _close_at(frame, t0 + dt.timedelta(minutes=minutes))
    if before is None or after is None or before == 0:
        return None
    return (after / before - 1) * 100


def change_bp(frame: pd.DataFrame, t0: dt.datetime, minutes: int) -> float | None:
    before = _close_at(frame, t0)
    after = _close_at(frame, t0 + dt.timedelta(minutes=minutes))
    if before is None or after is None:
        return None
    return (after - before) * 100


def _fmt(value: float | None, suffix: str, digits: int = 2) -> str:
    return "veri yok" if value is None else f"{value:+.{digits}f}{suffix}"


def _clock(moment: dt.datetime) -> str:
    return moment.astimezone(TR).strftime("%d.%m %H:%M TR")


def format_pre(event: dict) -> str:
    return (f"MAKRO OLAY · {event['title']} · {_clock(event['time_utc'])}\n"
            f"beklenti {event['forecast'] or 'kaynakta yok'} · "
            f"onceki {event['previous'] or 'kaynakta yok'}\n"
            "Olcum: Forex Factory takvimi. Yon bilgisi degildir.")


def measure(event: dict, minutes: int, fetch_bars: Callable[[str], pd.DataFrame]) -> dict:
    t0 = event["time_utc"]
    frames = {}
    for name in SERIES:
        try:
            frames[name] = fetch_bars(name)
        except Exception as exc:  # one feed down must not hide the others
            print(f"MAKRO_FEED_ERROR {name} {type(exc).__name__}", flush=True)
            frames[name] = None
    return {
        "key": event["key"], "title": event["title"], "time_utc": t0.isoformat(),
        "offset_min": minutes, "forecast": event["forecast"],
        "previous": event["previous"], "actual": event["actual"],
        "surprise": surprise(event["actual"], event["forecast"]),
        "nq_pct": reaction_pct(frames["NQ"], t0, minutes),
        "xau_pct": reaction_pct(frames["XAU"], t0, minutes),
        "zt_pct": reaction_pct(frames["ZT"], t0, minutes),
        "y5_bp": change_bp(frames["Y5"], t0, minutes),
    }


def format_post(rec: dict) -> str:
    actual = rec["actual"] or "kaynakta yok"
    surp = rec["surprise"] or "hesaplanamadi"
    t0 = dt.datetime.fromisoformat(rec["time_utc"])
    return (f"MAKRO OLCUM +{rec['offset_min']} dk · {rec['title']} · {_clock(t0)}\n"
            f"gerceklesen {actual} · beklenti {rec['forecast'] or 'kaynakta yok'} · "
            f"surpriz {surp}\n"
            f"NQ {_fmt(rec['nq_pct'], '%')} · XAU {_fmt(rec['xau_pct'], '%')}\n"
            f"2Y vadeli (ZT=F) {_fmt(rec['zt_pct'], '%', 3)} · "
            f"5Y getiri {_fmt(rec['y5_bp'], ' bp', 1)}\n"
            "Sadece olcum; yorum ve karar kullanicida.")


def _load(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {"sent": [], "records": [], "calendar": None, "fetched_at": None}


def _save(path: Path, state: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, ensure_ascii=False, indent=1), encoding="utf-8")


def _calendar(state: dict, now: dt.datetime, fetch: Callable[[], list]) -> list:
    fetched = state.get("fetched_at")
    fresh = fetched and now - dt.datetime.fromisoformat(fetched) < CALENDAR_TTL
    if state.get("calendar") is not None and fresh:
        return state["calendar"]
    try:
        raw = fetch()
    except Exception as exc:
        print(f"MAKRO_CALENDAR_ERROR {type(exc).__name__}", flush=True)
        return state.get("calendar") or []
    state["calendar"], state["fetched_at"] = raw, now.isoformat()
    return raw


def run(*, now: dt.datetime | None = None, state_path: Path = STATE_PATH,
        fetch_calendar: Callable[[], list] | None = None,
        fetch_bars: Callable[[str], pd.DataFrame] | None = None,
        send: Callable[[str], None] | None = None,
        dry_run: bool = False) -> list[str]:
    now = now or dt.datetime.now(UTC)
    fetch_calendar = fetch_calendar or _fetch_calendar
    fetch_bars = fetch_bars or _fetch_bars
    send = send or telegram_notify.send
    state = _load(state_path)
    sent = set(state.get("sent", []))
    out: list[str] = []

    for event in usd_high_events(_calendar(state, now, fetch_calendar)):
        t0 = event["time_utc"]
        jobs = []
        if dt.timedelta(0) < t0 - now <= PRE_WINDOW:
            jobs.append(("pre", None))
        for minutes in OFFSETS:
            due = t0 + dt.timedelta(minutes=minutes)
            if due <= now <= due + STALE_AFTER:
                jobs.append((f"+{minutes}", minutes))
        for tag, minutes in jobs:
            key = f"{event['key']}|{tag}"
            if key in sent:
                continue
            if minutes is None:
                message = format_pre(event)
            else:
                rec = measure(event, minutes, fetch_bars)
                state.setdefault("records", []).append(rec)
                message = format_post(rec)
            if dry_run:
                print(message, flush=True)
            else:
                send(message)
            sent.add(key)
            out.append(message)

    state["sent"] = sorted(sent)[-500:]
    state["records"] = state.get("records", [])[-2000:]
    _save(state_path, state)
    return out


def _fetch_calendar() -> list:
    import requests
    resp = requests.get(CALENDAR_URL, timeout=15,
                        headers={"User-Agent": "borsa-signalbot/1.0"})
    resp.raise_for_status()
    data = resp.json()
    if not isinstance(data, list):
        raise ValueError("calendar payload is not a list")
    return data


def _fetch_bars(name: str) -> pd.DataFrame:
    from . import free_data
    target, kind = SERIES[name]
    if kind == "key":
        return free_data.ohlcv(target, "5m", days=5)
    return free_data._normalize(free_data._yf_download(target, "5m", "5d"))


def main() -> None:
    parser = argparse.ArgumentParser(description="Macro event measurement (numbers only)")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    run(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
