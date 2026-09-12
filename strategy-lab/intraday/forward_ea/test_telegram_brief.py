from __future__ import annotations

from datetime import datetime, time, timezone
from types import SimpleNamespace

import numpy as np
import pandas as pd

from ..event_calendar import MacroEvent
from . import telegram_brief

UTC = timezone.utc

_PIYASA = telegram_brief.PiyasaOzeti(
    teknik="NQ 15dk: yukari trend, guclu (ADX 31.2); VWAP ustunde; son 1 saat %+0.42",
    hacim="Hacim: 1.6x, artiyor ve trendi destekliyor",
    firsat="YOK - NQ proxy Sweep tetiklenmedi",
    veri="Veri: NQ=F kapanmis 15dk bar 18:00 TR, 5 dk gecikme",
)


def _sabit(monkeypatch):
    monkeypatch.setattr(
        telegram_brief, "_anlik_nasdaq", lambda simdi, **kwargs: _PIYASA)
    monkeypatch.setattr(telegram_brief, "_stats", lambda: telegram_brief.KanitOzeti({
        "SWEEP_CORE_AVOID_MID_VWAP": (10, 0.613),
        "NQ_ORB_STRONG_TREND": (25, -0.106),
        "EUR_LONDON_FADE_EMA": (9, 0.308),
        "GBP_LONDON_STRONG_TREND": (11, -0.145),
    }, gecersiz_zaman_satiri=2))
    monkeypatch.setattr(telegram_brief.diskresyoner, "ozet", lambda: {
        "aday_acik": 0, "pas": 0, "n": 0, "exp_R": float("nan"),
        "durma_tetik": False,
    })


def test_durum_mesaji_live_paper_fon_ve_setuplari_ayirir(monkeypatch, tmp_path):
    _sabit(monkeypatch)
    state = tmp_path / "state.json"
    state.write_text(
        '{"updated_at":"2026-09-09T12:00:00+00:00","open_positions":['
        '{"module":"CAND_BTC_ABSORPTION","symbol":"BTCUSDT","direction":-1}]}'
    )
    metin = telegram_brief.durum_mesaji(
        datetime(2026, 9, 9, 13, 20, tzinfo=UTC), state)

    assert "16:20 TR" in metin
    assert "Hesap: Maven BNPL challenge" in metin
    assert "LIVE firsat adayi: YOK - NQ proxy Sweep tetiklenmedi" in metin
    assert "Paper test: kayit guncel degil" in metin
    assert "Veri: NQ=F kapanmis 15dk bar 18:00 TR, 5 dk gecikme" in metin
    assert "Bakiye: buluta bagli degil" in metin
    assert "NQ_ORB_STRONG_TREND" not in metin
    assert "exit<entry" not in metin
    assert len(metin) < 4096


def test_bayat_paper_state_anlik_piyasa_yorumunu_engellemez(monkeypatch, tmp_path):
    _sabit(monkeypatch)
    monkeypatch.setattr(telegram_brief, "takvim_olgusu", lambda: ([], []))
    monkeypatch.setattr(telegram_brief.market_context, "collect", lambda *a, **k: {})
    state = tmp_path / "state.json"
    state.write_text(
        '{"updated_at":"2026-09-10T12:00:00+00:00","open_positions":['
        '{"module":"SWEEP_CORE_AVOID_MID_VWAP","direction":1}]}'
    )

    metin = telegram_brief.edge_mesaji(
        datetime(2026, 9, 10, 15, 15, tzinfo=UTC), state)

    assert "NQ 15dk: yukari trend, guclu" in metin
    assert "Fırsat: YOK - NQ proxy Sweep tetiklenmedi" in metin
    assert "tarama güncel değil" not in metin


def test_edge_mesaji_pozitif_yontemleri_guncel_durumla_yazar(monkeypatch, tmp_path):
    _sabit(monkeypatch)
    olay = MacroEvent(datetime(2026, 9, 11).date(), "CPI", time(8, 30))
    monkeypatch.setattr(telegram_brief, "takvim_olgusu", lambda: ([], [olay]))
    monkeypatch.setattr(telegram_brief.market_context, "collect", lambda *a, **k: {
        "economic_calendar": [{
            "time_utc": "2026-09-10T12:30:00+00:00",
            "event": "Producer Price Index",
        }],
        "recent_news": [{"headline": "Federal Reserve publishes policy statement"}],
    })

    metin = telegram_brief.edge_mesaji(
        datetime(2026, 9, 10, 15, 15, tzinfo=UTC), tmp_path / "state.json")

    assert "NQ 15dk: yukari trend, guclu (ADX 31.2)" in metin
    assert "Hacim: 1.6x, artiyor ve trendi destekliyor" in metin
    assert "Fırsat: YOK - NQ proxy Sweep tetiklenmedi" in metin
    assert "Kanıt: NASDAQ100 Sweep: 10 forward islem, ort. +0.613R" in metin
    assert "NASDAQ100 Açılış Kırılımı" not in metin
    assert "GBPUSD London Trend" not in metin
    assert "CPI: 15:30 TR (08:30 ET)" in metin
    assert "BUGUN Producer Price Index: 15:30 TR" in metin
    assert "Resmî başlık: Federal Reserve publishes policy statement" in metin
    assert "FVG" not in metin
    assert len(metin) < 4096


def test_edge_negatifse_teknigi_edge_diye_sunmaz(monkeypatch):
    monkeypatch.setattr(
        telegram_brief, "_anlik_nasdaq", lambda simdi, **kwargs: _PIYASA)
    monkeypatch.setattr(telegram_brief, "_stats", lambda: telegram_brief.KanitOzeti({
        "SWEEP_CORE_AVOID_MID_VWAP": (25, -0.01),
    }))
    monkeypatch.setattr(telegram_brief.market_context, "collect", lambda *a, **k: {})
    monkeypatch.setattr(telegram_brief, "takvim_olgusu", lambda: ([], []))

    metin = telegram_brief.edge_mesaji(datetime(2026, 9, 10, 15, 15, tzinfo=UTC))

    assert "Kanıt: dogrulanmis pozitif LIVE yontem yok" in metin


def test_iki_mesaj_ayni_forward_kanitini_bir_kez_kullanir(monkeypatch, tmp_path):
    sayac = {"stats": 0}

    def stats():
        sayac["stats"] += 1
        return telegram_brief.KanitOzeti({
            "SWEEP_CORE_AVOID_MID_VWAP": (10, 0.613),
        })

    monkeypatch.setattr(telegram_brief, "_stats", stats)
    monkeypatch.setattr(
        telegram_brief, "_anlik_nasdaq", lambda simdi, **kwargs: _PIYASA)
    monkeypatch.setattr(telegram_brief.diskresyoner, "ozet", lambda: {
        "aday_acik": 0, "pas": 0, "n": 0, "exp_R": float("nan"),
        "durma_tetik": False,
    })
    monkeypatch.setattr(telegram_brief.market_context, "collect", lambda *a, **k: {})
    monkeypatch.setattr(telegram_brief, "takvim_olgusu", lambda: ([], []))

    durum, edge = telegram_brief.mesajlar(
        datetime(2026, 9, 10, 15, 15, tzinfo=UTC), tmp_path / "yok.json")

    assert sayac["stats"] == 1
    assert "LIVE firsat adayi: YOK - NQ proxy Sweep tetiklenmedi" in durum
    assert "Kanıt: NASDAQ100 Sweep: 10 forward islem, ort. +0.613R" in edge


def test_canli_ve_yerel_CPI_iki_kere_yazilmaz(monkeypatch):
    _sabit(monkeypatch)
    olay = MacroEvent(datetime(2026, 9, 11).date(), "CPI", time(8, 30))
    monkeypatch.setattr(telegram_brief, "takvim_olgusu", lambda: ([], [olay]))
    monkeypatch.setattr(telegram_brief.market_context, "collect", lambda *a, **k: {
        "economic_calendar": [{
            "time_utc": "2026-09-11T12:30:00+00:00",
            "event": "Consumer Price Index",
        }],
        "recent_news": [],
    })

    metin = telegram_brief.edge_mesaji(datetime(2026, 9, 10, 15, 15, tzinfo=UTC))

    assert metin.count("Consumer Price Index") == 1
    assert "2026-09-11 CPI:" not in metin


def test_anlik_nasdaq_trend_hacim_ve_sweep_setupini_hesaplar(monkeypatch):
    now = datetime(2026, 9, 10, 15, 20, tzinfo=UTC)
    index = pd.date_range(end="2026-09-10 15:00:00+00:00", periods=2200, freq="15min")
    close = np.linspace(29_000.0, 29_500.0, len(index))
    frame = pd.DataFrame({
        "open": close - 1,
        "high": close + 3,
        "low": close - 3,
        "close": close,
        "volume": np.r_[np.full(len(index) - 1, 100.0), 200.0],
    }, index=index)
    signal = SimpleNamespace(direction=1, entry=29_501.0, sl=29_496.0, tp=29_511.0)
    module = SimpleNamespace(
        name="SWEEP_CORE_AVOID_MID_VWAP",
        detect=lambda df: signal,
    )
    monkeypatch.setattr(telegram_brief, "default_modules", lambda: [module])

    kanit = telegram_brief.SweepKaniti(10, 0.613, True, "pozitif")
    sonuc = telegram_brief._anlik_nasdaq(
        now, fetch=lambda *a, **k: frame, kanit=kanit)

    assert "yukari trend" in sonuc.teknik
    assert sonuc.hacim == (
        "Hacim: ayni 15dk saat dilimi normalinin 2.0x'i; "
        "olagandisi ve trendi destekliyor"
    )
    assert "ADAY - NQ proxy Sweep LONG" in sonuc.firsat
    assert "MT5 US100 15dk grafikte ayni sweep ve yonu dogrula" in sonuc.firsat
    assert "giris P+1.0, stop P-4.0, hedef P+11.0" in sonuc.firsat
    assert "5 dk gecikme" in sonuc.veri


def test_hacim_acilis_periyodunu_anormal_sanmaz():
    index = pd.date_range(
        start="2026-08-10 13:00:00+00:00",
        end="2026-09-10 13:30:00+00:00",
        freq="15min",
    )
    new_york = index.tz_convert("America/New_York")
    acilis = (new_york.hour == 9) & (new_york.minute == 30)
    hacim = np.where(acilis, 200.0, 100.0)
    frame = pd.DataFrame({"volume": hacim}, index=index)

    oran = telegram_brief._ayni_saat_hacim_orani(frame)

    assert oran == 1.0


def test_hacim_new_york_saatiyle_dst_gecisinde_ayni_kutuyu_bulur():
    index = pd.date_range(
        start="2026-10-01 09:30",
        end="2026-11-20 09:30",
        freq="B",
        tz="America/New_York",
    ).tz_convert("UTC")
    frame = pd.DataFrame({"volume": 100.0}, index=index)
    frame.iloc[-1, 0] = 130.0

    oran = telegram_brief._ayni_saat_hacim_orani(frame)

    assert oran == 1.3


def test_hacim_ayni_saatteki_gercek_sicramayi_bulur():
    index = pd.date_range(
        start="2026-08-10 13:00:00+00:00",
        end="2026-09-10 15:00:00+00:00",
        freq="15min",
    )
    frame = pd.DataFrame({"volume": 100.0}, index=index)
    frame.iloc[-1, 0] = 175.0

    oran = telegram_brief._ayni_saat_hacim_orani(frame)

    assert oran == 1.75


def test_sweep_setup_kanit_yokken_gercek_islem_adayi_olmaz(monkeypatch):
    now = datetime(2026, 9, 10, 15, 20, tzinfo=UTC)
    index = pd.date_range(end="2026-09-10 15:00:00+00:00", periods=540, freq="15min")
    close = np.linspace(29_000.0, 29_500.0, len(index))
    frame = pd.DataFrame({
        "open": close - 1,
        "high": close + 3,
        "low": close - 3,
        "close": close,
        "volume": np.full(len(index), 100.0),
    }, index=index)
    signal = SimpleNamespace(direction=1, entry=29_501.0, sl=29_496.0, tp=29_511.0)
    module = SimpleNamespace(
        name="SWEEP_CORE_AVOID_MID_VWAP", detect=lambda df: signal)
    monkeypatch.setattr(telegram_brief, "default_modules", lambda: [module])
    kanit = telegram_brief.SweepKaniti(
        25, -0.01, False, "dogrulanmis pozitif LIVE yontem yok")

    sonuc = telegram_brief._anlik_nasdaq(
        now, fetch=lambda *a, **k: frame, kanit=kanit)

    assert "GORULDU - NQ proxy Sweep LONG" in sonuc.firsat
    assert "gercek islem adayi degildir" in sonuc.firsat
    assert "giris P" not in sonuc.firsat


def test_nyse_tatili_ve_erken_kapanisi_bilir():
    tatil = telegram_brief._seans_satiri(
        datetime(2026, 9, 7, 15, 0, tzinfo=UTC))
    erken = telegram_brief._seans_satiri(
        datetime(2026, 11, 27, 17, 30, tzinfo=UTC))

    assert "NYSE tatili; nakit seans kapali" in tatil
    assert "erken kapanis 13:00" in erken
    assert "kapanisa 30 dk" in erken


def test_cli_iki_ayri_dosya_yazar(monkeypatch, tmp_path):
    _sabit(monkeypatch)
    monkeypatch.setattr(telegram_brief, "takvim_olgusu", lambda: ([], []))
    monkeypatch.setattr(telegram_brief.market_context, "collect", lambda *a, **k: {})
    monkeypatch.setattr(telegram_brief, "DEFAULT_STATE", tmp_path / "yok.json")
    monkeypatch.setattr("sys.argv", ["telegram_brief", "--cikti-dir", str(tmp_path)])

    telegram_brief.main()

    assert (tmp_path / "durum.txt").read_text(encoding="utf-8").startswith("MAVEN DURUMU")
    assert (tmp_path / "brief.txt").read_text(encoding="utf-8").startswith("PİYASA ŞİMDİ")
