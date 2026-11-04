"""Bes edge'de 1s trend, haftalik COT/OI ve gunluk makro hiyerarsisi."""
from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import numpy as np
import pandas as pd

from .cross_asset_positioning_ab import (MARKET, MODULES, _daily_context,
                                          _macro_sources, _positioning_sources)
from .hierarchical_edge_lab import asof_weekly, hourly_ema_trend
from .history_fetch import load_history
from .long_history_ab import run_spec, spec_by_name
from .macro_context_ab import (_summary, _weekly_delta_ci,
                               gbp_causal_build)
from .overfit_stats import (align_trials, deflated_from_trials,
                            probability_of_backtest_overfitting)

OUT = (Path(__file__).resolve().parent.parent / "outputs" / "intraday" /
       "all_edges_context_hierarchy")


def _simulate(spec, df: pd.DataFrame, long_mask: pd.Series,
              short_mask: pd.Series) -> pd.Series:
    def filtered(frame: pd.DataFrame):
        le, se, lsl, ltp, ssl, stp = spec.build(frame)
        return le & long_mask, se & short_mask, lsl, ltp, ssl, stp
    return run_spec(replace(spec, build=filtered), df)


def context_masks(module: str, df: pd.DataFrame, positioning: pd.DataFrame,
                  sources: dict[str, pd.Series]) -> dict[str, tuple[pd.Series, pd.Series]]:
    weekly = asof_weekly(df.index, positioning, MARKET[module])
    dates = pd.DatetimeIndex(df.index.normalize().unique())
    daily = _daily_context(module, dates, sources)
    macro = daily.reindex(df.index.normalize()).set_axis(df.index)
    htf = hourly_ema_trend(df)

    coverage = weekly[["oi_change", "cot_change"]].notna().all(axis=1)
    coverage &= macro["valid"].fillna(False)
    hour_l, hour_s = htf == 1, htf == -1
    macro_l, macro_s = macro["score"] >= 0, macro["score"] <= 0
    cot_l, cot_s = weekly["cot_change"] >= 0, weekly["cot_change"] <= 0
    oi = weekly["oi_change"] >= 0
    return {
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


def run(refresh: bool = False) -> dict:
    OUT.mkdir(parents=True, exist_ok=True)
    sources = _macro_sources(refresh)
    positioning = _positioning_sources(refresh, 2026)
    report = {
        "design": {
            "modules": list(MODULES), "discovery": "2012-2021",
            "oos": "2022-2026", "weekly": "market-specific CFTC COT/OI",
            "daily": "market-specific cross-asset score, not-against rule",
            "hourly": "closed 1h EMA20/EMA50 alignment",
            "entry": "each module's existing fixed entry",
        },
        "modules": {},
    }
    for module in MODULES:
        spec = spec_by_name(module)
        if module == "GBP_LONDON":
            spec = replace(spec, build=gbp_causal_build)
        df = load_history(spec.symbol, spec.tf, start_year=2012)
        masks = context_masks(module, df, positioning, sources)
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
                    trials["coverage_baseline"], result
                )
            rows.append(row)
            folder = OUT / module
            folder.mkdir(parents=True, exist_ok=True)
            result.rename("R").to_csv(folder / f"trades_{name}.csv",
                                      index_label="entry_utc")
        pd.DataFrame(rows).to_csv(OUT / module / "variants.csv", index=False)
        report["modules"][module] = {
            "symbol": spec.symbol, "timeframe": spec.tf,
            "discovery_multiple_test": deflated_from_trials(discovery),
            "pbo": probability_of_backtest_overfitting(align_trials(discovery)),
            "variants": rows,
        }
    (OUT / "report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False, default=str), encoding="utf-8"
    )
    return report


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, ensure_ascii=False, default=str))
