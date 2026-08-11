"""Muhafazakâr R-bazlı backtest motoru (GERÇEK doldurma modeli).

vectorbt'nin iyimser doldurması edge'i şişiriyordu; bu motor her işlemi
bar-bar, muhafazakâr simüle eder:
  - Aynı barda hem SL hem TP varsa SL önce sayılır (en kötü durum).
  - Maliyet (spread+komisyon+kayma) gidiş-dönüş, R cinsinden düşülür.
  - Zaman limiti (MAX_HOLD) sonunda işlem piyasada kapanır.

Çıktı: her işlemin (giriş_zamanı, R-katsayısı) serisi + özet metrikler.
Tüm konfluens testleri bu motoru kullanır.

İki doldurma modu vardır (`fill_mode`):
  - `bar_sl_first` (VARSAYILAN, değişmedi): giriş sinyal mumunun kapanışı;
    aynı barda SL+TP görülürse SL yazılır.
  - `1m_then_sl_first` (opt-in): giriş sonraki barın open'ı; SL yapısal
    seviyede kalır, hedef R korunarak TP yeni girişe göre fiyatlanır. Yalnızca
    SL+TP'nin aynı barda görüldüğü belirsiz vakalarda o barın 1m OHLC'sine
    inilir. Çözülemezse yine SL yazılır — asla iyimser sonuç üretilmez.

Yeni mod yalnızca saf Python referans yolunda çalışır; numba çekirdeği
`bar_sl_first` için kalır (bkz test_honest_engine_1m.py).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .config import Instrument, ATR_LEN
from .fast_honest_core import FAST_CORE_AVAILABLE, simulate_trades_core
from .indicators import atr

MAX_HOLD_DEFAULT = 480   # 5 işlem günü (15m)

FILL_BAR_SL_FIRST = "bar_sl_first"
FILL_1M_THEN_SL_FIRST = "1m_then_sl_first"
FILL_MODES = (FILL_BAR_SL_FIRST, FILL_1M_THEN_SL_FIRST)


@dataclass(frozen=True)
class FillResult:
    """R serisi + doldurma teşhis sayaçları."""
    r: pd.Series
    stats: dict


def _empty_stats() -> dict:
    return {
        "overlap_bars": 0,            # 15m'de hem SL hem TP görülen bar sayısı
        "resolved_1m_tp": 0,          # 1m ile TP-first çözülen
        "resolved_1m_sl": 0,          # 1m ile SL-first çözülen
        "fallback_ambiguous_1m": 0,   # tek 1m mumda ikisi de -> SL
        "fallback_missing_1m": 0,     # 1m penceresi yok/bozuk -> SL
        "gap_skipped": 0,             # giriş stopun ötesinde açtı -> atlandı
    }


def _normalize_1m(df_1m: pd.DataFrame | None) -> pd.DataFrame | None:
    """1m veriyi UTC tz-naive'e indir ve sırala (15m indeksiyle hizalanmalı)."""
    if df_1m is None or len(df_1m) == 0:
        return None
    idx = df_1m.index
    if getattr(idx, "tz", None) is not None:
        df_1m = df_1m.tz_convert("UTC").tz_localize(None)
    return df_1m.sort_index()


def _bar_ends(idx: pd.DatetimeIndex) -> np.ndarray:
    """Her barın [başlangıç, bitiş) penceresindeki bitiş damgası."""
    if len(idx) == 0:
        return np.array([], dtype="datetime64[ns]")
    deltas = pd.Series(idx).diff().dropna()
    step = deltas.median() if len(deltas) else pd.Timedelta(minutes=15)
    return np.append(idx.to_numpy()[1:], (idx[-1] + step).to_numpy())


def _resolve_with_1m(
    df_1m: pd.DataFrame | None,
    bar_start,
    bar_end,
    is_long: bool,
    sl_px: float,
    tp_px: float,
    stats: dict,
) -> bool:
    """Belirsiz 15m barı 1m ile çöz. TP önce ise True, aksi halde False (SL)."""
    if df_1m is None:
        stats["fallback_missing_1m"] += 1
        return False
    win = df_1m.loc[(df_1m.index >= bar_start) & (df_1m.index < bar_end)]
    if len(win) == 0:
        stats["fallback_missing_1m"] += 1
        return False
    highs = win["high"].to_numpy(dtype=float)
    lows = win["low"].to_numpy(dtype=float)
    for k in range(len(win)):
        hit_sl = lows[k] <= sl_px if is_long else highs[k] >= sl_px
        hit_tp = highs[k] >= tp_px if is_long else lows[k] <= tp_px
        if hit_sl and hit_tp:      # tek dakikada ikisi de -> sıra yine bilinmiyor
            stats["fallback_ambiguous_1m"] += 1
            return False
        if hit_sl:
            stats["resolved_1m_sl"] += 1
            return False
        if hit_tp:
            stats["resolved_1m_tp"] += 1
            return True
    # 15m dokunduğunu söylüyor ama 1m hiçbirine değmiyor -> veri bütünlüğü bozuk
    stats["fallback_missing_1m"] += 1
    return False


def simulate_trades(
    df: pd.DataFrame,
    long_entry: pd.Series,
    short_entry: pd.Series,
    long_sl: pd.Series,
    long_tp: pd.Series,
    short_sl: pd.Series,
    short_tp: pd.Series,
    instrument: Instrument,
    min_rr: float = 2.0,
    max_rr: float = 6.0,
    max_hold: int = MAX_HOLD_DEFAULT,
    fill_mode: str = FILL_BAR_SL_FIRST,
    df_1m: pd.DataFrame | None = None,
) -> pd.Series:
    """Sinyalleri simüle et, (zaman -> R) serisi döndür."""
    return simulate_trades_with_stats(
        df, long_entry, short_entry, long_sl, long_tp, short_sl, short_tp,
        instrument, min_rr=min_rr, max_rr=max_rr, max_hold=max_hold,
        fill_mode=fill_mode, df_1m=df_1m,
    ).r


def simulate_trades_with_stats(
    df: pd.DataFrame,
    long_entry: pd.Series,
    short_entry: pd.Series,
    long_sl: pd.Series,
    long_tp: pd.Series,
    short_sl: pd.Series,
    short_tp: pd.Series,
    instrument: Instrument,
    min_rr: float = 2.0,
    max_rr: float = 6.0,
    max_hold: int = MAX_HOLD_DEFAULT,
    fill_mode: str = FILL_BAR_SL_FIRST,
    df_1m: pd.DataFrame | None = None,
) -> FillResult:
    """`simulate_trades` + doldurma teşhis sayaçları (karşılaştırma raporu için)."""
    if fill_mode not in FILL_MODES:
        raise ValueError(
            f"Bilinmeyen fill_mode: {fill_mode!r}. Gecerli: {FILL_MODES}"
        )
    if fill_mode == FILL_1M_THEN_SL_FIRST:
        return _simulate_1m_then_sl_first(
            df, long_entry, short_entry, long_sl, long_tp, short_sl, short_tp,
            instrument, min_rr, max_rr, max_hold, df_1m,
        )
    return FillResult(
        _simulate_bar_sl_first(
            df, long_entry, short_entry, long_sl, long_tp, short_sl, short_tp,
            instrument, min_rr, max_rr, max_hold,
        ),
        _empty_stats(),
    )


def _simulate_bar_sl_first(
    df: pd.DataFrame,
    long_entry: pd.Series,
    short_entry: pd.Series,
    long_sl: pd.Series,
    long_tp: pd.Series,
    short_sl: pd.Series,
    short_tp: pd.Series,
    instrument: Instrument,
    min_rr: float,
    max_rr: float,
    max_hold: int,
) -> pd.Series:
    """Varsayılan mod: giriş sinyal kapanışı, aynı barda SL+TP -> SL."""
    price = df["close"].to_numpy()
    high = df["high"].to_numpy()
    low = df["low"].to_numpy()
    idx = df.index
    n = len(df)
    cost = instrument.cost_per_side

    le = long_entry.fillna(False).to_numpy()
    se = short_entry.fillna(False).to_numpy()
    lsl = long_sl.to_numpy(dtype=float)
    ltp = long_tp.to_numpy(dtype=float)
    ssl = short_sl.to_numpy(dtype=float)
    stp = short_tp.to_numpy(dtype=float)

    if FAST_CORE_AVAILABLE:
        trade_i, trade_r = simulate_trades_core(
            price.astype(np.float64),
            high.astype(np.float64),
            low.astype(np.float64),
            le.astype(np.bool_),
            se.astype(np.bool_),
            lsl.astype(np.float64),
            ltp.astype(np.float64),
            ssl.astype(np.float64),
            stp.astype(np.float64),
            float(cost),
            float(min_rr),
            float(max_rr),
            int(max_hold),
        )
        if len(trade_i) == 0:
            return pd.Series(dtype=float)
        return pd.Series(trade_r, index=idx[trade_i]).sort_index()

    out = {}
    last_exit = -1   # üst üste binen işlemleri engelle (pozisyon yokken gir)
    for i in range(n):
        is_long = le[i]
        is_short = se[i]
        if not (is_long or is_short) or i <= last_exit:
            continue
        entry = price[i]
        if is_long:
            sl_px, tp_px = lsl[i], ltp[i]
        else:
            sl_px, tp_px = ssl[i], stp[i]
        if not (np.isfinite(sl_px) and np.isfinite(tp_px)):
            continue
        risk = (entry - sl_px) if is_long else (sl_px - entry)
        reward = (tp_px - entry) if is_long else (entry - tp_px)
        if risk <= 0 or reward <= 0:
            continue
        rr = reward / risk
        if rr < min_rr:
            continue
        if rr > max_rr:  # hedefi tavanla
            if is_long:
                tp_px = entry + max_rr * risk
            else:
                tp_px = entry - max_rr * risk
            rr = max_rr

        slf = risk / entry
        outcome = None
        for j in range(i + 1, min(i + 1 + max_hold, n)):
            if is_long:
                if low[j] <= sl_px:
                    outcome = -1.0; last_exit = j; break
                if high[j] >= tp_px:
                    outcome = rr; last_exit = j; break
            else:
                if high[j] >= sl_px:
                    outcome = -1.0; last_exit = j; break
                if low[j] <= tp_px:
                    outcome = rr; last_exit = j; break
        if outcome is None:
            jx = min(i + max_hold, n - 1)
            exitp = price[jx]
            move = (exitp - entry) if is_long else (entry - exitp)
            outcome = move / risk
            last_exit = jx
        outcome -= 2 * cost / slf      # gidiş-dönüş maliyet, R cinsinden
        out[idx[i]] = outcome

    return pd.Series(out).sort_index() if out else pd.Series(dtype=float)


def _simulate_1m_then_sl_first(
    df: pd.DataFrame,
    long_entry: pd.Series,
    short_entry: pd.Series,
    long_sl: pd.Series,
    long_tp: pd.Series,
    short_sl: pd.Series,
    short_tp: pd.Series,
    instrument: Instrument,
    min_rr: float,
    max_rr: float,
    max_hold: int,
    df_1m: pd.DataFrame | None,
) -> FillResult:
    """Opt-in mod: sonraki open girişi + belirsiz barlarda 1m çözümü.

    Saf Python; numba çekirdeği bu modda KULLANILMAZ (parite testiyle sabit).
    """
    opn = df["open"].to_numpy(dtype=float)
    price = df["close"].to_numpy(dtype=float)
    high = df["high"].to_numpy(dtype=float)
    low = df["low"].to_numpy(dtype=float)
    idx = df.index
    ends = _bar_ends(idx)
    n = len(df)
    cost = instrument.cost_per_side
    m1 = _normalize_1m(df_1m)
    stats = _empty_stats()

    le = long_entry.fillna(False).to_numpy()
    se = short_entry.fillna(False).to_numpy()
    lsl = long_sl.to_numpy(dtype=float)
    ltp = long_tp.to_numpy(dtype=float)
    ssl = short_sl.to_numpy(dtype=float)
    stp = short_tp.to_numpy(dtype=float)

    out = {}
    last_exit = -1
    for i in range(n):
        is_long = le[i]
        if not (is_long or se[i]) or i <= last_exit:
            continue
        e = i + 1                      # giriş barı: sinyalden SONRAKİ bar
        if e >= n:
            continue
        sl_px, tp_px = (lsl[i], ltp[i]) if is_long else (ssl[i], stp[i])
        if not (np.isfinite(sl_px) and np.isfinite(tp_px)):
            continue

        # rr sinyal anında kesinleşir (filtre kararı orada verilir)
        sig = price[i]
        risk0 = (sig - sl_px) if is_long else (sl_px - sig)
        reward0 = (tp_px - sig) if is_long else (sig - tp_px)
        if risk0 <= 0 or reward0 <= 0:
            continue
        rr = min(reward0 / risk0, max_rr)
        if reward0 / risk0 < min_rr:
            continue

        entry = opn[e]
        risk = (entry - sl_px) if is_long else (sl_px - entry)
        if risk <= 0:
            # Açılış stopun ötesinde: setup geçersiz, sinyal kullanıcıya hiç
            # gitmezdi (signalbot MAX_ADVERSE_ENTRY_DRIFT_R = 0.5).
            stats["gap_skipped"] += 1
            continue
        tp_new = (entry + rr * risk) if is_long else (entry - rr * risk)
        slf = risk / entry

        outcome = None
        for j in range(e, min(e + max_hold, n)):
            hit_sl = low[j] <= sl_px if is_long else high[j] >= sl_px
            hit_tp = high[j] >= tp_new if is_long else low[j] <= tp_new
            if hit_sl and hit_tp:
                stats["overlap_bars"] += 1
                tp_first = _resolve_with_1m(
                    m1, idx[j], ends[j], is_long, sl_px, tp_new, stats,
                )
                outcome = rr if tp_first else -1.0
                last_exit = j
                break
            if hit_sl:
                outcome = -1.0; last_exit = j; break
            if hit_tp:
                outcome = rr; last_exit = j; break
        if outcome is None:
            jx = min(e + max_hold - 1, n - 1)
            exitp = price[jx]
            move = (exitp - entry) if is_long else (entry - exitp)
            outcome = move / risk
            last_exit = jx
        outcome -= 2 * cost / slf      # gidiş-dönüş maliyet, R cinsinden
        out[idx[i]] = outcome

    r = pd.Series(out).sort_index() if out else pd.Series(dtype=float)
    return FillResult(r, stats)


def metrics(r: pd.Series) -> dict:
    """R serisinden özet metrikler."""
    n = len(r)
    if n == 0:
        return {"trades": 0, "exp_r": np.nan, "win_rate": np.nan, "pf": np.nan}
    wins = r[r > 0]
    losses = r[r < 0]
    gross_win = wins.sum()
    gross_loss = -losses.sum()
    return {
        "trades": n,
        "exp_r": round(float(r.mean()), 3),
        "win_rate": round(float((r > 0).mean() * 100), 1),
        "avg_win": round(float(wins.mean()), 2) if len(wins) else 0.0,
        "avg_loss": round(float(losses.mean()), 2) if len(losses) else 0.0,
        "pf": round(float(gross_win / gross_loss), 3) if gross_loss > 0 else np.inf,
    }


def oos_metrics(r: pd.Series, folds) -> dict:
    """Fold-bazlı OOS değerlendirme (tutarlılık için)."""
    rows = []
    for (_, _, te0, te1) in folds:
        sub = r.loc[te0:te1]
        m = metrics(sub)
        m["ret"] = float((sub * 1.0).sum())  # R toplamı
        rows.append(m)
    fr = pd.DataFrame(rows)
    valid = fr[fr["trades"] > 0]
    if valid.empty:
        return {"oos_exp_r": np.nan, "pos_folds": "0/0", "total_trades": 0}
    w = valid["trades"]
    return {
        "oos_exp_r": round(float(np.average(valid["exp_r"], weights=w)), 3),
        "pos_folds": f"{int((valid['ret'] > 0).sum())}/{len(valid)}",
        "total_trades": int(fr["trades"].sum()),
        "total_R": round(float(r.sum()), 1),
    }
