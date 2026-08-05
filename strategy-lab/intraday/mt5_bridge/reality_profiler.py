"""Gercek emir maliyeti profili (MT5 tick verisinden).

honest_engine her modulu tek bir `cost_per_side` (fiyat orani) ile cezalandirir.
Bu modul o varsayimi GERCEKLE kiyaslar:

  1. Baz spread  : tick'lerden medyan (ask-bid)/mid orani, seans saatine gore.
  2. Slippage    : ardisik tick'lerdeki ters yonlu sicramalarin 90. yuzdeligi
                   (stop fill'inin seviyeden ne kadar kotu dolabilecegi proxy'si).
  3. Fiyat-seviye duzeltmesi: spread PUAN olarak ~sabit; backtest doneminde fiyat
                   daha dusukse spread ORANI daha yuksekti. now->then olcekleme.

Cikti: sembol basina gercek tek-yon maliyet orani (+ guven bandi) ve config
varsayimiyla kiyas. Tum girdiler olculur, tahmin edilmez.

Calistir:
    python -m intraday.mt5_bridge.reality_profiler
"""
from __future__ import annotations

import json
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from ..config import INSTRUMENTS
from . import mt5_io

OUT = Path(__file__).resolve().parent.parent.parent / "outputs" / "intraday" / "mt5_bridge"
OUT.mkdir(parents=True, exist_ok=True)

# Hangi modul hangi sembolu kullaniyor + backtest doneminde tipik fiyat seviyesi.
# backtest_price ~ 2022-2025 ortalama (oran duzeltmesi icin). None ise duzeltme yok.
PROFILE_TARGETS = {
    "EURUSD": {"session": (7, 20), "backtest_price": 1.08},
    "XAUUSD": {"session": (7, 21), "backtest_price": 2100.0},
    "NASDAQ100": {"session": (13, 21), "backtest_price": 16000.0},
    "SP500": {"session": (13, 21), "backtest_price": 5000.0},
}


def _spread_by_hour(tk: pd.DataFrame) -> pd.DataFrame:
    g = tk.groupby(tk.index.hour)["spread_ratio"]
    return pd.DataFrame({
        "median": g.median(),
        "p90": g.quantile(0.90),
        "n": g.size(),
    })


def _session_spread(tk: pd.DataFrame, session: tuple[int, int]) -> dict:
    lo, hi = session
    mask = (tk.index.hour >= lo) & (tk.index.hour < hi)
    sub = tk.loc[mask, "spread_ratio"]
    if len(sub) == 0:
        sub = tk["spread_ratio"]
    return {
        "spread_one_side_median": float(sub.median()) / 2.0,
        "spread_one_side_p90": float(sub.quantile(0.90)) / 2.0,
        "ticks": int(len(sub)),
    }


def _slippage(tk: pd.DataFrame, session: tuple[int, int]) -> dict:
    """Tek-tick fiyat sicramasi dagilimi -> stop fill slippage proxy'si.

    Stop emri tetiklendiginde gercek fill, bir sonraki tick'tedir. Ardisik mid
    farkinin buyuklugu, o anki fill kaymasinin ust siniridir. Ters-yonlu
    hareketin 90. yuzdeligini tek-yon slippage orani kabul ederiz.
    """
    lo, hi = session
    mask = (tk.index.hour >= lo) & (tk.index.hour < hi)
    mid = tk.loc[mask, "mid"]
    if len(mid) < 100:
        mid = tk["mid"]
    jumps = mid.diff().abs() / mid
    jumps = jumps.replace([np.inf, -np.inf], np.nan).dropna()
    return {
        "slippage_median": float(jumps.median()),
        "slippage_p90": float(jumps.quantile(0.90)),
    }


def profile_symbol(key: str, days: int = 5) -> dict:
    cfg = PROFILE_TARGETS[key]
    meta = mt5_io.symbol_meta(key)
    tk = mt5_io.ticks(key, days=days)

    session = cfg["session"]
    spr = _session_spread(tk, session)
    slip = _slippage(tk, session)

    # Fiyat-seviye duzeltmesi: spread puan olarak ~sabit -> oran ~ 1/fiyat.
    price_now = float(tk["mid"].median())
    bt_price = cfg.get("backtest_price")
    level_factor = (price_now / bt_price) if bt_price else 1.0  # >1 => o donem oran daha yuksekti

    spread_then = spr["spread_one_side_median"] * level_factor
    spread_then_p90 = spr["spread_one_side_p90"] * level_factor
    # slippage da puan-temelli; ayni olcekleme.
    slip_then = slip["slippage_p90"] * level_factor

    assumed = INSTRUMENTS[key].cost_per_side if key in INSTRUMENTS else np.nan

    # Gercekci tek-yon maliyet = donem-duzeltilmis spread + slippage (stop fill).
    real_cost_central = spread_then + slip_then
    real_cost_high = spread_then_p90 + slip_then  # kotumser ust bant

    return {
        "symbol": key,
        "mt5_name": meta["name"],
        "price_now": round(price_now, 4),
        "backtest_price": bt_price,
        "level_factor": round(level_factor, 3),
        "spread_one_side_now": spr["spread_one_side_median"],
        "spread_one_side_period_adj": spread_then,
        "slippage_p90": slip["slippage_p90"],
        "real_cost_per_side_central": real_cost_central,
        "real_cost_per_side_high": real_cost_high,
        "assumed_cost_per_side": assumed,
        "assumed_vs_real_ratio": round(assumed / real_cost_central, 2) if real_cost_central > 0 else np.nan,
        "verdict": _verdict(assumed, real_cost_central, real_cost_high),
        "ticks": spr["ticks"],
    }


def _verdict(assumed: float, real_central: float, real_high: float) -> str:
    if np.isnan(assumed):
        return "config-yok"
    if assumed >= real_high:
        return "MUHAFAZAKAR (config gercekten kotu)"
    if assumed >= real_central:
        return "DENGELI (config medyani asiyor, p90 altinda)"
    return "IYIMSER (config gercegi hafife aliyor)"


def main(days: int = 5) -> None:
    print("\n" + "=" * 100)
    print("  MT5 REALITY PROFILER — config.cost_per_side vs gercek spread+slippage")
    print("=" * 100 + "\n")
    rows = []
    with mt5_io.session():
        acc = mt5_io.account()
        print(f"  Hesap: {acc['login']} @ {acc['server']} | connected={acc['connected']}\n")
        for key in PROFILE_TARGETS:
            try:
                rows.append(profile_symbol(key, days=days))
                print(f"  [OK] {key}")
            except mt5_io.MT5Error as e:
                print(f"  [ATLA] {key}: {e}")

    if not rows:
        print("\n  Profil uretilemedi.")
        return

    df = pd.DataFrame(rows)
    csv = OUT / "reality_profile.csv"
    js = OUT / "reality_profile.json"
    df.to_csv(csv, index=False)
    js.write_text(json.dumps(rows, indent=2, default=float), encoding="utf-8")

    cols = ["symbol", "price_now", "level_factor", "spread_one_side_period_adj",
            "slippage_p90", "real_cost_per_side_central", "assumed_cost_per_side",
            "assumed_vs_real_ratio", "verdict"]
    print("\n" + df[cols].to_string(index=False, float_format=lambda x: f"{x:.6f}"))
    print(f"\n  CSV : {csv}")
    print(f"  JSON: {js}")
    print("\n  Yorum: assumed_vs_real_ratio > 1 => config muhafazakar (iyi).")
    print("         verdict 'IYIMSER' ise o modul reality-discount'ta cezalanir.")
    print("\n" + "=" * 100 + "\n")


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--days", type=int, default=5)
    args = p.parse_args()
    main(args.days)
