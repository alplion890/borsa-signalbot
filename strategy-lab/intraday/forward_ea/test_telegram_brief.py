from __future__ import annotations

from datetime import datetime, time, timezone

from ..event_calendar import MacroEvent
from . import telegram_brief

UTC = timezone.utc


def _sabit(monkeypatch):
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
    assert "Fon profili (repo ayari): Maven BNPL challenge" in metin
    assert "LIVE: SWEEP_CORE_AVOID_MID_VWAP: n=10, exp_R=+0.613R" in metin
    assert "PAPER: NQ_ORB_STRONG_TREND: n=25, exp_R=-0.106R" in metin
    assert "CAND_BTC_ABSORPTION BTCUSDT SHORT [PAPER; gercek risk yok]" in metin
    assert "state 15:00 TR, BAYAT 80 dk" in metin
    assert "Guncel broker bakiyesi buluttan okunmuyor" in metin
    assert "exit<entry olan 2 satir kanita ALINMADI" in metin
    assert "Otomatik emir YOK" in metin
    assert len(metin) < 4096


def test_edge_mesaji_yalniz_olculmus_live_teknigi_ve_resmi_takvimi_yazar(monkeypatch):
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

    metin = telegram_brief.edge_mesaji(datetime(2026, 9, 10, 15, 15, tzinfo=UTC))

    assert "Tek pozitif LIVE teknik: NASDAQ100 15dk likidite sweep + VWAP yonu + ADX>25" in metin
    assert "forward: n=10, exp_R=+0.613R" in metin
    assert "CPI: 15:30 TR (08:30 ET)" in metin
    assert "BUGUN Producer Price Index: 15:30 TR" in metin
    assert "Fed+BLS/BEA" in metin
    assert "Son resmi baslik: Federal Reserve publishes policy statement" in metin
    assert "Orneklem kucuk" in metin
    assert "FVG/EMA/VWAP sinyal sayilmaz" in metin
    assert len(metin) < 4096


def test_edge_negatifse_teknigi_edge_diye_sunmaz(monkeypatch):
    monkeypatch.setattr(telegram_brief, "_stats", lambda: telegram_brief.KanitOzeti({
        "SWEEP_CORE_AVOID_MID_VWAP": (25, -0.01),
    }))
    monkeypatch.setattr(telegram_brief.market_context, "collect", lambda *a, **k: {})
    monkeypatch.setattr(telegram_brief, "takvim_olgusu", lambda: ([], []))

    metin = telegram_brief.edge_mesaji(datetime(2026, 9, 10, 15, 15, tzinfo=UTC))

    assert "Dogrulanmis pozitif LIVE edge YOK" in metin
    assert "Tek pozitif LIVE teknik" not in metin


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

    assert (tmp_path / "durum.txt").read_text(encoding="utf-8").startswith("1/2")
    assert (tmp_path / "brief.txt").read_text(encoding="utf-8").startswith("2/2")
