from __future__ import annotations

from datetime import datetime, time, timezone
from types import SimpleNamespace

import numpy as np
import pandas as pd

from ..event_calendar import MacroEvent
from . import telegram_brief

UTC = timezone.utc

_PIYASA = telegram_brief.PiyasaOzeti(
    teknik=(
        "Nasdaq vadeli, 15 dakikalık görünüm: kısa vadeli hareket yukarı ve "
        "belirgin. Fiyat bugünkü ortalama işlem fiyatının üzerinde; son 1 "
        "saat değişimi +0.42%."
    ),
    hacim=(
        "İşlem hacmi: Önceki işlem günlerinde aynı saatte görülen normal "
        "hacmin 1.6 katı; alışılmadık yüksek ve fiyat hareketini destekliyor."
    ),
    firsat=(
        "Yok — Nasdaq vadeli grafiğinde ölçülmüş kısa taşma ve geri dönüş "
        "koşulu oluşmadı."
    ),
    veri=(
        "Veri zamanı: Nasdaq vadeli işlemlerinin son tamamlanmış 15 dakikalık "
        "mumu 18:00 TR; veri 5 dakika gecikmeli."
    ),
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
    assert "Hesap aşaması: Maven 5K değerlendirme hesabı" in metin
    assert "Gerçek para bölümü (LIVE): Yok" in metin
    assert "Deneme bölümü (PAPER — gerçek para değil): bulut kaydı güncel değil" in metin
    assert "mumu 18:00 TR; veri 5 dakika gecikmeli" in metin
    assert "Hesap bakiyesi: Sistem uzaktan göremiyor" in metin
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

    assert "kısa vadeli hareket yukarı ve belirgin" in metin
    assert "Şu anki fırsat: Yok" in metin
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

    assert "kısa vadeli hareket yukarı ve belirgin" in metin
    assert "normal hacmin 1.6 katı" in metin
    assert "Şu anki fırsat: Yok" in metin
    assert "bağımsız ileri testte 10 işlem" in metin
    assert "başlangıçta göze alınan tutarın +0.613 katı" in metin
    assert "NASDAQ100 Açılış Kırılımı" not in metin
    assert "GBPUSD London Trend" not in metin
    assert "2026-09-11 ABD tüketici enflasyonu: 15:30 TR" in metin
    assert "BUGÜN ABD üretici enflasyonu: 15:30 TR" in metin
    assert "Federal Reserve publishes policy statement" not in metin
    for teknik_kisaltma in ("NQ", "ADX", "VWAP", "exp_R", "proxy", "2Y", "DXY", "VIX"):
        assert teknik_kisaltma not in metin
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

    assert "Olumlu sonucu doğrulanmış bir gerçek para yöntemi yok" in metin


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
    assert "Gerçek para bölümü (LIVE): Yok" in durum
    assert "bağımsız ileri testte 10 işlem" in edge


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

    assert metin.count("ABD tüketici enflasyonu") == 1
    assert "Consumer Price Index" not in metin


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

    assert "kısa vadeli hareket yukarı" in sonuc.teknik
    assert sonuc.hacim == (
        "İşlem hacmi: Önceki işlem günlerinde aynı saatte görülen normal "
        "hacmin 2.0 katı; alışılmadık yüksek ve fiyat hareketini destekliyor."
    )
    assert "Aday var" in sonuc.firsat
    assert "Maven US100 15 dakikalık grafikte aynı hareketi doğrula" in sonuc.firsat
    assert "giriş +1.0 puan, zarar durdur -4.0 puan, hedef +11.0 puan" in sonuc.firsat
    assert "veri 5 dakika gecikmeli" in sonuc.veri


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

    assert "alış yönünde kısa taşma ve geri dönüş görüldü" in sonuc.firsat
    assert "gerçek işlem adayı değildir" in sonuc.firsat
    assert "giriş" not in sonuc.firsat


def test_lse_yedek_baglam_verir_ama_live_aday_uretmez(monkeypatch):
    now = datetime(2026, 9, 10, 15, 20, tzinfo=UTC)
    index = pd.date_range(end="2026-09-10 15:00:00+00:00", periods=540, freq="15min")
    close = np.linspace(29_000.0, 29_500.0, len(index))
    frame = pd.DataFrame({
        "open": close - 1, "high": close + 3, "low": close - 3,
        "close": close, "volume": np.full(len(index), 100.0),
    }, index=index)
    frame.attrs["fallback_role"] = "LSE yedek"
    module = SimpleNamespace(
        name="SWEEP_CORE_AVOID_MID_VWAP",
        detect=lambda df: SimpleNamespace(direction=1, entry=1, sl=0, tp=2),
    )
    monkeypatch.setattr(telegram_brief, "default_modules", lambda: [module])

    sonuc = telegram_brief._anlik_nasdaq(
        now, fetch=lambda *a, **k: frame,
        kanit=telegram_brief.SweepKaniti(10, .613, True, "pozitif"),
    )

    assert "LSE yedek veri yalnız trend ve hacim bağlamıdır" in sonuc.firsat
    assert "Aday var" not in sonuc.firsat
    assert "LSE NQ.F yedeğinin" in sonuc.veri


def test_nyse_tatili_ve_erken_kapanisi_bilir():
    tatil = telegram_brief._seans_satiri(
        datetime(2026, 9, 7, 15, 0, tzinfo=UTC))
    erken = telegram_brief._seans_satiri(
        datetime(2026, 11, 27, 17, 30, tzinfo=UTC))

    assert "ABD borsası tatil; normal seans kapalı" in tatil
    assert "erken kapanış 13:00" in erken
    assert "kapanışa 30 dakika" in erken


def test_cli_iki_ayri_dosya_yazar(monkeypatch, tmp_path):
    _sabit(monkeypatch)
    monkeypatch.setattr(telegram_brief, "takvim_olgusu", lambda: ([], []))
    monkeypatch.setattr(telegram_brief.market_context, "collect", lambda *a, **k: {})
    monkeypatch.setattr(telegram_brief, "DEFAULT_STATE", tmp_path / "yok.json")
    monkeypatch.setattr("sys.argv", ["telegram_brief", "--cikti-dir", str(tmp_path)])

    telegram_brief.main()

    assert (tmp_path / "durum.txt").read_text(encoding="utf-8").startswith("MAVEN KISA DURUM")
    assert (tmp_path / "brief.txt").read_text(encoding="utf-8").startswith("BUGÜNÜN PİYASA ÖZETİ")
