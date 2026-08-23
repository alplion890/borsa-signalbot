"""Diskresyoner defterin kurallari -- gevsetilirse defter degerini kaybeder."""
from __future__ import annotations

import pytest

from .diskresyoner import MIN_N, ac, kapat, ozet, yukle


@pytest.fixture
def defter(tmp_path):
    return tmp_path / "diskresyoner_defter.csv"


def _ac(defter, **kw):
    varsayilan = dict(
        sembol="US100", yon="short", giris=25000.0, stop=25120.0,
        tez="makro haber negatif, fiyat 200EMA ustunde pahali bolgede",
        curuten="200EMA uzerinde gunluk kapanis gelirse tez yanlis",
        path=defter,
    )
    varsayilan.update(kw)
    return ac(**varsayilan)


def test_tez_kisaysa_islem_ACILMAZ(defter):
    """'iyi gorunuyor' tez degildir. Bu alan defterin tek dogrulamasi."""
    with pytest.raises(ValueError, match="tez"):
        _ac(defter, tez="iyi duruyor")


def test_curuten_alani_ZORUNLU(defter):
    """Tezi ne yanlislar? Onsuz her sonuc sonradan aciklanabilir."""
    with pytest.raises(ValueError, match="curuten"):
        _ac(defter, curuten="bilmiyorum")


def test_stop_yonle_TUTARLI_olmali(defter):
    with pytest.raises(ValueError, match="short"):
        _ac(defter, yon="short", giris=25000.0, stop=24900.0)
    with pytest.raises(ValueError, match="long"):
        _ac(defter, yon="long", giris=25000.0, stop=25100.0)


def test_ayni_anda_TEK_islem(defter):
    """Maven slot kisiti: acik islem varken ikincisi acilamaz."""
    _ac(defter)
    with pytest.raises(ValueError, match="acik islem"):
        _ac(defter, sembol="XAUUSD")


def test_R_stop_mesafesine_gore_hesaplanir(defter):
    i = _ac(defter, yon="short", giris=25000.0, stop=25100.0)  # risk 100
    k = kapat(i.id, cikis=24800.0, path=defter)                # 200 lehte
    assert k.r == pytest.approx(2.0)


def test_long_kayip_negatif_R(defter):
    i = _ac(defter, yon="long", giris=100.0, stop=90.0,
            tez="destek bolgesinden donus bekleniyor, hacim artiyor",
            curuten="destegin altinda kapanis gelirse tez yanlis")
    k = kapat(i.id, cikis=90.0, path=defter)
    assert k.r == pytest.approx(-1.0)


def test_kapali_islem_TEKRAR_kapanmaz(defter):
    i = _ac(defter)
    kapat(i.id, cikis=24800.0, path=defter)
    with pytest.raises(ValueError, match="zaten kapali"):
        kapat(i.id, cikis=24700.0, path=defter)


def test_tez_ve_curuten_deftere_YAZILIR(defter):
    """Sonradan okunamayan tez, tez degildir."""
    _ac(defter, tez="makro negatif, DXY guclu, endeks pahali bolgede islem goruyor",
        curuten="DXY 200EMA altina duserse makro tez cokmus olur")
    kayit = yukle(defter)[0]
    assert "DXY" in kayit.tez
    assert "DXY" in kayit.curuten


def test_ozet_bos_defterde_patlamaz(defter):
    o = ozet(defter)
    assert o["n"] == 0 and not o["durma_tetik"]


def test_durma_esigi_ALTINDA_tetiklenmez(defter):
    """n<20 iken negatif olmak durdurmaz -- erken durma da hatadir."""
    for _ in range(MIN_N - 1):
        i = _ac(defter, yon="long", giris=100.0, stop=90.0,
                tez="destek bolgesinden donus bekleniyor, hacim artiyor",
                curuten="destegin altinda kapanis gelirse tez yanlis")
        kapat(i.id, cikis=90.0, path=defter)
    o = ozet(defter)
    assert o["n"] == MIN_N - 1 and o["exp_R"] < 0
    assert not o["durma_tetik"], "esik gelmeden durma tetiklenmemeli"


def test_durma_esiginde_negatifse_TETIKLENIR(defter):
    for _ in range(MIN_N):
        i = _ac(defter, yon="long", giris=100.0, stop=90.0,
                tez="destek bolgesinden donus bekleniyor, hacim artiyor",
                curuten="destegin altinda kapanis gelirse tez yanlis")
        kapat(i.id, cikis=90.0, path=defter)
    assert ozet(defter)["durma_tetik"]


def test_esikte_POZITIFSE_tetiklenmez(defter):
    for _ in range(MIN_N):
        i = _ac(defter, yon="long", giris=100.0, stop=90.0,
                tez="destek bolgesinden donus bekleniyor, hacim artiyor",
                curuten="destegin altinda kapanis gelirse tez yanlis")
        kapat(i.id, cikis=120.0, path=defter)
    o = ozet(defter)
    assert o["exp_R"] > 0 and not o["durma_tetik"]
