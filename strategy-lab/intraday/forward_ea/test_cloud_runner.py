"""Bulut kosucusu — MT5 defterine dokunmadan, delik birakmadan olcer."""
from __future__ import annotations

import json

import pandas as pd

from . import cloud_runner
from .modules import LiveModule, Signal


def _bars(n: int = 260, start: str = "2026-08-01") -> pd.DataFrame:
    idx = pd.date_range(start, periods=n, freq="15min")
    close = pd.Series([100.0 + i * 0.1 for i in range(n)], index=idx)
    return pd.DataFrame(
        {"open": close, "high": close + 1.0, "low": close - 1.0,
         "close": close, "volume": 1000.0},
        index=idx,
    )


def _fetch(frame: pd.DataFrame):
    return lambda symbol_key, tf, days: frame


def _always_long(sub: pd.DataFrame) -> Signal | None:
    px = float(sub["close"].iloc[-1])
    return Signal(direction=1, entry=px, sl=px - 2.0, tp=px + 2.0)


def _never(sub: pd.DataFrame) -> Signal | None:
    return None


def _module(detect=_always_long) -> LiveModule:
    return LiveModule("TEST_MOD", "NASDAQ100", "15m", 0.0, 8, detect)


def test_kendi_defterine_yazar_mt5_defterine_DOKUNMAZ(tmp_path):
    mt5_ledger = tmp_path / "forward_ledger.csv"
    mt5_state = tmp_path / "forward_state.json"
    mt5_ledger.write_text("dokunma", encoding="utf-8")
    mt5_state.write_text("{}", encoding="utf-8")

    cloud_runner.run_once(modules=[_module()], fetch=_fetch(_bars()),
                          state_dir=tmp_path, warmup_days=3)

    assert (tmp_path / "cloud_ledger.csv").exists()
    assert (tmp_path / "cloud_state.json").exists()
    assert mt5_ledger.read_text(encoding="utf-8") == "dokunma"
    assert mt5_state.read_text(encoding="utf-8") == "{}"


def test_defter_kaynagi_isaretler(tmp_path):
    cloud_runner.run_once(modules=[_module()], fetch=_fetch(_bars()),
                          state_dir=tmp_path, warmup_days=3)
    led = pd.read_csv(tmp_path / "cloud_ledger.csv")
    assert len(led) > 0
    assert set(led["source"]) == {"yfinance"}
    assert set(led["module"]) == {"TEST_MOD"}


def test_ikinci_kosum_ayni_islemi_TEKRAR_YAZMAZ(tmp_path):
    frame = _bars()
    first = cloud_runner.run_once(modules=[_module()], fetch=_fetch(frame),
                                  state_dir=tmp_path, warmup_days=3)
    rows_1 = len(pd.read_csv(tmp_path / "cloud_ledger.csv"))
    second = cloud_runner.run_once(modules=[_module()], fetch=_fetch(frame),
                                   state_dir=tmp_path)
    rows_2 = len(pd.read_csv(tmp_path / "cloud_ledger.csv"))

    assert first["closed"] > 0
    assert second["closed"] == 0
    assert rows_1 == rows_2


def test_yeni_barlar_gelince_kaldigi_yerden_devam_eder(tmp_path):
    frame = _bars()
    cloud_runner.run_once(modules=[_module()], fetch=_fetch(frame),
                          state_dir=tmp_path, warmup_days=3)
    rows_1 = len(pd.read_csv(tmp_path / "cloud_ledger.csv"))

    grown = pd.concat([frame, _bars(40, "2026-08-04")])
    grown = grown[~grown.index.duplicated(keep="last")].sort_index()
    cloud_runner.run_once(modules=[_module()], fetch=_fetch(grown), state_dir=tmp_path)
    rows_2 = len(pd.read_csv(tmp_path / "cloud_ledger.csv"))

    assert rows_2 > rows_1


def test_acik_pozisyon_kosumlar_arasinda_KAYBOLMAZ(tmp_path):
    # max_hold cok uzun -> ilk kosumda pozisyon acik kalir
    mod = LiveModule("TEST_OPEN", "NASDAQ100", "15m", 0.0, 5000, _always_long)
    cloud_runner.run_once(modules=[mod], fetch=_fetch(_bars()),
                          state_dir=tmp_path, warmup_days=3)
    state = json.loads((tmp_path / "cloud_state.json").read_text(encoding="utf-8"))
    assert len(state["open_positions"]) == 1
    assert state["last_bar"]


def test_feed_hatasi_diger_modulleri_DUSURMEZ(tmp_path):
    frame = _bars()

    def kirik(symbol_key, tf, days):
        if symbol_key == "XAUUSD":
            raise RuntimeError("feed coktu")
        return frame

    saglam = _module()
    bozuk = LiveModule("TEST_BOZUK", "XAUUSD", "5m", 0.0, 8, _always_long)
    out = cloud_runner.run_once(modules=[bozuk, saglam], fetch=kirik,
                                state_dir=tmp_path, warmup_days=3)

    assert out["skipped"] == ["TEST_BOZUK"]
    assert out["closed"] > 0


def test_sinyal_yoksa_defter_bos_ama_state_yazilir(tmp_path):
    out = cloud_runner.run_once(modules=[_module(_never)], fetch=_fetch(_bars()),
                                state_dir=tmp_path, warmup_days=3)
    assert out["closed"] == 0
    assert (tmp_path / "cloud_state.json").exists()


def test_telegram_ve_emir_yolu_HIC_YOK():
    src = (cloud_runner.__file__ or "")
    text = open(src, encoding="utf-8").read()
    for yasak in ("notify", "OrderExecutor", "order_executor", "mt5_io"):
        assert yasak not in text, f"bulut kosucusunda olmamasi gereken yol: {yasak}"


def test_geriye_doldurulan_satirlar_backfill_olarak_isaretlenir(tmp_path):
    """Warmup = gecmis veriye bakmak; forward kaniti DEGILDIR.

    Isaretlenmezse ilk gunun backtest satirlari, aylar sonra 'bulutta canli
    olculdu' diye okunur. Bu projede sahte edge tam bu yolla uc kez cikti.
    """
    cloud_runner.run_once(modules=[_module()], fetch=_fetch(_bars()),
                          state_dir=tmp_path, warmup_days=3)
    led = pd.read_csv(tmp_path / "cloud_ledger.csv")
    assert set(led["backfill"]) == {1}


def test_normal_kosumun_satirlari_backfill_DEGILDIR(tmp_path):
    frame = _bars()
    cloud_runner.run_once(modules=[_module(_never)], fetch=_fetch(frame),
                          state_dir=tmp_path)
    grown = pd.concat([frame, _bars(40, "2026-08-04")])
    grown = grown[~grown.index.duplicated(keep="last")].sort_index()
    cloud_runner.run_once(modules=[_module()], fetch=_fetch(grown), state_dir=tmp_path)
    led = pd.read_csv(tmp_path / "cloud_ledger.csv")
    assert len(led) > 0
    assert set(led["backfill"]) == {0}
