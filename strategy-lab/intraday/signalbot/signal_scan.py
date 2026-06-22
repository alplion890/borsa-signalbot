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

from . import finnhub_live, free_data, sessions, telegram_notify
from .btc_absorption import module as btc_module
from .message import format_signal
from .risk import risk_plan, tier_of
from .symbols import resolve

STATE_PATH = Path(os.environ.get("SIGNALBOT_STATE_PATH", ".signalbot/state.json"))
MIN_BARS = {"5m": 200, "15m": 520, "1H": 220}
BAR_LENGTH = {"5m": dt.timedelta(minutes=5), "15m": dt.timedelta(minutes=15),
              "1H": dt.timedelta(hours=1)}
MAX_ENTRY_DRIFT_R = 0.5
STRUCTURE_MAX_AGE = dt.timedelta(hours=24)


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


def _structure(sig, bar_time) -> dict:
    return {
        "direction": int(sig.direction),
        "entry": float(sig.entry),
        "sl": float(sig.sl),
        "tp": float(sig.tp),
        "bar_time": bar_time.isoformat(),
    }


def _same_structure(previous: dict | None, current: dict) -> bool:
    """Treat small level revisions as the same still-open trading idea."""
    if not isinstance(previous, dict):
        return False
    try:
        if int(previous["direction"]) != int(current["direction"]):
            return False
        previous_time = pd.Timestamp(previous["bar_time"])
        current_time = pd.Timestamp(current["bar_time"])
        if previous_time.tzinfo is None:
            previous_time = previous_time.tz_localize("UTC")
        if current_time.tzinfo is None:
            current_time = current_time.tz_localize("UTC")
        age = current_time - previous_time
        if age < dt.timedelta(0) or age > STRUCTURE_MAX_AGE:
            return False
        previous_risk = abs(float(previous["entry"]) - float(previous["sl"]))
        current_risk = abs(float(current["entry"]) - float(current["sl"]))
        scale = max(previous_risk, current_risk, 1e-12)
        return (
            abs(float(previous["sl"]) - float(current["sl"])) <= 0.25 * scale
            and abs(float(previous["entry"]) - float(current["entry"])) <= 0.50 * scale
            and abs(float(previous["tp"]) - float(current["tp"])) <= 0.75 * scale
        )
    except (KeyError, TypeError, ValueError):
        return False


def _entry_drift_r(sig, reference_price: float) -> float:
    risk_distance = abs(float(sig.entry) - float(sig.sl))
    if risk_distance <= 0:
        return float("inf")
    return abs(float(reference_price) - float(sig.entry)) / risk_distance


def _prepare_es_div_feeds() -> None:
    """Inject free-data feeds into the existing ES-div detector cache."""
    from ..forward_ea import modules
    modules._ESDIV_CACHE["es"] = free_data.ohlcv("SP500", "15m", days=59)
    modules._ESDIV_CACHE["h1"] = free_data.ohlcv("NASDAQ100", "1H", days=59)


def _is_closed(bar_time, now: dt.datetime, tf: str) -> bool:
    bar_dt = bar_time.to_pydatetime()
    if bar_dt.tzinfo is None:
        bar_dt = bar_dt.replace(tzinfo=dt.timezone.utc)
    return bar_dt + BAR_LENGTH[tf] <= now


def run(*, now: dt.datetime | None = None, phase: str | None = None,
        balance: float | None = None, dry_run: bool = False,
        state_path: Path | None = None) -> list[str]:
    now = now or dt.datetime.now(dt.timezone.utc)
    phase = phase or os.environ.get("PHASE", "bnpl_challenge")
    balance = balance if balance is not None else float(os.environ.get("ACCOUNT_BALANCE", "5000"))
    path = state_path or STATE_PATH
    state = _load_state(path)
    sent_state = state.setdefault("sent", {})
    scanned_state = state.setdefault("scanned", {})
    structure_state = state.setdefault("structures", {})
    messages: list[str] = []
    pending: list[dict] = []
    active_modules = 0
    data_errors = 0

    for mod in _load_modules():
        if not sessions.is_active(mod.name, now):
            continue
        active_modules += 1
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
            latest_closed_price = float(df.iloc[closed_positions[-1]]["close"])
            if previous_scan:
                previous_ts = pd.Timestamp(previous_scan)
                if previous_ts.tzinfo is None and df.index.tz is not None:
                    previous_ts = previous_ts.tz_localize(df.index.tz)
                elif previous_ts.tzinfo is not None and df.index.tz is not None:
                    previous_ts = previous_ts.tz_convert(df.index.tz)
                candidate_positions = [
                    i for i in closed_positions
                    if df.index[i] > previous_ts
                ]
            else:
                candidate_positions = [closed_positions[-1]]
        except Exception as exc:
            data_errors += 1
            print(f"{mod.name}: tarama hatasi: {type(exc).__name__}: {exc}")
            continue
        for position in candidate_positions:
            bar_time = df.index[position]
            try:
                sig = mod.detect(df.iloc[: position + 1])
            except Exception as exc:
                data_errors += 1
                print(f"{mod.name}: detector hatasi: {type(exc).__name__}: {exc}")
                continue
            if sig is None:
                continue
            structure = _structure(sig, bar_time)
            if _same_structure(structure_state.get(mod.name), structure):
                continue
            if any(
                item["mod"].name == mod.name
                and _same_structure(item["structure"], structure)
                for item in pending
            ):
                continue
            drift_r = _entry_drift_r(sig, latest_closed_price)
            if drift_r > MAX_ENTRY_DRIFT_R:
                print(
                    f"{mod.name}: aday atlandi; fiyat giristen "
                    f"{drift_r:.2f}R uzak."
                )
                continue
            fingerprint = _fingerprint(mod.name, bar_time, sig.direction, sig.entry)
            if sent_state.get(mod.name) == fingerprint:
                continue
            plan = risk_plan(
                phase=phase, balance=balance, module_name=mod.name,
                module_weight=mod.weight, symbol_key=mod.symbol_key,
                entry=sig.entry, sl=sig.sl,
            )
            pending.append(
                {
                    "mod": mod,
                    "sig": sig,
                    "bar_time": bar_time,
                    "fingerprint": fingerprint,
                    "plan": plan,
                    "structure": structure,
                }
            )
        scanned_state[mod.name] = df.index[closed_positions[-1]].isoformat()

    quote_keys = {
        item["mod"].symbol_key
        for item in pending
        if resolve(item["mod"].symbol_key).live_quote_compatible
    }
    quotes = finnhub_live.collect_quotes(quote_keys)
    for item in pending:
        mod = item["mod"]
        sig = item["sig"]
        bar_time = item["bar_time"]
        plan = item["plan"]
        symbol_spec = resolve(mod.symbol_key)
        bar_dt = bar_time.to_pydatetime()
        if bar_dt.tzinfo is None:
            bar_dt = bar_dt.replace(tzinfo=dt.timezone.utc)
        signal_age = max(0.0, (now - bar_dt).total_seconds() / 60.0)
        message = format_signal(
            tier=tier_of(mod.name), module=mod.name, symbol_key=mod.symbol_key,
            direction=sig.direction, entry=sig.entry, sl=sig.sl, tp=sig.tp,
            lot=plan.normal_lot, risk_usd=plan.normal_usd, risk_plan=plan,
            trt_time=sessions.to_trt(now),
            expected_delay_minutes=resolve(mod.symbol_key).expected_delay_minutes,
            signal_age_minutes=signal_age,
            live_quote=quotes.get(mod.symbol_key),
            live_quote_supported=symbol_spec.live_quote_compatible,
        )
        if dry_run:
            print(message)
        else:
            telegram_notify.send(message)
        messages.append(message)
        sent_state[mod.name] = item["fingerprint"]
        structure_state[mod.name] = item["structure"]

    if not dry_run:
        _save_state(state, path)
    print(
        f"Tarama tamamlandi. Aktif modul {active_modules}, "
        f"yeni setup {len(messages)}, hata {data_errors}."
    )
    return messages


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--test-finnhub", action="store_true")
    parser.add_argument("--test-telegram", action="store_true")
    parser.add_argument("--ai-scout", action="store_true")
    parser.add_argument("--ai-report", action="store_true")
    args = parser.parse_args()
    if args.ai_report:
        from .ai_memory import report
        print(report(Path(os.environ.get("AI_LEDGER_PATH", ".signalbot/ai_ledger.jsonl"))))
        return
    if args.ai_scout:
        from .ai_scout import run as run_ai_scout
        run_ai_scout(dry_run=args.dry_run)
        return
    if args.test_finnhub:
        keys = {"XAUUSD", "NASDAQ100", "SP500", "EURUSD", "GBPUSD", "BTC"}
        print(f"Finnhub API tani: {json.dumps(finnhub_live.diagnose_api(), ensure_ascii=False)}")
        quotes = finnhub_live.collect_quotes(keys, timeout_seconds=12.0)
        for key in sorted(keys):
            quote = quotes.get(key)
            if quote is None:
                print(f"{key}: CANLI FIYAT GELMEDI ({finnhub_live.provider_symbol(key)})")
            else:
                print(f"{key}: {quote.price:g} ({quote.provider_symbol})")
        return
    if args.test_telegram:
        telegram_notify.send(
            "Borsa sinyal botu test mesaji. Telegram baglantisi calisiyor. "
            "Bot uygun her setupi sinir koymadan bildirecek."
        )
        print("Telegram test mesaji gonderildi.")
        return
    run(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
