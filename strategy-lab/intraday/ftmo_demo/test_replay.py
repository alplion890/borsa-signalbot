import hashlib
import json

import pandas as pd
import pytest

from intraday.ftmo_demo.replay import replay
from intraday.ftmo_demo.signals import strategy_hash
from intraday.forward_ea.modules import Signal


def export(tmp_path):
    frame = pd.DataFrame(
        {"open": 100.0, "high": 103.0, "low": 98.0, "close": 100.0},
        index=pd.date_range("2026-10-01", periods=522, freq="15min"),
    )
    csv = tmp_path / "bars.csv"
    csv.write_text(frame.to_csv(index_label="time"), encoding="utf-8")
    metadata = tmp_path / "metadata.json"
    metadata.write_text(
        json.dumps(
            {
                "source": "ftmo_mt5",
                "server": "FTMO-Demo",
                "symbol_key": "SP500",
                "tf": "15m",
                "time_basis": "UTC",
                "strategy_hash": strategy_hash(),
                "sha256": hashlib.sha256(csv.read_bytes()).hexdigest(),
            }
        )
    )
    return csv, metadata


def test_replay_uses_conservative_sl_first_and_explicit_non_maven_cost(tmp_path):
    csv, metadata = export(tmp_path)
    report = replay(
        csv,
        metadata,
        cost_per_side=0.001,
        detector=lambda frame: (
            Signal(1, 100.0, 99.0, 102.0) if len(frame) == 520 else None
        ),
    )
    assert len(report["trades"]) == 1
    assert report["trades"][0]["status"] == "sl"
    assert report["trades"][0]["r"] == pytest.approx(-1.2)


def test_replay_rejects_feed_tampering_and_nan_cost(tmp_path):
    csv, metadata = export(tmp_path)
    with pytest.raises(ValueError, match="maliyet"):
        replay(csv, metadata, cost_per_side=float("nan"))
    csv.write_text(csv.read_text() + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="hash"):
        replay(csv, metadata, cost_per_side=0)
