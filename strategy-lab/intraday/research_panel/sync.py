"""Mirror the two GitHub evidence files without merging a dirty checkout.

No broker, notification, strategy or order code is imported by this worker.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
from uuid import uuid4

from .data import LAB, strict_json, validate_state
from ..forward_ea.ledger import oku_defter

REMOTE_DIRECTORY = "strategy-lab/outputs/intraday/forward_ea/"


def atomic_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid4().hex}.tmp")
    try:
        with temporary.open("xb") as stream:
            stream.write(json.dumps(value, ensure_ascii=False, indent=2).encode("utf-8"))
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def git(root: Path, *args: str) -> bytes:
    # pythonw has no console: without this flag Windows can flash a new
    # console for every git fetch/show spawned by the scheduled refresh.
    result = subprocess.run(
        ["git", *args], cwd=root, capture_output=True, timeout=70,
        creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
    )
    if result.returncode:
        # Git errors can contain credential-bearing remote URLs. Do not persist them.
        raise RuntimeError(f"Git {args[0]} başarısız (kod {result.returncode}); ağ/erişim kontrol edilmeli")
    return result.stdout


def sync_cloud(lab: Path = LAB, run_git=git) -> dict:
    root = lab.parent
    directory = lab / "outputs/intraday/research_panel"
    status_path = directory / "sync_status.json"
    attempted = datetime.now(timezone.utc).isoformat()
    previous = {}
    try:
        previous = strict_json(status_path.read_text(encoding="utf-8"))
        if not isinstance(previous, dict):
            previous = {}
    except (OSError, ValueError):
        pass
    try:
        run_git(root, "fetch", "--no-tags", "origin", "main")
        commit = run_git(root, "rev-parse", "FETCH_HEAD").decode("ascii").strip()
        if not re.fullmatch(r"[0-9a-f]{40}", commit):
            raise ValueError("Geçersiz Git commit kimliği")
        generation = directory / "cloud" / commit
        generation.mkdir(parents=True, exist_ok=True)
        hashes = {}
        for filename in ("cloud_ledger.csv", "cloud_state.json"):
            content = run_git(root, "show", f"{commit}:{REMOTE_DIRECTORY}{filename}")
            target = generation / filename
            # A generation is not visible until its manifest pointer is published.
            temporary = target.with_name(f".{filename}.{uuid4().hex}.tmp")
            try:
                temporary.write_bytes(content)
                if filename.endswith(".csv"):
                    frame = oku_defter(temporary)
                    if not len(frame):
                        raise ValueError("Bulut defteri boş; önceki sağlam kopya korunuyor")
                    for column in ("module", "symbol"):
                        if not frame[column].map(lambda value: isinstance(value, str)).all():
                            raise ValueError(f"Bulut {column} alanı metin olmalı")
                else:
                    state = strict_json(content.decode("utf-8-sig"))
                    if (not isinstance(state, dict) or not isinstance(state.get("last_bar"), dict)
                            or not isinstance(state.get("open_positions"), list)
                            or not isinstance(state.get("updated_at"), str)):
                        raise ValueError("Bulut state şeması geçersiz")
                    validate_state(state)
                os.replace(temporary, target)
            finally:
                temporary.unlink(missing_ok=True)
            hashes[filename] = hashlib.sha256(content).hexdigest()
        success = datetime.now(timezone.utc).isoformat()
        manifest = {"commit": commit, "synced_at": success, "hashes": hashes}
        atomic_json(directory / "cloud_current.json", manifest)
        result = {"status": "ok", "attempted_at": attempted, "last_success_at": success,
                  "commit": commit, "error": None}
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
        result = {"status": "error", "attempted_at": attempted,
                  "last_success_at": previous.get("last_success_at"),
                  "commit": previous.get("commit"), "error": str(exc)}
    atomic_json(status_path, result)
    return result


def main():
    parser = argparse.ArgumentParser(description="GitHub bulut defterini panel için eşitle")
    parser.add_argument("--once", action="store_true")
    parser.parse_args()
    result = sync_cloud()
    print(json.dumps(result, ensure_ascii=True), flush=True)
    raise SystemExit(0 if result["status"] == "ok" else 1)


if __name__ == "__main__":
    main()
