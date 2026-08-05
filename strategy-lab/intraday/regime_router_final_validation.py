"""Validate the current final router portfolio.

Portfolio under test:
  quality_11 + Gold NY-ORB(w=1.0) + ES divergence(w=2.0) + BTC absorption(w=0.11)

This script does not search parameters. It rebuilds the fixed final ledger from
the existing module ledgers and writes compact summary/year/module reports.
"""
from __future__ import annotations

import logging
import sys
import warnings

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
logging.disable(logging.INFO)
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from .gold_orb_regime import build_orb_ledger
from .regime_router_factory import _load_ledger
from .regime_router_overfit_validation import _rows_for_candidate, _source_data
from .regime_router_quality_lift_scan import (
    EUR,
    GBP,
    NQ,
    OUT,
    PRIORITY,
    SWEEP,
    _challenge,
    _combo_metrics,
    _metrics,
    _weeks,
    _window_summary,
    _with_module,
)

GOLD = "GOLD_NY_ORB_TREND"
SWEEP_DIV = "SWEEP_ES_DIV"
BTC = "BTCUSDT_OF_ABSORPTION"
FINAL_BTC_WEIGHT = 0.11

PRIORITY[SWEEP_DIV] = 1
PRIORITY[NQ] = 2
PRIORITY[EUR] = 3
PRIORITY[GBP] = 4
PRIORITY[GOLD] = 5
PRIORITY[BTC] = 6


def _gold_part(weight: float) -> pd.DataFrame:
    led, _ = build_orb_ledger("XAUUSD", 13.5, days=1080, entry_mode="retest", trend="vwap")
    sub = led[led.adx_regime.isin(["trend", "strong_trend"])].copy()
    sub["setup"] = "XAUUSD NY-ORB vwap 13.5/60 rr1.0"
    return _with_module(sub, GOLD, "gold_trend", weight)


def _base_quality_11_parts() -> list[pd.DataFrame]:
    sweep, internet = _source_data()
    c = _rows_for_candidate("quality_11", sweep, internet)
    w = c["weights"]
    return [
        _with_module(c["sweep"], SWEEP, "q11_sweep", w[SWEEP]),
        _with_module(c["nq"], NQ, "q11_nq", w[NQ]),
        _with_module(c["eur"], EUR, "q11_eur", w[EUR]),
        _with_module(c["gbp"], GBP, "q11_gbp", w[GBP]),
    ]


def _final_parts(btc_weight: float = FINAL_BTC_WEIGHT) -> list[pd.DataFrame]:
    div_ledger = _load_ledger(OUT / "intermarket_divergence_ledger.csv")
    btc_ledger = _load_ledger(OUT / "btc_cvd_sweep_ledger.csv")
    parts = [
        *_base_quality_11_parts(),
        _gold_part(1.0),
        _with_module(div_ledger, SWEEP_DIV, "div_sweep", 2.0),
    ]
    if btc_weight > 0:
        parts.append(_with_module(btc_ledger, BTC, "btc_sweep", btc_weight))
    return parts


def _summary(name: str, ledger: pd.DataFrame) -> dict:
    m = _metrics(ledger["weighted_r"])
    m["trades_per_week"] = m["trades"] / _weeks(ledger.index)
    windows = _challenge(ledger)
    return {"candidate": name, **m, **_window_summary(windows)}


def _yearly(name: str, ledger: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for year, sub in ledger.groupby(ledger.index.year):
        m = _metrics(sub["weighted_r"])
        rows.append(
            {
                "candidate": name,
                "year": int(year),
                "trades_per_week": m["trades"] / _weeks(sub.index) if m["trades"] else 0.0,
                **m,
            }
        )
    return pd.DataFrame(rows)


def _module_breakdown(ledger: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for module, sub in ledger.groupby("module"):
        raw = _metrics(sub["r"])
        weighted = _metrics(sub["weighted_r"])
        rows.append(
            {
                "module": module,
                "weight": float(sub["weight"].median()),
                "trades": raw["trades"],
                "raw_exp_r": raw["exp_r"],
                "raw_pf": raw["pf"],
                "weighted_exp_r": weighted["exp_r"],
                "weighted_total_R": weighted["total_R"],
                "first_trade": sub.index.min(),
                "last_trade": sub.index.max(),
            }
        )
    return pd.DataFrame(rows).sort_values("weighted_total_R", ascending=False)


def _btc_weight_sanity() -> pd.DataFrame:
    rows = []
    for weight in [0.0, 0.05, 0.10, 0.11, 0.12, 0.20, 0.30, 0.40, 0.50]:
        parts = _final_parts(weight)
        ledger, _ = _combo_metrics(parts)
        s = _summary(f"final_btc_{weight:.1f}", ledger)
        rows.append(
            {
                "btc_w": weight,
                "trades": s["trades"],
                "trades_per_week": s["trades_per_week"],
                "exp_r": s["exp_r"],
                "pf": s["pf"],
                "pass_pct": s["pass_pct"],
                "timeout_pct": s["timeout_pct"],
                "daily_dd_pct": s["daily_dd_pct"],
                "total_dd_pct": s["total_dd_pct"],
                "median_trades_30d": s["median_trades_30d"],
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    print("\n" + "=" * 104)
    print("  FINAL ROUTER VALIDATION — quality_11 + Gold + ES_Div + BTC")
    print("=" * 104 + "\n")

    comparisons: dict[str, pd.DataFrame] = {}
    comparisons["quality_11"], _ = _combo_metrics(_base_quality_11_parts())
    comparisons["quality_11_gold_es"], _ = _combo_metrics(_final_parts(0.0))
    final_name = f"final_btc_{FINAL_BTC_WEIGHT:.2f}"
    comparisons[final_name], _ = _combo_metrics(_final_parts(FINAL_BTC_WEIGHT))

    summary = pd.DataFrame([_summary(name, ledger) for name, ledger in comparisons.items()])
    years = pd.concat([_yearly(name, ledger) for name, ledger in comparisons.items()], ignore_index=True)
    modules = _module_breakdown(comparisons[final_name])
    btc_weights = _btc_weight_sanity()

    summary_out = OUT / "regime_router_final_validation_summary.csv"
    years_out = OUT / "regime_router_final_validation_years.csv"
    modules_out = OUT / "regime_router_final_validation_modules.csv"
    btc_weights_out = OUT / "regime_router_final_validation_btc_weights.csv"
    ledger_out = OUT / "regime_router_final_validation_ledger.csv"

    summary.to_csv(summary_out, index=False)
    years.to_csv(years_out, index=False)
    modules.to_csv(modules_out, index=False)
    btc_weights.to_csv(btc_weights_out, index=False)
    comparisons[final_name].to_csv(ledger_out)

    summary_cols = [
        "candidate",
        "trades",
        "trades_per_week",
        "exp_r",
        "win_rate",
        "pf",
        "total_R",
        "pass_pct",
        "timeout_pct",
        "daily_dd_pct",
        "total_dd_pct",
        "median_pass_day",
        "median_trades_30d",
    ]
    print("SUMMARY")
    print(summary[summary_cols].to_string(index=False, float_format=lambda x: f"{x:.3f}"))

    print("\nYEARLY")
    print(
        years[
            ["candidate", "year", "trades", "trades_per_week", "exp_r", "pf", "total_R"]
        ].to_string(index=False, float_format=lambda x: f"{x:.3f}")
    )

    print("\nFINAL MODULE BREAKDOWN")
    print(
        modules[
            ["module", "weight", "trades", "raw_exp_r", "raw_pf", "weighted_total_R"]
        ].to_string(index=False, float_format=lambda x: f"{x:.3f}")
    )

    print("\nBTC WEIGHT SANITY")
    print(btc_weights.to_string(index=False, float_format=lambda x: f"{x:.3f}"))

    risk_note = ""
    final_row = summary[summary["candidate"] == final_name].iloc[0]
    if float(final_row["total_dd_pct"]) > 10.0:
        risk_note = "NOT: total DD fail orani %10'un ustunde; pass hedefi gecti ama risk yorumu agresif kalir."
        print(f"\n{risk_note}")

    print("\nCSV")
    print(f"  summary: {summary_out}")
    print(f"  years:   {years_out}")
    print(f"  modules: {modules_out}")
    print(f"  weights: {btc_weights_out}")
    print(f"  ledger:  {ledger_out}")
    print("\n" + "=" * 104 + "\n")


if __name__ == "__main__":
    main()
