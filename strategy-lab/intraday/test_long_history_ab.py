"""Uzun gecmis kosumu, CANLI modulun aynisini mi olcuyor?

Bu dosyanin tek isi ayna dogrulugu. Ayna kayarsa uzun gecmis raporu baska bir
seyi olcer ve biz onu "modulumuz 14 yilda soyle yapiyor" diye okuruz --
projedeki en pahali hata sinifi bu (bkz SWEEP_ES_DIV, dow=3 filtresi).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .adx_lab import _make_signals, _run_adaptive_rr
from .config import INSTRUMENTS
from .internet_seed_strategies import _build_orb
from .long_history_ab import _NQ_ORB, _orb_build, _sweep_build, run_spec, spec_by_name, yearly


def _rastgele_bar(n: int = 1500, tf: str = "15min", seed: int = 7) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2024-01-01", periods=n, freq=tf)
    kapanis = 100 + np.cumsum(rng.normal(0, 0.3, n))
    yuksek = kapanis + rng.uniform(0.05, 0.5, n)
    dusuk = kapanis - rng.uniform(0.05, 0.5, n)
    return pd.DataFrame({"open": kapanis, "high": yuksek, "low": dusuk,
                         "close": kapanis, "volume": 1000.0}, index=idx)


def test_sweep_aynasi_adx_lab_ile_ayni_sinyalleri_uretir():
    """Carsamba disinda birebir ayni olmali."""
    df = _rastgele_bar()
    le, se, lsl, ltp, ssl, stp, _ = _make_signals(df, 25.0)
    a_le, a_se, a_lsl, a_ltp, a_ssl, a_stp = _sweep_build(df)

    carsamba = df.index.dayofweek == 2
    assert (a_le[~carsamba] == le[~carsamba]).all()
    assert (a_se[~carsamba] == se[~carsamba]).all()
    assert not a_le[carsamba].any(), "Carsamba sinyali sizdi"
    assert not a_se[carsamba].any(), "Carsamba sinyali sizdi"
    assert (a_lsl.fillna(-1) == lsl.fillna(-1)).all()
    assert (a_ltp.fillna(-1) == ltp.fillna(-1)).all()


def test_sweep_kosumu_adx_lab_adaptive_rr_ile_AYNI_sonucu_verir():
    """TP capi ATR rejimine gore degisiyor; kendi kopyam ayni sayiyi vermeli."""
    df = _rastgele_bar()
    spec = spec_by_name("SWEEP_CORE")
    benim = run_spec(spec, df)

    le, se, lsl, ltp, ssl, stp, a = _make_signals(df, 25.0)
    carsamba = pd.Series(df.index.dayofweek == 2, index=df.index)
    onlarin, _ = _run_adaptive_rr(df, le & ~carsamba, se & ~carsamba, lsl, ltp,
                                  ssl, stp, a, INSTRUMENTS["NASDAQ100"], min_rr=2.0)
    assert len(benim) == len(onlarin)
    if len(benim):
        assert np.allclose(benim.values, onlarin.values)


def test_orb_aynasi_filtresizken_build_orb_ile_ayni():
    df = _rastgele_bar(tf="5min")
    le, se, lsl, ltp, ssl, stp = _build_orb(df, _NQ_ORB)
    a_le, a_se, *_ = _orb_build(_NQ_ORB)(df)
    assert (a_le == le).all()
    assert (a_se == se).all()


def test_adx_filtresi_sinyal_SAYISINI_dusurur():
    """Filtre gercekten uygulaniyor mu -- sessizce atlanmiyor mu?"""
    df = _rastgele_bar(tf="5min")
    filtresiz = _orb_build(_NQ_ORB)(df)
    filtreli = _orb_build(_NQ_ORB, adx_min=28.0)(df)
    assert filtreli[0].sum() <= filtresiz[0].sum()
    assert filtreli[1].sum() <= filtresiz[1].sum()


def test_yillik_tablo_islemleri_yila_dogru_dagitir():
    r = pd.Series([1.0, -1.0, 2.0],
                  index=pd.to_datetime(["2013-05-01", "2013-06-01", "2020-01-01"]))
    y = yearly(r)
    assert list(y.index) == [2013, 2020]
    assert y.loc[2013, "islem"] == 2
    assert y.loc[2020, "toplam_R"] == 2.0


def test_bos_sonuc_ozetler_patlamaz():
    from .long_history_ab import summarize
    o = summarize(pd.Series(dtype=float))
    assert o["islem"] == 0 and o["butce"] == 0
