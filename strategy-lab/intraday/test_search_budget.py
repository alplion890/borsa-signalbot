"""Arama butcesi hesabi -- yon dogru mu?"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .search_budget import sr_variance, trial_budget, weekly_sharpe


def test_daha_cok_veri_butceyi_BUYUTUR():
    az = trial_budget(0.383, 35)
    cok = trial_budget(0.383, 181)
    assert cok > az * 100, f"14 yil butcesi ({cok}) 3 yildan ({az}) cok daha buyuk olmali"


def test_daha_zayif_sinyal_butceyi_KUCULTUR():
    assert trial_budget(0.2, 100) < trial_budget(0.6, 100)


def test_negatif_sharpe_butce_biraKMAZ():
    assert trial_budget(-0.5, 100) == 0
    assert trial_budget(0.0, 100) == 0


def test_mevcut_verimiz_kucuk_bir_butce_veriyor():
    """3 yillik ornek ~onlarca hipotez finanse ediyor, milyonlarca degil.

    Bu sayi degisirse (veri uzarsa) test guncellenmeli -- ama sessizce
    milyonlara ciktigini varsaymak, bu projenin uc kez dustugu tuzak.
    """
    butce = trial_budget(0.383, 35)
    assert butce < 1000, f"3 yillik ornek {butce} hipotez finanse ediyor gorunuyor"


def test_sr_varyansi_gozlemle_kuculur():
    assert sr_variance(0.4, 200) < sr_variance(0.4, 20)


def test_haftalik_sharpe_islemsiz_haftalari_saymaz():
    idx = pd.date_range("2026-01-01", periods=60, freq="D")
    r = pd.Series(0.0, index=idx)
    r.iloc[0] = 1.0
    r.iloc[30] = 1.0
    sr, n = weekly_sharpe(r)
    assert n == 2
