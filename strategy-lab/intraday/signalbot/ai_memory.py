"""AI firsat defteri, otomatik sonuc hesaplama ve performans hafizasi."""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import math
import os
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

import pandas as pd

LEDGER_PATH = Path(os.environ.get("AI_LEDGER_PATH", ".signalbot/ai_ledger.jsonl"))
MAX_HOLD_HOURS = int(os.environ.get("AI_MAX_HOLD_HOURS", "72"))


def load(path: Path = LEDGER_PATH) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    records = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            item = json.loads(line)
            if isinstance(item, dict):
                records.append(item)
        except json.JSONDecodeError:
            continue
    return records


def save(records: list[dict[str, Any]], path: Path = LEDGER_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = "\n".join(json.dumps(item, sort_keys=True) for item in records)
    path.write_text(text + ("\n" if text else ""), encoding="utf-8")


def _setup_key(value: str) -> str:
    words = re.sub(r"[^a-z0-9 ]+", " ", value.lower()).split()
    return " ".join(words[:6]) or "unknown"


def make_record(idea: dict[str, Any], *, now: dt.datetime,
                market_context: dict[str, Any], atr_at_signal: float) -> dict[str, Any]:
    midpoint = (float(idea["entry_low"]) + float(idea["entry_high"])) / 2
    risk = (
        midpoint - float(idea["stop"])
        if idea["direction"] == "long"
        else float(idea["stop"]) - midpoint
    )
    raw = (
        f"{now.isoformat()}|{idea['symbol']}|{idea['direction']}|"
        f"{idea['setup']}|{midpoint:.8f}"
    )
    return {
        "id": hashlib.sha256(raw.encode("utf-8")).hexdigest()[:20],
        "created_utc": now.isoformat(),
        "symbol": idea["symbol"],
        "direction": idea["direction"],
        "setup": idea["setup"],
        "setup_family": idea["setup_family"],
        "session": idea["session"],
        "structure_level": float(idea["structure_level"]),
        "setup_key": _setup_key(idea["setup"]),
        "confidence": int(idea["confidence"]),
        "entry_low": float(idea["entry_low"]),
        "entry_high": float(idea["entry_high"]),
        "entry_mid": midpoint,
        "stop": float(idea["stop"]),
        "target": float(idea["target"]),
        "risk": risk,
        "planned_rr": float(idea["rr"]),
        "atr_at_signal": float(atr_at_signal),
        "news_risk": market_context.get("trade_risk", "unknown"),
        "outcome": "open",
        "entered_utc": None,
        "resolved_utc": None,
        "result_r": None,
        "mfe_r": 0.0,
        "mae_r": 0.0,
    }


def structural_duplicate(
    records: list[dict[str, Any]],
    idea: dict[str, Any],
    *,
    atr_now: float,
) -> dict[str, Any] | None:
    """Return the matching open thesis, not a time-based cooldown.

    A new thesis is allowed when direction/setup family changes, the prior idea
    has resolved, or the entry structure has moved by at least one ATR.
    """
    midpoint = (float(idea["entry_low"]) + float(idea["entry_high"])) / 2
    stop = float(idea["stop"])
    for record in reversed(records):
        if record.get("outcome") != "open":
            continue
        if record.get("symbol") != idea["symbol"]:
            continue
        if record.get("direction") != idea["direction"]:
            continue
        if record.get("setup_family") != idea["setup_family"]:
            continue
        if record.get("session") != idea["session"]:
            continue
        reference_atr = max(
            float(atr_now),
            float(record.get("atr_at_signal") or 0),
            abs(midpoint) * 1e-8,
        )
        entry_distance = abs(midpoint - float(record["entry_mid"])) / reference_atr
        stop_distance = abs(stop - float(record["stop"])) / reference_atr
        structure_distance = abs(
            float(idea["structure_level"]) - float(record.get("structure_level", math.inf))
        ) / reference_atr
        if entry_distance < 1.0 and stop_distance < 1.0 and structure_distance < 0.5:
            return record
    return None


def add(records: list[dict[str, Any]], record: dict[str, Any]) -> bool:
    if any(item.get("id") == record["id"] for item in records):
        return False
    records.append(record)
    return True


def _created(value: str) -> dt.datetime:
    parsed = dt.datetime.fromisoformat(value)
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=dt.timezone.utc)


def settle(records: list[dict[str, Any]], frames: dict[str, pd.DataFrame],
           now: dt.datetime) -> int:
    """Sonraki mumlarda giris, TP/SL sirasi ve R sonucunu hesapla."""
    changed = 0
    for record in records:
        if record.get("outcome") != "open":
            continue
        frame = frames.get(record.get("symbol"))
        if frame is None or frame.empty:
            continue
        created = _created(record["created_utc"])
        bars = frame[frame.index > created]
        if bars.empty:
            continue
        direction = record["direction"]
        entry_low = float(record["entry_low"])
        entry_high = float(record["entry_high"])
        stop = float(record["stop"])
        target = float(record["target"])
        midpoint = float(record["entry_mid"])
        risk = max(float(record["risk"]), 1e-12)

        if record.get("entered_utc"):
            entered = _created(record["entered_utc"])
            active = bars[bars.index >= entered]
        else:
            touched = bars[(bars["low"] <= entry_high) & (bars["high"] >= entry_low)]
            if touched.empty:
                if now - created >= dt.timedelta(hours=MAX_HOLD_HOURS):
                    record["outcome"] = "not_triggered"
                    record["resolved_utc"] = now.isoformat()
                    changed += 1
                continue
            entered_index = touched.index[0]
            record["entered_utc"] = entered_index.isoformat()
            active = bars[bars.index >= entered_index]
            changed += 1

        if direction == "long":
            favorable = (active["high"] - midpoint) / risk
            adverse = (midpoint - active["low"]) / risk
            stop_hit = active["low"] <= stop
            target_hit = active["high"] >= target
        else:
            favorable = (midpoint - active["low"]) / risk
            adverse = (active["high"] - midpoint) / risk
            stop_hit = active["high"] >= stop
            target_hit = active["low"] <= target
        record["mfe_r"] = round(max(float(record.get("mfe_r", 0)), float(favorable.max())), 3)
        record["mae_r"] = round(max(float(record.get("mae_r", 0)), float(adverse.max())), 3)

        stop_times = active.index[stop_hit]
        target_times = active.index[target_hit]
        first_stop = stop_times[0] if len(stop_times) else None
        first_target = target_times[0] if len(target_times) else None
        if first_stop is not None and first_target is not None and first_stop == first_target:
            record["outcome"] = "ambiguous"
            record["result_r"] = None
            record["resolved_utc"] = first_stop.isoformat()
            changed += 1
        elif first_target is not None and (first_stop is None or first_target < first_stop):
            record["outcome"] = "target"
            record["result_r"] = round(float(record["planned_rr"]), 3)
            record["resolved_utc"] = first_target.isoformat()
            changed += 1
        elif first_stop is not None:
            record["outcome"] = "stop"
            record["result_r"] = -1.0
            record["resolved_utc"] = first_stop.isoformat()
            changed += 1
        elif now - created >= dt.timedelta(hours=MAX_HOLD_HOURS):
            close = float(active["close"].iloc[-1])
            result = (close - midpoint) / risk if direction == "long" else (midpoint - close) / risk
            record["outcome"] = "expired"
            record["result_r"] = round(result, 3)
            record["resolved_utc"] = active.index[-1].isoformat()
            changed += 1
    return changed


def summary(records: list[dict[str, Any]], limit: int = 8) -> dict[str, Any]:
    resolved = [
        item for item in records
        if isinstance(item.get("result_r"), (int, float))
        and item.get("outcome") in {"target", "stop", "expired"}
    ]
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for item in resolved:
        groups[(item["symbol"], item.get("setup_key") or _setup_key(item["setup"]))].append(item)
    patterns = []
    for (symbol, setup), items in groups.items():
        results = [float(item["result_r"]) for item in items]
        patterns.append({
            "symbol": symbol,
            "setup": setup,
            "samples": len(items),
            "win_rate": round(sum(value > 0 for value in results) / len(results), 3),
            "avg_r": round(sum(results) / len(results), 3),
            "avg_mfe_r": round(sum(float(x.get("mfe_r", 0)) for x in items) / len(items), 3),
            "news_high_risk_samples": sum(x.get("news_risk") == "high" for x in items),
        })
    patterns.sort(key=lambda x: (x["samples"], abs(x["avg_r"])), reverse=True)
    all_results = [float(item["result_r"]) for item in resolved]
    return {
        "total_records": len(records),
        "resolved_samples": len(resolved),
        "wins": sum(float(item["result_r"]) > 0 for item in resolved),
        "losses": sum(float(item["result_r"]) <= 0 for item in resolved),
        "win_rate": round(
            sum(float(item["result_r"]) > 0 for item in resolved) / len(resolved), 3
        ) if resolved else None,
        "open_samples": sum(item.get("outcome") == "open" for item in records),
        "not_triggered_samples": sum(item.get("outcome") == "not_triggered" for item in records),
        "ambiguous_samples": sum(item.get("outcome") == "ambiguous" for item in records),
        "overall_avg_r": round(sum(all_results) / len(all_results), 3) if all_results else None,
        "patterns": patterns[:limit],
        "instruction": (
            "Treat patterns with fewer than 8 samples as weak evidence. "
            "Historical statistics may reduce confidence but never justify invalid levels."
        ),
    }


def report(path: Path = LEDGER_PATH) -> str:
    records = load(path)
    data = summary(records)
    lines = [
        "AI PERFORMANCE REPORT",
        f"Toplam kayit {data['total_records']}",
        f"Sonuclanmis {data['resolved_samples']}",
        f"Kazanan {data['wins']} kaybeden {data['losses']}",
        f"Win rate {data['win_rate'] * 100:.1f}%"
        if data["win_rate"] is not None else "Win rate icin henuz sonuclanmis ornek yok",
        f"Ortalama R {data['overall_avg_r']:+.3f}"
        if data["overall_avg_r"] is not None else "Ortalama R henuz yok",
        f"Acik {data['open_samples']} tetiklenmeyen {data['not_triggered_samples']} "
        f"belirsiz {data['ambiguous_samples']}",
    ]
    for item in records[-20:]:
        lines.append(
            f"{item.get('created_utc')} {item.get('symbol')} {item.get('direction')} "
            f"{item.get('setup')} plan {item.get('planned_rr')}R "
            f"sonuc {item.get('outcome')} R {item.get('result_r')} "
            f"MFE {item.get('mfe_r')} MAE {item.get('mae_r')}"
        )
    return "\n".join(lines)
