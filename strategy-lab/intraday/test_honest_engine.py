"""honest_engine denetimi -- cevabi ONCEDEN bilinen sentetik vakalar.

Neden: motor vectorbt'den cok farkli sonuc veriyor (+0.33R vs -0.027R). Fark
tasarim geregi mi (muhafazakar doldurma) yoksa BUG mu? Bu dosya farkin
tasarimdan geldigini sabitler.

Denetlenen sozlesmeler:
  1. Giris sinyal barinin KAPANISINDA olur, cikis TARAMASI bir sonraki bardan
     baslar -> ileriye bakma (lookahead) yok.
  2. Ayni barda hem SL hem TP varsa SL sayilir (muhafazakar).
  3. Maliyet gidis-donus, R cinsine dogru cevrilir.
  4. max_hold sonunda piyasa fiyatindan kapanir.
  5. Pozisyon acikken yeni sinyal alinmaz.
  6. numba hizli cekirdegi ile saf python yolu AYNI sonucu verir.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from . import honest_engine as he
from .config import Instrument

# maliyetsiz enstruman: R hesabini izole eder
FREE = Instrument("TEST", "", 0.0, (0, 24), 1.0)
COSTLY = Instrument("TEST", "", 0.001, (0, 24), 1.0)  # 10 bps tek yon


def _frame(closes, highs=None, lows=None) -> pd.DataFrame:
    n = len(closes)
    idx = pd.date_range("2026-01-01", periods=n, freq="5min")
    c = np.asarray(closes, dtype=float)
    return pd.DataFrame({
        "open": c,
        "high": c if highs is None else np.asarray(highs, dtype=float),
        "low": c if lows is None else np.asarray(lows, dtype=float),
        "close": c,
    }, index=idx)


def _sig(n, i, side="long"):
    le = pd.Series(False, index=range(n))
    se = pd.Series(False, index=range(n))
    (le if side == "long" else se)[i] = True
    return le, se


def _run(df, i, sl, tp, side="long", inst=FREE, **kw):
    n = len(df)
    le, se = _sig(n, i, side)
    le.index = se.index = df.index
    nan = pd.Series(np.nan, index=df.index)
    lsl = ltp = ssl = stp = nan
    if side == "long":
        lsl = pd.Series(np.where(np.arange(n) == i, sl, np.nan), index=df.index)
        ltp = pd.Series(np.where(np.arange(n) == i, tp, np.nan), index=df.index)
    else:
        ssl = pd.Series(np.where(np.arange(n) == i, sl, np.nan), index=df.index)
        stp = pd.Series(np.where(np.arange(n) == i, tp, np.nan), index=df.index)
    kw.setdefault("min_rr", 0.5)
    kw.setdefault("max_rr", 10.0)
    kw.setdefault("max_hold", 50)
    return he.simulate_trades(df, le, se, lsl, ltp, ssl, stp, inst, **kw)


# --- 1. temel sonuclar ------------------------------------------------------


def test_clean_tp_gives_exact_rr() -> None:
    """Giris 100, SL 99 (risk 1), TP 102 (rr 2) -> fiyat 102'ye giderse +2R."""
    df = _frame([100, 101, 102.5], highs=[100, 101, 102.5], lows=[100, 101, 101])
    r = _run(df, 0, sl=99.0, tp=102.0)
    assert len(r) == 1
    assert r.iloc[0] == pytest.approx(2.0)


def test_clean_sl_gives_exact_minus_one() -> None:
    df = _frame([100, 99.5, 98.9], highs=[100, 99.5, 99.5], lows=[100, 99.5, 98.9])
    r = _run(df, 0, sl=99.0, tp=102.0)
    assert r.iloc[0] == pytest.approx(-1.0)


def test_short_side_mirrors_long() -> None:
    df = _frame([100, 99, 97.9], highs=[100, 99.2, 99], lows=[100, 99, 97.9])
    r = _run(df, 0, sl=101.0, tp=98.0, side="short")
    assert r.iloc[0] == pytest.approx(2.0)


# --- 2. muhafazakarlik sozlesmesi ------------------------------------------


def test_same_bar_sl_and_tp_counts_as_sl() -> None:
    """Kritik sozlesme: bar hem SL hem TP'ye degiyorsa EN KOTU sayilir."""
    df = _frame([100, 100.5], highs=[100, 103.0], lows=[100, 98.0])
    r = _run(df, 0, sl=99.0, tp=102.0)
    assert r.iloc[0] == pytest.approx(-1.0), "ayni barda SL once sayilmali"


def test_no_lookahead_signal_bar_is_not_scanned() -> None:
    """Sinyal barinin kendi low'u SL'in altinda olsa bile islem oradan kapanmaz.

    Giris o barin KAPANISINDA olur; bar ici hareket zaten gecmistir.
    """
    # bar 0: low 90 (SL 99'un cok altinda) ama kapanis 100 -> giris burada
    df = _frame([100, 102.5], highs=[100, 102.5], lows=[90, 100])
    r = _run(df, 0, sl=99.0, tp=102.0)
    assert r.iloc[0] == pytest.approx(2.0), "sinyal bari cikis icin taranmamali"


# --- 3. maliyet -------------------------------------------------------------


def test_cost_is_round_trip_and_scaled_to_r() -> None:
    """cost_per_side=0.001, giris 100, risk 1 -> risk fiyatin %1'i.

    R cinsinden maliyet = 2 * 0.001 / 0.01 = 0.2R
    """
    df = _frame([100, 101, 102.5], highs=[100, 101, 102.5], lows=[100, 101, 101])
    r = _run(df, 0, sl=99.0, tp=102.0, inst=COSTLY)
    assert r.iloc[0] == pytest.approx(2.0 - 0.2)


def test_tighter_stop_pays_more_cost_in_r() -> None:
    """Ayni maliyet, yari risk -> R cinsinden maliyet iki kat.

    SWEEP_ES_DIV'i olduren mekanizma tam buydu (igne-ince stop).
    """
    df = _frame([100, 101, 102.5], highs=[100, 101, 102.5], lows=[100, 101, 101])
    wide = _run(df, 0, sl=99.0, tp=102.0, inst=COSTLY)      # risk %1
    tight = _run(df, 0, sl=99.5, tp=101.0, inst=COSTLY)     # risk %0.5
    assert (2.0 - wide.iloc[0]) == pytest.approx(0.2)
    assert (2.0 - tight.iloc[0]) == pytest.approx(0.4)


# --- 4. timeout / pozisyon yonetimi ----------------------------------------


def test_timeout_exits_at_market_price() -> None:
    """max_hold=2: ne SL ne TP -> 2 bar sonraki fiyattan cikis."""
    df = _frame([100, 100.4, 100.6, 105], highs=[100, 100.4, 100.6, 105],
                lows=[100, 100.4, 100.6, 105])
    r = _run(df, 0, sl=99.0, tp=102.0, max_hold=2)
    assert r.iloc[0] == pytest.approx(0.6), "timeout barindaki fiyattan kapanmali"


def test_no_overlapping_positions() -> None:
    """Pozisyon acikken gelen ikinci sinyal alinmaz."""
    n = 8
    df = _frame([100] * n, highs=[100] * n, lows=[100] * n)
    idx = df.index
    le = pd.Series([True, True] + [False] * (n - 2), index=idx)
    se = pd.Series(False, index=idx)
    arr = lambda v: pd.Series(np.where(np.arange(n) < 2, v, np.nan), index=idx)
    nan = pd.Series(np.nan, index=idx)
    r = he.simulate_trades(df, le, se, arr(99.0), arr(102.0), nan, nan,
                           FREE, min_rr=0.5, max_rr=10.0, max_hold=3)
    assert len(r) == 1, "ikinci sinyal ilk pozisyon aciken alinmamali"


def test_rr_below_min_is_skipped() -> None:
    df = _frame([100, 102.5], highs=[100, 102.5], lows=[100, 100])
    assert len(_run(df, 0, sl=99.0, tp=101.0, min_rr=2.0)) == 0


def test_rr_above_max_is_capped() -> None:
    df = _frame([100, 110], highs=[100, 110], lows=[100, 100])
    r = _run(df, 0, sl=99.0, tp=109.0, max_rr=3.0)
    assert r.iloc[0] == pytest.approx(3.0)


# --- 5. numba cekirdegi <-> python yolu PARITE -----------------------------


@pytest.mark.skipif(not he.FAST_CORE_AVAILABLE, reason="numba cekirdegi yok")
def test_fast_core_matches_python_reference() -> None:
    """En riskli yer: hizli cekirdek ile referans yol AYNI sonucu vermeli.

    Ayrisirlarsa tum backtest sonuclari hangi yolun secildigine bagli olur.
    """
    rng = np.random.default_rng(7)
    n = 4000
    close = 100 * np.exp(np.cumsum(rng.normal(0, 0.001, n)))
    noise = np.abs(rng.normal(0, 0.15, n))
    df = _frame(close, highs=close + noise, lows=close - noise)
    idx = df.index

    sig = rng.random(n) < 0.02
    le = pd.Series(sig & (rng.random(n) < 0.5), index=idx)
    se = pd.Series(sig & ~le.to_numpy(), index=idx)
    risk = close * 0.004
    lsl = pd.Series(np.where(le, close - risk, np.nan), index=idx)
    ltp = pd.Series(np.where(le, close + 2.5 * risk, np.nan), index=idx)
    ssl = pd.Series(np.where(se, close + risk, np.nan), index=idx)
    stp = pd.Series(np.where(se, close - 2.5 * risk, np.nan), index=idx)
    inst = Instrument("TEST", "", 0.00009, (0, 24), 1.0)

    fast = he.simulate_trades(df, le, se, lsl, ltp, ssl, stp, inst,
                              min_rr=1.0, max_rr=6.0, max_hold=100)
    he.FAST_CORE_AVAILABLE = False
    try:
        slow = he.simulate_trades(df, le, se, lsl, ltp, ssl, stp, inst,
                                  min_rr=1.0, max_rr=6.0, max_hold=100)
    finally:
        he.FAST_CORE_AVAILABLE = True

    assert len(fast) == len(slow), f"islem sayisi farkli: {len(fast)} vs {len(slow)}"
    assert list(fast.index) == list(slow.index), "islem zamanlari farkli"
    np.testing.assert_allclose(fast.to_numpy(), slow.to_numpy(), rtol=1e-9, atol=1e-12)
