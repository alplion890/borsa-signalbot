"""ADX filtresi + ATR-adaptif RR + dinamik risk simulasyonu.

3 katmanli iyilestirme:
  1) ADX > 25: sadece trendli piyasada islem
  2) ATR-adaptif max_rr: dusuk vol -> 4R, orta -> 6R, yuksek -> 8R
     (mantik: oynakligin yuksek oldugu donemde kazananlari kosturalim)
  3) Dinamik risk: kazandikca 2x risk, kaybedince baza don
     - kombinasyon A: 1% / 2%
     - kombinasyon B: 0.5% / 1%
"""
from __future__ import annotations

import sys
import warnings

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from . import data
from .config import INSTRUMENTS, ATR_LEN, SL_ATR_BUFFER
from .indicators import atr, swing_high, swing_low, rolling_high, rolling_low
from .honest_engine import simulate_trades, metrics, oos_metrics
try:
    from .walkforward import _folds
except ModuleNotFoundError:
    _folds = None
from .edge_lab import _vwap_trend, _adx


ADX_THRESH = 25.0


# ---------------------------------------------------------------------------
# ADX-filtreli sinyaller
# ---------------------------------------------------------------------------

def _make_signals(df, adx_thresh=ADX_THRESH):
    trend, _ = _vwap_trend(df)
    adx = _adx(df, 14)
    a = atr(df, ATR_LEN)
    buf = a * SL_ATR_BUFFER
    rlo = rolling_low(df, 20)
    rhi = rolling_high(df, 20)
    sh = swing_high(df)
    sl_ = swing_low(df)

    long_raw  = (df["low"] < rlo)  & (df["close"] > rlo) & (trend > 0) & (adx > adx_thresh)
    short_raw = (df["high"] > rhi) & (df["close"] < rhi) & (trend < 0) & (adx > adx_thresh)

    le = long_raw  & ~long_raw.shift(1).fillna(False)
    se = short_raw & ~short_raw.shift(1).fillna(False)

    return (
        le, se,
        df["low"].where(le)  - buf.where(le),
        sh.where(le),
        df["high"].where(se) + buf.where(se),
        sl_.where(se),
        a,
    )


def _run_adaptive_rr(df, le, se, lsl, ltp, ssl, stp, atr_s, inst, min_rr=2.5):
    """ATR percentile'ina gore 3 rejime ayrilmis simulasyon, sonra birlestir."""
    atr_pct = atr_s / df["close"]
    pct_rank = atr_pct.rolling(500, min_periods=100).rank(pct=True)

    regimes = [
        ("low",  pct_rank < 0.33,                          4.0),
        ("mid",  (pct_rank >= 0.33) & (pct_rank < 0.67),   6.0),
        ("high", pct_rank >= 0.67,                         8.0),
    ]

    all_r = []
    per_regime = {}
    for name, mask, max_rr in regimes:
        le_m = le & mask
        se_m = se & mask
        r = simulate_trades(df, le_m, se_m, lsl, ltp, ssl, stp,
                             inst, min_rr=min_rr, max_rr=max_rr)
        per_regime[name] = (max_rr, r)
        if len(r) > 0:
            all_r.append(r)

    merged = pd.concat(all_r).sort_index() if all_r else pd.Series(dtype=float)
    return merged, per_regime


# ---------------------------------------------------------------------------
# Dinamik risk Monte Carlo (martingale-lite)
# ---------------------------------------------------------------------------

def monte_carlo_dynamic(r: pd.Series, runs: int = 5000,
                         risk_base: float = 0.01, risk_boost: float = 0.02,
                         target: float = 0.10, daily_dd: float = 0.05,
                         total_dd: float = 0.10, days: int = 30,
                         trades_per_day: float = 0.12) -> dict:
    """Kazandikca 2x risk, kaybedince baza don."""
    arr = r.to_numpy()
    n_trades = int(np.ceil(days * trades_per_day)) + 5
    rng = np.random.default_rng(42)

    passed = daily_fail = total_fail = timeout = 0
    final_eqs, max_dds = [], []
    trades_per_day_int = max(1, int(round(1 / trades_per_day)))

    for _ in range(runs):
        sample = rng.choice(arr, size=n_trades, replace=True)
        eq = 1.0
        peak = 1.0
        max_dd = 0.0
        day_start_eq = 1.0
        prev_win = False        # ilk islemde False -> risk_base
        outcome = None

        for k, ri in enumerate(sample):
            if k % trades_per_day_int == 0:
                day_start_eq = eq

            # Dinamik risk: bir onceki kazanc varsa boost
            risk = risk_boost if prev_win else risk_base

            eq *= (1 + ri * risk)
            peak = max(peak, eq)
            dd = (peak - eq) / peak
            max_dd = max(max_dd, dd)
            day_dd = (day_start_eq - eq) / day_start_eq

            if day_dd >= daily_dd:
                outcome = "daily"; break
            if dd >= total_dd:
                outcome = "total"; break
            if eq >= 1 + target:
                outcome = "pass"; break

            prev_win = ri > 0

        if outcome is None:
            outcome = "timeout"

        if outcome == "pass":     passed += 1
        elif outcome == "daily":  daily_fail += 1
        elif outcome == "total":  total_fail += 1
        else:                     timeout += 1

        final_eqs.append(eq)
        max_dds.append(max_dd)

    n = runs
    return {
        "pass_rate":      passed / n,
        "daily_dd_hit":   daily_fail / n,
        "total_dd_hit":   total_fail / n,
        "time_out":       timeout / n,
        "median_final":   float(np.median(final_eqs)),
        "p10_final":      float(np.percentile(final_eqs, 10)),
        "median_max_dd":  float(np.median(max_dds)),
        "p90_max_dd":     float(np.percentile(max_dds, 90)),
    }


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def run(symbol="NASDAQ100", min_rr=2.5):
    df = data.load_ohlcv(symbol, "15m", 1080)
    folds = _folds(df.index) if _folds is not None else []
    inst = INSTRUMENTS[symbol]
    weeks = (df.index[-1] - df.index[0]).days / 7

    print(f"\n{'='*72}")
    print(f"  VWAP+sweep + ADX>{ADX_THRESH} + ATR-adaptif RR")
    print(f"  {symbol} 15m | min_rr={min_rr} | dinamik risk")
    print(f"{'='*72}\n")

    le, se, lsl, ltp, ssl, stp, atr_s = _make_signals(df)

    # --- BAZ (sabit max_rr=6) ---
    r_base = simulate_trades(df, le, se, lsl, ltp, ssl, stp,
                              inst, min_rr=min_rr, max_rr=6.0)
    m_b = metrics(r_base)
    o_b = oos_metrics(r_base, folds) if folds else {"oos_exp_r": np.nan, "pos_folds": "0/0", "total_R": float(r_base.sum())}

    print(f"  [A] ADX>{ADX_THRESH} + sabit max_rr=6")
    print(f"      {m_b['trades']} trade ({m_b['trades']/weeks:.2f}/hf), "
          f"exp={m_b['exp_r']:+.3f}R, WR={m_b['win_rate']}%, "
          f"PF={m_b['pf']}, OOS={o_b.get('oos_exp_r')}, "
          f"poz={o_b.get('pos_folds')}, toplam={o_b.get('total_R')}R\n")

    # --- ATR-adaptif RR ---
    r_adap, per_reg = _run_adaptive_rr(df, le, se, lsl, ltp, ssl, stp,
                                        atr_s, inst, min_rr=min_rr)
    m_a = metrics(r_adap)
    o_a = oos_metrics(r_adap, folds) if folds else {"oos_exp_r": np.nan, "pos_folds": "0/0", "total_R": float(r_adap.sum())}

    print(f"  [B] ADX>{ADX_THRESH} + ATR-adaptif max_rr (4/6/8)")
    print(f"      {m_a['trades']} trade ({m_a['trades']/weeks:.2f}/hf), "
          f"exp={m_a['exp_r']:+.3f}R, WR={m_a['win_rate']}%, "
          f"PF={m_a['pf']}, OOS={o_a.get('oos_exp_r')}, "
          f"poz={o_a.get('pos_folds')}, toplam={o_a.get('total_R')}R\n")

    print(f"      Rejim kirilimi:")
    for name, (mx, r) in per_reg.items():
        if len(r):
            print(f"        {name:5} (max_rr={mx}): {len(r)} trade, "
                  f"exp={r.mean():+.3f}R, toplam={r.sum():.1f}R")
        else:
            print(f"        {name:5} (max_rr={mx}): 0 trade")
    print()

    # Karsilastirma icin onceki baz (ADX yok)
    print(f"  [C] Onceki baz (ADX'siz, tum saatler, max_rr=6): "
          f"94 trade, exp=+0.383R, OOS=+0.348, 8/15\n")

    # --- Monte Carlo karsilastirmasi ---
    print(f"{'-'*72}\n  MONTE CARLO (3000 bootstrap, 30 gun)\n{'-'*72}")

    sets = []
    if len(r_base) >= 5:  sets.append(("ADX + sabit_rr6", r_base, m_b['trades']/weeks*5))
    if len(r_adap) >= 5:  sets.append(("ADX + adap_rr",   r_adap, m_a['trades']/weeks*5))

    print(f"\n  >> SABIT %1 risk (referans)")
    for name, r, _ in sets:
        tpd = len(r) / (weeks * 5)
        from .edge_lab import monte_carlo as mc_fixed
        for risk in [0.01, 0.015]:
            mc = mc_fixed(r, runs=3000, risk_pct=risk, trades_per_day=tpd)
            print(f"    {name:18}  risk={risk*100:.1f}%  pas={mc['pass_rate']*100:5.1f}%  "
                  f"daily_yan={mc['daily_dd_hit']*100:5.1f}%  "
                  f"zaman={mc['time_out']*100:5.1f}%")

    print(f"\n  >> DINAMIK risk (kazaninca 2x, kaybedince baza don)")
    for combo_name, base, boost in [("0.5%/1%", 0.005, 0.01),
                                      ("1%/2%",   0.01,  0.02)]:
        print(f"\n    {combo_name}:")
        for name, r, _ in sets:
            tpd = len(r) / (weeks * 5)
            mc = monte_carlo_dynamic(r, runs=3000,
                                       risk_base=base, risk_boost=boost,
                                       trades_per_day=tpd)
            print(f"      {name:18}  pas={mc['pass_rate']*100:5.1f}%  "
                  f"daily_yan={mc['daily_dd_hit']*100:5.1f}%  "
                  f"total_yan={mc['total_dd_hit']*100:5.1f}%  "
                  f"zaman={mc['time_out']*100:5.1f}%  "
                  f"medyan_DD={mc['median_max_dd']*100:.2f}%  "
                  f"p90_DD={mc['p90_max_dd']*100:.2f}%")

    print(f"\n{'='*72}\n  TAMAM\n{'='*72}\n")


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--symbol", default="NASDAQ100")
    p.add_argument("--min_rr", type=float, default=2.5)
    args = p.parse_args()
    run(args.symbol, args.min_rr)
