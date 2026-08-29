"""Parite raporu — yanlis pencere karsilastirmasi bir daha yapilmasin."""
from __future__ import annotations

import pandas as pd

from .cloud_parity import match, summarize


def _row(mod, t, r, status="tp", symbol="NASDAQ100", dir=1):
    # symbol/dir kimlik alani: tolerans icinde zit yonlu ya da baska sembolde
    # AYRI islemler olabiliyor (Hermes denetimi 2026-08-28, BULGU 2).
    return {"module": mod, "entry_time": pd.Timestamp(t), "r": r,
            "status": status, "symbol": symbol, "dir": dir}


def test_MT5_in_eski_kayitlari_kayip_islem_sayilmaz():
    """Bulut defteri dun basladiysa, MT5'in mayis kayitlari 'eksik' degildir.

    Ilk olcumde tam bu hata yapildi: toplamlar yan yana konunca bulut
    defteri feed'i temsil etmiyor gibi gorundu.
    """
    cloud = pd.DataFrame([_row("M", "2026-08-19 10:00", 1.0)])
    mt5 = pd.DataFrame([_row("M", "2026-05-01 10:00", -1.0),
                        _row("M", "2026-08-19 10:00", 1.0)])
    res = match(cloud, mt5)
    assert len(res["matched"]) == 1
    assert res["only_mt5"].empty


def test_tolerans_disindaki_islem_eslesmez():
    cloud = pd.DataFrame([_row("M", "2026-08-19 10:00", 1.0)])
    mt5 = pd.DataFrame([_row("M", "2026-08-19 14:00", 1.0)])
    res = match(cloud, mt5)
    assert res["matched"].empty
    assert len(res["only_cloud"]) == 1 and len(res["only_mt5"]) == 1


def test_bir_MT5_islemi_iki_kere_eslesmez():
    cloud = pd.DataFrame([_row("M", "2026-08-19 10:00", 1.0),
                          _row("M", "2026-08-19 10:20", 1.0)])
    mt5 = pd.DataFrame([_row("M", "2026-08-19 10:05", 1.0)])
    res = match(cloud, mt5)
    assert len(res["matched"]) == 1
    assert len(res["only_cloud"]) == 1


def test_ozet_ayni_sonuclari_sayar():
    cloud = pd.DataFrame([_row("M", "2026-08-19 10:00", 1.0, "tp"),
                          _row("M", "2026-08-19 12:00", -1.0, "sl")])
    mt5 = pd.DataFrame([_row("M", "2026-08-19 10:00", 1.1, "tp"),
                        _row("M", "2026-08-19 12:00", 1.2, "tp")])
    s = summarize(match(cloud, mt5)["matched"])
    assert s.loc["M", "n"] == 2
    assert s.loc["M", "ayni_sonuc"] == 1
