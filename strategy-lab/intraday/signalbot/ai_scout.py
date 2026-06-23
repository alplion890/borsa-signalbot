"""DeepSeek destekli bagimsiz piyasa firsat tarayicisi.

Ana strateji tarayicisini asla bloke etmez. GitHub Actions icinde ana bot
tamamlandiktan sonra ayri bir adim olarak calisir ve ayni Telegram kanalina
yalnizca Pro teyitli AI FIRSAT mesajlari yollar.
"""
from __future__ import annotations

import datetime as dt
import json
import math
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd
import requests

from ..edge_lab import _adx
from ..indicators import atr, daily_vwap, ema, prev_day_levels
from . import ai_memory, finnhub_live, free_data, market_context, sessions, telegram_notify
from .symbols import resolve

API_URL = "https://api.deepseek.com/chat/completions"
STATE_PATH = Path(os.environ.get("AI_SCOUT_STATE_PATH", ".signalbot/ai_state.json"))
MONTHLY_BUDGET_USD = float(os.environ.get("AI_MONTHLY_BUDGET_USD", "2.0"))
MIN_RUN_INTERVAL_MINUTES = int(os.environ.get("AI_MIN_RUN_INTERVAL_MINUTES", "9"))
MIN_REWARD_RISK = float(os.environ.get("AI_MIN_REWARD_RISK", "2.0"))
MIN_OPPORTUNITY_CONFIDENCE = int(os.environ.get("AI_MIN_CONFIDENCE", "80"))
FLASH_MODEL = os.environ.get("AI_FLASH_MODEL", "deepseek-v4-flash")
PRO_MODEL = os.environ.get("AI_PRO_MODEL", "deepseek-v4-pro")

_MODEL_PRICES = {
    "deepseek-v4-flash": {"hit": 0.0028, "miss": 0.14, "output": 0.28},
    "deepseek-v4-pro": {"hit": 0.003625, "miss": 0.435, "output": 0.87},
}
_SPECS = {
    "XAUUSD": "15m",
    "NASDAQ100": "15m",
    "SP500": "15m",
    "EURUSD": "15m",
    "GBPUSD": "15m",
    "BTC": "1H",
}
_MAX_DATA_AGE_MINUTES = {"15m": 45.0, "1H": 120.0}
_HUMAN = {
    "XAUUSD": "Gold",
    "NASDAQ100": "NQ",
    "SP500": "ES",
    "EURUSD": "EURUSD",
    "GBPUSD": "GBPUSD",
    "BTC": "BTC",
}
_ALLOWED_STATUS = {"none", "watch", "opportunity", "risk"}
_ALLOWED_DIRECTION = {"long", "short", "neutral"}
_SETUP_FAMILIES = {
    "liquidity_sweep",
    "failed_breakout",
    "orb_retest",
    "trend_pullback",
    "momentum_continuation",
    "intermarket_divergence",
    "absorption",
}
_SESSIONS = {"asia", "london", "new_york", "crypto_24h"}


@dataclass(frozen=True)
class ModelReply:
    data: dict[str, Any]
    cost_usd: float


def _load_state(path: Path = STATE_PATH) -> dict[str, Any]:
    if not path.exists():
        return {"month": "", "spent_usd": 0.0, "calls": 0}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def _save_state(state: dict[str, Any], path: Path = STATE_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2, sort_keys=True), encoding="utf-8")


def _reset_month(state: dict[str, Any], now: dt.datetime) -> None:
    month = now.strftime("%Y-%m")
    if state.get("month") != month:
        state["month"] = month
        state["spent_usd"] = 0.0
        state["calls"] = 0


def _parse_time(value: str | None) -> dt.datetime | None:
    if not value:
        return None
    try:
        parsed = dt.datetime.fromisoformat(value)
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=dt.timezone.utc)
    except ValueError:
        return None


def _run_due(state: dict[str, Any], now: dt.datetime) -> bool:
    previous = _parse_time(state.get("last_run_utc"))
    if previous is None:
        return True
    return (now - previous).total_seconds() >= MIN_RUN_INTERVAL_MINUTES * 60


def _active_symbols(now: dt.datetime) -> list[str]:
    """Yalnizca o saatte anlamli piyasalari modele gonder."""
    if now.weekday() >= 5:
        return ["BTC"]
    hour = now.hour + now.minute / 60
    symbols = ["BTC"]
    if 6.5 <= hour < 12:
        symbols += ["XAUUSD", "EURUSD", "GBPUSD"]
    if 12.5 <= hour < 21:
        symbols += ["XAUUSD", "NASDAQ100", "SP500", "EURUSD", "GBPUSD"]
    return list(dict.fromkeys(symbols))


def _session_for(symbol: str, now: dt.datetime) -> str:
    """Derive session from the clock; never trust a model label for dedupe."""
    if symbol == "BTC":
        return "crypto_24h"
    hour = now.hour + now.minute / 60
    if hour < 6.5:
        return "asia"
    if hour < 12.5:
        return "london"
    return "new_york"


def _last_number(series: pd.Series) -> float | None:
    value = series.iloc[-1]
    return None if pd.isna(value) or not math.isfinite(float(value)) else round(float(value), 8)


def build_snapshot(symbol: str, df: pd.DataFrame, now: dt.datetime,
                   live_price: float | None = None) -> dict[str, Any]:
    """Ham mumlari modele tasimadan kompakt, hesaplanabilir piyasa ozeti olustur."""
    if df is None or len(df) < 60:
        raise ValueError(f"{symbol}: yetersiz veri")
    frame = df.iloc[-220:].copy()
    a = atr(frame, 14)
    adx = _adx(frame, 14)
    fast = ema(frame["close"], 20)
    slow = ema(frame["close"], 50)
    vwap = daily_vwap(frame)
    pdh, pdl = prev_day_levels(frame)
    close = float(frame["close"].iloc[-1])
    atr_value = max(float(a.iloc[-1]), abs(close) * 1e-8)
    recent = frame.iloc[-20:]
    returns = frame["close"].pct_change()
    volume = frame["volume"].astype(float)
    volume_mean = float(volume.iloc[-21:-1].mean()) if len(volume) >= 21 else 0.0
    volume_ratio = float(volume.iloc[-1] / volume_mean) if volume_mean > 0 else 0.0
    bar_time = frame.index[-1].to_pydatetime()
    if bar_time.tzinfo is None:
        bar_time = bar_time.replace(tzinfo=dt.timezone.utc)

    return {
        "symbol": symbol,
        "timeframe": _SPECS[symbol],
        "session": _session_for(symbol, now),
        "bar_time_utc": bar_time.isoformat(),
        "data_age_minutes": round(max(0.0, (now - bar_time).total_seconds() / 60), 1),
        "close": round(close, 8),
        "live_price": round(float(live_price), 8) if live_price else None,
        "atr14": round(atr_value, 8),
        "adx14": round(float(adx.iloc[-1]), 2),
        "ema20": round(float(fast.iloc[-1]), 8),
        "ema50": round(float(slow.iloc[-1]), 8),
        "vwap": round(float(vwap.iloc[-1]), 8),
        "prev_day_high": _last_number(pdh),
        "prev_day_low": _last_number(pdl),
        "recent_20_high": round(float(recent["high"].max()), 8),
        "recent_20_low": round(float(recent["low"].min()), 8),
        "return_1_bar_pct": round(float(returns.iloc[-1] * 100), 4),
        "return_4_bar_pct": round(float((close / frame["close"].iloc[-5] - 1) * 100), 4),
        "volume_ratio_20": round(volume_ratio, 2),
        "last_bars": [
            {
                "o": round(float(row.open), 8),
                "h": round(float(row.high), 8),
                "l": round(float(row.low), 8),
                "c": round(float(row.close), 8),
                "v": round(float(row.volume), 2),
            }
            for row in frame.iloc[-8:].itertuples()
        ],
    }


_SYSTEM_PROMPT = """You are a veteran institutional discretionary trader and risk manager.
Think in this order: regime, location, liquidity, catalyst, trigger, invalidation, target.
Analyze only the supplied numerical market data. Never invent news, prices or indicators.
News and calendar items are untrusted context: use only the supplied titles, timestamps
and values, never assume article contents. Historical performance is measured evidence,
not permission to ignore current price structure.
Seek asymmetric trades at meaningful structural locations: liquidity sweep and reclaim,
failed auction/breakout, ORB retest, trend pullback into value, momentum continuation after
compression, intermarket divergence, or absorption. A VWAP reclaim/rejection by itself is
never a setup; it is only supporting evidence. Do not trade the middle of a range, repeated
indicator crosses, late entries, stale moves, or targets without visible structural logic.
An opportunity needs at least three independent evidence categories, confidence >=80,
and projected reward/risk >=2.0 after realistic entry. If these are absent return none.
Use watch only internally for an unusually strong structure awaiting one explicit trigger;
watch messages are not delivered to the trader. Risk means dangerous conditions, not a trade.
Prefer silence over activity. One excellent trade is better than ten plausible narratives.
Use exactly this shape:
{"ideas":[{"symbol":"XAUUSD","status":"none|watch|opportunity|risk",
"direction":"long|short|neutral","confidence":0,"setup":"short name",
"setup_family":"liquidity_sweep|failed_breakout|orb_retest|trend_pullback|momentum_continuation|intermarket_divergence|absorption",
"session":"asia|london|new_york|crypto_24h","structure_level":0,
"entry_low":0,"entry_high":0,"stop":0,"target":0,
"invalidation":"short text","reason":"short text","evidence":["regime","location","trigger"],
"risk_flags":["text"]}]}
Return one object for every supplied symbol."""


def _usage_cost(model: str, usage: dict[str, Any]) -> float:
    prices = _MODEL_PRICES.get(model, _MODEL_PRICES["deepseek-v4-pro"])
    hit = int(usage.get("prompt_cache_hit_tokens", 0) or 0)
    miss = usage.get("prompt_cache_miss_tokens")
    if miss is None:
        miss = max(0, int(usage.get("prompt_tokens", 0) or 0) - hit)
    output = int(usage.get("completion_tokens", 0) or 0)
    return (
        hit * prices["hit"] + int(miss) * prices["miss"] + output * prices["output"]
    ) / 1_000_000


def _estimated_request_cost(model: str, payload: dict[str, Any], max_tokens: int) -> float:
    prices = _MODEL_PRICES.get(model, _MODEL_PRICES["deepseek-v4-pro"])
    input_tokens = max(1, len(json.dumps(payload, ensure_ascii=False)) // 4)
    return (input_tokens * prices["miss"] + max_tokens * prices["output"]) / 1_000_000


def _call_deepseek(*, model: str, messages: list[dict[str, str]],
                   max_tokens: int, thinking: bool, api_key: str) -> ModelReply:
    payload: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "response_format": {"type": "json_object"},
        "stream": False,
    }
    payload["thinking"] = {"type": "enabled" if thinking else "disabled"}
    if thinking:
        payload["reasoning_effort"] = "high"
    else:
        payload["temperature"] = 0.1
    response = requests.post(
        API_URL,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json=payload,
        timeout=45,
    )
    response.raise_for_status()
    body = response.json()
    content = body["choices"][0]["message"]["content"]
    return ModelReply(json.loads(content), _usage_cost(model, body.get("usage", {})))


def _number(value: Any) -> float | None:
    try:
        number = float(value)
        return number if math.isfinite(number) else None
    except (TypeError, ValueError):
        return None


def _evidence_categories(evidence: list[str]) -> set[str]:
    keywords = {
        "regime": ("regime", "trend", "ema", "adx", "momentum", "compression"),
        "location": (
            "location", "liquidity", "sweep", "level", "pdh", "pdl",
            "high", "low", "range", "value", "orb", "auction",
        ),
        "trigger": (
            "trigger", "reclaim", "reject", "break", "close", "absorption",
            "divergence", "volume", "continuation",
        ),
    }
    text_items = [item.lower() for item in evidence]
    return {
        category
        for category, words in keywords.items()
        if any(any(word in item for word in words) for item in text_items)
    }


def validate_idea(raw: dict[str, Any], snapshots: dict[str, dict[str, Any]]) -> dict[str, Any] | None:
    """Model seviyelerini piyasa verisine karsi deterministik olarak dogrula."""
    symbol = str(raw.get("symbol", "")).upper()
    if symbol not in snapshots:
        return None
    status = str(raw.get("status", "none")).lower()
    direction = str(raw.get("direction", "neutral")).lower()
    if status not in _ALLOWED_STATUS or direction not in _ALLOWED_DIRECTION:
        return None
    confidence = int(max(0, min(100, _number(raw.get("confidence")) or 0)))
    if status == "opportunity" and confidence < MIN_OPPORTUNITY_CONFIDENCE:
        status = "none"
    if status == "watch" and confidence < 65:
        status = "none"
    snap = snapshots[symbol]
    current = float(snap.get("live_price") or snap["close"])
    atr_value = max(float(snap["atr14"]), abs(current) * 1e-8)
    if (
        status == "opportunity"
        and float(snap["data_age_minutes"]) > _MAX_DATA_AGE_MINUTES[snap["timeframe"]]
    ):
        return None
    entry_low = _number(raw.get("entry_low"))
    entry_high = _number(raw.get("entry_high"))
    stop = _number(raw.get("stop"))
    target = _number(raw.get("target"))

    if status in {"watch", "opportunity"}:
        if direction not in {"long", "short"} or None in {entry_low, entry_high, stop, target}:
            return None
        entry_low, entry_high = sorted((float(entry_low), float(entry_high)))
        midpoint = (entry_low + entry_high) / 2
        if abs(midpoint - current) > 4 * atr_value:
            return None
        risk = midpoint - float(stop) if direction == "long" else float(stop) - midpoint
        reward = float(target) - midpoint if direction == "long" else midpoint - float(target)
        if risk <= 0 or reward <= 0:
            return None
        if risk < 0.2 * atr_value or risk > 4 * atr_value:
            return None
        if entry_high - entry_low > 1.5 * atr_value:
            return None
        rr = reward / risk
        if rr < MIN_REWARD_RISK:
            return None
    else:
        rr = 0.0
    evidence = raw.get("evidence", [])
    evidence = [str(x)[:100] for x in evidence[:5]] if isinstance(evidence, list) else []
    if status == "opportunity":
        if len({item.strip().lower() for item in evidence if item.strip()}) < 3:
            return None
        if len(_evidence_categories(evidence)) < 3:
            return None
    setup_family = str(raw.get("setup_family", "")).lower()
    if status == "opportunity" and setup_family not in _SETUP_FAMILIES:
        return None
    session = str(snap["session"])
    structure_level = _number(raw.get("structure_level"))
    setup = str(raw.get("setup", "")).strip()[:80]
    invalidation = str(raw.get("invalidation", "")).strip()[:180]
    reason = str(raw.get("reason", "")).strip()[:240]
    if status == "opportunity":
        if session not in _SESSIONS or structure_level is None:
            return None
        if abs(float(structure_level) - current) > 6 * atr_value:
            return None
        if not setup or not invalidation or not reason:
            return None

    return {
        "symbol": symbol,
        "status": status,
        "direction": direction,
        "confidence": confidence,
        "setup": setup,
        "setup_family": setup_family,
        "session": session,
        "structure_level": structure_level,
        "entry_low": entry_low,
        "entry_high": entry_high,
        "stop": stop,
        "target": target,
        "rr": round(rr, 2),
        "invalidation": invalidation,
        "reason": reason,
        "evidence": evidence,
        "risk_flags": [str(x)[:100] for x in raw.get("risk_flags", [])[:4]]
        if isinstance(raw.get("risk_flags", []), list) else [],
        "data_age_minutes": snap["data_age_minutes"],
    }


def _pro_confirm(candidate_ideas: list[dict[str, Any]], snapshots: dict[str, dict[str, Any]], *,
                 context: dict[str, Any], memory: dict[str, Any],
                 api_key: str, state: dict[str, Any]) -> list[dict[str, Any]]:
    if not candidate_ideas:
        return []
    messages = [
        {"role": "system", "content": _SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                "Review every candidate independently in one response. Return exactly one "
                "idea for each candidate symbol, using status none when rejected. Reject weak "
                "structure, stale levels or poor reward/risk. VWAP alone is not a thesis. "
                "Require at least three independent evidence categories and at least 2.0R. "
                "Do not increase confidence without clear numerical evidence.\n"
                + json.dumps(
                    {
                        "candidates": candidate_ideas,
                        "markets": {
                            idea["symbol"]: snapshots[idea["symbol"]]
                            for idea in candidate_ideas
                        },
                        "news_and_calendar": context,
                        "measured_history": memory,
                    },
                    separators=(",", ":"),
                )
            ),
        },
    ]
    max_tokens = min(2600, 700 + 350 * len(candidate_ideas))
    estimate = _estimated_request_cost(PRO_MODEL, {"messages": messages}, max_tokens)
    if float(state.get("spent_usd", 0.0)) + estimate > MONTHLY_BUDGET_USD:
        return []
    reply = _call_deepseek(
        model=PRO_MODEL, messages=messages, max_tokens=max_tokens, thinking=True, api_key=api_key
    )
    state["spent_usd"] = float(state.get("spent_usd", 0.0)) + reply.cost_usd
    state["calls"] = int(state.get("calls", 0)) + 1
    raw_ideas = reply.data.get("ideas", [])
    if not isinstance(raw_ideas, list):
        return []
    candidates = {idea["symbol"]: idea for idea in candidate_ideas}
    confirmed_by_symbol: dict[str, dict[str, Any]] = {}
    for raw in raw_ideas:
        if not isinstance(raw, dict):
            continue
        symbol = str(raw.get("symbol", "")).upper()
        candidate = candidates.get(symbol)
        if candidate is None:
            continue
        idea = validate_idea(raw, snapshots)
        if idea is None or idea["status"] != "opportunity":
            continue
        if (
            idea["direction"] != candidate["direction"]
            or idea["setup_family"] != candidate["setup_family"]
        ):
            continue
        atr_value = float(snapshots[symbol]["atr14"])
        candidate_mid = (candidate["entry_low"] + candidate["entry_high"]) / 2
        confirmed_mid = (idea["entry_low"] + idea["entry_high"]) / 2
        if abs(confirmed_mid - candidate_mid) > 0.5 * atr_value:
            continue
        if abs(float(idea["structure_level"]) - float(candidate["structure_level"])) > 0.5 * atr_value:
            continue
        previous = confirmed_by_symbol.get(symbol)
        if previous is None or idea["confidence"] > previous["confidence"]:
            confirmed_by_symbol[symbol] = idea
    return list(confirmed_by_symbol.values())


def _append_audit(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
    fresh = [json.dumps(row, sort_keys=True) for row in rows]
    path.write_text("\n".join((existing + fresh)[-5000:]) + "\n", encoding="utf-8")


def _message(idea: dict[str, Any], now: dt.datetime) -> str:
    symbol = _HUMAN[idea["symbol"]]
    flags = ", ".join(idea["risk_flags"]) if idea["risk_flags"] else "belirgin ek risk yok"
    evidence = ", ".join(idea["evidence"])
    return (
        f"AI FIRSAT {symbol} {idea['direction']} adayi. Setup {idea['setup']}. "
        f"Giris bolgesi {idea['entry_low']:g} ile {idea['entry_high']:g}, "
        f"stop {idea['stop']:g}, hedef {idea['target']:g}, yaklasik {idea['rr']:.2f}R. "
        f"Guven {idea['confidence']}. Kanitlar {evidence}. {idea['reason']} "
        f"Gecersizlik {idea['invalidation']}. Riskler {flags}. "
        f"Veri yasi {idea['data_age_minutes']:.0f} dakika. Saat {sessions.to_trt(now)}. "
        "Bu AI adayidir, fiyat giris bolgesine gelmeden islem alma."
    )


def run(*, now: dt.datetime | None = None, dry_run: bool = False,
        state_path: Path | None = None, api_key: str | None = None) -> list[str]:
    now = now or dt.datetime.now(dt.timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=dt.timezone.utc)
    key = api_key or os.environ.get("DEEPSEEK_API_KEY")
    if not key:
        print("AI scout beklemede: DEEPSEEK_API_KEY eksik.")
        return []

    path = state_path or STATE_PATH
    state = _load_state(path)
    # Eski zaman/adet tabanli filtreler artik kullanilmiyor.
    state.pop("sent", None)
    state.pop("daily", None)
    state.pop("symbol_cooldown", None)
    _reset_month(state, now)
    if not _run_due(state, now):
        print("AI scout atlandi: minimum tarama araligi dolmadi.")
        return []
    if float(state.get("spent_usd", 0.0)) >= MONTHLY_BUDGET_USD:
        print("AI scout atlandi: aylik butce tavani doldu.")
        return []

    symbols = _active_symbols(now)
    snapshots: dict[str, dict[str, Any]] = {}
    frames: dict[str, pd.DataFrame] = {}
    sources: dict[str, str] = {}
    for symbol in symbols:
        try:
            frame = free_data.ohlcv(symbol, _SPECS[symbol], days=59)
            frames[symbol] = frame
            sources[symbol] = free_data.source_of(frame)
        except Exception as exc:
            print(f"AI scout {symbol} veri hatasi: {type(exc).__name__}: {exc}")

    quote_symbols = {
        symbol
        for symbol, source in sources.items()
        if source != "binance" and resolve(symbol).live_quote_compatible
    }
    quotes = finnhub_live.collect_quotes(quote_symbols, timeout_seconds=5.0)
    for symbol, frame in frames.items():
        try:
            quote = quotes.get(symbol)
            source = sources[symbol]
            live_price = (
                float(frame["close"].iloc[-1])
                if source == "binance" and not frame.empty
                else quote.price if quote else None
            )
            snapshots[symbol] = build_snapshot(
                symbol, frame, now, live_price=live_price
            )
            snapshots[symbol]["data_source"] = source
        except Exception as exc:
            print(f"AI scout {symbol} snapshot hatasi: {type(exc).__name__}: {exc}")
    if not snapshots:
        return []

    ledger_path = path.with_name("ai_ledger.jsonl")
    ledger = ai_memory.load(ledger_path)
    settled = ai_memory.settle(ledger, frames, now)
    if settled:
        ai_memory.save(ledger, ledger_path)
    history = ai_memory.summary(ledger)
    context = market_context.collect(now)

    messages = [
        {"role": "system", "content": _SYSTEM_PROMPT},
        {
            "role": "user",
            "content": "Scan these markets and return strict json.\n"
            + json.dumps(
                {
                    "asof_utc": now.isoformat(),
                    "markets": list(snapshots.values()),
                    "news_and_calendar": context,
                    "measured_history": history,
                },
                separators=(",", ":"),
            ),
        },
    ]
    estimate = _estimated_request_cost(FLASH_MODEL, {"messages": messages}, 1800)
    if float(state.get("spent_usd", 0.0)) + estimate > MONTHLY_BUDGET_USD:
        print("AI scout atlandi: bu istek aylik butceyi asabilir.")
        return []

    try:
        reply = _call_deepseek(
            model=FLASH_MODEL, messages=messages, max_tokens=1800,
            thinking=False, api_key=key,
        )
    except Exception as exc:
        print(f"AI scout API hatasi: {type(exc).__name__}: {exc}")
        return []
    state["spent_usd"] = float(state.get("spent_usd", 0.0)) + reply.cost_usd
    state["calls"] = int(state.get("calls", 0)) + 1
    state["last_run_utc"] = now.isoformat()
    # Flash cagrisi ucretlendi; sonraki Pro/Telegram adimi hata verse bile
    # harcama ve run araligi kaybolmasin.
    _save_state(state, path)

    raw_ideas = reply.data.get("ideas", [])
    audit_rows: list[dict[str, Any]] = []
    valid: list[dict[str, Any]] = []
    if isinstance(raw_ideas, list):
        for raw in raw_ideas:
            if not isinstance(raw, dict):
                continue
            idea = validate_idea(raw, snapshots)
            audit_rows.append({
                "timestamp_utc": now.isoformat(),
                "stage": "flash",
                "raw": raw,
                "validated": idea,
            })
            if idea is not None and idea["status"] != "none":
                valid.append(idea)

    candidates: list[dict[str, Any]] = []
    candidate_symbols: set[str] = set()
    for idea in sorted(valid, key=lambda x: x["confidence"], reverse=True):
        suppression_reason = "internal_non_opportunity"
        if (
            context.get("trade_risk") == "high"
            and idea["status"] == "opportunity"
            and idea["symbol"] != "BTC"
        ):
            idea = {
                **idea,
                "status": "watch",
                "risk_flags": [*idea["risk_flags"], "60 dakika icinde yuksek etkili veri"][:4],
            }
            suppression_reason = "high_impact_calendar"
        # Telegram yalnizca uygulanabilir 2R+ firsatlar icindir.
        # Watch/risk yorumlari audit'te kalir.
        if idea["status"] != "opportunity":
            audit_rows.append({
                "timestamp_utc": now.isoformat(),
                "stage": "suppressed",
                "reason": suppression_reason,
                "idea": idea,
            })
            continue
        if idea["symbol"] in candidate_symbols:
            audit_rows.append({
                "timestamp_utc": now.isoformat(),
                "stage": "suppressed",
                "reason": "duplicate_flash_symbol",
                "idea": idea,
            })
            continue
        candidate_symbols.add(idea["symbol"])
        candidates.append(idea)

    try:
        confirmed_ideas = _pro_confirm(
            candidates, snapshots, context=context, memory=history,
            api_key=key, state=state,
        )
    except Exception as exc:
        print(f"AI scout Pro API hatasi: {type(exc).__name__}: {exc}")
        confirmed_ideas = []
        for candidate in candidates:
            audit_rows.append({
                "timestamp_utc": now.isoformat(),
                "stage": "suppressed",
                "reason": "pro_api_error",
                "idea": candidate,
            })
    _save_state(state, path)
    confirmed_symbols = {idea["symbol"] for idea in confirmed_ideas}
    for candidate in candidates:
        if (
            candidate["symbol"] not in confirmed_symbols
            and not any(
                row.get("reason") == "pro_api_error"
                and row.get("idea", {}).get("symbol") == candidate["symbol"]
                for row in audit_rows
            )
        ):
            audit_rows.append({
                "timestamp_utc": now.isoformat(),
                "stage": "suppressed",
                "reason": "pro_rejected",
                "idea": candidate,
            })

    final_ideas: list[dict[str, Any]] = []
    dedupe_records = list(ledger)
    for idea in sorted(confirmed_ideas, key=lambda x: x["confidence"], reverse=True):
        duplicate = ai_memory.structural_duplicate(
            dedupe_records,
            idea,
            atr_now=float(snapshots[idea["symbol"]]["atr14"]),
        )
        if duplicate is not None:
            audit_rows.append({
                "timestamp_utc": now.isoformat(),
                "stage": "suppressed",
                "reason": "same_open_structure",
                "matching_record_id": duplicate.get("id"),
                "idea": idea,
            })
            continue
        final_ideas.append(idea)
        dedupe_records.append(
            ai_memory.make_record(
                idea,
                now=now,
                market_context=context,
                atr_at_signal=float(snapshots[idea["symbol"]]["atr14"]),
            )
        )

    output: list[str] = []
    for idea in final_ideas:
        text = _message(idea, now)
        if dry_run:
            print(text)
        else:
            telegram_notify.send(text)
        output.append(text)
        if not dry_run:
            ai_memory.add(
                ledger,
                ai_memory.make_record(
                    idea,
                    now=now,
                    market_context=context,
                    atr_at_signal=float(snapshots[idea["symbol"]]["atr14"]),
                ),
            )

    # Dry-run da gercek API tokeni tuketir; harcama tavani her durumda saklanir.
    _save_state(state, path)
    ai_memory.save(ledger, ledger_path)
    _append_audit(path.with_name("ai_audit.jsonl"), audit_rows)
    print(
        f"AI scout tamamlandi. Piyasa {len(snapshots)}, mesaj {len(output)}, "
        f"haber {len(context.get('recent_news', []))}, "
        f"takvim {len(context.get('economic_calendar', []))}, "
        f"hafiza {history.get('resolved_samples', 0)} sonuc, "
        f"aylik tahmini harcama {float(state.get('spent_usd', 0.0)):.4f} dolar."
    )
    return output
