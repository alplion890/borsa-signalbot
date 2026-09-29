"""NY first 5m candle / EMA12: observational PAPER forward, never orders."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd

from . import free_data, telegram_notify

UTC = dt.timezone.utc
NY = ZoneInfo("America/New_York")
TR = ZoneInfo("Europe/Istanbul")
STATE_PATH = Path(os.environ.get("EMA12_PAPER_STATE_PATH", ".signalbot/ema12_paper.json"))
COST_PER_SIDE = 0.00009  # Same fixed research assumption, not Maven's spread.
HOLD_BARS = 72
MAX_ALERT_AGE_MINUTES = 35


def _closed(frame: pd.DataFrame, now: dt.datetime) -> pd.DataFrame:
    if frame.empty or frame.index.tz is None:
        return frame.iloc[:0]
    return frame.loc[frame.index + pd.Timedelta(minutes=5) <= pd.Timestamp(now)]


def signal(frame: pd.DataFrame, now: dt.datetime) -> dict | None:
    """Inspect only today's closed 09:30 NY candle, with no future bars."""
    if now.tzinfo is None:
        raise ValueError("now must be timezone aware")
    bars = _closed(frame, now)
    if len(bars) < 60:
        return None
    ny_now = now.astimezone(NY)
    if ny_now.weekday() >= 5:
        return None
    ny_index = bars.index.tz_convert(NY)
    mask = ((ny_index.date == ny_now.date()) & (ny_index.hour == 9) &
            (ny_index.minute == 30))
    if not mask.any():
        return None
    position = int(mask.nonzero()[0][-1])
    bar_time = bars.index[position].to_pydatetime()
    bar_close = bar_time + dt.timedelta(minutes=5)
    age = (now - bar_close).total_seconds() / 60
    if not 0 <= age <= MAX_ALERT_AGE_MINUTES:
        return None
    candle = bars.iloc[position]
    entry = float(candle["close"])
    distance = float(candle["high"] - candle["low"])
    if not entry > 0 or distance < 2 * COST_PER_SIDE * entry:
        return None
    ema12 = float(bars["close"].iloc[:position + 1].ewm(
        span=12, adjust=False).mean().iloc[-1])
    if entry == ema12:
        return None
    direction = "LONG" if entry > ema12 else "SHORT"
    stop = entry - distance if direction == "LONG" else entry + distance
    return {
        "key": ny_now.date().isoformat(),
        "bar_time": bar_time.isoformat(),
        "bar_close": bar_close.isoformat(),
        "observed_at": now.isoformat(),
        "age_minutes": round(age, 1),
        "direction": direction,
        "entry_proxy": round(entry, 6),
        "ema12": round(ema12, 6),
        "range": round(distance, 6),
        "stop_proxy": round(stop, 6),
        "feed": free_data.source_of(frame),
        "status": "open",
    }


def settle(item: dict, frame: pd.DataFrame, now: dt.datetime) -> dict | None:
    """Replay the preregistered stop-first / six-hour rule on closed bars."""
    bars = _closed(frame, now)
    start = pd.Timestamp(item["bar_time"])
    if start not in bars.index:
        return None
    i = int(bars.index.get_loc(start))
    if i + HOLD_BARS >= len(bars):
        return None
    window = bars.iloc[i:i + HOLD_BARS + 1]
    if (window.index[-1] - window.index[0] != pd.Timedelta(hours=6) or
            not window.index.to_series().diff().iloc[1:].eq(pd.Timedelta(minutes=5)).all()):
        return {**item, "status": "unscorable", "reason": "5dk veri boslugu"}
    entry = float(item["entry_proxy"])
    distance = float(item["range"])
    stop = float(item["stop_proxy"])
    is_long = item["direction"] == "LONG"
    exit_price = float(window["close"].iloc[-1])
    exit_time = window.index[-1].to_pydatetime() + dt.timedelta(minutes=5)
    exit_reason = "6 saat"
    for stamp, bar in window.iloc[1:].iterrows():
        hit = float(bar["low"]) <= stop if is_long else float(bar["high"]) >= stop
        if hit:
            exit_price = stop
            exit_time = stamp.to_pydatetime() + dt.timedelta(minutes=5)
            exit_reason = "stop"
            break
    gross_r = (exit_price - entry) / distance * (1 if is_long else -1)
    net_r = gross_r - 2 * COST_PER_SIDE * entry / distance
    return {**item, "status": "closed", "exit_time": exit_time.isoformat(),
            "exit_reason": exit_reason, "exit_proxy": round(exit_price, 6),
            "net_r": round(net_r, 6)}


def format_signal(item: dict, source: str) -> str:
    close_tr = dt.datetime.fromisoformat(item["bar_close"]).astimezone(TR)
    return "\n".join([
        f"PAPER FORWARD | NQ ilk 5dk EMA12 | {source}",
        f"NY 09:30 mumu {close_tr:%H:%M} TR'de kapandi; veri {item['age_minutes']:.0f} dk sonra goruldu.",
        f"Kural etiketi: {item['direction']} (kapanis {item['entry_proxy']:.1f}, EMA12 {item['ema12']:.1f}).",
        f"Varsayimsal giris {item['entry_proxy']:.1f}; stop {item['stop_proxy']:.1f}; mum araligi {item['range']:.1f}; hedef yok, en fazla 6 saat.",
        "Veri: Yahoo NQ=F vadeli 5dk. Maven US100 fiyati ve gercek dolum DEGIL.",
        "Bu yalniz olcum kaydidir: emir acma cagrisi, LIVE edge veya fon riski degildir.",
    ])


def format_result(item: dict) -> str:
    source = "BULUT" if os.environ.get("GITHUB_ACTIONS") else "PC"
    return "\n".join([
        f"PAPER SONUC | NQ ilk 5dk EMA12 | {source} | {item['key']}",
        f"Kural etiketi {item['direction']}; cikis nedeni {item['exit_reason']}; varsayimsal net {item['net_r']:+.3f}R.",
        "Yahoo NQ=F ve sabit maliyet varsayimiyla hesaplandi. Maven islemi veya hesap getirisi degildir.",
    ])


def run(*, now: dt.datetime | None = None, state_path: Path = STATE_PATH,
        fetch=None, send=None, dry_run: bool = False,
        suppress_alert: bool = False, suppress_result: bool = False) -> dict:
    now = now or dt.datetime.now(UTC)
    if now.tzinfo is None:
        raise ValueError("now must be timezone aware")
    try:
        state = json.loads(state_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        state = {"signals": {}}
    records = state.get("signals", {})
    if not isinstance(records, dict):
        raise ValueError("EMA12 PAPER state bozuk")
    ny_now = now.astimezone(NY)
    signal_window = (ny_now.weekday() < 5 and
                     dt.time(9, 35) <= ny_now.time() <= dt.time(10, 10))
    if not signal_window and not any(x.get("status") == "open" for x in records.values()):
        print("EMA12 PAPER: pencere disi, acik kayit yok.")
        return state
    frame = (fetch or free_data.ohlcv)("NASDAQ100", "5m", days=5)
    sender = send or telegram_notify.send
    for key, previous in list(records.items()):
        if previous.get("status") != "open":
            continue
        result = settle(previous, frame, now)
        if result is None:
            continue
        if result["status"] == "closed" and not suppress_result:
            if dry_run:
                print(format_result(result))
            else:
                sender(format_result(result))
        records[key] = result
    item = signal(frame, now)
    is_new = bool(item and item["key"] not in records)
    if is_new:
        item["alert_sent"] = False
        records[item["key"]] = item
    if item and not records[item["key"]].get("alert_sent", False) and not suppress_alert:
        message = format_signal(item, "BULUT" if os.environ.get("GITHUB_ACTIONS") else "PC")
        if dry_run:
            print(message)
        else:
            sender(message)
            records[item["key"]]["alert_sent"] = True
    state = {"version": 1, "signals": records}
    if not dry_run:
        state_path.parent.mkdir(parents=True, exist_ok=True)
        state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"EMA12 PAPER: {len(records)} kayit, yeni={is_new}")
    return state


def main() -> None:
    parser = argparse.ArgumentParser(description="NY 5dk EMA12 PAPER forward gozlemi")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--suppress-alert", action="store_true")
    parser.add_argument("--suppress-result", action="store_true")
    args = parser.parse_args()
    run(dry_run=args.dry_run, suppress_alert=args.suppress_alert,
        suppress_result=args.suppress_result)


if __name__ == "__main__":
    main()
