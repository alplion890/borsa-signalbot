"""Re-run the 2026-10-29 long-history table on frozen-day-cleaned data.

Same logic as the 10-29 audit runner (archived specs, gap-v2 engine, Sweep ATR
regime cap); the only difference is data_quality.clean() on each frame.

    python -m intraday.long_history_clean_rerun
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from .config import INSTRUMENTS
from .data_quality import clean, frozen_days
from .history_fetch import load_history
from .honest_engine import simulate_trades
from .long_history_ab import SPECS, _atr_rank, run_spec

OUT = Path(__file__).resolve().parent.parent / "outputs" / "intraday" / "fairness_audit" / "20261106_clean"
OLD = OUT.parent / "20261027" / "long_history_rerun.json"


def _run(spec, df: pd.DataFrame) -> pd.Series:
    if spec.name != "SWEEP_CORE":
        return run_spec(spec, df)
    le, se, lsl, ltp, ssl, stp = spec.build(df)
    rank = _atr_rank(df)
    cap = pd.Series(np.select([rank < .33, rank < .67], [4., 6.], default=8.), index=df.index)
    ltp = pd.Series(np.minimum(ltp, df.close + (df.close - lsl) * cap), index=df.index)
    stp = pd.Series(np.maximum(stp, df.close - (ssl - df.close) * cap), index=df.index)
    ok = rank.notna()
    return simulate_trades(df, le & ok, se & ok, lsl, ltp, ssl, stp, INSTRUMENTS[spec.symbol],
                           min_rr=spec.min_rr, max_rr=spec.max_rr, max_hold=spec.max_hold)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    old = {r["name"]: r for r in json.loads(OLD.read_text())}
    rows = []
    for spec in SPECS:
        raw = load_history(spec.symbol, spec.tf, start_year=2012)
        bad = frozen_days(raw)
        df = clean(raw)
        r = _run(spec, df)
        r.to_csv(OUT / f"{spec.name}_long_history_trades.csv")
        o = old.get(spec.name, {})
        row = {"name": spec.name, "symbol": spec.symbol, "tf": spec.tf,
               "days_total": int(len(set(raw.index.date))), "frozen_days": len(bad),
               "frozen_weekday": sum(1 for d in bad if d.weekday() < 5),
               "bars_dropped": int(len(raw) - len(df)),
               "n": int(len(r)), "mean_r": round(float(r.mean()), 4), "sum_r": round(float(r.sum()), 2),
               "worst": round(float(r.min()), 2),
               "pre2022": round(float(r[r.index.year < 2022].mean()), 4),
               "post2022": round(float(r[r.index.year >= 2022].mean()), 4),
               "old_n": o.get("n"), "old_mean_r": round(o["mean_r"], 4) if "mean_r" in o else None,
               "note": "GBP archive mirror has look-ahead; not a clean comparison" if spec.name == "GBP_LONDON" else ""}
        rows.append(row)
        print(json.dumps(row), flush=True)
    (OUT / "long_history_clean_rerun.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
