"""macro_day_drift_nq zamanlama kurallari -- sessizce kayarsa burada patlar.

En kritik olan: sinyalin ve cikisin duyurudan ONCE olmasi. Bir bar kayma
bu hipotezi "duyuru oncesi prim" olmaktan cikarip "duyuru sonrasi spike'a
bin"e cevirir ve sonuc tamamen degisir.
"""
from __future__ import annotations

import pandas as pd
import pytest

from .event_calendar import fomc_events
from .history_fetch import load_history
from .macro_day_lab import (
    VARYANTLAR,
    _duyuru_utc,
    gunluk_atr,
    sinyal_kur,
)


@pytest.fixture(scope="module")
def df():
    return load_history("NASDAQ100", "15m", start_year=2024)


def test_duyuru_saati_yaz_kis_dogru_cevriliyor():
    """ET -> UTC cevriminde yaz/kis saati kaymasi olmamali."""
    from datetime import date, time
    # Eylul = yaz saati (EDT, UTC-4) -> 14:00 ET = 18:00 UTC
    assert _duyuru_utc(date(2024, 9, 18), time(14, 0)) == pd.Timestamp("2024-09-18 18:00")
    # Ocak = kis saati (EST, UTC-5) -> 14:00 ET = 19:00 UTC
    assert _duyuru_utc(date(2024, 1, 31), time(14, 0)) == pd.Timestamp("2024-01-31 19:00")


def test_duyuru_bari_15m_izgarasina_oturuyor():
    """12:30 / 14:00 / 14:15 ET hepsi tam 15m siniri olmali.

    Olmasaydi `get_indexer` duyuru barini bulamaz, sessizce 0 sinyal olurdu.
    """
    for e in fomc_events():
        t = _duyuru_utc(e.gun, e.aciklama_et)
        assert t.minute % 15 == 0, f"{e.gun} {e.aciklama_et} 15m izgarasinda degil"


@pytest.mark.parametrize("varyant", list(VARYANTLAR))
def test_sinyal_DUYURUDAN_ONCE(df, varyant):
    """Sinyal bari + tutus suresi, duyuru barina ULASMAMALI.

    Cikis en gec duyuruyu iceren barin BIR ONCEKI barinin kapanisidir.
    """
    ofset, max_hold = VARYANTLAR[varyant]
    le = sinyal_kur(df, ofset)
    duyuru_konum = set()
    for e in fomc_events():
        loc = df.index.get_indexer([_duyuru_utc(e.gun, e.aciklama_et)])[0]
        if loc != -1:
            duyuru_konum.add(loc)

    for i in range(len(le)):
        if not le.iloc[i]:
            continue
        cikis = i + max_hold          # zaman-cikisi bari
        assert cikis < min(k for k in duyuru_konum if k > i), (
            f"{df.index[i]}: cikis bari {df.index[cikis]} duyuru barina degiyor"
        )


@pytest.mark.parametrize("varyant", list(VARYANTLAR))
def test_her_FOMC_gunu_EN_FAZLA_bir_sinyal(df, varyant):
    ofset, _ = VARYANTLAR[varyant]
    le = sinyal_kur(df, ofset)
    gunler = pd.Series(le[le].index.normalize())
    assert gunler.is_unique, "ayni gunde birden fazla sinyal"


@pytest.mark.parametrize("varyant", list(VARYANTLAR))
def test_sinyal_SADECE_fomc_gunlerinde(df, varyant):
    ofset, _ = VARYANTLAR[varyant]
    le = sinyal_kur(df, ofset)
    fomc_gunleri = {e.gun for e in fomc_events()}
    for t in le[le].index:
        assert t.date() in fomc_gunleri, f"{t} FOMC gunu degil"


def test_gunluk_atr_ONCEKI_gunu_kullaniyor(df):
    """Islem gununun kendi ATR'si o gun kapanmadan bilinemez -- shift(1) sart."""
    a = gunluk_atr(df)
    gun = df.resample("1D").agg({"open": "first", "high": "max",
                                 "low": "min", "close": "last"}).dropna()
    from .indicators import atr
    ham = atr(gun, 14)
    ornek = a.dropna().index[500]
    beklenen = ham.loc[:ornek.normalize()].iloc[-2]  # bir onceki gun
    assert a.loc[ornek] == pytest.approx(beklenen)
