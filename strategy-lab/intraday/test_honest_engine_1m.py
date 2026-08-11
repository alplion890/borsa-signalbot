"""1m intrabar fill-modeli denetimi -- cevabi ONCEDEN bilinen sentetik vakalar.

Mevcut `bar_sl_first` modu 15m mumda hem SL hem TP gorulunce SL yazar; bar ici
gercek sirayi bilmez. Yeni `1m_then_sl_first` modu SADECE bu belirsiz mumlarda
1m OHLC'ye iner. Bu dosya iki modun sozlesmesini sabitler.

Denetlenen sozlesmeler:
  1. Giris sinyal mumunun kapanisi degil, SONRAKI 15m mumun open'idir.
  2. SL yapisal seviye olarak kalir; hedef R korunur, TP yeni girise gore
     yeniden fiyatlanir.
  3. Yalniz SL / yalniz TP gorulen 15m mumda 1m'ye INILMEZ.
  4. Ikisi de gorulurse yalnizca o [bar_basi, bar_sonu) penceresinin 1m mumlari
     kronolojik taranir; ilk dokunan kazanir.
  5. Tek 1m mumda ikisi de varsa veya 1m veri eksikse -> SL-first fallback
     (asla iyimser sonuc yazilmaz).
  6. Giris sonraki open'da stopun diger tarafindaysa islem ATLANIR ve ayri
     sayilir (bkz signalbot MAX_ADVERSE_ENTRY_DRIFT_R = 0.5).
  7. Eski `bar_sl_first` modu varsayilan ve degismemis kalir.
  8. Yeni mod numba yolunda sessizce farkli sonuc uretmez.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from . import honest_engine as he
from .config import Instrument

FREE = Instrument("TEST", "", 0.0, (0, 24), 1.0)

NEW = "1m_then_sl_first"
OLD = "bar_sl_first"


def _frame15(rows: list[tuple[float, float, float, float]]) -> pd.DataFrame:
    """rows = [(open, high, low, close), ...] -> 15m OHLC, UTC tz-naive."""
    idx = pd.date_range("2026-01-01", periods=len(rows), freq="15min")
    arr = np.asarray(rows, dtype=float)
    return pd.DataFrame(
        {"open": arr[:, 0], "high": arr[:, 1], "low": arr[:, 2], "close": arr[:, 3]},
        index=idx,
    )


def _frame1m(bar_start: str, rows: list[tuple[float, float, float, float]]) -> pd.DataFrame:
    """Tek 15m pencerenin 1m mumlari; rows[0] pencerenin ilk dakikasidir."""
    idx = pd.date_range(bar_start, periods=len(rows), freq="1min")
    arr = np.asarray(rows, dtype=float)
    return pd.DataFrame(
        {"open": arr[:, 0], "high": arr[:, 1], "low": arr[:, 2], "close": arr[:, 3]},
        index=idx,
    )


def _run(df, sl, tp, side="long", df_1m=None, fill_mode=NEW, inst=FREE, **kw):
    """Bar 0'da tek sinyal; kalan seviyeler NaN."""
    n = len(df)
    idx = df.index
    first = np.arange(n) == 0
    le = pd.Series(first if side == "long" else False, index=idx)
    se = pd.Series(first if side == "short" else False, index=idx)
    nan = pd.Series(np.nan, index=idx)
    lvl = lambda v: pd.Series(np.where(first, v, np.nan), index=idx)
    lsl, ltp, ssl, stp = (lvl(sl), lvl(tp), nan, nan) if side == "long" \
        else (nan, nan, lvl(sl), lvl(tp))
    kw.setdefault("min_rr", 0.5)
    kw.setdefault("max_rr", 10.0)
    kw.setdefault("max_hold", 50)
    return he.simulate_trades(df, le, se, lsl, ltp, ssl, stp, inst,
                              fill_mode=fill_mode, df_1m=df_1m, **kw)


# --- 1. giris fiyati: sonraki 15m open --------------------------------------


def test_entry_is_next_bar_open_not_signal_close() -> None:
    """Sinyal kapanisi 100, sonraki open 100.5 -> giris 100.5 olmali.

    max_hold=2 ile islem duz fiyatta zaman asimina ugrar:
      yeni mod : (100.5 - 100.5) / 1.5 = 0.0R
      eski mod : (100.5 - 100.0) / 1.0 = +0.5R
    Fark yalnizca giris fiyatindan gelir.
    """
    df = _frame15([
        (100.0, 100.0, 100.0, 100.0),      # sinyal mumu
        (100.5, 100.6, 100.4, 100.5),
        (100.5, 100.6, 100.4, 100.5),
    ])
    new = _run(df, sl=99.0, tp=102.0, max_hold=2)
    old = _run(df, sl=99.0, tp=102.0, max_hold=2, fill_mode=OLD)
    assert new.iloc[0] == pytest.approx(0.0), "giris sonraki open (100.5) olmali"
    assert old.iloc[0] == pytest.approx(0.5), "eski mod sinyal kapanisindan girmeli"


def test_target_r_is_preserved_and_tp_repriced_from_new_entry() -> None:
    """Sinyalde rr=2. Giris 101'e kayarsa risk 2 olur, TP 105'e tasinir.

    Eski TP (102) bar 1'de goruluyor ama yeni TP (105) gorulmuyor; islem
    devam eder ve bar 2'de SL'e dusser -> -1R. Eski mod +2R yazardi.
    """
    df = _frame15([
        (100.0, 100.0, 100.0, 100.0),      # sinyal: sl 99, tp 102, rr=2
        (101.0, 102.5, 100.8, 102.4),      # eski TP 102 gorulur, yeni TP 105 gorulmez
        (102.4, 102.4, 98.5, 98.6),        # SL 99
    ])
    new = _run(df, sl=99.0, tp=102.0)
    old = _run(df, sl=99.0, tp=102.0, fill_mode=OLD)
    assert new.iloc[0] == pytest.approx(-1.0), "TP yeni girise gore fiyatlanmali"
    assert old.iloc[0] == pytest.approx(2.0)


# --- 2. belirsiz 15m mumda 1m cozumu ---------------------------------------


def _ambiguous_long() -> pd.DataFrame:
    """Giris 100 (bar1 open), SL 99, TP 102; bar 1 ikisine de degiyor."""
    return _frame15([
        (100.0, 100.0, 100.0, 100.0),
        (100.0, 102.5, 98.5, 100.0),       # hem TP hem SL -> belirsiz
        (100.0, 100.0, 100.0, 100.0),
    ])


def test_long_tp_first_in_1m_gives_positive_r() -> None:
    df = _ambiguous_long()
    m1 = _frame1m("2026-01-01 00:15", [
        (100.0, 102.5, 99.9, 102.4),       # TP 102 ilk dakikada
        (102.4, 102.4, 98.5, 98.6),        # SL sonra
    ])
    r = _run(df, sl=99.0, tp=102.0, df_1m=m1)
    assert r.iloc[0] == pytest.approx(2.0), "1m TP'yi once gorduyse TP yazilmali"


def test_long_sl_first_in_1m_gives_minus_one() -> None:
    df = _ambiguous_long()
    m1 = _frame1m("2026-01-01 00:15", [
        (100.0, 100.2, 98.5, 98.6),        # SL 99 ilk dakikada
        (98.6, 102.5, 98.6, 102.4),        # TP sonra
    ])
    r = _run(df, sl=99.0, tp=102.0, df_1m=m1)
    assert r.iloc[0] == pytest.approx(-1.0)


def _ambiguous_short() -> pd.DataFrame:
    """Giris 100 (bar1 open), SL 101, TP 98."""
    return _frame15([
        (100.0, 100.0, 100.0, 100.0),
        (100.0, 101.5, 97.5, 100.0),       # hem SL hem TP -> belirsiz
        (100.0, 100.0, 100.0, 100.0),
    ])


def test_short_tp_first_in_1m_gives_positive_r() -> None:
    df = _ambiguous_short()
    m1 = _frame1m("2026-01-01 00:15", [
        (100.0, 100.1, 97.5, 97.6),        # TP 98 ilk dakikada
        (97.6, 101.5, 97.6, 101.4),        # SL sonra
    ])
    r = _run(df, sl=101.0, tp=98.0, side="short", df_1m=m1)
    assert r.iloc[0] == pytest.approx(2.0)


def test_short_sl_first_in_1m_gives_minus_one() -> None:
    df = _ambiguous_short()
    m1 = _frame1m("2026-01-01 00:15", [
        (100.0, 101.5, 99.9, 101.4),       # SL 101 ilk dakikada
        (101.4, 101.4, 97.5, 97.6),        # TP sonra
    ])
    r = _run(df, sl=101.0, tp=98.0, side="short", df_1m=m1)
    assert r.iloc[0] == pytest.approx(-1.0)


# --- 3. fallback: belirsizlik cozulemezse asla iyimser ---------------------


def test_same_1m_bar_touching_both_falls_back_to_sl_first() -> None:
    """Tek 1m mumda hem TP hem SL -> sira yine bilinmiyor -> SL."""
    df = _ambiguous_long()
    m1 = _frame1m("2026-01-01 00:15", [
        (100.0, 102.5, 98.5, 100.0),       # ayni dakikada ikisi de
    ])
    r = _run(df, sl=99.0, tp=102.0, df_1m=m1)
    assert r.iloc[0] == pytest.approx(-1.0), "1m ici belirsizlik SL sayilmali"


def test_missing_1m_window_is_not_written_as_optimistic() -> None:
    """Ilgili pencerede 1m veri yok -> TP yazilmaz, SL-first uygulanir."""
    df = _ambiguous_long()
    far = _frame1m("2026-01-02 00:15", [(100.0, 100.1, 99.9, 100.0)])  # baska gun
    assert _run(df, sl=99.0, tp=102.0, df_1m=far).iloc[0] == pytest.approx(-1.0)
    assert _run(df, sl=99.0, tp=102.0, df_1m=None).iloc[0] == pytest.approx(-1.0)


def test_tz_aware_1m_data_is_aligned_not_silently_missed() -> None:
    """1m veri tz-aware gelirse UTC'ye indirilip ayni pencereye dusmeli.

    Hizalama bozulursa her vaka 'veri yok' sayilir ve mod sessizce eski
    davranisa doner -- yani hata yerine yanlis sonuc uretir.
    """
    df = _ambiguous_long()
    m1 = _frame1m("2026-01-01 00:15", [
        (100.0, 102.5, 99.9, 102.4),
        (102.4, 102.4, 98.5, 98.6),
    ])
    m1 = m1.tz_localize("UTC")
    r = _run(df, sl=99.0, tp=102.0, df_1m=m1)
    assert r.iloc[0] == pytest.approx(2.0), "tz-aware 1m veri hizalanmali"


# --- 4. gap sozlesmesi ------------------------------------------------------


def test_gap_beyond_stop_is_skipped_deterministically() -> None:
    """Sonraki open stopun altinda (long) -> setup gecersiz, islem atlanir.

    Gerekce: signalbot MAX_ADVERSE_ENTRY_DRIFT_R = 0.5; stopun otesine gecmis
    bir acilis >=1.0R aleyhine kaymadir, o sinyal kullaniciya hic gitmezdi.
    """
    df = _frame15([
        (100.0, 100.0, 100.0, 100.0),
        (98.5, 99.0, 98.0, 98.5),          # SL 99'un altinda aciyor
        (98.5, 103.0, 98.0, 102.0),
    ])
    r = _run(df, sl=99.0, tp=102.0)
    assert len(r) == 0, "stopun otesinde acilan islem alinmamali"


def test_gap_skip_is_counted_not_silent() -> None:
    df = _frame15([
        (100.0, 100.0, 100.0, 100.0),
        (98.5, 99.0, 98.0, 98.5),
        (98.5, 103.0, 98.0, 102.0),
    ])
    n = len(df)
    idx = df.index
    first = np.arange(n) == 0
    lvl = lambda v: pd.Series(np.where(first, v, np.nan), index=idx)
    nan = pd.Series(np.nan, index=idx)
    res = he.simulate_trades_with_stats(
        df, pd.Series(first, index=idx), pd.Series(False, index=idx),
        lvl(99.0), lvl(102.0), nan, nan, FREE,
        min_rr=0.5, max_rr=10.0, max_hold=50, fill_mode=NEW, df_1m=None,
    )
    assert res.stats["gap_skipped"] == 1


def test_stats_report_1m_resolution_counts() -> None:
    """Rapor icin: kac 15m bar cakisti, kaci 1m ile cozuldu, kaci fallback."""
    df = _ambiguous_long()
    m1 = _frame1m("2026-01-01 00:15", [
        (100.0, 102.5, 99.9, 102.4),
        (102.4, 102.4, 98.5, 98.6),
    ])
    n = len(df)
    idx = df.index
    first = np.arange(n) == 0
    lvl = lambda v: pd.Series(np.where(first, v, np.nan), index=idx)
    nan = pd.Series(np.nan, index=idx)
    res = he.simulate_trades_with_stats(
        df, pd.Series(first, index=idx), pd.Series(False, index=idx),
        lvl(99.0), lvl(102.0), nan, nan, FREE,
        min_rr=0.5, max_rr=10.0, max_hold=50, fill_mode=NEW, df_1m=m1,
    )
    assert res.stats["overlap_bars"] == 1
    assert res.stats["resolved_1m_tp"] == 1
    assert res.stats["resolved_1m_sl"] == 0
    assert res.stats["fallback_missing_1m"] == 0
    assert res.stats["fallback_ambiguous_1m"] == 0


# --- 5. eski mod regresyonu -------------------------------------------------


def test_default_mode_is_bar_sl_first_and_unchanged() -> None:
    """fill_mode verilmezse davranis eskisiyle birebir ayni olmali."""
    df = _ambiguous_long()
    n = len(df)
    idx = df.index
    first = np.arange(n) == 0
    lvl = lambda v: pd.Series(np.where(first, v, np.nan), index=idx)
    nan = pd.Series(np.nan, index=idx)
    args = (df, pd.Series(first, index=idx), pd.Series(False, index=idx),
            lvl(99.0), lvl(102.0), nan, nan, FREE)
    kw = dict(min_rr=0.5, max_rr=10.0, max_hold=50)

    implicit = he.simulate_trades(*args, **kw)
    explicit = he.simulate_trades(*args, fill_mode=OLD, **kw)
    assert implicit.iloc[0] == pytest.approx(-1.0)
    np.testing.assert_allclose(implicit.to_numpy(), explicit.to_numpy())


def test_old_mode_ignores_1m_data_entirely() -> None:
    """1m veri verilse bile eski mod onu kullanmamali (regresyon kalkani)."""
    df = _ambiguous_long()
    m1 = _frame1m("2026-01-01 00:15", [
        (100.0, 102.5, 99.9, 102.4),       # 1m'ye inilse TP cikardi
        (102.4, 102.4, 98.5, 98.6),
    ])
    r = _run(df, sl=99.0, tp=102.0, df_1m=m1, fill_mode=OLD)
    assert r.iloc[0] == pytest.approx(-1.0), "eski mod 1m veriyi dikkate almamali"


# --- 6. numba / python parite ----------------------------------------------


def test_new_mode_does_not_silently_use_numba_core() -> None:
    """Yeni mod numba cekirdeginde uygulanmadi; her iki bayrakta da AYNI sonuc.

    SINIRLAMA: `1m_then_sl_first` yalnizca saf Python referans yolunda calisir.
    Bu test o sinirlamayi sabitler -- cekirdek sonradan yazilirsa burasi kirilir
    ve parite bilincli olarak yeniden dogrulanmak zorunda kalir.
    """
    df = _ambiguous_long()
    m1 = _frame1m("2026-01-01 00:15", [
        (100.0, 102.5, 99.9, 102.4),
        (102.4, 102.4, 98.5, 98.6),
    ])
    with_fast = _run(df, sl=99.0, tp=102.0, df_1m=m1)
    original = he.FAST_CORE_AVAILABLE
    he.FAST_CORE_AVAILABLE = False
    try:
        without_fast = _run(df, sl=99.0, tp=102.0, df_1m=m1)
    finally:
        he.FAST_CORE_AVAILABLE = original
    np.testing.assert_allclose(with_fast.to_numpy(), without_fast.to_numpy())
    assert with_fast.iloc[0] == pytest.approx(2.0)


def test_unknown_fill_mode_raises() -> None:
    df = _ambiguous_long()
    with pytest.raises(ValueError, match="fill_mode"):
        _run(df, sl=99.0, tp=102.0, fill_mode="optimistic")
