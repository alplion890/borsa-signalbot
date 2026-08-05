"""Stricter overfit validation for quality-lift router candidates.

This script intentionally compares the best quality candidates against simpler
versions with day filters removed. If the quality result only survives because
of narrow day-of-week pockets, it should not be promoted to a new finalist.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from .regime_router_quality_lift_scan import (
    EUR,
    GBP,
    NQ,
    OUT,
    SWEEP,
    _challenge,
    _combo_metrics,
    _load_time_csv,
    _metrics,
    _weeks,
    _window_summary,
    _with_module,
)


def _source_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    sweep = _load_time_csv(OUT / "sweep_regime_ledger.csv")
    sweep["setup"] = "NQ sweep"
    internet = _load_time_csv(OUT / "internet_seed_regime_ledgers.csv")
    return sweep, internet


def _rows_for_candidate(name: str, sweep: pd.DataFrame, internet: pd.DataFrame) -> dict:
    nq = internet[
        internet["setup"].eq("NASDAQ100 ORB open=14.5 range=15 retest none rr=1.5 sl=other_side hold=48")
        & internet["adx_regime"].eq("strong_trend")
    ]

    if name == "baseline":
        return {
            "sweep": sweep[sweep["vwap_dist_regime"] != "mid_vwap_dist"],
            "nq": nq,
            "eur": internet[
                internet["setup"].eq("EURUSD London range=2.0-7.0 none rr=1.0 sl=other_side hold=48")
                & internet["ema_aligned"].eq(False)
            ],
            "gbp": internet[
                internet["setup"].eq("GBPUSD London range=2.0-7.0 none rr=2.0 sl=other_side hold=48")
                & internet["adx_regime"].eq("strong_trend")
            ],
            "weights": {SWEEP: 1.0, NQ: 0.70, EUR: 0.60, GBP: 0.25},
            "notes": "current finalist",
        }

    if name == "quality_11":
        return {
            "sweep": sweep[sweep["dow"].astype(str) != "2"],
            "nq": nq,
            "eur": internet[
                internet["setup"].eq("EURUSD London range=2.0-7.0 none rr=1.5 sl=other_side hold=48")
                & internet["adx_regime"].eq("chop")
                & internet["dow"].eq(3)
            ],
            "gbp": internet[
                internet["setup"].eq("GBPUSD London range=0.0-7.0 ema rr=1.5 sl=other_side hold=48")
                & internet["range_regime"].eq("normal_range")
                & internet["dow"].eq(3)
            ],
            "weights": {SWEEP: 1.0, NQ: 1.0, EUR: 1.0, GBP: 0.25},
            "notes": "best fixed validation pass",
        }

    if name == "quality_11_no_day":
        return {
            "sweep": sweep[sweep["vwap_dist_regime"] != "mid_vwap_dist"],
            "nq": nq,
            "eur": internet[
                internet["setup"].eq("EURUSD London range=2.0-7.0 none rr=1.5 sl=other_side hold=48")
                & internet["adx_regime"].eq("chop")
            ],
            "gbp": internet[
                internet["setup"].eq("GBPUSD London range=0.0-7.0 ema rr=1.5 sl=other_side hold=48")
                & internet["range_regime"].eq("normal_range")
            ],
            "weights": {SWEEP: 1.0, NQ: 1.0, EUR: 1.0, GBP: 0.25},
            "notes": "quality_11 with day filters removed",
        }

    if name == "quality_08":
        return {
            "sweep": sweep[sweep["dow"].astype(str) != "2"],
            "nq": nq,
            "eur": internet[
                internet["setup"].eq("EURUSD London range=2.0-7.0 none rr=1.0 sl=other_side hold=48")
                & internet["atr_regime"].eq("mid_vol")
                & internet["ema_aligned"].eq(False)
            ],
            "gbp": internet[
                internet["setup"].eq("GBPUSD London range=0.0-7.0 ema rr=1.5 sl=other_side hold=48")
                & internet["range_regime"].eq("normal_range")
                & internet["dow"].eq(3)
            ],
            "weights": {SWEEP: 1.0, NQ: 1.0, EUR: 1.0, GBP: 0.50},
            "notes": "walk-forward selected quality candidate",
        }

    if name == "quality_08_no_day":
        return {
            "sweep": sweep[sweep["vwap_dist_regime"] != "mid_vwap_dist"],
            "nq": nq,
            "eur": internet[
                internet["setup"].eq("EURUSD London range=2.0-7.0 none rr=1.0 sl=other_side hold=48")
                & internet["atr_regime"].eq("mid_vol")
                & internet["ema_aligned"].eq(False)
            ],
            "gbp": internet[
                internet["setup"].eq("GBPUSD London range=0.0-7.0 ema rr=1.5 sl=other_side hold=48")
                & internet["range_regime"].eq("normal_range")
            ],
            "weights": {SWEEP: 1.0, NQ: 1.0, EUR: 1.0, GBP: 0.50},
            "notes": "quality_08 with day filters removed",
        }

    if name == "quality_08_no_gbp":
        data = _rows_for_candidate("quality_08", sweep, internet)
        data["gbp"] = internet.iloc[0:0]
        data["weights"][GBP] = 0.0
        data["notes"] = "quality_08 without GBP helper"
        return data

    if name == "quality_08_simple":
        return {
            "sweep": sweep[sweep["vwap_dist_regime"] != "mid_vwap_dist"],
            "nq": nq,
            "eur": internet[
                internet["setup"].eq("EURUSD London range=2.0-7.0 none rr=1.0 sl=other_side hold=48")
                & internet["atr_regime"].eq("mid_vol")
                & internet["ema_aligned"].eq(False)
            ],
            "gbp": internet.iloc[0:0],
            "weights": {SWEEP: 1.0, NQ: 1.0, EUR: 1.0, GBP: 0.0},
            "notes": "no day filters, no GBP",
        }

    raise KeyError(name)


def _ledger(name: str, sweep: pd.DataFrame, internet: pd.DataFrame) -> tuple[pd.DataFrame, str]:
    spec = _rows_for_candidate(name, sweep, internet)
    weights = spec["weights"]
    parts = [
        _with_module(spec["sweep"], SWEEP, f"{name}:sweep", weights[SWEEP]),
        _with_module(spec["nq"], NQ, f"{name}:nq", weights[NQ]),
        _with_module(spec["eur"], EUR, f"{name}:eur", weights[EUR]),
    ]
    if weights[GBP] > 0:
        parts.append(_with_module(spec["gbp"], GBP, f"{name}:gbp", weights[GBP]))
    out, _ = _combo_metrics(parts)
    return out, str(spec["notes"])


def _candidate_summary(name: str, ledger: pd.DataFrame, notes: str) -> dict:
    trade_m = _metrics(ledger["weighted_r"])
    trade_m["trades_per_week"] = trade_m["trades"] / _weeks(ledger.index)
    windows = _challenge(ledger)
    return {"candidate": name, "notes": notes, **trade_m, **_window_summary(windows)}


def _yearly(name: str, ledger: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for year, sub in ledger.groupby(ledger.index.year):
        m = _metrics(sub["weighted_r"])
        rows.append({
            "candidate": name,
            "year": int(year),
            "trades_per_week": m["trades"] / _weeks(sub.index) if m["trades"] else 0.0,
            **m,
        })
    return pd.DataFrame(rows)


def _score_train(r: pd.Series, weeks: float) -> float:
    m = _metrics(r)
    if m["trades"] < 45:
        return -1e9
    tpw = m["trades"] / weeks
    if tpw < 1.2:
        return -1e9
    return float(m["exp_r"]) * 180.0 + min(tpw, 4.0) * 3.0 + min(float(m["pf"]), 2.5) * 4.0


def _purged_expanding_wf(ledgers: dict[str, pd.DataFrame], purge_days: int = 30) -> pd.DataFrame:
    years = [2024, 2025, 2026]
    rows = []
    for test_year in years:
        test_start = pd.Timestamp(f"{test_year}-01-01")
        test_end = pd.Timestamp(f"{test_year + 1}-01-01")
        train_end = test_start - pd.Timedelta(days=purge_days)
        scored = []
        for name, ledger in ledgers.items():
            train = ledger[ledger.index < train_end]
            if train.empty:
                continue
            scored.append((_score_train(train["weighted_r"], _weeks(train.index)), name))
        scored.sort(reverse=True)
        chosen = scored[0][1]
        test = ledgers[chosen][(ledgers[chosen].index >= test_start) & (ledgers[chosen].index < test_end)]
        tm = _metrics(test["weighted_r"])
        rows.append({
            "test_year": test_year,
            "chosen_candidate": chosen,
            "train_score": scored[0][0],
            "test_trades": tm["trades"],
            "test_trades_per_week": tm["trades"] / _weeks(test.index) if tm["trades"] else 0.0,
            "test_exp_r": tm["exp_r"],
            "test_win_rate": tm["win_rate"],
            "test_avg_win_r": tm["avg_win_r"],
            "test_avg_loss_r": tm["avg_loss_r"],
            "test_pf": tm["pf"],
            "test_total_R": tm["total_R"],
        })
    return pd.DataFrame(rows)


def _decision(summary: pd.DataFrame, wf: pd.DataFrame, yearly: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in summary.iterrows():
        cand = row["candidate"]
        y = yearly[yearly["candidate"] == cand]
        min_year_exp = float(y["exp_r"].min()) if len(y) else np.nan
        positive_years = int((y["total_R"] > 0).sum()) if len(y) else 0
        rows.append({
            "candidate": cand,
            "pass_overfit_gate": bool(
                row["exp_r"] >= 0.14
                and row["trades_per_week"] >= 2.5
                and row["pass_pct"] >= 32.0
                and row["total_dd_pct"] <= 8.0
                and positive_years >= 4
                and min_year_exp > 0.0
            ),
            "positive_years": positive_years,
            "min_year_exp": min_year_exp,
            "pass_pct": row["pass_pct"],
            "timeout_pct": row["timeout_pct"],
            "total_dd_pct": row["total_dd_pct"],
            "exp_r": row["exp_r"],
            "trades_per_week": row["trades_per_week"],
        })
    wf_pass = bool(len(wf) and (wf["test_exp_r"] > 0).all() and (wf["test_total_R"] > 0).all())
    out = pd.DataFrame(rows)
    out["wf_selected_all_positive"] = wf_pass
    return out


def main() -> None:
    sweep, internet = _source_data()
    names = [
        "baseline",
        "quality_11",
        "quality_11_no_day",
        "quality_08",
        "quality_08_no_day",
        "quality_08_no_gbp",
        "quality_08_simple",
    ]
    ledgers: dict[str, pd.DataFrame] = {}
    notes: dict[str, str] = {}
    for name in names:
        ledgers[name], notes[name] = _ledger(name, sweep, internet)

    summary = pd.DataFrame([_candidate_summary(name, ledgers[name], notes[name]) for name in names])
    years = pd.concat([_yearly(name, ledger) for name, ledger in ledgers.items()], ignore_index=True)
    wf = _purged_expanding_wf(ledgers)
    decision = _decision(summary, wf, years)

    summary_out = OUT / "regime_router_overfit_summary.csv"
    years_out = OUT / "regime_router_overfit_years.csv"
    wf_out = OUT / "regime_router_overfit_walk_forward.csv"
    decision_out = OUT / "regime_router_overfit_decision.csv"
    summary.to_csv(summary_out, index=False)
    years.to_csv(years_out, index=False)
    wf.to_csv(wf_out, index=False)
    decision.to_csv(decision_out, index=False)

    cols = [
        "candidate", "trades_per_week", "exp_r", "win_rate", "avg_win_r",
        "avg_loss_r", "pf", "pass_pct", "timeout_pct", "daily_dd_pct",
        "total_dd_pct", "median_trades_30d", "notes",
    ]
    print("\nREGIME ROUTER OVERFIT VALIDATION")
    print(f"summary:  {summary_out}")
    print(f"years:    {years_out}")
    print(f"wf:       {wf_out}")
    print(f"decision: {decision_out}")
    print("\nSUMMARY")
    print(summary[cols].sort_values(["pass_pct", "exp_r"], ascending=False).to_string(index=False))
    print("\nPURGED EXPANDING WALK-FORWARD")
    print(wf.to_string(index=False))
    print("\nDECISION")
    print(decision.to_string(index=False))


if __name__ == "__main__":
    main()
