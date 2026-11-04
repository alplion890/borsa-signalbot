import json
import pandas as pd
import pytest

from .evidence import compare_sources, metrics, strategy_evidence
from . import jobs


def row(time, r=1):
    return dict(module="test", symbol="NASDAQ100", dir=1, entry_time="2026-10-01T"+time+":00Z", r=r, backfill=0)


def test_canonical_matching_maximum_and_boundary_tolerance():
    left = [row(t) for t in ("09:00", "10:00", "10:10", "11:00")]
    right = [row(t) for t in ("09:00", "09:50", "10:00", "11:00")]
    assert compare_sources(left, right)["matched"] == 4
    assert compare_sources([row("10:00")], [row("10:05")])["matched"] == 1


def test_opposite_outcomes_cannot_be_aligned():
    result = compare_sources([row("10:00", 2)], [row("10:00", -1)])
    assert result["status"] == "conflict" and result["sign_conflicts"] == 1
    assert compare_sources([], [row("10:00")])["status"] == "insufficient"
    assert compare_sources([row("09:00"),row("11:00")], [row("10:00")])["matched"] == 0


def test_drawdown_includes_initial_zero_and_absence_is_not_zero():
    assert metrics([row("10:00", -1), row("10:05", -2)])["drawdown_r"] == 3
    assert metrics([])["sum_r"] is None


def test_gold_retired_and_authority_never_follows_positive_sum():
    sources = [dict(key=k, ledger_valid=True, quarantined_modules=[], rows=[], state_valid=True,
                    freshness={"status":"fresh"}) for k in ("mt5", "cloud")]
    result = strategy_evidence(sources, [{"name":"GOLD_NY_ORB_TREND"}, {"name":"CAND_SWEEP_JAP225"}])
    assert next(x for x in result if x["name"]=="GOLD_NY_ORB_TREND")["authority"] == "Emekli"
    assert next(x for x in result if x["name"]=="CAND_SWEEP_JAP225")["authority"] == "PAPER / araştırma"


def config():
    return dict(strategy="SWEEP_CORE", dataset="NASDAQ100_15m_test.csv", start="2025-01-01", end="2025-02-15", cost_factor=1)


def fixture(tmp):
    root = tmp / "outputs/intraday/research_panel/broker_history"
    root.mkdir(parents=True)
    idx = pd.date_range("2024-12-01", "2025-02-16", freq="15min")
    path = root / config()["dataset"]
    pd.DataFrame(dict(timestamp=idx, open=100., high=102., low=98., close=101., volume=1.)).to_csv(path, index=False)
    import hashlib
    path.with_name(path.name+".json").write_text(json.dumps(dict(source="maven_mt5",symbol="NASDAQ100",tf="15m",broker="Maven",server="Maven-test",closed_bars_only=True,start=str(idx[0]),end=str(idx[-1]),data_sha256=hashlib.sha256(path.read_bytes()).hexdigest())))


@pytest.mark.parametrize("change", [{"dataset":"../../secret.csv"}, {"strategy":"shell"}, {"strategy":{}}, {"dataset":[]}, {"cost_factor":"nan"}, {"cost_factor":0}, {"start":"2025-03-01"}, {"dataset":"EURUSD_5m_test.csv"}])
def test_reject_arbitrary_path_strategy_and_invalid_config(tmp_path, change):
    fixture(tmp_path)
    with pytest.raises(ValueError):
        jobs.validate({**config(), **change}, tmp_path)


def test_restart_recovers_stale_job(tmp_path):
    jobs.write_job(tmp_path, {"id":"test", "created_at":"2025-01-01", "status":"running", "config": config()})
    jobs.recover_interrupted(tmp_path)
    assert jobs.list_jobs(tmp_path)[0]["status"] == "interrupted"


def test_backtest_cost_and_source_metadata(tmp_path, monkeypatch):
    fixture(tmp_path)
    from .. import honest_engine
    costs = []
    def simulate(frame, *args, **kwargs):
        costs.append(args[6].cost_per_side)
        # Constant gross performance makes net cost relation observable.
        return pd.Series([2 - 1000*args[6].cost_per_side], index=[pd.Timestamp("2025-01-03")])
    monkeypatch.setattr(honest_engine, "simulate_trades", simulate)
    a = jobs.execute(config(), tmp_path)
    b = jobs.execute({**config(), "cost_factor":2}, tmp_path)
    assert costs[1] == 2*costs[0]
    assert b["metrics"]["sum_r"] < a["metrics"]["sum_r"]
    assert len(a["metadata"]["data_sha256"]) == 64
    assert a["metadata"]["warmup_bars"] == 2000
    json.dumps(a, allow_nan=False)


def test_reject_corrupt_ohlc(tmp_path):
    fixture(tmp_path)
    path = tmp_path / "outputs/intraday/research_panel/broker_history" / config()["dataset"]
    frame = pd.read_csv(path)
    frame.loc[1,"high"] = 1
    frame.to_csv(path,index=False)
    import hashlib
    meta_path=path.with_name(path.name+".json")
    meta=json.loads(meta_path.read_text())
    meta["data_sha256"]=hashlib.sha256(path.read_bytes()).hexdigest()
    meta_path.write_text(json.dumps(meta))
    with pytest.raises(ValueError, match="OHLC"):
        jobs.execute(config(),tmp_path)
