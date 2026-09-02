"""Trend katmani: sabit tanim, eleme yok, yorum yok.

Bu dosyanin varlik sebebi bir SINIR: "trend haline gelmis pariteleri bul"
sorusunu bir dil modeline sordurmak, ona hangi evreni gorecegimizi sectirmek
demekti. Kodlanmis tanim her gun ayni soruyu sorar; testler tanimin sessizce
kaymasini engelliyor.
"""
from __future__ import annotations

import pandas as pd
import pytest

from . import trend_katmani


def _seri(gun: int = 400, egim: float = 0.5, baslangic: float = 100.0):
    idx = pd.date_range("2025-01-01", periods=gun, freq="1D")
    fiyat = pd.Series([baslangic + i * egim for i in range(gun)]).to_numpy()
    return pd.DataFrame(
        {"open": fiyat, "high": fiyat + 1, "low": fiyat - 1, "close": fiyat,
         "volume": [1000.0] * gun}, index=idx)


def test_evrenin_TAMAMI_listelenir_ELEME_yok():
    """Esik koyup filtrelemek bir hipotez olurdu ve olculmesi gerekirdi."""
    satirlar = trend_katmani.tara(lambda s: _seri())
    assert len(satirlar) == len(trend_katmani.EVREN)
    assert {s["sembol"] for s in satirlar} == {s for s, _ in trend_katmani.EVREN}


def test_siralama_PERFORMANSA_gore_degismez():
    hizli, yavas = _seri(egim=2.0), _seri(egim=0.1)
    satirlar = trend_katmani.tara(
        lambda s: hizli if s == "NASDAQ100" else yavas)
    assert [s["sembol"] for s in satirlar] == [s for s, _ in trend_katmani.EVREN]


def test_VERI_YOK_satiri_ELENMEZ_yeri_degismez():
    """Veri gelmeyen sembol gizlenmemeli; gizlenirse evren sessizce daralir."""
    def veri(s):
        if s == "WTI":
            raise RuntimeError("feed yok")
        return _seri()
    satirlar = trend_katmani.tara(veri)
    assert len(satirlar) == len(trend_katmani.EVREN)
    wti = next(s for s in satirlar if s["sembol"] == "WTI")
    assert not wti["veri"]
    assert [s["sembol"] for s in satirlar] == [s for s, _ in trend_katmani.EVREN]
    assert "VERI YOK" in "\n".join(trend_katmani.markdown(satirlar))


def test_KAPANMAMIS_gun_EMA_ve_getiriyi_degistirmez():
    kapali = _seri(gun=260)
    bugun = pd.Timestamp.now(tz="UTC").tz_localize(None).normalize()
    kismi = kapali.iloc[[-1]].copy()
    kismi.index = [bugun]
    kismi[["open", "high", "low", "close"]] = [1000.0, 1001.0, 999.0, 1000.0]

    yalniz_kapali = trend_katmani.sembol_satiri("X", "fx", kapali)
    kismi_dahil = trend_katmani.sembol_satiri("X", "fx", pd.concat([kapali, kismi]))

    for alan in ("kapanis", "ema200", "ema200_uzaklik_yuzde",
                 "adx", "getiri_20g", "getiri_50g"):
        assert kismi_dahil[alan] == pytest.approx(yalniz_kapali[alan]), alan


def test_YETERSIZ_gecmis_uydurma_EMA200_uretmez():
    satir = trend_katmani.sembol_satiri("X", "fx", _seri(gun=50))
    assert not satir["veri"], "200 bar yokken EMA200 hesaplanmis"


def test_ortak_ADX_varsayilani_GERIYE_UYUMLU_kalir():
    """Trend kapalı veri için shift=0 kullanırken diğer tüketiciler değişmemeli."""
    from ..indicators import adx

    veri = _seri(gun=260)
    pd.testing.assert_series_equal(adx(veri), adx(veri, shift=0).shift(1))


def test_ciktida_YORUM_SIFATI_yok():
    metin = "\n".join(trend_katmani.markdown(
        trend_katmani.tara(lambda s: _seri()))).lower()
    for yasak in ("guclu", "zayif", "firsat", "pahali", "ucuz", "trendde",
                  "yukselis egiliminde", "al ", "sat "):
        assert yasak not in metin, f"trend katmaninda yorum: {yasak}"
    # "ustunde/altinda" OLGU'dur: fiyatin ortalamaya gore konumu.
    assert "ustunde" in metin or "altinda" in metin


def test_liste_ISLEM_EVRENI_olmadigini_soyler():
    """Genis evren, portfoyun genisledigi anlamina gelmemeli."""
    metin = "\n".join(trend_katmani.markdown(
        trend_katmani.tara(lambda s: _seri())))
    assert "islem evreni DEGIL" in metin


def test_tanim_KILITLI():
    """Tanim sonuca bakilarak degistirilirse bu test dusurulmeli, sessizce degil.

    2026-09-01'de sabitlendi: 200EMA konumu + ADX(14) + 20/50 gunluk degisim.
    Degistirmek yeni bir karar ve gerekcesi yazilmali.
    """
    assert trend_katmani.EMA_UZUN == 200
    assert trend_katmani.ADX_PENCERE == 14
    assert trend_katmani.GETIRI_PENCERELERI == (20, 50)


def test_evrende_TEKRAR_yok():
    isimler = [s for s, _ in trend_katmani.EVREN]
    assert len(isimler) == len(set(isimler))


@pytest.mark.parametrize("sembol", [s for s, _ in trend_katmani.EVREN])
def test_her_sembol_bulut_feedinde_COZULEBILIR(sembol):
    """Ticker eslemesi eksik olan sembol her gun sessizce VERI YOK basardi."""
    from .cloud_feed import supports
    assert supports(sembol), f"{sembol} bulut feed tablosunda yok"
