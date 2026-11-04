from concurrent.futures import ThreadPoolExecutor
from http.server import ThreadingHTTPServer
import json
from pathlib import Path
from threading import Thread
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest

from .__main__ import make_handler
from .data import SWEEP, experiments, read_report, save_experiment, snapshot, source_snapshot


def fixture_ledger(lab: Path, stem="forward", rows=None):
    directory = lab / "outputs/intraday/forward_ea"
    directory.mkdir(parents=True, exist_ok=True)
    header = "module,symbol,dir,entry_time,exit_time,r,backfill\n"
    body = rows if rows is not None else (
        f"{SWEEP},NASDAQ100,1,2026-10-01 10:00,2026-10-01 11:00,2,0\n"
        f"{SWEEP},NASDAQ100,-1,2026-10-02 10:00,2026-10-02 11:00,-1,1\n")
    (directory / f"{stem}_ledger.csv").write_text(header+body, encoding="utf-8")
    (directory / f"{stem}_state.json").write_text(json.dumps({
        "last_bar": {}, "open_positions": [], "account_secret": "do-not-expose"}), encoding="utf-8")


def test_source_separation_and_provenance(tmp_path):
    fixture_ledger(tmp_path)
    fixture_ledger(tmp_path, "cloud", f"{SWEEP},NASDAQ100,1,2026-10-01 10:00,2026-10-01 11:00,-3,0\n")
    result = snapshot(tmp_path)
    assert len(result["sources"][0]["rows"]) == 2
    assert result["sources"][0]["rows"][1]["backfill"] == 1
    assert result["sources"][1]["rows"][0]["r"] == -3
    assert "do-not-expose" not in json.dumps(result)


@pytest.mark.parametrize("bad", ["NaN", "inf", "broken"])
def test_bad_evidence_is_visible_and_never_counted(tmp_path, bad):
    fixture_ledger(tmp_path, rows=f"{SWEEP},NASDAQ100,1,2026-10-01,2026-10-02,{bad},0\n")
    result = source_snapshot(tmp_path, "mt5")
    assert result["errors"] and result["rows"] == []


def test_conflicting_duplicate_rejected(tmp_path):
    fixture_ledger(tmp_path, rows=(f"{SWEEP},NASDAQ100,1,2026-10-01,2026-10-02,1,0\n"
                                 f"{SWEEP},NASDAQ100,1,2026-10-01,2026-10-02,2,0\n"))
    assert source_snapshot(tmp_path, "mt5")["errors"]


def test_invalid_exit_rejected(tmp_path):
    fixture_ledger(tmp_path, rows=f"{SWEEP},NASDAQ100,1,2026-10-02,2026-10-01,1,0\n")
    assert not source_snapshot(tmp_path, "mt5")["rows"]


def test_missing_is_not_success(tmp_path):
    source = source_snapshot(tmp_path, "mt5")
    assert not source["exists"] and source["errors"]
    assert not source["ledger_valid"] and not source["state_valid"]


def test_numeric_module_isolated_from_healthy_source(tmp_path):
    fixture_ledger(tmp_path, rows="123,NASDAQ100,1,2026-10-01,2026-10-02,1,0\n")
    fixture_ledger(tmp_path, "cloud")
    result = snapshot(tmp_path)
    assert not result["sources"][0]["ledger_valid"]
    assert result["sources"][0]["errors"]
    assert len(result["sources"][1]["rows"]) == 2


def test_surrogate_state_isolated(tmp_path):
    fixture_ledger(tmp_path)
    (tmp_path / "outputs/intraday/forward_ea/forward_state.json").write_text(
        '{"updated_at":"\\ud800"}')
    result = snapshot(tmp_path)
    assert result["sources"][0]["errors"]
    assert not result["sources"][0]["state_valid"]
    json.dumps(result, ensure_ascii=False).encode("utf-8")


def test_surrogate_experiment_never_leaves_partial_record(tmp_path):
    with pytest.raises(UnicodeError):
        save_experiment(tmp_path, {**payload(), "title": "\ud800"})
    assert not list((tmp_path / "research-experiments").glob("*"))


def test_failed_flush_never_publishes_partial_record(tmp_path, monkeypatch):
    from . import data
    def fail(_):
        raise OSError("disk failure")
    monkeypatch.setattr(data.os, "fsync", fail)
    with pytest.raises(OSError):
        save_experiment(tmp_path, payload())
    assert not list((tmp_path / "research-experiments").glob("*"))


def test_zero_byte_is_warning(tmp_path):
    fixture_ledger(tmp_path)
    (tmp_path / "outputs/intraday/forward_ea/forward_ledger.csv").write_bytes(b"")
    assert source_snapshot(tmp_path, "mt5")["errors"]


def test_open_only_module_selectable(tmp_path):
    fixture_ledger(tmp_path)
    state = tmp_path / "outputs/intraday/forward_ea/forward_state.json"
    state.write_text(json.dumps({"last_bar": {}, "open_positions": [{
        "module": "OPEN_ONLY", "backfill": 0, "symbol": "NQ", "direction": 1,
        "entry_time": "2026-10-01T10:00:00Z", "entry": 100, "sl": 99, "tp": 102}]}))
    assert "OPEN_ONLY" in {m["name"] for m in snapshot(tmp_path)["modules"]}


@pytest.mark.parametrize("bad", ['{"updated_at":NaN}', '{"last_bar":null}', '{"open_positions":[null]}',
                                 '{}', '{"last_bar":{},"open_positions":[{"module":"OPEN","backfill":0}]}'])
def test_bad_state_does_not_hide_ledger(tmp_path, bad):
    fixture_ledger(tmp_path)
    (tmp_path / "outputs/intraday/forward_ea/forward_state.json").write_text(bad)
    result = source_snapshot(tmp_path, "mt5")
    assert len(result["rows"]) == 2 and result["errors"]
    json.dumps(snapshot(tmp_path), allow_nan=False)


@pytest.mark.parametrize("bad", ["null", "[]", '{"title":"missing fields"}'])
def test_wrong_experiment_schema_is_visible(tmp_path, bad):
    directory = tmp_path / "research-experiments"
    directory.mkdir()
    (directory / "bad.json").write_text(bad)
    assert experiments(tmp_path)[0]["status"] == "HATA"


def test_report_allowlist(tmp_path):
    report = tmp_path / "outputs/intraday/example/REPORT.md"
    report.parent.mkdir(parents=True)
    report.write_text("# Test", encoding="utf-8")
    assert read_report(tmp_path, "example/REPORT.md") == "# Test"
    with pytest.raises(ValueError):
        read_report(tmp_path, "../../.env")


def payload():
    return dict(title="Deneme", hypothesis="Hipotez", falsifier="Çürüten", data_scope="Veri", decision_rule="Durma")


def test_experiments_are_unique_and_require_falsifier(tmp_path):
    with pytest.raises(ValueError):
        save_experiment(tmp_path, {**payload(), "falsifier": " "})
    with ThreadPoolExecutor(4) as pool:
        results = list(pool.map(lambda _: save_experiment(tmp_path, payload()), range(8)))
    assert len({x["id"] for x in results}) == 8
    assert len(list((tmp_path / "research-experiments").glob("*.json"))) == 8


def test_http_security_and_roundtrip(tmp_path):
    fixture_ledger(tmp_path)
    server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(tmp_path))
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{server.server_port}"
    try:
        with urlopen(base+"/api/snapshot") as response:
            token = json.load(response)["csrf_token"]
        body = json.dumps(payload()).encode()
        with pytest.raises(HTTPError) as rejected:
            urlopen(Request(base+"/api/experiments", data=body, headers={"Content-Type": "application/json"}))
        assert rejected.value.code == 403
        headers = {"Content-Type": "application/json", "X-Panel-Token": token, "Origin": base}
        with urlopen(Request(base+"/api/experiments", data=body, headers=headers)) as response:
            assert response.status == 201
        for path in ("/", "/app.js", "/style.css"):
            with urlopen(base+path) as response:
                assert response.status == 200
                assert response.headers["X-Content-Type-Options"] == "nosniff"
        headers["Origin"] = "https://evil.example"
        with pytest.raises(HTTPError) as rejected:
            urlopen(Request(base+"/api/experiments", data=body, headers=headers))
        assert rejected.value.code == 403
        with pytest.raises(HTTPError) as rejected:
            urlopen(Request(base+"/api/snapshot", headers={"Host": "evil.example"}))
        assert rejected.value.code == 403
    finally:
        server.shutdown()
        server.server_close()
        thread.join()
