"""Muhafazakâr R-bazlı backtest motoru (GERÇEK doldurma modeli).

vectorbt'nin iyimser doldurması edge'i şişiriyordu; bu motor her işlemi
bar-bar, muhafazakâr simüle eder:
  - Aynı barda hem SL hem TP varsa SL önce sayılır (en kötü durum).
  - Maliyet (spread+komisyon+kayma) gidiş-dönüş, R cinsinden düşülür.
  - Zaman limiti (MAX_HOLD) sonunda işlem piyasada kapanır.

Çıktı: her işlemin (giriş_zamanı, R-katsayısı) serisi + özet metrikler.
Tüm konfluens testleri bu motoru kullanır.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .config import Instrument, ATR_LEN
from .fast_honest_core import FAST_CORE_AVAILABLE, simulate_trades_core
from .indicators import atr

MAX_HOLD_DEFAULT = 480   # 5 işlem günü (15m)


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
) -> pd.Series:
    """Sinyalleri muhafazakâr modelle simüle et, (zaman -> R) serisi döndür."""
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
