"""Read existing evidence through its canonical ledger contract."""
from __future__ import annotations

from datetime import datetime, timezone
import json
import hashlib
import math
import os
import re
from pathlib import Path
from uuid import uuid4

import pandas as pd

from ..forward_ea.ledger import oku_defter

LAB = Path(__file__).resolve().parents[2]
SWEEP = "SWEEP_CORE_AVOID_MID_VWAP"
EXPERIMENT_FIELDS = ("title", "hypothesis", "falsifier", "data_scope", "decision_rule")


def strict_json(text: str):
    def reject(value):
        raise ValueError(f"Sonlu olmayan JSON değeri: {value}")
    value = json.loads(text, parse_constant=reject)
    # Reject overflow and lone surrogates before they reach HTTP or a file write.
    json.dumps(value, allow_nan=False, ensure_ascii=False).encode("utf-8")
    return value


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def classification(module: str) -> str:
    if module == SWEEP:
        return "LIVE yetkili · manuel emir"
    if module.startswith("CAND_"):
        return "CAND · sessiz ölçüm"
    if "EMA12" in module:
        return "PAPER gözlem"
    return "Tarihsel / yetki tablosundan kontrol et"


def records(frame: pd.DataFrame) -> list[dict]:
    # pandas handles timestamps and NaN without invalid JSON NaN literals.
    return json.loads(frame.to_json(orient="records", date_format="iso", double_precision=15))


def cloud_location(lab: Path) -> tuple[Path, dict, list[str]]:
    directory = lab / "outputs/intraday/research_panel"
    pointer = directory / "cloud_current.json"
    legacy = lab / "outputs/intraday/forward_ea"
    if not pointer.exists():
        return legacy, {"origin": "Yerel bulut kopyası · GitHub ile henüz eşitlenmedi"}, []
    try:
        manifest = strict_json(pointer.read_text(encoding="utf-8"))
        commit = manifest["commit"]
        if not isinstance(commit, str) or not re.fullmatch(r"[0-9a-f]{40}", commit):
            raise ValueError("Bulut kopyası commit kimliği geçersiz")
        generation = directory / "cloud" / commit
        for filename in ("cloud_ledger.csv", "cloud_state.json"):
            actual = hashlib.sha256((generation / filename).read_bytes()).hexdigest()
            if actual != manifest["hashes"][filename]:
                raise ValueError("Bulut kopyasında dosya bütünlüğü hatası")
        return generation, {"origin": "GitHub bulut defteri", "commit": commit,
                            "synced_at": manifest.get("synced_at")}, []
    except (OSError, ValueError, KeyError, TypeError) as exc:
        return legacy, {"origin": "Yedek yerel kopya · GitHub eşitlemesi doğrulanamadı"}, [str(exc)]


def source_freshness(state: dict, key: str, now=None) -> dict:
    now = now or datetime.now(timezone.utc)
    stamp = state.get("last_bar", {}).get(SWEEP + ":NASDAQ100")
    result = {"status": "unknown", "bar_open": stamp, "bar_close": None,
              "age_minutes": None, "expected_minutes": 30 if key == "mt5" else 120}
    try:
        opened = pd.to_datetime(stamp, utc=True, errors="raise")
        if pd.isna(opened):
            return result
        closed = opened + pd.Timedelta(minutes=15)
        age = (pd.Timestamp(now) - closed).total_seconds() / 60
        result.update(bar_close=closed.isoformat(), age_minutes=round(age, 1),
                      status="fresh" if 0 <= age <= result["expected_minutes"] else "stale")
    except (ValueError, TypeError):
        pass
    return result


def validate_state(state: dict) -> dict:
    if not isinstance(state, dict):
        raise ValueError("State nesne olmalı")
    if not {"last_bar", "open_positions"}.issubset(state):
        raise ValueError("State içinde last_bar ve open_positions gerekli")
    bars = state["last_bar"]
    positions = state["open_positions"]
    if not isinstance(bars, dict) or not all(isinstance(v, str) for v in bars.values()):
        raise ValueError("last_bar zaman damgalı nesne olmalı")
    if not isinstance(positions, list) or not all(isinstance(p, dict) for p in positions):
        raise ValueError("open_positions nesne listesi olmalı")
    for pos in positions:
        if not isinstance(pos.get("module"), str) or not pos["module"].strip():
            raise ValueError("Açık pozisyon modülü eksik")
        if pos.get("backfill") not in (0, 1):
            raise ValueError("Açık pozisyonda backfill 0 veya 1 olmalı")
        if not isinstance(pos.get("symbol"), str) or not pos["symbol"].strip():
            raise ValueError("Açık pozisyon sembolü eksik")
        if pos.get("direction") not in (-1, 1):
            raise ValueError("Açık pozisyon yönü -1 veya 1 olmalı")
        for field in ("entry", "sl", "tp"):
            value = pos.get(field)
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
                raise ValueError(f"Açık pozisyon {field} sayısal ve sonlu olmalı")
        if not isinstance(pos.get("entry_time"), str) or pd.isna(pd.to_datetime(
                pos["entry_time"], utc=True, errors="coerce")):
            raise ValueError("Açık pozisyon giriş zamanı geçersiz")
    # Never expose arbitrary state fields: they may contain account information.
    provenance = state.get("broker_source")
    if provenance is not None:
        if not isinstance(provenance, dict) or not all(isinstance(provenance.get(k), str)
                for k in ("provider", "broker", "server", "verified_at", "verified_since")):
            raise ValueError("Broker kaynak kimliği geçersiz")
        provenance = {k: provenance[k] for k in ("provider", "broker", "server", "verified_at", "verified_since")}
    return {"updated_at": state.get("updated_at"), "broker_source": provenance,
                        "last_bar": bars,
                        "open_positions": [
                            {k: pos.get(k) for k in ("module", "symbol", "direction",
                             "entry_time", "entry", "sl", "tp", "backfill")}
                            for pos in positions]}


def source_snapshot(lab: Path, key: str) -> dict:
    directory = lab / "outputs/intraday/forward_ea"
    origin, location_errors = {"origin": "Yerel MT5 sanal defteri"}, []
    if key == "cloud":
        directory, origin, location_errors = cloud_location(lab)
    stem = "forward" if key == "mt5" else "cloud"
    path = directory / f"{stem}_ledger.csv"
    result = {"key": key, "label": "MT5" if key == "mt5" else "Bulut",
              "path": str(path.relative_to(lab)), "rows": [], "errors": location_errors,
              "state": {}, "exists": path.exists(), "quarantined_modules": [],
              "ledger_valid": False, "state_valid": False, **origin}
    if path.exists():
        result["file_modified_at"] = datetime.fromtimestamp(
            path.stat().st_mtime, timezone.utc).isoformat()
        if path.stat().st_size == 0:
            result["errors"].append("Defter sıfır bayt; veri yokluğu/eksik yazım kontrol edilmeli.")
    else:
        result["errors"].append("Defter bulunamadı; sıfır performans olarak yorumlanamaz.")
    try:
        frame = oku_defter(path)
        if not frame.empty:
            for column in ("module", "symbol"):
                if not frame[column].map(lambda value: isinstance(value, str)).all():
                    raise ValueError(f"{column} metin olmalı; bu kaynak metriklere alınmadı")
            # The canonical contract checks entry_time, r, provenance and identity.
            # A closed-trade curve additionally requires a valid causal exit time.
            if "exit_time" not in frame:
                raise ValueError("Kapalı işlem defterinde exit_time eksik")
            exits = pd.to_datetime(frame["exit_time"], errors="coerce", utc=True)
            entries = pd.to_datetime(frame["entry_time"], errors="coerce", utc=True)
            invalid = exits.isna() | (exits < entries)
            if invalid.any():
                rejected = sorted(frame.loc[invalid, "module"].unique().tolist())
                result["quarantined_modules"] = rejected
                result["errors"].append(
                    f"{int(invalid.sum())} kayıtta geçersiz çıkış zamanı. Etkilenen modüllerin "
                    f"TÜM kayıtları metrik dışında: {', '.join(rejected)}. Defter değiştirilmedi.")
                frame = frame.loc[~frame["module"].isin(rejected)].copy()
                exits = exits.loc[frame.index]
                entries = entries.loc[frame.index]
            frame = frame.assign(exit_time=exits, entry_time=entries)
            allowed = [c for c in ("module", "symbol", "dir", "entry_time", "exit_time",
                       "entry", "exit", "sl", "tp", "status", "r", "backfill") if c in frame]
            result["rows"] = records(frame[allowed].sort_values("exit_time"))
        result["ledger_valid"] = path.exists() and path.stat().st_size > 0
    except (ValueError, OSError, pd.errors.ParserError) as exc:
        result["errors"].append(str(exc))
    state_path = directory / f"{stem}_state.json"
    try:
        state = strict_json(state_path.read_text(encoding="utf-8-sig"))
        result["state"] = validate_state(state)
        result["state_valid"] = True
    except (OSError, ValueError, TypeError, AttributeError) as exc:
        result["errors"].append(f"State okunamadı: {exc}")
    result["freshness"] = source_freshness(result["state"], key)
    return result


def report_catalog(lab: Path) -> list[dict]:
    root = (lab / "outputs/intraday").resolve()
    result = []
    for path in sorted(root.rglob("*.md")):
        if path.name.upper() != "REPORT.MD" or not path.resolve().is_relative_to(root):
            continue
        result.append({"id": path.relative_to(root).as_posix(),
                       "title": path.parent.name.replace("_", " "),
                       "bytes": path.stat().st_size,
                       "modified_at": datetime.fromtimestamp(path.stat().st_mtime,
                                                               timezone.utc).isoformat()})
    return result


def read_report(lab: Path, report_id: str) -> str:
    allowed = {item["id"] for item in report_catalog(lab)}
    if report_id not in allowed:
        raise ValueError("Rapor katalogda yok")
    path = lab / "outputs/intraday" / report_id
    if path.stat().st_size > 2_000_000:
        raise ValueError("Rapor çok büyük; yerel dosyadan açın")
    return path.read_text(encoding="utf-8-sig")


def experiments(lab: Path) -> list[dict]:
    result = []
    for path in sorted((lab / "research-experiments").glob("*.json"), reverse=True):
        try:
            note = strict_json(path.read_text(encoding="utf-8"))
            if not isinstance(note, dict) or not all(
                    isinstance(note.get(k), str) and note[k].strip()
                    for k in (*EXPERIMENT_FIELDS, "id", "created_at", "status")):
                raise ValueError("Deney şeması bozuk")
            result.append(note)
        except (OSError, ValueError):
            result.append({"id": path.name, "title": "Bozuk deney kaydı", "status": "HATA"})
    return result


def save_experiment(lab: Path, payload: dict) -> dict:
    fields = EXPERIMENT_FIELDS
    if not isinstance(payload, dict):
        raise ValueError("JSON nesnesi gerekli")
    for field in fields:
        value = payload.get(field)
        if not isinstance(value, str) or not value.strip() or len(value) > 8000:
            raise ValueError(f"Geçerli ve dolu alan gerekli: {field} (en fazla 8000 karakter)")
    note = {"id": str(uuid4()), "created_at": utc_now(), "status": "ÖN KAYIT · çalıştırılmadı",
            **{field: payload[field].strip() for field in fields}}
    directory = lab / "research-experiments"
    directory.mkdir(parents=True, exist_ok=True)
    # Encode first: rejected text must never leave a half-written JSON record.
    encoded = json.dumps(note, ensure_ascii=False, indent=2, allow_nan=False).encode("utf-8")
    temporary = directory / f".{note['id']}.tmp"
    try:
        with temporary.open("xb") as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
        temporary.rename(directory / f"{note['id']}.json")
    finally:
        temporary.unlink(missing_ok=True)
    return note


def snapshot(lab: Path = LAB) -> dict:
    sources = [source_snapshot(lab, key) for key in ("mt5", "cloud")]
    names = sorted({row["module"] for source in sources for row in source["rows"]}
                   | {name for source in sources for name in source["quarantined_modules"]}
                   | {pos["module"] for source in sources
                      for pos in source["state"].get("open_positions", [])})
    audit_path = lab / "outputs/intraday/lse_audit/report.json"
    audit = {"available": False}
    try:
        content = strict_json(audit_path.read_text(encoding="utf-8-sig"))
        audit = {"available": True, "scope": content.get("scope"),
                 "symbols": {symbol: {k: values.get(k) for k in (
                     "aligned_bars", "overlap_start", "overlap_end",
                     "return_dislocations_over_50bps")}
                     for symbol, values in content.get("symbols", {}).items()}}
    except (OSError, ValueError, AttributeError):
        pass
    sync_status = {"status": "not_configured"}
    try:
        value = strict_json((lab / "outputs/intraday/research_panel/sync_status.json").read_text(encoding="utf-8"))
        if isinstance(value, dict):
            sync_status = {k: value.get(k) for k in ("status", "attempted_at", "last_success_at", "commit", "error")}
    except (OSError, ValueError):
        pass
    return {"generated_at": utc_now(), "sources": sources, "cloud_sync": sync_status,
            "modules": [{"name": name, "classification": classification(name)} for name in names],
            "reports": report_catalog(lab), "experiments": experiments(lab), "audit": audit,
            "default_module": SWEEP}
