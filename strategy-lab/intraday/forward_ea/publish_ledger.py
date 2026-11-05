"""Publish the local Maven forward ledger to GitHub via the contents API.

Why (2026-11-05): the single measurement source is the Maven MT5 ledger on
the user's PC, but the phone brief runs in GitHub Actions. The local file is
NOT tracked by git any more (the runner rewrote it every 5 minutes, which kept
the working tree dirty and blocked `git pull` for weeks). Instead this script
writes a copy to REMOTE_PATH through the API, so the local checkout only ever
receives it via pull and never conflicts.

Runs after each forward cycle; does nothing when the file is unchanged.
Failures are printed and never break the measurement cycle.
"""
from __future__ import annotations

import base64
import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Callable

from .ledger import _OUT

LOCAL_LEDGER = _OUT / "forward_ledger.csv"
MARKER = _OUT / ".published.sha256"
REMOTE_PATH = "strategy-lab/outputs/intraday/forward_ea/published/forward_ledger.csv"
BRANCH = "main"

Gh = Callable[[list[str], "dict | None"], dict]


def _gh(args: list[str], payload: dict | None = None) -> dict:
    proc = subprocess.run(
        ["gh", "api", *args, *(["--input", "-"] if payload else [])],
        input=json.dumps(payload) if payload else None,
        capture_output=True, text=True, timeout=60, check=True,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    return json.loads(proc.stdout or "{}")


def _normalized(data: bytes) -> bytes:
    return data.replace(b"\r\n", b"\n")


def repo_slug() -> str:
    url = subprocess.run(["git", "remote", "get-url", "origin"], capture_output=True,
                         text=True, check=True,
                         cwd=Path(__file__).resolve().parent).stdout.strip()
    match = re.search(r"github\.com[:/](.+?)(?:\.git)?$", url)
    if not match:
        raise ValueError("origin is not a GitHub remote")
    return match.group(1)


def publish(ledger: Path = LOCAL_LEDGER, repo: str | None = None, *,
            gh: Gh = _gh, marker: Path = MARKER) -> str:
    """Return 'missing' | 'unchanged' | 'same' | 'published'."""
    if not ledger.exists():
        return "missing"
    body = _normalized(ledger.read_bytes())
    digest = hashlib.sha256(body).hexdigest()
    if marker.exists() and marker.read_text(encoding="utf-8").strip() == digest:
        return "unchanged"
    repo = repo or repo_slug()
    url = f"repos/{repo}/contents/{REMOTE_PATH}"
    sha = None
    try:
        current = gh([f"{url}?ref={BRANCH}"], None)
        sha = current.get("sha")
        remote = base64.b64decode(current.get("content", ""))
        if _normalized(remote) == body:
            marker.write_text(digest, encoding="utf-8")
            return "same"
    except subprocess.CalledProcessError as exc:
        if "Not Found" not in (exc.stderr or ""):
            raise
    payload = {"message": "chore(forward_ledger): publish Maven ledger [skip ci]",
               "content": base64.b64encode(body).decode("ascii"), "branch": BRANCH}
    if sha:
        payload["sha"] = sha
    gh(["-X", "PUT", url], payload)
    marker.write_text(digest, encoding="utf-8")
    return "published"


def main() -> None:
    try:
        print(f"[publish_ledger] {publish()}")
    except Exception as exc:  # never break the forward cycle
        print(f"[publish_ledger] ERROR {type(exc).__name__}: {exc}")


if __name__ == "__main__":
    main()
