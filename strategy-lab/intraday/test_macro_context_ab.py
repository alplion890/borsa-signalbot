"""Makro A/B testindeki yayin gecikmesi ve haftalik kiyas kontrolleri."""
from __future__ import annotations

import pandas as pd

from .macro_context_ab import _weekly_delta_ci, delayed_change


def test_reel_faiz_degisiminde_bugun_ve_dun_kullanilmaz():
    days = pd.date_range("2026-01-05", periods=10, freq="B")
    values = pd.Series(range(10), index=days, dtype=float)
    first = delayed_change(values, days, lag=2)
    changed = values.copy()
    changed.iloc[-2:] = 10_000.0
    second = delayed_change(changed, days, lag=2)
    assert first.iloc[-1] == 5.0
    assert second.iloc[-1] == first.iloc[-1]


def test_haftalik_fark_barisina_denk_gelmeyen_saatte_sifir_olmaz():
    base = pd.Series([1.0, 1.0], index=pd.to_datetime([
        "2026-01-06 15:15", "2026-01-13 15:15"
    ]))
    filtered = pd.Series([2.0, 2.0], index=base.index)
    lo, hi = _weekly_delta_ci(base, filtered)
    assert lo > 0 and hi > 0
