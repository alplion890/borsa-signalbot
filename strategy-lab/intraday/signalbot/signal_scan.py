"""Seven-module Telegram signal scanner.

Every valid setup is sent. The scanner only suppresses an identical signal
from the same closed bar, so GitHub's repeated cron runs do not spam Telegram.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path

import pandas as pd

from . import free_data, sessions, telegram_notify
from .btc_absorption import module as btc_module
from .message import format_signal
from .risk import risk_plan, tier_of

STATE_PATH = Path(os.environ.get("SIGNALBOT_STATE_PATH", ".signalbot/state.json"))
MIN_BARS = {"5m": 200, "15m": 520, "1H": 220}
FRESHNESS = {"5m": dt.timedelta(minutes=24), "15m": dt.timedelta(minutes=34),
             "1H": dt.timedelta(minutes=79)}
BAR_LENGTH = {"5m": dt.timedelta(minutes=5), "15m": dt.timedelta(minutes=15),
              "1H": dt.timedelta(hours=1)}


def _load_modules() -> list:
    from ..forward_ea.modules import default_modules
    return [*default_modules(), btc_module()]


def _load_state(path: Path = STATE_PATH) -> dict:
    if not path.exists():
        return {"sent": {}}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {"sent": {}}
    except (OSError, json.JSONDecodeError):
        return {"sent": {}}


def _save_state(state: dict, path: Path = STATE_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2, sort_keys=True), encoding="utf-8")


def _fingerprint(module_name: str, bar_time, direction: int, entry: float) -> str:
    raw = f"{module_name}|{bar_time.isoformat()}|{direction}|{entry:.8f}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]


def _prepare_es_div_feeds() -> None:
    """Inject free-data feeds into the existing ES-div detector cache."""
    from ..forward_ea import modules
    modules._ESDIV_CACHE["es"] = free_data.ohlcv("SP500", "15m", days=59)
    modules._ESDIV_CACHE["h1"] = free_data.ohlcv("NASDAQ100", "1H", days=59)


def _is_fresh(bar_time, now: dt.datetime, tf: str) -> bool:
    bar_dt = bar_time.to_pydatetime()
    if bar_dt.tzinfo is None:
        bar_dt = bar_dt.replace(tzinfo=dt.timezone.utc)
    return dt.timedelta(0) <= now - bar_dt <= FRESHNESS[tf]


def _is_closed(bar_time, now: dt.datetime, tf: str) -> bool:
    bar_dt = bar_time.to_pydatetime()
    if bar_dt.tzinfo is None:
        bar_dt = bar_dt.replace(tzinfo=dt.timezone.utc)
    return bar_dt + BAR_LENGTH[tf] <= now


def run(*, now: dt.datetime | None = None, phase: str | None = None,
        balance: float | None = None, dry_run: bool = False,
        state_path: Path | None = None) -> list[str]:
    now = now or dt.datetime.now(dt.timezone.utc)
    phase = phase or os.environ.get("PHASE", "challenge")
    balance = balance if balance is not None else float(os.environ.get("ACCOUNT_BALANCE", "5000"))
    path = state_path or STATE_PATH
    state = _load_state(path)
    sent_state = state.setdefault("sent", {})
    scanned_state = state.setdefault("scanned", {})
    messages: list[str] = []

    for mod in _load_modules():
        if not sessions.is_active(mod.name, now):
            continue
        try:
            if mod.name == "SWEEP_ES_DIV":
                _prepare_es_div_feeds()
            df = free_data.ohlcv(mod.symbol_key, mod.tf, days=59)
            if df is None or len(df) < MIN_BARS[mod.tf]:
                continue
            previous_scan = scanned_state.get(mod.name)
            closed_positions = [
                i for i, bar_time in enumerate(df.index) if _is_closed(bar_time, now, mod.tf)
            ]
            if not closed_positions:
                continue
            if previous_scan:
                previous_ts = pd.Timestamp(previous_scan)
                if previous_ts.tzinfo is None and df.index.tz is not None:
                    previous_ts = previous_ts.tz_localize(df.index.tz)
                elif previous_ts.tzinfo is not None and df.index.tz is not None:
                    previous_ts = previous_ts.tz_convert(df.index.tz)
                candidate_positions = [
                    i for i in closed_positions
                    if df.index[i] > previous_ts and _is_fresh(df.index[i], now, mod.tf)
                ]
            else:
                candidate_positions = [closed_positions[-1]]
        except Exception as exc:
            print(f"{mod.name}: tarama hatasi: {type(exc).__name__}: {exc}")
            continue
        for position in candidate_positions:
            bar_time = df.index[position]
            if not _is_fresh(bar_time, now, mod.tf):
                continue
            try:
                sig = mod.detect(df.iloc[: position + 1])
            except Exception as exc:
                print(f"{mod.name}: detector hatasi: {type(exc).__name__}: {exc}")
                continue
            if sig is None:
                continue
            fingerprint = _fingerprint(mod.name, bar_time, sig.direction, sig.entry)
            if sent_state.get(mod.name) == fingerprint:
                continue
            plan = risk_plan(
                phase=phase, balance=balance, module_name=mod.name,
                module_weight=mod.weight, symbol_key=mod.symbol_key,
                entry=sig.entry, sl=sig.sl,
            )
            message = format_signal(
                tier=tier_of(mod.name), module=mod.name, symbol_key=mod.symbol_key,
                direction=sig.direction, entry=sig.entry, sl=sig.sl, tp=sig.tp,
                lot=plan.normal_lot, risk_usd=plan.normal_usd, risk_plan=plan,
                trt_time=sessions.to_trt(now),
            )
            if dry_run:
                print(message)
            else:
                telegram_notify.send(message)
            messages.append(message)
            sent_state[mod.name] = fingerprint
        scanned_state[mod.name] = df.index[closed_positions[-1]].isoformat()

    _save_state(state, path)
    return messages


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    run(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
