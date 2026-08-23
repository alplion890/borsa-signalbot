"""Olay takvimi kurallari -- tarih listesi sessizce bozulursa burada patlar."""
from __future__ import annotations

from datetime import date, time

import pytest

from .event_calendar import all_events, cpi_events, fomc_events, nfp_events


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
def test_bls_yayinlari_ayda_TEK(fn):
    """Ayda birden fazla yayin = revizyon elenmemis demektir.

    FRED bir release altinda yillik revizyonlari da listeler (ornek:
    2024-02-09 CPI mevsimsel duzeltme revizyonu vs 2024-02-13 gercek Ocak
    CPI'i). `event_calendar_fetch` bunlari eliyor; elemezse burada patlar.
    """
    from collections import Counter
    sayim = Counter((e.gun.year, e.gun.month) for e in fn())
    fazla = {k: v for k, v in sayim.items() if v > 1}
    assert not fazla, f"ayda birden fazla yayin: {fazla}"


@pytest.mark.parametrize("fn", [cpi_events, nfp_events])
def test_bls_yayinlari_haftaici_ve_sirali(fn):
    gunler = [e.gun for e in fn()]
    assert gunler == sorted(gunler)
    assert len(gunler) == len(set(gunler))
    for g in gunler:
        assert g.weekday() < 5, f"{g} haftasonuna dusmus"


@pytest.mark.parametrize("fn", [cpi_events, nfp_events])
def test_bls_saati_0830_ET(fn):
    for e in fn():
        assert e.aciklama_et == time(8, 30), f"{e.gun}: {e.aciklama_et}"


def test_2025_kapanma_bosluklari_KORUNUYOR():
    """2025 hukumet kapanmasi CPI Kasim / NFP Ekim yayinlarini dusurdu.

    Bu bosluk GERCEK. 'Her ay bir yayin olmali' diye doldurmak, olmayan bir
    olay gunune islem acmak demektir. Bosluk korunuyor mu diye kilitliyoruz.
    """
    cpi_2025 = {e.gun.month for e in cpi_events() if e.gun.year == 2025}
    nfp_2025 = {e.gun.month for e in nfp_events() if e.gun.year == 2025}
    assert 11 not in cpi_2025, "2025 Kasim CPI yayini yok olmali (kapanma)"
    assert 10 not in nfp_2025, "2025 Ekim NFP yayini yok olmali (kapanma)"


def test_ayni_gun_CPI_ve_NFP_ikisi_birden_SAYILMAZ():
    """On-kayit kurali: ayni gune duserlerse gun CPI sayilir, NFP atlanir."""
    hepsi = all_events()
    nfp_gunleri = {e.gun for e in hepsi if e.tip == "NFP"}
    cpi_gunleri = {e.gun for e in hepsi if e.tip == "CPI"}
    assert not (nfp_gunleri & cpi_gunleri), "ayni gun hem CPI hem NFP sayilmis"


def test_all_events_sirali_ve_uc_tipi_de_iceriyor():
    hepsi = all_events()
    assert [e.gun for e in hepsi] == sorted(e.gun for e in hepsi)
    assert {e.tip for e in hepsi} == {"FOMC", "CPI", "NFP"}
