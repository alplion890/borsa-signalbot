"""Gold NY-ORB parametrelerini GA ile ara, overfit gate'ten gecir.

Her GA adayi:
  1. Verilen parametrelerle XAUUSD ORB ledger'i kurar (cache'li df + indikator).
  2. Mevcut quality_11 + ES_Div + BTC portfoyune ekler (gercek baglam).
  3. challenge sim + overfit gate metriklerini hesaplar.
  4. fitness = gate-gecen pass_pct (gate.fitness).

GA yalniz arar; KARAR gate'in. Gate-gecen tum adaylar CSV'ye yazilir.

Calistir:
    python -m intraday.ga.optimize_gold_orb --pop 24 --generations 18
"""
from __future__ import annotations

import json
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
from ..config import INSTRUMENTS, ATR_LEN
from ..edge_lab import _adx
from ..honest_engine import simulate_trades
from ..indicators import atr
from ..internet_seed_strategies import ORBCase, _build_orb
from ..regime_router_factory import _load_ledger
from ..regime_router_overfit_validation import _rows_for_candidate, _source_data
from ..regime_router_quality_lift_scan import (
    EUR, GBP, NQ, OUT, SWEEP, _combo_metrics, _with_module,
)
from .ga_core import GeneChoice, GeneFloat, GeneInt, run_ga
from .gate import GateConfig, evaluate_ledger, fitness, gate_status

GOLD = "GOLD_NY_ORB_TREND"
SWEEP_DIV = "SWEEP_ES_DIV"
BTC = "BTCUSDT_OF_ABSORPTION"
BRIDGE = OUT / "ga"
BRIDGE.mkdir(parents=True, exist_ok=True)

# --- Cache (GA boyunca tek sefer yuklenir) ------------------------------
_CACHE: dict = {}


def _gold_df():
    if "gold_df" not in _CACHE:
        df = data.load_ohlcv("XAUUSD", "5m", days=1080)
        a = atr(df, ATR_LEN)
        adx = _adx(df, 14)
        _CACHE["gold_df"] = df
        _CACHE["gold_adx"] = adx
        _CACHE["gold_atr_pct"] = a / df["close"]
    return _CACHE["gold_df"]


def _base_parts() -> list[pd.DataFrame]:
    """quality_11 (sweep+nq+eur+gbp) + ES_Div + BTC — gold HARIC, cache'li."""
    if "base_parts" not in _CACHE:
        sweep, internet = _source_data()
        c = _rows_for_candidate("quality_11", sweep, internet)
        w = c["weights"]
        parts = [
            _with_module(c["sweep"], SWEEP, "q11_sweep", w[SWEEP]),
            _with_module(c["nq"], NQ, "q11_nq", w[NQ]),
            _with_module(c["eur"], EUR, "q11_eur", w[EUR]),
            _with_module(c["gbp"], GBP, "q11_gbp", w[GBP]),
        ]
        div = _load_ledger(OUT / "intermarket_divergence_ledger.csv")
        btc = _load_ledger(OUT / "btc_cvd_sweep_ledger.csv")
        parts.append(_with_module(div, SWEEP_DIV, "div_sweep", 2.0))
        parts.append(_with_module(btc, BTC, "btc_sweep", 0.11))
        _CACHE["base_parts"] = parts
    return list(_CACHE["base_parts"])


def _gold_ledger(genome: dict, weight: float) -> pd.DataFrame:
    df = _gold_df()
    case = ORBCase(
        symbol="XAUUSD",
        open_hour=float(genome["open_hour"]),
        range_minutes=int(genome["range_minutes"]),
        trade_end_hour=21.0,
        entry_mode=genome["entry_mode"],
        trend_filter=genome["trend_filter"],
        rr=float(genome["rr"]),
        sl_mode=genome["sl_mode"],
        atr_mult=1.0,
        max_hold=int(genome["max_hold"]),
    )
    le, se, lsl, ltp, ssl, stp = _build_orb(df, case)
    r = simulate_trades(df, le, se, lsl, ltp, ssl, stp, INSTRUMENTS["XAUUSD"],
                        min_rr=max(0.5, float(genome["rr"]) - 0.01),
                        max_rr=float(genome["rr"]) + 0.5,
                        max_hold=int(genome["max_hold"]))
    if r.empty:
        return r.to_frame("r")
    led = pd.DataFrame(index=r.index)
    led["r"] = r
    led["adx"] = _CACHE["gold_adx"].reindex(r.index)
    led["adx_regime"] = pd.cut(led["adx"], [-np.inf, 20, float(genome["adx_thresh"]), np.inf],
                               labels=["chop", "trend", "strong_trend"]).astype(str)
    # rejim filtresi: chop disla (trend + strong_trend tut)
    led = led[led["adx_regime"].isin(["trend", "strong_trend"])]
    led["setup"] = f"XAUUSD ORB {genome['open_hour']}/{genome['range_minutes']} rr{genome['rr']:.2f}"
    return _with_module(led.dropna(subset=["r"]), GOLD, "ga_gold", weight)


def _portfolio_metrics(genome: dict, weight: float = 1.0) -> dict:
    gold = _gold_ledger(genome, weight)
    parts = _base_parts() + ([gold] if len(gold) else [])
    ledger, _ = _combo_metrics(parts)
    return evaluate_ledger(ledger)


def _space():
    return [
        GeneFloat("open_hour", 13.0, 15.0),
        GeneInt("range_minutes", 30, 90),
        GeneFloat("rr", 0.8, 2.5),
        GeneInt("max_hold", 24, 72),
        GeneFloat("adx_thresh", 25.0, 40.0),
        GeneChoice("entry_mode", ["close", "retest"]),
        GeneChoice("trend_filter", ["ema", "vwap"]),
        GeneChoice("sl_mode", ["other_side", "half_range", "atr"]),
    ]


def main(pop: int = 24, generations: int = 18, seed: int = 7,
         gold_weight: float = 1.0) -> None:
    print("\n" + "=" * 100)
    print("  GA: Gold NY-ORB parametre aramasi — overfit gate arkasinda")
    print("=" * 100 + "\n")
    print("  Baseline (mevcut gold 13.5/60 rr1.0) yukleniyor...")

    cfg = GateConfig()
    baseline_genome = {
        "open_hour": 13.5, "range_minutes": 60, "rr": 1.0, "max_hold": 48,
        "adx_thresh": 30.0, "entry_mode": "retest", "trend_filter": "vwap",
        "sl_mode": "other_side",
    }
    base_m = _portfolio_metrics(baseline_genome, gold_weight)
    b_pass, b_fails = gate_status(base_m, cfg)
    print(f"  Baseline pass={base_m['pass_pct']:.1f}% totalDD={base_m['total_dd_pct']:.1f}% "
          f"exp={base_m['exp_r']:.3f} tpw={base_m['trades_per_week']:.2f} "
          f"gate={'GECTI' if b_pass else 'KALDI '+str(b_fails)}\n")

    survivors: list[dict] = []
    seen = set()

    def collect(genome, fit):
        m = _portfolio_metrics(genome, gold_weight)
        passed, fails = gate_status(m, cfg)
        if passed:
            key = tuple(sorted((k, round(v, 4) if isinstance(v, float) else v)
                               for k, v in genome.items()))
            if key not in seen:
                seen.add(key)
                survivors.append({**genome, "pass_pct": m["pass_pct"],
                                  "total_dd_pct": m["total_dd_pct"], "exp_r": m["exp_r"],
                                  "trades_per_week": m["trades_per_week"],
                                  "positive_years": m["positive_years"],
                                  "min_year_R": m["min_year_R"], "fitness": fit})

    print("  GA calisiyor...")
    best, best_f, hist = run_ga(
        _space(),
        lambda g: fitness(_portfolio_metrics(g, gold_weight), cfg),
        pop=pop, generations=generations, seed=seed, on_eval=collect, verbose=True,
    )

    print("\n  " + "-" * 90)
    if not survivors:
        print("  Gate-gecen aday BULUNAMADI. Mevcut baseline en saglam kalir.")
        print("  (GA daha parlak backtest buldu olabilir ama gate'i gecemedi -> overfit reddi.)")
    else:
        sv = pd.DataFrame(survivors).sort_values("pass_pct", ascending=False)
        csv = BRIDGE / "ga_gold_survivors.csv"
        sv.to_csv(csv, index=False)
        print(f"  Gate-gecen {len(sv)} aday (curve-fit elendi). En iyi 8:\n")
        cols = ["open_hour", "range_minutes", "rr", "max_hold", "adx_thresh",
                "entry_mode", "trend_filter", "sl_mode", "pass_pct", "total_dd_pct",
                "exp_r", "trades_per_week"]
        print(sv[cols].head(8).to_string(index=False, float_format=lambda x: f"{x:.2f}"))
        top = sv.iloc[0]
        print(f"\n  EN IYI gate-gecen: pass %{top['pass_pct']:.1f} (baseline %{base_m['pass_pct']:.1f}, "
              f"fark {top['pass_pct']-base_m['pass_pct']:+.1f} puan), "
              f"totalDD %{top['total_dd_pct']:.1f}")
        print(f"  CSV: {csv}")
        (BRIDGE / "ga_gold_run_card.json").write_text(json.dumps({
            "baseline": {k: base_m[k] for k in ("pass_pct", "total_dd_pct", "exp_r", "trades_per_week")},
            "best": top[cols].to_dict(),
            "n_survivors": len(sv),
            "history": hist,
            "gate": cfg.__dict__,
        }, indent=2, default=float), encoding="utf-8")
    print("\n" + "=" * 100 + "\n")


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--pop", type=int, default=24)
    p.add_argument("--generations", type=int, default=18)
    p.add_argument("--seed", type=int, default=7)
    p.add_argument("--gold-weight", type=float, default=1.0)
    args = p.parse_args()
    main(args.pop, args.generations, args.seed, args.gold_weight)
