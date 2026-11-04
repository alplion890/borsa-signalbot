"""NQ ORB edge'inde 1s trend, haftalik COT/OI ve gunluk makro katmanlari."""
from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pandas as pd

from .hierarchical_edge_lab import build_features
from .history_fetch import load_history
from .long_history_ab import run_spec, spec_by_name
from .macro_context_ab import _summary, _weekly_delta_ci
from .overfit_stats import (align_trials, deflated_from_trials,
                            probability_of_backtest_overfitting)

OUT = (Path(__file__).resolve().parent.parent / "outputs" / "intraday" /
       "orb_context_hierarchy")


def _simulate(spec, df: pd.DataFrame, long_mask: pd.Series,
              short_mask: pd.Series) -> pd.Series:
    def filtered(frame: pd.DataFrame):
        le, se, lsl, ltp, ssl, stp = spec.build(frame)
        return le & long_mask, se & short_mask, lsl, ltp, ssl, stp
    return run_spec(replace(spec, build=filtered), df)


def run(refresh: bool = False) -> dict:
    OUT.mkdir(parents=True, exist_ok=True)
    spec = spec_by_name("NQ_ORB")
    df = load_history(spec.symbol, spec.tf, start_year=2012)
    f = build_features(df, refresh)
    weekly, macro, htf = f["weekly"], f["macro"], f["htf"]
    coverage = weekly[["oi_change", "cot_change"]].notna().all(axis=1)
    coverage &= macro["valid"].fillna(False)
    hour_l, hour_s = htf == 1, htf == -1
    macro_l, macro_s = macro["score"] >= 0, macro["score"] <= 0
    cot_l, cot_s = weekly["cot_change"] >= 0, weekly["cot_change"] <= 0
    oi = weekly["oi_change"] >= 0
    masks = {
        "coverage_baseline": (coverage, coverage),
        "hourly": (coverage & hour_l, coverage & hour_s),
        "hourly_macro": (coverage & hour_l & macro_l,
                         coverage & hour_s & macro_s),
        "hourly_cot": (coverage & hour_l & cot_l,
                       coverage & hour_s & cot_s),
        "hourly_oi": (coverage & hour_l & oi,
                      coverage & hour_s & oi),
        "hourly_cot_oi": (coverage & hour_l & cot_l & oi,
                          coverage & hour_s & cot_s & oi),
        "full_stack": (coverage & hour_l & cot_l & oi & macro_l,
                       coverage & hour_s & cot_s & oi & macro_s),
    }
    trials = {name: _simulate(spec, df, lm, sm)
              for name, (lm, sm) in masks.items()}
    discovery = {k: v[v.index.year <= 2021] for k, v in trials.items()}
    rows = []
    for name, result in trials.items():
        is_r = result[result.index.year <= 2021]
        oos_r = result[result.index.year >= 2022]
        row = {"variant": name,
               **{f"is_{k}": v for k, v in _summary(is_r).items()},
               **{f"oos_{k}": v for k, v in _summary(oos_r).items()},
               **{f"full_{k}": v for k, v in _summary(result).items()}}
        if name != "coverage_baseline":
            row["delta_weekly_R_ci95"] = _weekly_delta_ci(
                trials["coverage_baseline"], result)
        rows.append(row)
        result.rename("R").to_csv(OUT / f"trades_{name}.csv", index_label="entry_utc")
    table = pd.DataFrame(rows)
    table.to_csv(OUT / "variants.csv", index=False)
    report = {
        "design": "Fixed NQ_ORB 5m retest; context layers only; 2012-2021 IS, 2022-2026 OOS",
        "discovery_multiple_test": deflated_from_trials(discovery),
        "pbo": probability_of_backtest_overfitting(align_trials(discovery)),
        "variants": rows,
    }
    (OUT / "report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False),
                                      encoding="utf-8")
    return report


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, ensure_ascii=False))
