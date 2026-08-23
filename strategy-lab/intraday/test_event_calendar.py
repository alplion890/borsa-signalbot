"""Olay takvimi kurallari -- tarih listesi sessizce bozulursa burada patlar."""
from __future__ import annotations

from datetime import date, time

import pytest

from .event_calendar import cpi_events, fomc_events, nfp_events


def test_fomc_gunleri_tekrarsiz():
    gunler = [e.gun for e in fomc_events()]
    assert len(gunler) == len(set(gunler)), "ayni gun iki kez listelenmis"


def test_fomc_gunleri_sirali():
    gunler = [e.gun for e in fomc_events()]
    assert gunler == sorted(gunler)


def test_her_yil_sekiz_toplanti_2020_HARIC():
    """FOMC yilda 8 duzenli toplanti yapar. Sapma = eksik/fazla tarih.

    2020 tek istisna: 17-18 Mart toplantisi IPTAL edildi (yerine 15 Mart
    plansiz acil toplantisi yapildi, o da onceden bilinemezdi -> listede yok).
    Yani 2020'de gerceklesen duzenli toplanti sayisi 7.
    """
    from collections import Counter
    sayim = Counter(e.gun.year for e in fomc_events())
    for yil in range(2012, 2027):
        beklenen = 7 if yil == 2020 else 8
        assert sayim[yil] == beklenen, f"{yil}: {sayim[yil]}, {beklenen} bekleniyordu"


def test_fomc_hicbiri_haftasonu_degil():
    for e in fomc_events():
        assert e.gun.weekday() < 5, f"{e.gun} haftasonuna dusmus"


def test_2013_mart_sonrasi_hepsi_saat_14_00():
    """2013-03-13 duyurusu sonrasi tum duzenli metinler 14:00 ET."""
    for e in fomc_events():
        if e.gun >= date(2013, 3, 20):
            assert e.aciklama_et == time(14, 0), f"{e.gun}: {e.aciklama_et}"
            assert not e.erken_aciklama


def test_2012_basin_toplantili_gunler_ERKEN_isaretli():
    """13:55 cikis kuralinin kirildigi gunler acikca isaretli olmali.

    Bu gunler sessizce 14:00 varsayilirsa pozisyon duyuruyu TASIR --
    hipotezin 'fat-tail'e bilerek girme' varsayimi ihlal edilir.
    """
    erken = {e.gun for e in fomc_events() if e.erken_aciklama}
    assert date(2012, 1, 25) in erken
    assert date(2012, 12, 12) in erken
    assert len(erken) == 9, f"beklenen 9 erken gun, bulunan {len(erken)}"


def test_erken_gunlerin_hepsi_2013_martindan_once():
    for e in fomc_events():
        if e.erken_aciklama:
            assert e.gun < date(2013, 3, 20), f"{e.gun} erken isaretli ama yeni rejimde"


@pytest.mark.parametrize("fn", [cpi_events, nfp_events])
def test_cpi_nfp_HENUZ_YOK_ve_sessizce_bos_donmuyor(fn):
    """Veri yoksa bos liste degil HATA donmeli.

    Bos liste donen bir takvim, 'CPI gunu hic olmadi' anlamina gelir ve
    backtest sessizce 0 islemle gecer -- hata gorunmez olur.
    """
    with pytest.raises(NotImplementedError):
        fn()
