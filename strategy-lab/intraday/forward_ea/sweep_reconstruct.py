"""NQ sweep core'u mevcut ledger'a karsi yeniden kur ve DOGRULA.

Sweep ureteci temizlenmis kodda yok; bu script smc_sweep + honest_engine ile
sweep_regime_ledger.csv'yi (39 trade, win %43.6, exp +0.855) yeniden uretmeyi
dener. Amac: canli detektore guvenmeden ONCE config'in dogru oldugunu kanitlamak
(EUR hatasini tekrarlamamak).

Calistir:
    python -m intraday.forward_ea.sweep_reconstruct
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
import logging
logging.disable(logging.INFO)
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from .. import data
from ..config import INSTRUMENTS
from ..edge_lab import _adx
from ..honest_engine import simulate_trades
from ..indicators import atr, htf_trend
from ..strategies import smc_sweep

OUT = Path(__file__).resolve().parent.parent.parent / "outputs" / "intraday"
REF = OUT / "sweep_regime_ledger.csv"


def reconstruct(lookback: int, min_rr: float, trend_mode: str, ote: bool,
                adx_min: float = 20.0, atr_rank_max: float = 0.67,
                days: int = 1080) -> pd.Series:
    df = data.load_ohlcv("NASDAQ100", "15m", days)
    df_1h = data.load_ohlcv("NASDAQ100", "1H", days)
    trend = htf_trend(df.index, df_1h)
    sig = smc_sweep(df, trend, lookback=lookback, trend_mode=trend_mode, ote=ote)

    # PREMIUM filtre (ledger rejimlerinden geri cikarildi):
    #   adx > adx_min (hic chop yok) + atr_pct rank < atr_rank_max (hic high_vol yok)
    adx = _adx(df, 14)
    atr_pct = atr(df, 14) / df["close"]
    atr_rank = atr_pct.rolling(500, min_periods=100).rank(pct=True)
    ok = (adx > adx_min) & (atr_rank < atr_rank_max)

    le = sig.long_entry & ok
    se = sig.short_entry & ok
    r = simulate_trades(
        df, le, se, sig.long_sl, sig.long_tp, sig.short_sl, sig.short_tp,
        INSTRUMENTS["NASDAQ100"], min_rr=min_rr, max_rr=6.0,
    )
    return r


def _stats(r: pd.Series) -> dict:
    return {
        "trades": len(r),
        "win_pct": round((r > 0).mean() * 100, 1) if len(r) else 0,
        "exp_r": round(r.mean(), 3) if len(r) else 0,
        "total_R": round(r.sum(), 2) if len(r) else 0,
    }


def main() -> None:
    ref = pd.read_csv(REF)
    ref_stats = {"trades": len(ref), "win_pct": round((ref["r"] > 0).mean() * 100, 1),
                 "exp_r": round(ref["r"].mean(), 3), "total_R": round(ref["r"].sum(), 2)}
    print("\n" + "=" * 92)
    print("  SWEEP CORE RECONSTRUCTION — ledger'a karsi dogrulama")
    print("=" * 92)
    print(f"  HEDEF (ledger): {ref_stats}\n")

    grid = []
    for lookback in (15, 20, 25):
        for min_rr in (2.0, 2.5):
            for trend_mode in ("strict", "loose"):
                for ote in (False, True):
                    try:
                        r = reconstruct(lookback, min_rr, trend_mode, ote)
                        s = _stats(r)
                        # ledger'a yakinlik skoru (trade sayisi + exp)
                        score = abs(s["trades"] - ref_stats["trades"]) + \
                                abs(s["exp_r"] - ref_stats["exp_r"]) * 20
                        grid.append({"lookback": lookback, "min_rr": min_rr,
                                     "trend_mode": trend_mode, "ote": ote,
                                     "score": round(score, 1), **s})
                    except Exception as e:
                        print(f"  hata: {e}")
    g = pd.DataFrame(grid).sort_values("score")
    print(g.to_string(index=False))
    best = g.iloc[0]
    print(f"\n  EN YAKIN config: lookback={best['lookback']} min_rr={best['min_rr']} "
          f"trend_mode={best['trend_mode']} ote={best['ote']}")
    print(f"  -> trades={best['trades']} (hedef {ref_stats['trades']}), "
          f"win%={best['win_pct']} (hedef {ref_stats['win_pct']}), "
          f"exp={best['exp_r']} (hedef {ref_stats['exp_r']})")
    match = abs(best["trades"] - ref_stats["trades"]) <= 4 and abs(best["exp_r"] - ref_stats["exp_r"]) <= 0.15
    print(f"\n  SONUC: {'ESLESTI — config guvenilir, canliya wire edilebilir.' if match else 'ESLESMEDI — config geri cikarilamadi, wire RISKLI.'}")
    print("=" * 92 + "\n")


if __name__ == "__main__":
    main()
