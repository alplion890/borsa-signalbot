"""Telefon brifingi OLGU kalmali, ikinci bir olgu ureticisi olmamali.

NEDEN BU TESTLER: brifing telefondaki asistan tarafindan SESLI okunacak.
Oraya bir yorum sifati sizarsa ("guclu trend", "pahali bolge"), kullanici onu
kendi yorumu sanip uzerine islem kurar -- diskresyoner deneyin olctugu sey tam
da kullanicinin kendi yorumu oldugu icin, bu deneyi sessizce bozar.
"""
from __future__ import annotations

import re
from datetime import datetime, timezone

import pandas as pd
import pytest

from . import telefon_brief
from .seans_brief import sembol_olgusu

UTC = timezone.utc

# "Olgu" degil "yorum" olan kelimeler. Sayi ve tarih serbest; bunlar degil.
YORUM_SIFATLARI = (
    "guclu", "zayif", "pahali", "ucuz", "asiri", "firsat", "riskli",
    "olumlu", "olumsuz", "pozitif gorunum", "negatif gorunum",
    "long ac", "short ac", "onerilir", "beklenir",
    "muhtemelen", "gorunuyor ki",
)

# Emir KALIPLARI aranir. Tek basina "al"/"sat" taramak fazla kaba: uyari
# metnindeki "farki kendin hesapla" ya da katalogdaki "sicrama al" tezi
# yorum degildir. Aranan sey, brifingin OKUYANA IS BUYURMASI.
YORUM_FIILLERI = (
    r"\bal sinyali\b", r"\bsat sinyali\b", r"\balim yap", r"\bsatim yap",
    r"long (ac|gir)", r"short (ac|gir)", r"pozisyon (ac|al)",
    r"\btavsiye", r"\boneri(yorum|lir)",
)


def _bar_serisi(gun: int = 400, baslangic: float = 100.0) -> pd.DataFrame:
    idx = pd.date_range("2025-01-01", periods=gun, freq="1D")
    fiyat = pd.Series(baslangic + pd.Series(range(gun)) * 0.5).to_numpy()
    return pd.DataFrame(
        {"open": fiyat, "high": fiyat + 2, "low": fiyat - 2, "close": fiyat,
         "volume": [1000.0] * gun},
        index=idx,
    )


def test_brief_YORUM_SIFATI_icermez():
    metin = telefon_brief.brief_metni(
        semboller=[], simdi_utc=datetime(2026, 9, 1, 15, 0, tzinfo=UTC)).lower()
    bulunan = [k for k in YORUM_SIFATLARI if k in metin]
    bulunan += [k for k in YORUM_FIILLERI if re.search(k, metin)]
    assert not bulunan, (
        f"brifingde yorum sifati var: {bulunan}. Yorum kullanicinin isi; "
        "asistan bunu tekrarlarsa deney bozulur.")


def test_brief_KAYNAK_ve_BASIS_uyarisi_tasir():
    """Endeks kotasyonu broker fiyati degil -- ~-170 puan basis olculdu."""
    metin = telefon_brief.brief_metni(
        semboller=[], simdi_utc=datetime(2026, 9, 1, 15, 0, tzinfo=UTC))
    assert "broker fiyati DEGIL" in metin
    assert "basis" in metin.lower()


def test_brief_MEKANIK_ve_DISKRESYONER_durumu_yazar():
    metin = telefon_brief.brief_metni(
        semboller=[], simdi_utc=datetime(2026, 9, 1, 15, 0, tzinfo=UTC))
    assert "Mekanik ray" in metin and "dondurulmus" in metin
    assert "Diskresyoner ray" in metin


def test_brief_KATALOG_statusunu_tasir():
    """Telefondaki asistan veto ile 'secilmedi'yi karistirmamali."""
    metin = telefon_brief.brief_metni(
        semboller=[], simdi_utc=datetime(2026, 9, 1, 15, 0, tzinfo=UTC))
    assert "veto DEGIL" in metin, "statu ayrimi brifinge tasinmamis"
    assert "VETO" in metin


def test_IKINCI_olgu_ureticisi_YOK():
    """Alan seti tek yerde: telefon_brief kendi gostergesini hesaplamamali.

    Bu projedeki tekrar eden hata sinifi (whitelist iki kopya, defterin bes
    okuyucusu, iki eslestirici) burada da kolayca olusurdu.
    """
    kaynak = (telefon_brief.__file__)
    metin = open(kaynak, encoding="utf-8").read()
    for yasak in ("def _yuzdelik", "ema(", "atr(", "resample("):
        assert yasak not in metin, (
            f"telefon_brief kendi gostergesini hesapliyor ({yasak}); "
            "olgu uretimi seans_brief.sembol_olgusu'nda kalmali")


# --- kismi gun regresyonu -----------------------------------------------
#
# 2026-09-01: NASDAQ brifingi "ATR 100 gunun %0. yuzdeligi" basiyordu. Sebep:
# bugunun HENUZ KAPANMAMIS gunluk bari gostergelere giriyordu -- yarim gunun
# araligi elbette en dar. Olgu bastigini soyleyen bir dosyada sessiz yalan.


def test_gostergeler_KAPANMAMIS_gunu_saymaz():
    seri = _bar_serisi()
    bugun = pd.Timestamp.now(tz=UTC).tz_localize(None).normalize()
    # Bugun icin YARIM bar: araligi bilerek cok dar.
    kismi = pd.DataFrame(
        {"open": [500.0], "high": [500.1], "low": [499.9], "close": [500.0],
         "volume": [1.0]}, index=[bugun + pd.Timedelta(hours=1)])
    tam_seri = pd.concat([seri, kismi])

    o = sembol_olgusu("X", "1d", veri=lambda s, t: tam_seri)

    kapali_son = seri.iloc[-1]
    assert o.hacim_bugun == kapali_son["volume"], (
        "hacim yarim gunden alinmis")
    assert o.atr_bugun > 1.0, (
        f"ATR yarim gunun araligina dusmus: {o.atr_bugun}")
    # Bugunun ham araligi AYRI alan olarak yine gorunmeli.
    assert o.bugun_yuksek == pytest.approx(500.1)


def test_gunluk_feed_AYRI_verilebilir():
    """yfinance 15m'i 60 gun veriyor; EMA200 o pencereye sigmaz."""
    intraday = _bar_serisi(gun=30, baslangic=900.0)
    gunluk = _bar_serisi(gun=400, baslangic=100.0)

    o = sembol_olgusu("X", "15m",
                      veri=lambda s, t: intraday,
                      gunluk_veri=lambda s: gunluk)

    assert o.son_kapanis == pytest.approx(float(intraday["close"].iloc[-1])), (
        "son kapanis intraday seriden gelmeli")
    assert o.ema200 < 300, (
        f"EMA200 gunluk seriden gelmeli, intraday'den degil: {o.ema200}")


# --- feed hacim vermiyorsa ------------------------------------------------
#
# 2026-09-01, ilk canli telefon seansinda goruldu: EURUSD ve GBPUSD icin brief
# "hacim 0 (20 gunun %0. yuzdeligi)" basiyordu. yfinance spot FX'te hacim
# vermiyor -- son 20 gunun 20'si de sifir. "Hacim cok dusuk" ile "hacim
# olculmemis" ayri seyler; ikincisini birincisi gibi gostermek, katman
# kapisinda hacim katmanini yanlislikla DOLU saydirabilir.


def test_feed_hacim_vermiyorsa_SIFIR_basmaz():
    sifir_hacim = _bar_serisi()
    sifir_hacim["volume"] = 0.0

    o = sembol_olgusu("EURUSD", "1d", veri=lambda s, t: sifir_hacim)

    assert o.hacim_bugun != o.hacim_bugun, "hacim yoksa sayi basilmamali (NaN bekleniyor)"
    assert o.hacim_yuzdelik != o.hacim_yuzdelik


def test_brief_hacim_yoksa_ACIKCA_soyler(monkeypatch):
    sifir_hacim = _bar_serisi()
    sifir_hacim["volume"] = 0.0
    monkeypatch.setattr(telefon_brief, "_bulut_veri", lambda s, t: sifir_hacim)
    monkeypatch.setattr(telefon_brief, "_bulut_gunluk", lambda s: sifir_hacim)

    metin = telefon_brief.brief_metni(
        semboller=[("EURUSD", "5m")],
        simdi_utc=datetime(2026, 9, 1, 15, 0, tzinfo=UTC))

    hacim_satiri = next(l for l in metin.splitlines()
                        if l.startswith("- hacim"))
    assert "HACIM VERMIYOR" in hacim_satiri
    assert "yuzdelig" not in hacim_satiri, (
        f"hacimsiz feed yuzdelik gibi basilmis: {hacim_satiri}")


def test_hacim_VARSA_hala_sayi_basar(monkeypatch):
    """Duzeltme, gercek hacmi olan sembolu bozmamali."""
    hacimli = _bar_serisi()
    monkeypatch.setattr(telefon_brief, "_bulut_veri", lambda s, t: hacimli)
    monkeypatch.setattr(telefon_brief, "_bulut_gunluk", lambda s: hacimli)

    metin = telefon_brief.brief_metni(
        semboller=[("NASDAQ100", "15m")],
        simdi_utc=datetime(2026, 9, 1, 15, 0, tzinfo=UTC))

    assert "hacim (son kapali gun): 1,000" in metin


def test_dusurme_esigi_TRIPWIRE_ile_AYNI_kaynaktan():
    """Brifing "esige 3 islem" derken tripwire baska esikten karar veremez."""
    from ..signalbot.risk import DEMOTION_MIN_N
    from ..signalbot import test_demotion_tripwire as tw

    assert telefon_brief.MIN_N is DEMOTION_MIN_N
    assert tw.MIN_N is DEMOTION_MIN_N
