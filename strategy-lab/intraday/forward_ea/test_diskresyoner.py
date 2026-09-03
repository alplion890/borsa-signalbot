"""Diskresyoner defterin kurallari -- gevsetilirse defter degerini kaybeder."""
from __future__ import annotations

import pytest

from .diskresyoner import (
    ISLEM_EVRENI,
    MIN_KATMAN,
    MIN_N,
    ac,
    aday,
    kapat,
    ozet,
    pas,
    tetikle,
    yukle,
)

TEZ = "makro haber negatif, fiyat 200EMA ustunde pahali bolgede"
CURUTEN = "200EMA uzerinde gunluk kapanis gelirse tez yanlis"
KAT3 = "narrative,hacim,trend"


@pytest.fixture
def defter(tmp_path):
    return tmp_path / "diskresyoner_defter.csv"


def _ac(defter, **kw):
    v = dict(sembol="US100", yon="short", giris=25000.0, stop=25120.0,
             tez=TEZ, curuten=CURUTEN, katmanlar=KAT3, path=defter)
    v.update(kw)
    return ac(**v)


def _aday(defter, **kw):
    v = dict(sembol="US100", yon="short", tetik=25000.0, stop=25120.0,
             tez=TEZ, curuten=CURUTEN, katmanlar=KAT3, path=defter)
    v.update(kw)
    return aday(**v)


def _long_kaybeden(defter):
    i = _ac(defter, yon="long", giris=100.0, stop=90.0)
    return kapat(i.id, cikis=90.0, path=defter)


# --- giris kapilari -----------------------------------------------------


def test_tez_kisaysa_islem_ACILMAZ(defter):
    """'iyi gorunuyor' tez degildir. Bu alan defterin tek dogrulamasi."""
    with pytest.raises(ValueError, match="tez"):
        _ac(defter, tez="iyi duruyor")


def test_curuten_alani_ZORUNLU(defter):
    """Tezi ne yanlislar? Onsuz her sonuc sonradan aciklanabilir."""
    with pytest.raises(ValueError, match="curuten"):
        _ac(defter, curuten="bilmiyorum")


def test_katman_kapisi_TEK_katmani_reddeder(defter):
    """Giris filtresi 2026-09-03'te 3/4'ten 2/4'e indi (kullanici karari).

    Tek gerekce hala yetmiyor: kapinin varlik sebebi "bir sey gordum, girdim"
    kaydini engellemek. Iki ayri gerekce, sonradan hatirlanabilir bir tez birakir.
    """
    with pytest.raises(ValueError, match="katman kapisi"):
        _ac(defter, katmanlar="narrative")


def test_bilinmeyen_katman_reddedilir(defter):
    with pytest.raises(ValueError, match="bilinmeyen katman"):
        _ac(defter, katmanlar="narrative,hacim,fvg")


def test_tekrarli_katman_sayiyi_SISIRMEZ(defter):
    with pytest.raises(ValueError, match="katman kapisi"):
        _ac(defter, katmanlar="narrative,narrative")


def test_IKI_katman_kabul(defter):
    """2/4 karari: kod iki gerekceli girisi kabul etmeli."""
    k = _ac(defter, katmanlar="narrative,trend")
    assert k.katman_sayisi == 2


def test_dort_katman_kabul(defter):
    k = _ac(defter, katmanlar="narrative,hacim,trend,destek")
    assert k.katman_sayisi == 4


def test_stop_yonle_TUTARLI_olmali(defter):
    with pytest.raises(ValueError, match="short"):
        _ac(defter, yon="short", giris=25000.0, stop=24900.0)
    with pytest.raises(ValueError, match="long"):
        _ac(defter, yon="long", giris=25000.0, stop=25100.0)


@pytest.mark.parametrize("sembol", ("USDJPY", "XAGUSD", "SP500"))
def test_gozlem_evrenindeki_YENI_sembol_islem_evrenine_giremez(defter, sembol):
    with pytest.raises(ValueError, match="islem evreni"):
        _aday(defter, sembol=sembol)


def test_islem_evreni_ON_KAYITLI_kumeye_esittir():
    assert ISLEM_EVRENI == ("NASDAQ100", "US100", "XAUUSD", "EURUSD", "GBPUSD")


def test_dogrudan_AC_yolu_da_evren_disini_reddeder(defter):
    with pytest.raises(ValueError, match="islem evreni"):
        _ac(defter, sembol="XAGUSD")


def test_US100_broker_aliasi_islem_evreninde_kalir(defter):
    assert _aday(defter, sembol=" us100 ").sembol == "US100"


def test_ayni_anda_TEK_islem(defter):
    """Maven slot kisiti: acik islem varken ikincisi acilamaz."""
    _ac(defter)
    with pytest.raises(ValueError, match="acik islem"):
        _ac(defter, sembol="XAUUSD")


def test_aday_ACIK_ISLEMI_engellemez(defter):
    """Slot kisiti islemler icin; aday yazmak serbest olmali."""
    _ac(defter)
    _aday(defter, sembol="XAUUSD")
    assert len([k for k in yukle(defter) if k.durum == "aday"]) == 1


# --- aday akisi ---------------------------------------------------------


def test_aday_tetiklenince_ACIK_olur(defter):
    a = _aday(defter)
    assert a.durum == "aday" and a.giris is None
    k = tetikle(a.id, giris=24990.0, path=defter)
    assert k.durum == "acik" and k.giris == 24990.0 and k.tetik == 25000.0


def test_pas_gecilen_aday_ISLEM_SAYILMAZ(defter):
    a = _aday(defter)
    pas(a.id, sebep="tetige hic gelmedi, seans bitti", path=defter)
    o = ozet(defter)
    assert o["n"] == 0 and o["pas"] == 1


def test_pas_SEBEBI_zorunlu(defter):
    """Neden girmedigin de veridir."""
    a = _aday(defter)
    with pytest.raises(ValueError, match="pas sebebi"):
        pas(a.id, sebep="yok", path=defter)


def test_kapali_islem_TEKRAR_tetiklenemez(defter):
    a = _aday(defter)
    tetikle(a.id, giris=24990.0, path=defter)
    with pytest.raises(ValueError, match="durumu"):
        tetikle(a.id, giris=24980.0, path=defter)


def test_secicilik_pas_oranindan_hesaplanir(defter):
    """3 aday: 1 alindi, 2 pas -> secicilik %66."""
    a1 = _aday(defter)
    tetikle(a1.id, giris=24990.0, path=defter)
    kapat(a1.id, cikis=24800.0, path=defter)
    for _ in range(2):
        a = _aday(defter)
        pas(a.id, sebep="tetige gelmedi, pencere kapandi", path=defter)
    o = ozet(defter)
    assert o["pas"] == 2 and o["n"] == 1
    assert o["secicilik"] == pytest.approx(200 / 3)


# --- sonuc muhasebesi ---------------------------------------------------


def test_R_stop_mesafesine_gore_hesaplanir(defter):
    i = _ac(defter, yon="short", giris=25000.0, stop=25100.0)  # risk 100
    k = kapat(i.id, cikis=24800.0, path=defter)                # 200 lehte
    assert k.r == pytest.approx(2.0)


def test_long_kayip_negatif_R(defter):
    assert _long_kaybeden(defter).r == pytest.approx(-1.0)


def test_kapali_islem_TEKRAR_kapanmaz(defter):
    i = _ac(defter)
    kapat(i.id, cikis=24800.0, path=defter)
    with pytest.raises(ValueError, match="durumu"):
        kapat(i.id, cikis=24700.0, path=defter)


# --- kalicilik ----------------------------------------------------------


def test_tez_curuten_ve_ETIKETLER_deftere_yazilir(defter):
    """Sonradan okunamayan tez, tez degildir. Etiketler alt-kume analizi icin."""
    _ac(defter, narrative="ai_dalgasi_soguma", timeframe="1H",
        katmanlar="narrative,hacim,destek",
        tez="makro negatif, DXY guclu, endeks pahali bolgede islem goruyor",
        curuten="DXY 200EMA altina duserse makro tez cokmus olur")
    k = yukle(defter)[0]
    assert "DXY" in k.tez and "DXY" in k.curuten
    assert k.narrative == "ai_dalgasi_soguma" and k.timeframe == "1H"
    assert k.katman_sayisi == 3


# --- durma kurali -------------------------------------------------------


def test_ozet_bos_defterde_patlamaz(defter):
    o = ozet(defter)
    assert o["n"] == 0 and not o["durma_tetik"]


def test_durma_esigi_ALTINDA_tetiklenmez(defter):
    """n<20 iken negatif olmak durdurmaz -- erken durma da hatadir."""
    for _ in range(MIN_N - 1):
        _long_kaybeden(defter)
    o = ozet(defter)
    assert o["n"] == MIN_N - 1 and o["exp_R"] < 0
    assert not o["durma_tetik"], "esik gelmeden durma tetiklenmemeli"


def test_durma_esiginde_negatifse_TETIKLENIR(defter):
    for _ in range(MIN_N):
        _long_kaybeden(defter)
    assert ozet(defter)["durma_tetik"]


def test_PAS_kayitlari_esigi_DOLDURMAZ(defter):
    """Durma esigi kapanmis ISLEM sayar; bakip gectiklerin degil."""
    for _ in range(MIN_N):
        a = _aday(defter)
        pas(a.id, sebep="katman kapisi doldu ama tetige gelmedi", path=defter)
    o = ozet(defter)
    assert o["pas"] == MIN_N and o["n"] == 0 and not o["durma_tetik"]


def test_esikte_POZITIFSE_tetiklenmez(defter):
    for _ in range(MIN_N):
        i = _ac(defter, yon="long", giris=100.0, stop=90.0)
        kapat(i.id, cikis=120.0, path=defter)
    o = ozet(defter)
    assert o["exp_R"] > 0 and not o["durma_tetik"]


def test_MIN_KATMAN_taahhudu_kodda_sabit():
    """Esik 2026-09-03'te 3 -> 2 indi; kullanici karari, git gecmisinde gorunur.

    Sayi burada kilitli kalmali: bir sonraki degisiklik de sessiz olmasin,
    sonuca bakilarak gevsetilmesin. Katmanlar deftere yazilmaya devam ettigi
    icin "2 katmanli girisler 4 katmanlilardan kotu muydu" sorusu 20 islem
    sonunda OLCULEBILIR -- filtre gevsedi, olcum gevsemedi.
    """
    assert MIN_KATMAN == 2


# --- risk politikasi ve solvency kapisi (2026-09-03) ---------------------
#
# Kullanici riski %3'ten %6'ya cikardi. Bootstrap (20.000 yol, defterin kendi R
# dagilimi): gecme %57 -> %50, breach %43 -> %50, medyan 3 -> 1 islem. Karar
# kullanicinin; ama %6 = ~300 USD ve breach'e tampon 500 USD = 1.67R, yani bir
# tam stop sonrasi ikinci ayni islem hesabi bitirebilir. Durma kurali
# (n>=20 & exp_R<0) EDGE olcer, hayatta kalmayi garanti etmez -- bu kapi onu
# tamamliyor. Hermes denetimi 2026-09-03.


def test_RISK_diskresyoner_rayda_AYRI_mekanige_dokunmaz():
    """Mekanik ray dondurulmus; challenge cap'i risk.py'de %3 kalmali."""
    from .diskresyoner import RISK_PCT
    from ..signalbot.risk import _PROFILES

    assert RISK_PCT == 0.06
    challenge = _PROFILES["bnpl_challenge"]
    assert challenge.max_open_risk_pct <= 0.03, (
        "diskresyoner karari mekanik profile sizmis")


def test_risk_GUNCEL_bakiyeden_hesaplanir():
    """Sabit dolar degil: kaybettikce risk kuculmeli."""
    from .diskresyoner import risk_dolar

    assert risk_dolar(5000.0) == 300.0
    assert risk_dolar(4800.0) == 288.0


def test_SOLVENCY_tamponu_asan_islem_REDDEDILIR(defter):
    """Ikinci -1R hesabi patlatacaksa kod islemi kabul etmemeli."""
    from .diskresyoner import BREACH_BAKIYE, GUVENLIK_TAMPONU

    # 4700: breach'e 200, guvenlik payindan sonra 100 USD kullanilabilir.
    # %6 = 282 USD -> tampondan buyuk.
    with pytest.raises(ValueError, match="SOLVENCY"):
        _ac(defter, bakiye=4700.0)
    assert 4700.0 - BREACH_BAKIYE - GUVENLIK_TAMPONU < 4700.0 * 0.06


def test_SOLVENCY_tampon_bittiginde_islem_YOK(defter):
    with pytest.raises(ValueError, match="tampon yok"):
        _ac(defter, bakiye=4550.0)


def test_saglikli_bakiyede_islem_ACILIR_ve_risk_KAYDEDILIR(defter):
    k = _ac(defter, bakiye=5000.0)
    assert k.bakiye == 5000.0
    assert k.risk_pct == 0.06
    assert k.risk_usd == 300.0


def test_bakiye_verilmezse_risk_alanlari_BOS_kalir(defter):
    """Eski satirlarla uyum: kayit yazilir ama '%6 ile ne oldu' cevaplanamaz."""
    k = _ac(defter)
    assert k.bakiye is None and k.risk_usd is None


def test_risk_alanlari_DEFTERE_yazilip_geri_OKUNUR(defter):
    _ac(defter, bakiye=5000.0)
    okunan = yukle(defter)[-1]
    assert okunan.risk_usd == 300.0 and okunan.bakiye == 5000.0
