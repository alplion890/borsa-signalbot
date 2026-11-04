"""Durable append-only audit and single-process lease, isolated from Maven."""

from __future__ import annotations

import contextlib
import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


def utc_now():
    return datetime.now(timezone.utc)


def atomic_json(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False, default=str),
        encoding="utf-8",
    )
    os.replace(temporary, path)


class Store:
    def __init__(self, directory: Path):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(self.directory / "audit.sqlite")
        self.db.execute(
            "CREATE TABLE IF NOT EXISTS events (id INTEGER PRIMARY KEY, time TEXT NOT NULL, kind TEXT NOT NULL, signal_id TEXT, payload TEXT NOT NULL)"
        )
        self.db.execute(
            "CREATE TABLE IF NOT EXISTS state (key TEXT PRIMARY KEY, payload TEXT NOT NULL)"
        )
        self.db.commit()

    def event(self, kind, payload, signal_id=None):
        self.db.execute(
            "INSERT INTO events(time,kind,signal_id,payload) VALUES (?,?,?,?)",
            (
                utc_now().isoformat(),
                kind,
                signal_id,
                json.dumps(payload, default=str, allow_nan=False),
            ),
        )
        self.db.commit()

    def get(self, key, default=None):
        row = self.db.execute(
            "SELECT payload FROM state WHERE key=?", (key,)
        ).fetchone()
        return json.loads(row[0]) if row else default

    def set(self, key, value):
        self.db.execute(
            "INSERT OR REPLACE INTO state(key,payload) VALUES (?,?)",
            (key, json.dumps(value, default=str, allow_nan=False)),
        )
        self.db.commit()

    def close(self):
        self.db.close()


@contextlib.contextmanager
def single_process(directory: Path):
    """OS releases the lock on crashes; the file itself is not the lease."""
    directory.mkdir(parents=True, exist_ok=True)
    handle = (directory / "runner.lock").open("a+b")
    handle.seek(0)
    handle.write(b"0")
    handle.flush()
    handle.seek(0)
    try:
        if os.name == "nt":
            import msvcrt

            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl

            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        handle.close()
        raise RuntimeError("FTMO calistiricisi zaten acik") from None
    try:
        yield
    finally:
        handle.close()
