"""Fill-modeli A/B: `bar_sl_first` (eski) vs `1m_then_sl_first` (yeni).

Ayni sembol, ayni donem, ayni fee/slippage, ayni sinyaller. Tek degisen
doldurma varsayimi. Amac bir edge iddiasi DEGIL: backtest varsayiminin
sonucu ne kadar tasidigini olcmek.

Calistir:
    python -m intraday.fill_model_ab
"""
from __future__ import annotations

import sys
import warnings

warnings.filterwarnings("ignore")
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

import numpy as np
import pandas as pd

from . import data
from .config import INSTRUMENTS
from .edge_lab import _adx
from .honest_engine import (
    FILL_1M_THEN_SL_FIRST,
    FILL_BAR_SL_FIRST,
    metrics,
    simulate_trades_with_stats,
)
from .internet_seed_strategies import ORBCase, _build_orb

DAYS = 540
ADX_MIN = 30.0
SYMBOLS = ["NASDAQ100", "SP500"]

# NQ_ORB kanitli config -- degistirilmez (bkz orb_cross_symbol.py)
BASE = dict(open_hour=14.5, range_minutes=15, trade_end_hour=20.5,
            entry_mode="retest", trend_filter="none", rr=1.5,
            sl_mode="other_side", atr_mult=1.0, max_hold=48)

# SWEEP_CORE canli dedektoruyle ayni esikler (forward_ea/modules.py:182)
SWEEP_ADX = 25.0
SWEEP_MIN_RR = 2.0


def _max_drawdown(r: pd.Series) -> float:
    """R egrisinin en buyuk tepe-dip dususu (R cinsinden)."""
    if len(r) == 0:
        return 0.0
    curve = r.cumsum()
    return float((curve - curve.cummax()).min())


def _orb_signals(df: pd.DataFrame, symbol: str):
    case = ORBCase(symbol, **BASE)
    le, se, lsl, ltp, ssl, stp = _build_orb(df, case)
    ok = _adx(df, 14) > ADX_MIN
    return le & ok, se & ok, lsl, ltp, ssl, stp


def _sweep_signals(df: pd.DataFrame, symbol: str):
    """SWEEP_CORE sinyalleri -- dar (sweep dibi - 0.25xATR) stop."""
    from .adx_lab import _make_signals

    le, se, lsl, ltp, ssl, stp, _ = _make_signals(df, SWEEP_ADX)
    return le, se, lsl, ltp, ssl, stp


# (etiket, timeframe, sinyal_fn, min_rr, max_rr, max_hold)
CASES = [
    ("NQ_ORB", "5m", _orb_signals, 0.5, 10.0, BASE["max_hold"]),
    ("SWEEP_CORE", "15m", _sweep_signals, SWEEP_MIN_RR, 6.0, 480),
]


def run_case(strategy: str, tf: str, sig_fn, min_rr: float, max_rr: float,
             max_hold: int, symbol: str) -> dict:
    df = data.load_ohlcv(symbol, tf, DAYS)
    df_1m = data.load_ohlcv(symbol, "1m", DAYS)
    le, se, lsl, ltp, ssl, stp = sig_fn(df, symbol)
    inst = INSTRUMENTS[symbol]
    kw = dict(min_rr=min_rr, max_rr=max_rr, max_hold=max_hold)

    old = simulate_trades_with_stats(df, le, se, lsl, ltp, ssl, stp, inst,
                                     fill_mode=FILL_BAR_SL_FIRST, **kw)
    new = simulate_trades_with_stats(df, le, se, lsl, ltp, ssl, stp, inst,
                                     fill_mode=FILL_1M_THEN_SL_FIRST,
                                     df_1m=df_1m, **kw)
    return {"symbol": f"{strategy} / {symbol} ({tf})", "old": old, "new": new,
            "bars_1m": len(df_1m), "period": (df.index.min(), df.index.max()),
            "reach": _reach_diagnostic(df, min_rr)}


def _reach_diagnostic(df: pd.DataFrame, min_rr: float) -> dict:
    """`overlap_bars=0` cikarsa bunun BUG mu gercek mi oldugunu olcer.

    Bir barin hem SL'e hem TP'ye degmesi icin menzilinin ~(1+rr)R olmasi
    gerekir. Bu sayilar o esigin bar menziline gore nerede durdugunu gosterir.
    """
    rng = ((df["high"] - df["low"]) / df["close"] * 100)
    return {
        "bar_median_pct": float(rng.median()),
        "bar_p99_pct": float(rng.quantile(0.99)),
        "span_needed_r": 1.0 + min_rr,
    }


def _row(label: str, res) -> dict:
    m = metrics(res.r)
    return {
        "mod": label,
        "islem": m["trades"],
        "toplam_R": round(float(res.r.sum()), 2) if len(res.r) else 0.0,
        "exp_R": m["exp_r"],
        "win%": m["win_rate"],
        "PF": m["pf"],
        "maxDD_R": round(_max_drawdown(res.r), 2),
    }


def report(results: list[dict]) -> None:
    for res in results:
        sym = res["symbol"]
        p0, p1 = res["period"]
        print("\n" + "=" * 78)
        print(f"  {sym}  |  {p0.date()} -> {p1.date()}  |  1m bar: {res['bars_1m']:,}")
        print("=" * 78)

        rows = [_row("bar_sl_first (eski)", res["old"]),
                _row("1m_then_sl_first", res["new"])]
        head = ["mod", "islem", "toplam_R", "exp_R", "win%", "PF", "maxDD_R"]
        w = {"mod": 22, "islem": 7, "toplam_R": 10, "exp_R": 8,
             "win%": 7, "PF": 7, "maxDD_R": 9}
        print("".join(f"{h:>{w[h]}}" if h != "mod" else f"{h:<{w[h]}}" for h in head))
        for r in rows:
            print("".join(f"{r[h]:>{w[h]}}" if h != "mod" else f"{r[h]:<{w[h]}}"
                          for h in head))

        s = res["new"].stats
        resolved = s["resolved_1m_tp"] + s["resolved_1m_sl"]
        fallback = s["fallback_ambiguous_1m"] + s["fallback_missing_1m"]
        print(f"\n  TP/SL cakisan bar          : {s['overlap_bars']}")
        print(f"    1m ile TP-first cozulen  : {s['resolved_1m_tp']}")
        print(f"    1m ile SL-first cozulen  : {s['resolved_1m_sl']}")
        print(f"    ayni 1m mumda ikisi de   : {s['fallback_ambiguous_1m']} (SL fallback)")
        print(f"    1m veri eksik/bozuk      : {s['fallback_missing_1m']} (SL fallback)")
        print(f"    -> cozulen / fallback    : {resolved} / {fallback}")
        print(f"  Gap nedeniyle atlanan islem: {s['gap_skipped']}")
        if s["overlap_bars"] == 0:
            d = res["reach"]
            print(f"  [neden 0] cakisma icin bar menzili ~{d['span_needed_r']:.1f}R "
                  f"olmali; bu tf'de menzil medyan %{d['bar_median_pct']:.3f}, "
                  f"p99 %{d['bar_p99_pct']:.3f} -> islem o bara varmadan kapaniyor")


def main() -> None:
    print("FILL-MODEL A/B — ayni sinyal, ayni maliyet, tek degisen: doldurma")
    print(f"Donem: {DAYS} gun. Stratejiler: NQ_ORB (genis stop) + "
          f"SWEEP_CORE (dar stop)")
    print("\nUYARI: bu bir edge iddiasi degildir. Sonuc modul tier'ini DEGISTIRMEZ;")
    print("paper/forward kanit kapilari gecerliligini korur.")
    results = [run_case(*case, symbol)
               for case in CASES for symbol in SYMBOLS]
    report(results)

    print("\n" + "=" * 78)
    print("  HAVUZ (tum semboller)")
    print("=" * 78)
    for label, key in (("bar_sl_first (eski)", "old"), ("1m_then_sl_first", "new")):
        pooled = pd.concat([r[key].r for r in results]).sort_index()
        m = metrics(pooled)
        print(f"  {label:<22} islem={m['trades']:>4}  exp_R={m['exp_r']:+.3f}  "
              f"win%={m['win_rate']:>5}  PF={m['pf']:>6}  "
              f"toplam_R={float(pooled.sum()):+.2f}")
    print()


if __name__ == "__main__":
    main()
