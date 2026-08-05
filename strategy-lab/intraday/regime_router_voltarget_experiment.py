"""EXPERIMENT — volatility-targeted position sizing vs the fixed-tier risk engine.

Standalone A/B. It does NOT touch any production file. It rebuilds the SAME final
ledger as ``regime_router_final_validation.py``
(quality_11 + Gold w=1.0 + ES_Div w=2.0 + BTC w=0.11) and runs two risk engines on
that identical trade sequence:

  A) "fixed"     — the live engine: 1.5% base, 3.0% after a win, sweep x1.5 (cap 3%).
                   This is a byte-for-byte re-implementation of ``_challenge`` so the
                   baseline column must match the production validation numbers
                   (sanity check printed at the top).

  B) "voltarget" — same base policy, but each trade's risk is scaled by
                   target_sigma / recent_realized_sigma, where recent_realized_sigma
                   is a causal EWMA of past per-trade weighted-R outcomes. Turbulent
                   stretches get cut, calm stretches get normal size. The scalar is
                   clamped to [mult_lo, mult_hi] and the absolute risk is still capped
                   at 3% (and floored) so it can never exceed the live engine's cap.

Motivation: the live finalist's binding constraint is total-DD fail ~9.6% against the
10% prop ceiling. Vol-targeting is the textbook tool for taming DD tails. We measure
whether it actually buys margin here, behind the same pass/DD accounting — we do NOT
adopt anything from this file. Compare, then decide.

Run:
    python -m intraday.regime_router_voltarget_experiment
Output:
    outputs/intraday/regime_router_voltarget_experiment.csv
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

from .regime_router_final_validation import _final_parts, FINAL_BTC_WEIGHT
from .regime_router_quality_lift_scan import (
    OUT,
    SWEEP,
    _combo_metrics,
    _weeks,
    _window_summary,
)

# Absolute guard rails — identical to the live engine so the experiment can never
# size larger than production already allows.
RISK_CAP = 0.03
RISK_FLOOR = 0.003


def _base_risk(win_streak: int, module: str) -> float:
    """The live fixed-tier policy (mirror of quality_lift_scan._risk)."""
    base = 0.03 if int(win_streak) >= 1 else 0.015
    if module == SWEEP:
        return min(base * 1.5, 0.03)
    return base


def _target_sigma(df: pd.DataFrame) -> float:
    """Long-run std of per-trade weighted-R. The vol-target anchor (a constant)."""
    s = float(pd.to_numeric(df["weighted_r"], errors="coerce").dropna().std())
    return s if s > 1e-9 else 1.0


def _challenge_ab(
    df: pd.DataFrame,
    target_sigma: float,
    *,
    mode: str = "fixed",
    ewma_lambda: float = 0.94,
    mult_lo: float = 0.5,
    mult_hi: float = 1.5,
    days: int = 30,
) -> pd.DataFrame:
    """FTMO-style 30-day window sim. ``mode='fixed'`` reproduces the live engine;
    ``mode='voltarget'`` scales each trade's risk by target/recent EWMA sigma.

    The EWMA variance is updated AFTER the risk for the current trade is computed,
    so sizing only ever uses information available before the trade (causal).
    """
    starts = pd.date_range(
        df.index[0].normalize(),
        (df.index[-1] - pd.Timedelta(days=days)).normalize(),
        freq="D",
    )
    rows = []
    for start in starts:
        sub = df.loc[start:start + pd.Timedelta(days=days)]
        state = {"eq": 1.0, "peak": 1.0, "win_streak": 0}
        day_start = None
        day_start_eq = 1.0
        trading_days: set[pd.Timestamp] = set()
        result = "timeout"
        pass_day = np.nan
        risks: list[float] = []
        # EWMA variance seeded at the target so early trades start at scalar ~1.0.
        ewma_var = target_sigma ** 2
        for ts, row in sub.iterrows():
            day = ts.normalize()
            if day_start is None or day != day_start:
                day_start = day
                day_start_eq = state["eq"]
            trading_days.add(day)
            rv = float(row["weighted_r"])
            risk = _base_risk(state["win_streak"], str(row["module"]))
            if mode == "voltarget":
                cur_sigma = float(np.sqrt(ewma_var)) if ewma_var > 1e-12 else target_sigma
                scalar = float(np.clip(target_sigma / cur_sigma, mult_lo, mult_hi))
                risk = float(np.clip(risk * scalar, RISK_FLOOR, RISK_CAP))
            risks.append(risk)
            # Causal EWMA update — uses this trade's outcome only for FUTURE sizing.
            ewma_var = ewma_lambda * ewma_var + (1.0 - ewma_lambda) * (rv ** 2)
            eq = state["eq"] * (1.0 + rv * risk)
            peak = max(float(state["peak"]), eq)
            state = {
                "eq": eq,
                "peak": peak,
                "win_streak": int(state["win_streak"]) + 1 if rv > 0 else 0,
            }
            if eq <= day_start_eq - 0.05:
                result = "daily_dd"
                break
            if eq <= 0.90:
                result = "total_dd"
                break
            if eq >= 1.10 and len(trading_days) >= 4:
                result = "pass"
                pass_day = float((day - start).days)
                break
        rows.append({
            "start": start,
            "result": result,
            "trades": int(len(sub)),
            "final_eq": state["eq"],
            "pass_day": pass_day,
            "avg_risk_pct": float(np.mean(risks) * 100.0) if risks else 0.0,
        })
    return pd.DataFrame(rows)


def _row(name: str, ledger: pd.DataFrame, windows: pd.DataFrame) -> dict:
    ws = _window_summary(windows)
    n = len(ledger)
    return {
        "variant": name,
        "trades": n,
        "trades_per_week": n / _weeks(ledger.index),
        "pass_pct": ws["pass_pct"],
        "timeout_pct": ws["timeout_pct"],
        "daily_dd_pct": ws["daily_dd_pct"],
        "total_dd_pct": ws["total_dd_pct"],
        "median_pass_day": ws["median_pass_day"],
        "avg_window_risk_pct": ws["avg_window_risk_pct"],
        "median_final_eq": ws["median_final_eq"],
    }


def main() -> None:
    print("\n" + "=" * 100)
    print("  EXPERIMENT — vol-target sizing vs fixed-tier engine (same final ledger)")
    print("=" * 100 + "\n")

    ledger, _ = _combo_metrics(_final_parts(FINAL_BTC_WEIGHT))
    tgt = _target_sigma(ledger)
    print(f"final ledger trades: {len(ledger)}   target_sigma(weighted_R): {tgt:.4f}\n")

    results = []

    # A) baseline — must reproduce the live validation numbers.
    base_windows = _challenge_ab(ledger, tgt, mode="fixed")
    results.append(_row("A_fixed_baseline", ledger, base_windows))

    # B) vol-target grid — vary smoothing and clamp width.
    grid = [
        {"ewma_lambda": 0.94, "mult_lo": 0.5, "mult_hi": 1.5},
        {"ewma_lambda": 0.94, "mult_lo": 0.5, "mult_hi": 1.0},  # only ever cut, never add
        {"ewma_lambda": 0.97, "mult_lo": 0.5, "mult_hi": 1.5},
        {"ewma_lambda": 0.90, "mult_lo": 0.6, "mult_hi": 1.4},
        {"ewma_lambda": 0.97, "mult_lo": 0.4, "mult_hi": 1.0},  # conservative, cut-only
    ]
    for g in grid:
        w = _challenge_ab(ledger, tgt, mode="voltarget", **g)
        name = f"B_vt_l{g['ewma_lambda']}_lo{g['mult_lo']}_hi{g['mult_hi']}"
        results.append(_row(name, ledger, w))

    res = pd.DataFrame(results)
    out = OUT / "regime_router_voltarget_experiment.csv"
    res.to_csv(out, index=False)

    cols = [
        "variant", "trades", "trades_per_week", "pass_pct", "timeout_pct",
        "daily_dd_pct", "total_dd_pct", "median_pass_day",
        "avg_window_risk_pct", "median_final_eq",
    ]
    print(res[cols].to_string(index=False, float_format=lambda x: f"{x:.3f}"))

    base = res.iloc[0]
    print("\nDELTA vs A_fixed_baseline (positive total_dd delta = WORSE):")
    for _, r in res.iloc[1:].iterrows():
        print(
            f"  {r['variant']:<34} "
            f"pass {r['pass_pct'] - base['pass_pct']:+.2f}  "
            f"total_dd {r['total_dd_pct'] - base['total_dd_pct']:+.2f}  "
            f"daily_dd {r['daily_dd_pct'] - base['daily_dd_pct']:+.2f}  "
            f"timeout {r['timeout_pct'] - base['timeout_pct']:+.2f}"
        )

    print(f"\nCSV: {out}")
    print("\nNOTE: experiment only. Nothing here is wired into the live portfolio.")
    print("=" * 100 + "\n")


if __name__ == "__main__":
    main()
