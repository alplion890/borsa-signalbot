"""Elenenler katalogunun butunlugu.

Katalogun degeri, her maddenin bir OLCUME dayanmasindan geliyor. "Bence
calismaz" maddesi girerse katalog fikir listesine doner ve veto araci olmaktan
cikar. Buradaki testler o cizgiyi koruyor.
"""
from __future__ import annotations

import re

import pytest

from .elenenler import KATALOG, YAPILAR, ara


def test_katalog_bos_degil():
    assert len(KATALOG) >= 10


def test_id_tekrari_yok():
    idler = [x.id for x in KATALOG]
    assert len(idler) == len(set(idler)), f"tekrarli id: {idler}"


@pytest.mark.parametrize("x", KATALOG, ids=lambda x: x.id)
def test_her_madde_SAYI_iceriyor(x):
    """Olcum alani rakam icermeli -- 'bence calismaz' katalog maddesi degildir."""
    assert re.search(r"\d", x.olcum), f"{x.id}: olcum alaninda sayi yok"


@pytest.mark.parametrize("x", KATALOG, ids=lambda x: x.id)
def test_her_madde_KAYNAK_gosteriyor(x):
    """Nerede olculdugu yazmayan madde denetlenemez."""
    assert x.kaynak.strip(), f"{x.id}: kaynak bos"
    assert (".py" in x.kaynak) or ("[[" in x.kaynak), (
        f"{x.id}: kaynak ne dosya ne vault notu -- izlenemez")


@pytest.mark.parametrize("x", KATALOG, ids=lambda x: x.id)
def test_her_madde_TARIHLI(x):
    assert re.match(r"\d{4}-\d{2}-\d{2}", x.tarih), f"{x.id}: tarih formati"


@pytest.mark.parametrize("x", KATALOG, ids=lambda x: x.id)
def test_her_madde_ANAHTAR_tasiyor(x):
    """Anahtari olmayan madde aramada bulunamaz, yani hic yok gibidir."""
    assert x.anahtarlar, f"{x.id}: anahtar listesi bos"


@pytest.mark.parametrize("x", KATALOG, ids=lambda x: x.id)
def test_hicbir_madde_TERSINI_AL_demiyor(x):
    """Katalog VETO araci. 'Tersini al' onerisi buraya giremez.

    Gerekce modul docstring'inde: R'nin isaretini cevirerek ters stratejiyi
    hesaplayamazsin (stop/hedef asimetrik). Ters strateji yeni backtest,
    yani yeni hipotez, yani butce.
    """
    metin = f"{x.iddia} {x.olcum} {x.neden}".lower()
    for yasak in ("tersini al", "ters isleme gir", "tam tersi calisir"):
        assert yasak not in metin, f"{x.id}: katalog sinyal onermemeli ({yasak})"


def test_arama_fvg_bulur():
    e, _ = ara("fvg")
    assert any(x.id == "fvg_doldurma" for x in e)


def test_arama_ict_smc_fvg_maddesine_gider():
    """Kullanici 'ICT gordum' derse FVG olcumune ulasmali."""
    e, _ = ara("ict")
    assert any(x.id == "fvg_doldurma" for x in e)


def test_arama_bulunmayan_sorgu_BOS_doner():
    """Bulamamak 'calisir' demek degil -- CLI bunu ayrica soyluyor."""
    e, y = ara("zzzz_olmayan_bir_sey")
    assert not e and not y


def test_yapisal_bulgular_UYARI_tasiyor():
    """Yapisal bulgu giris kurali sanilirsa katalog zarar verir."""
    for y in YAPILAR:
        assert y.uyari.strip(), f"{y.baslik}: uyari bos"
        assert re.search(r"\d", y.olcum), f"{y.baslik}: olcumde sayi yok"


def test_btc_maddesi_forward_tersligini_kaydediyor():
    """Projenin en net backtest-forward ayrismasi kayitli kalmali."""
    e, _ = ara("btc")
    btc = next(x for x in e if x.id == "btc_absorption")
    assert "-0.326" in btc.olcum and "0.073" in btc.iddia


def test_fomc_maddesi_literaturu_CURUTMUS_gibi_yazmiyor():
    """Null sonucun fazla okunmasi da bir hata bicimi."""
    e, _ = ara("fomc")
    f = next(x for x in e if x.id == "fomc_oncesi_drift")
    assert "CURUTMEZ" in f.neden or "curutmez" in f.neden.lower()
