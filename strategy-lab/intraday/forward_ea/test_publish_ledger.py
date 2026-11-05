"""Maven ledger publisher: local file stays untracked, repo gets a copy via API."""
from __future__ import annotations

import base64
import json
import subprocess

from . import publish_ledger as pl


class _Gh:
    def __init__(self, remote_text: str | None):
        self.remote_text = remote_text
        self.calls: list[list[str]] = []

    def __call__(self, args: list[str], payload: dict | None = None) -> dict:
        self.calls.append(args + ([json.dumps(payload)] if payload else []))
        if "PUT" in args:
            return {"commit": {"sha": "abc"}}
        if self.remote_text is None:
            raise subprocess.CalledProcessError(1, args, stderr="Not Found")
        return {"sha": "old-sha",
                "content": base64.b64encode(self.remote_text.encode()).decode()}


def test_publishes_changed_ledger_with_skip_ci(tmp_path):
    ledger = tmp_path / "forward_ledger.csv"
    ledger.write_text("a,b\n1,2\n", encoding="utf-8")
    gh = _Gh("a,b\n")
    assert pl.publish(ledger, "owner/repo", gh=gh, marker=tmp_path / "m") == "published"
    put = gh.calls[-1]
    body = json.loads(put[-1])
    assert "[skip ci]" in body["message"]
    assert body["sha"] == "old-sha"
    assert base64.b64decode(body["content"]).decode() == "a,b\n1,2\n"
    assert pl.REMOTE_PATH in " ".join(put)


def test_skips_api_when_local_file_unchanged_since_last_publish(tmp_path):
    ledger = tmp_path / "forward_ledger.csv"
    ledger.write_text("a,b\n1,2\n", encoding="utf-8")
    marker = tmp_path / "m"
    pl.publish(ledger, "owner/repo", gh=_Gh(None), marker=marker)
    gh = _Gh("a,b\n1,2\n")
    assert pl.publish(ledger, "owner/repo", gh=gh, marker=marker) == "unchanged"
    assert gh.calls == []


def test_same_content_remote_is_not_rewritten(tmp_path):
    ledger = tmp_path / "forward_ledger.csv"
    ledger.write_bytes(b"a,b\r\n1,2\r\n")
    gh = _Gh("a,b\n1,2\n")  # CRLF vs LF is the same ledger
    assert pl.publish(ledger, "owner/repo", gh=gh, marker=tmp_path / "m") == "same"
    assert not any("PUT" in c for c in gh.calls)


def test_creates_file_when_remote_missing(tmp_path):
    ledger = tmp_path / "forward_ledger.csv"
    ledger.write_text("a\n", encoding="utf-8")
    gh = _Gh(None)
    assert pl.publish(ledger, "owner/repo", gh=gh, marker=tmp_path / "m") == "published"
    assert "sha" not in json.loads(gh.calls[-1][-1])


def test_missing_local_ledger_is_reported_not_raised(tmp_path):
    out = pl.publish(tmp_path / "nope.csv", "owner/repo", gh=_Gh("x"),
                     marker=tmp_path / "m")
    assert out == "missing"


def test_ledger_path_can_point_at_published_copy(monkeypatch, tmp_path):
    import importlib
    from . import ledger
    monkeypatch.setenv("FORWARD_LEDGER_PATH", str(tmp_path / "pub.csv"))
    try:
        assert importlib.reload(ledger).LEDGER_CSV == tmp_path / "pub.csv"
    finally:
        monkeypatch.delenv("FORWARD_LEDGER_PATH")
        importlib.reload(ledger)
