"""XAUUSD NY-acilis ORB edge'ini rejimlere bolup saglam cep ariyoruz.

new_edge_scan ham gold ORB'u +0.03R (marjinal) buldu ama 4.3 trade/hf ile saglam
frekans var. NQ ORB da tek basina zayifti, strong_trend rejiminde guclendi. Ayni
yaklasimla gold ORB'a ADX/ATR/saat rejim filtresi uygulayip exp_r'yi kullanilabilir
seviyeye (>=0.08R) cikaran, >=3/4 yil pozitif cep ariyoruz.

Baz setup (new_edge_scan en iyi saglam): XAUUSD 13.5 open, 60dk range, vwap trend,
rr=1.0, other_side SL, hold=48.

Calistir:
    python -m intraday.gold_orb_regime
"""
from __future__ import annotations

import sys
import warnings
import logging
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
logging.disable(logging.INFO)
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from . import data
from .config import INSTRUMENTS, ATR_LEN
from .edge_lab import _adx
from .honest_engine import simulate_trades, metrics
from .indicators import atr
from .internet_seed_strategies import ORBCase, _build_orb

OUT = Path(__file__).resolve().parent.parent / "outputs" / "intraday"


def build_orb_ledger(symbol: str = "XAUUSD", open_hour: float = 13.5,
                     days: int = 1080, entry_mode: str = "close",
                     trend: str = "vwap") -> tuple[pd.DataFrame, pd.DataFrame]:
    df = data.load_ohlcv(symbol, "5m", days)
    case = ORBCase(symbol, open_hour, 60, 21.0, entry_mode, trend, 1.0, "other_side", 1.0, 48)
    le, se, lsl, ltp, ssl, stp = _build_orb(df, case)
    r = simulate_trades(df, le, se, lsl, ltp, ssl, stp, INSTRUMENTS[symbol],
                        min_rr=0.99, max_rr=1.0, max_hold=48)

    a = atr(df, ATR_LEN)
    atr_pct = a / df["close"]
    atr_rank = atr_pct.rolling(500, min_periods=100).rank(pct=True)
    adx = _adx(df, 14)

    led = pd.DataFrame(index=r.index)
    led["r"] = r
    led["dir"] = np.where(le.reindex(r.index).fillna(False), "long", "short")
    led["year"] = led.index.year.astype(str)
    led["dow"] = led.index.dayofweek
    led["hour"] = led.index.hour
    led["adx"] = adx.reindex(r.index)
    led["atr_rank"] = atr_rank.reindex(r.index)
    led["adx_regime"] = pd.cut(led["adx"], [-np.inf, 20, 30, np.inf],
                               labels=["chop", "trend", "strong_trend"]).astype(str)
    led["atr_regime"] = pd.cut(led["atr_rank"], [-0.01, 0.33, 0.67, 1.01],
                               labels=["low_vol", "mid_vol", "high_vol"]).astype(str)
    return led.dropna(subset=["r"]), df


def build_gold_orb_ledger(days: int = 1080, entry_mode: str = "close") -> tuple[pd.DataFrame, pd.DataFrame]:
    """Geriye uyumluluk: XAUUSD NY-ORB (13.5) ledger."""
    return build_orb_ledger("XAUUSD", 13.5, days, entry_mode, "vwap")


def _summ(name, sub, weeks):
    if len(sub) < 12:
        return None
    yr = sub["r"].groupby(sub.index.year).mean()
    posy = sum(1 for v in yr if v > 0)
    wins = sub.loc[sub.r > 0, "r"].sum()
    loss = -sub.loc[sub.r < 0, "r"].sum()
    pf = wins / loss if loss > 0 else np.inf
    return {
        "filter": name, "trades": len(sub), "tr_wk": round(len(sub) / weeks, 2),
        "exp_r": round(float(sub.r.mean()), 3),
        "win_rate": round(float((sub.r > 0).mean() * 100), 1),
        "pf": round(float(pf), 3), "pos_years": f"{posy}/{len(yr)}",
        "min_yr": round(float(yr.min()), 3), "total_R": round(float(sub.r.sum()), 1),
    }


def main(days: int = 1080) -> None:
    print(f"\n{'='*96}")
    print("  XAUUSD NY-ORB REJIM TARAMASI (honest engine, vwap/13.5/60dk/rr1.0)")
    print(f"{'='*96}\n")

    for em in ("close", "retest"):
        led, df = build_gold_orb_ledger(days, entry_mode=em)
        weeks = (df.index[-1] - df.index[0]).days / 7
        base = _summ(f"BAZ ({em})", led, weeks)
        print(f"  BAZ [{em}]: {base['trades']}tr {base['tr_wk']}/hf exp={base['exp_r']:+.3f} "
              f"WR={base['win_rate']}% PF={base['pf']} posY={base['pos_years']} minYr={base['min_yr']}")

        rows = []
        # tekli rejim filtreleri
        for reg in ("trend", "strong_trend"):
            rows.append(_summ(f"adx={reg}", led[led.adx_regime == reg], weeks))
        rows.append(_summ("adx>=trend", led[led.adx_regime.isin(["trend", "strong_trend"])], weeks))
        for reg in ("low_vol", "mid_vol", "high_vol"):
            rows.append(_summ(f"atr={reg}", led[led.atr_regime == reg], weeks))
        rows.append(_summ("atr<high", led[led.atr_regime != "high_vol"], weeks))
        for d in ("long", "short"):
            rows.append(_summ(f"dir={d}", led[led.dir == d], weeks))
        # kombinasyonlar
        rows.append(_summ("adx>=trend & atr<high",
                          led[led.adx_regime.isin(["trend", "strong_trend"]) & (led.atr_regime != "high_vol")], weeks))
        rows.append(_summ("strong_trend & atr<high",
                          led[(led.adx_regime == "strong_trend") & (led.atr_regime != "high_vol")], weeks))
        rows.append(_summ("adx>=trend & long",
                          led[led.adx_regime.isin(["trend", "strong_trend"]) & (led.dir == "long")], weeks))

        res = pd.DataFrame([x for x in rows if x]).sort_values("exp_r", ascending=False)
        print(res.to_string(index=False))
        print()

    print(f"{'='*96}\n")


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--days", type=int, default=1080)
    a = p.parse_args()
    main(a.days)
