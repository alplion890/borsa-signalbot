from datetime import datetime, timezone
import json

from .data import cloud_location, snapshot, source_freshness, SWEEP
from .sync import sync_cloud
from .test_panel import fixture_ledger


def fake_remote(tmp_path, commit="a" * 40, bad_state=False, bad_positions=False):
    fixture_ledger(tmp_path, "cloud")
    directory = tmp_path / "outputs/intraday/forward_ea"
    state = {"updated_at": "2026-10-15T15:00:00Z", "last_bar": {
        SWEEP+":NASDAQ100": "2026-10-15 14:30:00"}, "open_positions": []}
    if bad_positions:
        state["open_positions"] = [None]
    def run_git(root, *args):
        if args[0] == "fetch":
            return b""
        if args[0] == "rev-parse":
            return commit.encode()
        if args[1].endswith("cloud_state.json"):
            return b"{}" if bad_state else json.dumps(state).encode()
        return (directory / "cloud_ledger.csv").read_bytes()
    return run_git


def test_cloud_mirror_does_not_overwrite_local_evidence(tmp_path):
    run_git = fake_remote(tmp_path)
    local = tmp_path / "outputs/intraday/forward_ea/cloud_ledger.csv"
    before = local.read_bytes()
    result = sync_cloud(tmp_path, run_git)
    assert result["status"] == "ok"
    path, origin, errors = cloud_location(tmp_path)
    assert path.name == "a" * 40 and not errors
    assert origin["origin"] == "GitHub bulut defteri"
    assert local.read_bytes() == before
    assert snapshot(tmp_path)["sources"][1]["commit"] == "a" * 40


def test_failed_sync_keeps_last_known_generation(tmp_path):
    assert sync_cloud(tmp_path, fake_remote(tmp_path))["status"] == "ok"
    pointer = tmp_path / "outputs/intraday/research_panel/cloud_current.json"
    before = pointer.read_bytes()
    assert sync_cloud(tmp_path, fake_remote(tmp_path, commit="b"*40, bad_state=True))["status"] == "error"
    assert pointer.read_bytes() == before
    assert snapshot(tmp_path)["cloud_sync"]["status"] == "error"
    assert snapshot(tmp_path)["sources"][1]["commit"] == "a" * 40


def test_mirror_tampering_is_visible(tmp_path):
    sync_cloud(tmp_path, fake_remote(tmp_path))
    directory, _, _ = cloud_location(tmp_path)
    (directory / "cloud_state.json").write_text("{}")
    _, origin, errors = cloud_location(tmp_path)
    assert errors and "doğrulanamadı" in origin["origin"]


def test_nested_bad_state_cannot_replace_good_generation(tmp_path):
    sync_cloud(tmp_path, fake_remote(tmp_path))
    assert sync_cloud(tmp_path, fake_remote(tmp_path, commit="c"*40, bad_positions=True))["status"] == "error"
    assert snapshot(tmp_path)["sources"][1]["commit"] == "a"*40
    assert snapshot(tmp_path)["sources"][1]["state_valid"]


def test_freshness_uses_processed_bar_not_file_time():
    now = datetime(2026, 10, 15, 16, 0, tzinfo=timezone.utc)
    state = {"last_bar": {SWEEP+":NASDAQ100": "2026-10-15 15:30:00"},
             "updated_at": "2026-10-15T16:00:00Z"}
    assert source_freshness(state, "mt5", now)["age_minutes"] == 15
    state["last_bar"][SWEEP+":NASDAQ100"] = "2026-10-15 14:30:00"
    assert source_freshness(state, "mt5", now)["status"] == "stale"
    assert source_freshness(state, "cloud", now)["status"] == "fresh"
    assert source_freshness({}, "mt5", now)["status"] == "unknown"


def test_manifest_commit_cannot_escape_mirror_directory(tmp_path):
    pointer = tmp_path / "outputs/intraday/research_panel/cloud_current.json"
    pointer.parent.mkdir(parents=True)
    pointer.write_text(json.dumps({"commit": "../../.."}))
    _, _, errors = cloud_location(tmp_path)
    assert errors
