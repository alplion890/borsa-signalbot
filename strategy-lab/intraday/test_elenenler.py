"""Elenenler katalogunun butunlugu.

Katalogun degeri, her maddenin bir OLCUME dayanmasindan geliyor. "Bence
calismaz" maddesi girerse katalog fikir listesine doner ve veto araci olmaktan
cikar. Buradaki testler o cizgiyi koruyor.
"""
from __future__ import annotations

import re

import pytest

from .elenenler import KATALOG, STATULER, VETO_STATULERI, YAPILAR, ara


def test_katalog_bos_degil():
    assert len(KATALOG) >= 10


def test_id_tekrari_yok():
    idler = [x.id for x in KATALOG]
    assert len(idler) == len(set(idler)), f"tekrarli id: {idler}"


def test_her_madde_ALAN_SOZLESMESINI_saglar():
    """Tek test, tum katalog.

    Once alan basina ayri parametrik test vardi: 13 madde x 6 alan = 78 test.
    Hermes denetimi (2026-08-29) hakli olarak bunu sisme saydi -- hepsi ayni
    seyi soruyordu: "madde olcume dayaniyor mu?". Hangi maddenin bozuk oldugu
    assert mesajinda zaten yaziyor.
    """
    for x in KATALOG:
        assert re.search(r"\d", x.olcum), f"{x.id}: olcum alaninda sayi yok"
        assert x.kaynak.strip(), f"{x.id}: kaynak bos"
        assert (".py" in x.kaynak) or ("[[" in x.kaynak), (
            f"{x.id}: kaynak ne dosya ne vault notu -- izlenemez")
        assert re.match(r"\d{4}-\d{2}-\d{2}", x.tarih), f"{x.id}: tarih formati"
        assert x.anahtarlar, f"{x.id}: anahtar listesi bos"
        # Katalog VETO/kayit araci; "tersini al" onerisi buraya giremez.
        # Gerekce docstring'de: R'nin isaretini cevirerek ters stratejiyi
        # hesaplayamazsin (stop/hedef asimetrik) -- o yeni backtest demek.
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


# --- Hermes denetimi 2026-08-29: statu ayrimi ----------------------------
#
# Ilk surumde her madde "ELENMIS -- BU TEZI KULLANMA" basligina giriyordu.
# Uc kategori hatasi: (a) Donchian metninde "elenmis degil" diyor ama veto gibi
# gorunuyordu, (b) "tek basina edge degil" ile "olcum negatif" ayni sayiliyordu,
# (c) isim benzerligi calisan modulleri vetoluyordu (sweep -> SWEEP_CORE,
# orb -> canli NQ_ORB).


def test_her_maddenin_GECERLI_statusu_var():
    from .elenenler import STATULER
    for x in KATALOG:
        assert x.statu in STATULER, f"{x.id}: bilinmeyen statu {x.statu}"


def test_bilinmeyen_statu_KABUL_EDILMEZ():
    from .elenenler import Elenen
    with pytest.raises(ValueError, match="statu"):
        Elenen(id="x", statu="uydurma", baslik="b", iddia="i", olcum="1",
               neden="n", tarih="2026-01-01", kaynak="x.py")


def test_DONCHIAN_veto_statusunde_DEGIL():
    """Metninde 'elenmis degil' yazan madde veto basligi altina giremez."""
    x = next(x for x in KATALOG if x.id == "donchian_xau")
    assert x.statu == "not_adopted", (
        "olculup secilmeyen fikir ile olcumu negatif cikan fikir ayni sey degil")


def test_TEK_BASINA_elenenler_veto_statusunde_DEGIL():
    """FVG/EMA/VWAP sonucu 'standalone reddedildi', 'hicbir baglamda kullanma' degil."""
    for mid in ("fvg_doldurma", "ema_vwap_sicrama"):
        x = next(x for x in KATALOG if x.id == mid)
        assert x.statu == "standalone_rejected", f"{mid}: kategori hatasi"


def test_CALISAN_modulle_cakisan_maddeler_KAPSAM_tasir():
    """Isim benzarligi canli modulu vetolamamali.

    `--kontrol sweep` calisan SWEEP_CORE_AVOID_MID_VWAP'i, `--kontrol orb`
    canli NQ_ORB_STRONG_TREND'i kapsiyormus gibi gorunuyordu.
    """
    for mid in ("sweep_cok_endeks", "gold_ny_orb", "equal_high_low_raid"):
        x = next(x for x in KATALOG if x.id == mid)
        assert x.kapsam.strip(), f"{mid}: kapsam bos -- blanket veto riski"


def test_kapsam_CALISAN_modulun_adini_veriyor():
    sweep = next(x for x in KATALOG if x.id == "sweep_cok_endeks")
    assert "SWEEP_CORE" in sweep.kapsam
    gold = next(x for x in KATALOG if x.id == "gold_ny_orb")
    assert "NQ_ORB" in gold.kapsam


def test_veto_statusu_calisan_modul_kumesiyle_CELISMIYOR():
    """rejected/retired bir madde, canli bir modulun ADINI tasiyamaz.

    Tasiyorsa katalog kendi portfoyunu vetoluyor demektir.
    """
    from .forward_ea.modules import default_modules
    canli = {m.name for m in default_modules()}
    for x in KATALOG:
        if x.statu not in ("rejected", "retired"):
            continue
        for ad in canli:
            assert ad not in x.baslik, f"{x.id}: canli modul {ad} vetolanmis"


# Hermes: "FOMC/Donchian sonuclari hypotheses.json'un ikinci elle yazilmis
# kopyasi; Donchian statusu simdiden ayrismis." Katalogu registry'den TURETMEK
# bugun mumkun degil (registry 2 hipotez tutuyor, katalog 13 madde -- geri
# kalani lab kosumlari ve forward defteri). Yapilabilecek dogru sey: kesisim
# kumesinde ayrismayi TESTE baglamak.

KATALOG_REGISTRY_ESLEMESI = {
    "fomc_oncesi_drift": "macro_day_drift_nq",
    "donchian_xau": "donchian_xau_1h",
}


def test_katalog_ve_hipotez_registry_CELISMIYOR():
    from .hypothesis_registry import load

    kayitlar = {h["id"]: h for h in load()}
    for katalog_id, registry_id in KATALOG_REGISTRY_ESLEMESI.items():
        x = next(x for x in KATALOG if x.id == katalog_id)
        h = kayitlar.get(registry_id)
        assert h is not None, f"{registry_id} registry'den kaybolmus"
        if h["durum"] == "elendi":
            assert x.statu == "rejected", (
                f"{katalog_id}: registry 'elendi' diyor, katalog '{x.statu}'")
        else:
            # TUM veto statuleri yasak, yalniz 'rejected' degil (Hermes
            # denetimi 2026-08-31, orta bulgu 3): Donchian'i 'retired'
            # yapan mutasyon eski testten geciyordu.
            assert x.statu not in VETO_STATULERI, (
                f"{katalog_id}: registry '{h['durum']}' diyor ama katalog "
                f"veto statusu '{x.statu}' veriyor")


# Canli modul adlarindan turetilen anahtar kelimeler. Bir veto maddesi bu
# kelimelerden birini tasiyorsa, kapsam satiri ZORUNLU -- yoksa arama calisan
# modulu de vetolar. Onceki testler yalniz onceden secilmis ID'lere bakiyordu,
# bu yuzden "genel ORB elendi" gibi YENI bir madde hepsinden geciyordu
# (Hermes denetimi 2026-08-31, orta bulgu 3).
CANLI_ANAHTARLAR = ("orb", "sweep", "london", "nq", "vwap", "ema")


def test_HERHANGI_bir_veto_maddesi_canli_kelimeyi_KAPSAMSIZ_tasiyamaz():
    for x in KATALOG:
        if x.statu not in VETO_STATULERI:
            continue
        metin = f"{x.baslik} {' '.join(x.anahtarlar)}".lower()
        carpisan = [k for k in CANLI_ANAHTARLAR if k in metin]
        if not carpisan:
            continue
        assert x.kapsam.strip(), (
            f"{x.id}: veto statusunde ve {carpisan} kelimelerini tasiyor ama "
            "kapsam satiri bos -- calisan modulu blanket vetolar")


def test_veto_kapsami_HANGI_modulun_disarida_kaldigini_SOYLER():
    """Kapsam metni serbest yazi degil: canli bir modul adi gecmeli."""
    from .forward_ea.modules import default_modules

    canli = {m.name for m in default_modules()}
    for x in KATALOG:
        if x.statu not in VETO_STATULERI or not x.kapsam:
            continue
        metin = f"{x.baslik} {' '.join(x.anahtarlar)}".lower()
        if not any(k in metin for k in CANLI_ANAHTARLAR):
            continue
        assert any(ad.split("_")[0] in x.kapsam for ad in canli), (
            f"{x.id}: kapsam hangi canli modulun HARIC oldugunu yazmiyor: "
            f"{x.kapsam[:60]}")


@pytest.mark.parametrize("sorgu", ["sweep", "orb", "donchian", "fvg"])
def test_CLI_ciktisi_veto_ile_secilmedigi_KARISTIRMAZ(sorgu, capsys):
    """Cikti seviyesinde sinama: dataclass dogru ama sunum yanlis olabilirdi."""
    from .elenenler import _gruplu_yaz, ara

    e, _ = ara(sorgu)
    assert e, f"'{sorgu}' katalogda bulunmuyor -- test anlamsizlasti"
    _gruplu_yaz(e)
    cikti = capsys.readouterr().out

    for x in e:
        baslik = STATULER[x.statu][0]
        assert baslik in cikti, f"{x.id}: '{baslik}' basligi altinda gosterilmedi"
        if x.kapsam:
            assert "KAPSAM" in cikti, f"{x.id}: kapsam satiri basilmadi"
    if any(x.statu not in VETO_STATULERI for x in e):
        assert "veto DEGIL" in cikti, (
            f"'{sorgu}': veto olmayan madde var ama cikti bunu soylemiyor")
