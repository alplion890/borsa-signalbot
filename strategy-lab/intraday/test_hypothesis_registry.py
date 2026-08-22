"""On-kayit defteri kurallari -- iki arastirmacinin butcesi ortak kalmali."""
from __future__ import annotations

import json

import pytest

from .hypothesis_registry import (
    AYLIK_TAVAN,
    GECERLI_DURUM,
    ZORUNLU_ALANLAR,
    aylik_sayim,
    kapasite_var_mi,
    load,
    toplam_deneme,
)


def _kayit(**kw) -> dict:
    temel = {
        "id": "test_hipotez", "tarih": "2026-09-01", "yazan": "claude",
        "neden_var": "yapisal sebep", "enstruman": "NASDAQ100", "tutus": "1 gun",
        "min_n": 30, "deneme_sayisi": 12, "durum": "kayitli",
    }
    temel.update(kw)
    return temel


def test_aylik_tavan_IKI_ARASTIRMACININ_TOPLAMI():
    """Claude 2 + Hermes 2 = 4 degil; tavan ortak."""
    kayitlar = [_kayit(id="a", yazan="claude"), _kayit(id="b", yazan="hermes")]
    var, mesaj = kapasite_var_mi(kayitlar, "2026-09-15")
    assert not var, f"tavan asilmis olmali: {mesaj}"


def test_tavan_dolmadan_kapasite_var():
    var, _ = kapasite_var_mi([_kayit(id="a")], "2026-09-15")
    assert var


def test_ay_degisince_kapasite_yenilenir():
    kayitlar = [_kayit(id="a"), _kayit(id="b")]
    var, _ = kapasite_var_mi(kayitlar, "2026-10-01")
    assert var


def test_elenen_hipotezler_de_DENEME_sayisina_girer():
    """9 fikir eleyip 10.'yu adopte etmek, 1 fikir denemekle ayni degil."""
    kayitlar = [_kayit(id="a", durum="elendi", deneme_sayisi=40),
                _kayit(id="b", durum="adopte", deneme_sayisi=10)]
    assert toplam_deneme(kayitlar) == 50


def test_gercek_defter_SEMA_uyumlu():
    """Repodaki gercek dosya bozuksa burada patlar."""
    for k in load():
        eksik = ZORUNLU_ALANLAR - set(k)
        assert not eksik, f"{k.get('id', '?')} eksik alan: {eksik}"
        assert k["durum"] in GECERLI_DURUM, f"{k['id']}: gecersiz durum {k['durum']}"
        assert int(k["deneme_sayisi"]) >= 1, f"{k['id']}: deneme_sayisi >= 1 olmali"
        assert len(k["neden_var"]) >= 20, (
            f"{k['id']}: 'neden_var' cok kisa. Yapisal sebep yazilmali; "
            "'backtest iyi cikti' gecerli bir sebep degil.")


def test_gercek_defterde_ID_tekrari_yok():
    idler = [k["id"] for k in load()]
    assert len(idler) == len(set(idler)), f"tekrarli id: {idler}"


def test_gercek_defter_aylik_tavani_asmiyor():
    for ay, adet in aylik_sayim(load()).items():
        assert adet <= AYLIK_TAVAN, f"{ay}: {adet} hipotez, tavan {AYLIK_TAVAN}"


def test_kosulmus_hipotez_SONUC_tasimali():
    """Kosulup sonucu yazilmayan hipotez, sessizce unutulan hipotezdir."""
    for k in load():
        if k["durum"] in {"kosuldu", "elendi", "adopte"}:
            assert k.get("sonuc"), f"{k['id']}: durum={k['durum']} ama 'sonuc' yok"
