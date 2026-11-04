"""Python replay of hash-verified FTMO bars; this is not the MQL5 Tester."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import pandas as pd

from .signals import MODULES, VERSION, strategy_hash
from .storage import atomic_json


def replay(csv_path: Path, metadata_path: Path, *, cost_per_side: float, detector=None):
    """Fixed-parameter OHLC diagnostic; broker fills remain authoritative."""
    from ..forward_ea.modules import _sweep_core_detector
    from ..forward_ea.positions import PaperPosition

    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    raw = csv_path.read_bytes()
    if (
        metadata.get("source") != "ftmo_mt5"
        or not metadata.get("server")
        or metadata.get("strategy_hash") != strategy_hash()
        or metadata.get("sha256") != hashlib.sha256(raw).hexdigest()
        or metadata.get("tf") != "15m"
        or metadata.get("time_basis") != "UTC"
    ):
        raise ValueError("FTMO kaynak/hash/surum dogrulamasi basarisiz")
    if not math.isfinite(cost_per_side) or cost_per_side < 0:
        raise ValueError("Acikca belirtilmis sonlu maliyet gerekli")
    key = metadata["symbol_key"]
    module = next((name for name, symbol in MODULES.items() if symbol == key), None)
    if module is None:
        raise ValueError("Sweep paketi disinda sembol")
    frame = pd.read_csv(csv_path)
    frame.index = pd.to_datetime(frame.pop("time"), utc=True).dt.tz_localize(None)
    if not frame.index.is_monotonic_increasing or frame.index.has_duplicates:
        raise ValueError("Bar zamanlari tekil ve sirali olmali")
    required = frame[["open", "high", "low", "close"]]
    if required.isna().any().any() or not required.map(math.isfinite).all().all():
        raise ValueError("Eksik/sonlu olmayan OHLC")
    detect = detector or _sweep_core_detector(
        adx_thresh=25.0, min_rr=2.0, skip_wednesday=True
    )
    current = None
    trades = []
    for index in range(519, len(frame)):
        bar, stamp = frame.iloc[index], frame.index[index]
        if current is not None and current.update(stamp, bar.high, bar.low, bar.close):
            trades.append(current.to_row())
            current = None
        if current is None:
            signal = detect(frame.iloc[: index + 1])
            if signal is not None:
                current = PaperPosition(
                    module,
                    key,
                    signal.direction,
                    stamp,
                    signal.entry,
                    signal.sl,
                    signal.tp,
                    1.0,
                    480,
                    cost_per_side,
                )
    return {
        "source": metadata,
        "version": VERSION,
        "model": "Python OHLC / SL-first",
        "cost_per_side": cost_per_side,
        "trades": trades,
        "open_position": current.to_row() if current else None,
        "notes": [
            "Bu replay haber/seans cikisli icra simulasyonu degildir; sabit dedektor ve baz cikis tanisidir.",
            "Spread, komisyon, swap, kayma gercek emir defterinde ayrica karsilastirilir.",
            "Eksik FTMO barlari baska feed ile tamamlanmaz.",
        ],
    }


def compare_audit(report, audit_path: Path):
    """Match replay and recorded execution candidates by module/bar, not by profit."""
    import sqlite3

    with sqlite3.connect(f"{audit_path.resolve().as_uri()}?mode=ro", uri=True) as db:
        rows = db.execute(
            "SELECT kind,payload FROM events WHERE kind IN ('intent','execution','signal_block')"
        ).fetchall()
    observations = []
    module = next(
        name for name, key in MODULES.items() if key == report["source"]["symbol_key"]
    )
    for kind, payload in rows:
        value = json.loads(payload)
        if value.get("module") == module:
            observations.append(
                {
                    "kind": kind,
                    "bar_time": value.get("bar_time"),
                    "id": value.get("id"),
                    "reason": value.get("reason"),
                    "plan": value.get("plan"),
                }
            )
    with sqlite3.connect(f"{audit_path.resolve().as_uri()}?mode=ro", uri=True) as db:
        row = db.execute("SELECT payload FROM state WHERE key='completed'").fetchone()
    actual = (
        [
            r
            for r in json.loads(row[0])
            if r.get("module") == module and not r.get("micro")
        ]
        if row
        else []
    )
    return {
        "replay_closed_count": len(report["trades"]),
        "recorded_candidates": observations,
        "broker_completed": actual,
        "note": "Replay R ile hesap USD getirisi ayni olcu degildir; farklar otomatik edge kaniti sayilmaz.",
    }


def cli():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bars", type=Path, required=True)
    parser.add_argument("--metadata", type=Path, required=True)
    parser.add_argument("--cost-per-side", type=float, required=True)
    parser.add_argument("--audit", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    report = replay(args.bars, args.metadata, cost_per_side=args.cost_per_side)
    if args.audit:
        report["comparison"] = compare_audit(report, args.audit)
    atomic_json(args.out, report)


if __name__ == "__main__":
    cli()
