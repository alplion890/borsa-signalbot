import json
import sqlite3
import threading
import urllib.request

import pytest

from intraday.ftmo_demo.dashboard import create_server, load_state, render_dashboard


def sample_state():
    return {
        "updated_at": "2026-10-16T12:00:00Z",
        "source": "manual-demo",
        "status": "PAPER",
        "account": {"label": "Test", "currency": "USD", "mode": "Free Trial"},
        "metrics": {
            "balance": 5000,
            "equity": 5100.5,
            "profit": 100.5,
            "drawdown_pct": 0.7,
            "daily_loss_pct": 0.2,
            "consistency_pct": 14,
            "payout_ready": False,
            "accepted_trades": 7,
            "required_trades": 20,
            "eligible_days": 4,
            "required_days": 14,
        },
        "floors": [
            {
                "name": "Max loss",
                "value": 10,
                "unit": "%",
                "status": "OK",
                "source": "manual",
            }
        ],
        "equity_history": [
            {"time": "d1", "value": 5000},
            {"time": "d2", "value": 5100.5},
        ],
        "open_risk": [
            {
                "symbol": "EURUSD",
                "side": "long",
                "size": 0.1,
                "risk": 25,
                "currency": "USD",
            }
        ],
        "modules": [
            {"name": "SWEEP_CORE_AVOID_MID_VWAP", "trades": 2, "net": 10.5, "r": 0.4}
        ],
        "notes": ["Macro is observation only"],
    }


def test_render_dashboard_shows_sections_and_escapes_untrusted_values():
    state = sample_state()
    state["account"]["label"] = "<script>alert(1)</script>"
    page = render_dashboard(state)
    assert "Özkaynak geçmişi" in page
    assert "7 / 20" in page
    assert "4 / 14" in page
    assert "&lt;script&gt;" in page
    assert "<script>alert(1)</script>" not in page
    assert "Payout uygunluğu" in page
    assert "Açık risk" in page
    assert "Modül sonuçları" in page
    assert "SWEEP_CORE_AVOID_MID_VWAP" in page
    assert "0.40" in page


def test_load_json_and_sqlite_snapshots(tmp_path):
    state = sample_state()
    json_path = tmp_path / "state.json"
    json_path.write_text(json.dumps(state), encoding="utf-8")
    assert load_state(json_path)["metrics"]["accepted_trades"] == 7

    db_path = tmp_path / "state.sqlite"
    with sqlite3.connect(db_path) as db:
        db.execute("CREATE TABLE snapshots (id INTEGER PRIMARY KEY, state_json TEXT)")
        db.execute("INSERT INTO snapshots(state_json) VALUES (?)", (json.dumps(state),))
    assert load_state(db_path)["source"] == "manual-demo"


def test_server_serves_read_only_html_and_state_api(tmp_path):
    path = tmp_path / "state.json"
    path.write_text(json.dumps(sample_state()), encoding="utf-8")

    server = create_server(path, "127.0.0.1", 0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        port = server.server_port
        with urllib.request.urlopen(
            f"http://127.0.0.1:{port}/api/state", timeout=1
        ) as response:
            result = json.loads(response.read())
            assert result["state"]["status"] == "PAPER"
            assert response.headers["Cache-Control"] == "no-store"
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/", timeout=1) as response:
            assert "Özkaynak geçmişi" in response.read().decode("utf-8")
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=1)


def test_reject_non_loopback_host(tmp_path):
    with pytest.raises(ValueError, match="localhost"):
        create_server(tmp_path / "unused.json", "0.0.0.0", 8767)
