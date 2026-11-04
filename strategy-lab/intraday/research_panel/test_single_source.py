import json
import pandas as pd
import pytest

from .policy import primary_snapshot
from .evidence import strategy_evidence
from .broker_history import publish, catalog, root
from .test_panel import fixture_ledger
from .data import SWEEP


def test_cloud_disagreement_cannot_change_primary_assessment(tmp_path):
    fixture_ledger(tmp_path)
    fixture_ledger(tmp_path,"cloud",f"{SWEEP},NASDAQ100,1,2026-10-01,2026-10-02,-999,0\n")
    a=primary_snapshot(tmp_path)
    assessment=strategy_evidence(a["sources"],a["modules"])
    assert len(a["sources"])==1 and a["sources"][0]["key"]=="mt5"
    assert a["audit_sources"][0]["key"]=="cloud"
    assert assessment[0]["primary"]["forward"]["sum_r"]==2
    assert not any("uyuşmaz" in r for r in assessment[0]["reasons"])


def test_local_binance_rows_never_masquerade_as_mt5(tmp_path):
    fixture_ledger(tmp_path,rows="CAND_BTC_ABSORPTION,BTCUSDT,1,2026-10-01,2026-10-02,50,0\n")
    data=primary_snapshot(tmp_path)
    assert data["sources"][0]["rows"]==[] and data["modules"]==[]
    assert "CAND_BTC_ABSORPTION" in data["source_policy"]["excluded_external_modules"]


def test_missing_mt5_never_falls_back_to_cloud(tmp_path):
    fixture_ledger(tmp_path,"cloud")
    data=primary_snapshot(tmp_path)
    assert not data["sources"][0]["ledger_valid"] and data["modules"]==[]
    assert data["source_policy"]["fallback"] is False


def frame():
    return pd.DataFrame(dict(open=[100.,101.],high=[102.,103.],low=[99.,100.],close=[101.,102.],volume=[1.,1.]),index=pd.date_range("2026-01-01",periods=2,freq="15min"))


def test_broker_fingerprint_and_no_unverified_cache(tmp_path):
    info=publish(tmp_path,"NASDAQ100","15m",frame(),"Maven","Maven-Server")
    assert len(catalog(tmp_path))==1
    path=root(tmp_path)/info["id"]
    path.write_text("broken")
    assert catalog(tmp_path)==[]


def test_wrong_broker_is_not_silently_accepted(tmp_path):
    with pytest.raises(ValueError,match="Maven"):
        publish(tmp_path,"NASDAQ100","15m",frame(),"Other Broker","Other-Server")


def test_old_duka_cache_cannot_become_new_backtest_input(tmp_path):
    from .jobs import datasets
    cache=tmp_path/"outputs/intraday/cache"
    cache.mkdir(parents=True)
    frame().to_csv(cache/"NASDAQ100_15m_540d.csv")
    assert datasets(tmp_path)==[]


def test_selected_immutable_snapshot_survives_new_export(tmp_path):
    from .broker_history import resolve_dataset
    first=publish(tmp_path,"NASDAQ100","15m",frame(),"Maven","Maven-Server")
    newer=frame()
    newer.index += pd.Timedelta(days=1)
    second=publish(tmp_path,"NASDAQ100","15m",newer,"Maven","Maven-Server")
    assert catalog(tmp_path)[0]["id"]==second["id"]
    assert resolve_dataset(tmp_path,first["id"])["provenance"]["data_sha256"]==first["data_sha256"]


def test_closed_bar_export_uses_verified_running_broker(tmp_path,monkeypatch):
    import sys
    from contextlib import nullcontext
    from types import SimpleNamespace
    from . import broker_history
    from .. import mt5_bridge
    fake_io=SimpleNamespace(session=lambda:nullcontext(),resolve=lambda key:"US100",_TF={"15m":"TIMEFRAME_M15"})
    monkeypatch.setattr(mt5_bridge,"mt5_io",fake_io,raising=False)
    monkeypatch.setitem(sys.modules,"intraday.mt5_bridge.mt5_io",fake_io)
    monkeypatch.setattr(broker_history,"PAIRS",(("NASDAQ100","15m"),))
    base=pd.Timestamp.now(tz="UTC").floor("15min")
    times=[int((base-pd.Timedelta(minutes=30)).timestamp()),int((base-pd.Timedelta(minutes=15)).timestamp()),int((base+pd.Timedelta(minutes=15)).timestamp())]
    calls=[]
    def copy(*args):
        calls.append(args)
        return pd.DataFrame(dict(time=times,open=100.,high=102.,low=99.,close=101.,tick_volume=1.)).to_records(index=False)
    api=SimpleNamespace(account_info=lambda:SimpleNamespace(company="Maven",server="Maven-Server"),
                        terminal_info=lambda:SimpleNamespace(connected=True),TIMEFRAME_M15=15,copy_rates_from_pos=copy)
    monkeypatch.setitem(sys.modules,"MetaTrader5",api)
    result=broker_history.export(tmp_path,1000)
    assert not result["errors"] and result["exported"][0]["bars"]==2
    assert calls[0][2]==1


def test_known_wrong_broker_blocks_panel_metrics(tmp_path):
    fixture_ledger(tmp_path)
    target=tmp_path/"outputs/intraday/forward_ea/forward_state.json"
    state=json.loads(target.read_text())
    state["broker_source"]=dict(provider="other",broker="Other",server="Other",verified_at="2026-10-15",verified_since="2026-10-15")
    target.write_text(json.dumps(state))
    data=primary_snapshot(tmp_path)
    assert not data["sources"][0]["ledger_valid"]
