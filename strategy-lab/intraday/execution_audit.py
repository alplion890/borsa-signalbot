"""Read-only execution audit of a saved fixed-spec Maven Sweep panel job.

The reference uses a separate position state machine, not honest_engine or its
compiled core. Signals are shared deliberately: this tests execution, not an
independent implementation of the strategy. Results are historical diagnostics.
"""
from __future__ import annotations

import argparse
from dataclasses import replace
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from .config import INSTRUMENTS
from .honest_engine import simulate_trades, FILL_BAR_SL_FIRST, FILL_1M_THEN_SL_FIRST
from .long_history_ab import _sweep_build, _atr_rank, spec_by_name
from .research_panel import broker_history, jobs


def reference_trades(frame, signals, instrument, min_rr, max_rr, max_hold, mode):
    """Independent state machine, market-stop / resting-limit OHLC contract.

    Without ticks the open is observable first, then simultaneous touches use
    stop first. Stop gaps execute at open, target limits at the target. Costs
    use the same declared fixed round-trip R formula as the main model.
    """
    if mode not in (FILL_BAR_SL_FIRST, FILL_1M_THEN_SL_FIRST):
        raise ValueError(mode)
    if max_hold < 1:
        raise ValueError("max_hold must be positive")
    result, position = [], None
    le, se, lsl, ltp, ssl, stp = signals
    for bar, (time, candle) in enumerate(frame.iterrows()):
        if position is not None and bar >= position["scan_start"]:
            p = position
            direction = p["direction"]
            stop, target = p["stop"], p["target"]
            stop_gap = direction * (candle.open - stop) <= 0
            target_open = direction * (candle.open - target) >= 0
            stop_touch = candle.low <= stop if direction == 1 else candle.high >= stop
            target_touch = candle.high >= target if direction == 1 else candle.low <= target
            exit_price, reason = None, None
            if stop_gap:
                exit_price, reason = candle.open, "stop_gap"
            elif target_open:
                exit_price, reason = target, "target_at_open"
            elif stop_touch:
                exit_price, reason = stop, "stop"
            elif target_touch:
                exit_price, reason = target, "target"
            elif bar >= p["expiry"] or bar == len(frame) - 1:
                exit_price = candle.close
                reason = "timeout" if bar >= p["expiry"] else "data_end"
            if exit_price is not None:
                gross = direction * (exit_price - p["entry"]) / p["risk"]
                cost_r = 2 * instrument.cost_per_side * p["entry"] / p["risk"]
                result.append({**p, "exit_time": time.isoformat(), "exit_bar": bar,
                               "exit": float(exit_price), "reason": reason,
                               "gross_r": float(gross), "cost_r": float(cost_r),
                               "r": float(gross - cost_r)})
                position = None
                continue  # engine forbids another entry on the exit bar
        if position is not None:
            continue
        direction = 1 if bool(le.iloc[bar]) else (-1 if bool(se.iloc[bar]) else 0)
        if not direction:
            continue
        stop = float(lsl.iloc[bar] if direction == 1 else ssl.iloc[bar])
        target = float(ltp.iloc[bar] if direction == 1 else stp.iloc[bar])
        signal_price = float(candle.close)
        initial_risk = direction * (signal_price - stop)
        initial_reward = direction * (target - signal_price)
        if not np.isfinite([stop, target, initial_risk, initial_reward]).all():
            continue
        if initial_risk <= 0 or initial_reward <= 0 or initial_reward / initial_risk < min_rr:
            continue
        rr = min(initial_reward / initial_risk, max_rr)
        entry_bar = bar if mode == FILL_BAR_SL_FIRST else bar + 1
        if entry_bar >= len(frame):
            continue
        entry = signal_price if entry_bar == bar else float(frame.iloc[entry_bar].open)
        risk = direction * (entry - stop)
        if risk <= 0:
            continue
        scan_start = bar + 1
        expiry = bar + max_hold if mode == FILL_BAR_SL_FIRST else entry_bar + max_hold - 1
        position = {"signal_time": time.isoformat(), "signal_bar": bar,
                    "entry_time": frame.index[entry_bar].isoformat(), "entry_bar": entry_bar,
                    "entry": entry, "direction": direction, "stop": stop,
                    "target": entry + direction * rr * risk, "risk": risk,
                    "scan_start": scan_start, "expiry": expiry}
        # Default model liquidates a last-bar entry immediately at data end.
        if bar == len(frame) - 1:
            cost_r = 2 * instrument.cost_per_side * entry / risk
            result.append({**position, "exit_time": time.isoformat(), "exit_bar": bar,
                           "exit": entry, "reason": "data_end", "gross_r": 0.,
                           "cost_r": float(cost_r), "r": float(-cost_r)})
            position = None
    return result


def _summary(series):
    equity = np.r_[0., series.to_numpy(dtype=float).cumsum()]
    return {"n": len(series), "sum_r": float(series.sum()),
            "mean_r": float(series.mean()) if len(series) else None,
            "drawdown_r": float(np.max(np.maximum.accumulate(equity) - equity))}


def audit(saved_job, output):
    """Freeze inputs before running the declared diagnostic scenarios."""
    saved_job, output = Path(saved_job), Path(output)
    original = json.loads(saved_job.read_text(encoding="utf-8"))
    config = jobs.validate(original["config"])
    if config["strategy"] != "SWEEP_CORE":
        raise ValueError("This audit is scoped to the fixed NQ Sweep definition")
    source = broker_history.root(jobs.LAB) / config["dataset"]
    raw = source.read_bytes()
    data_hash = hashlib.sha256(raw).hexdigest()
    provenance = broker_history.resolve_dataset(jobs.LAB, config["dataset"])["provenance"]
    if data_hash != provenance["data_sha256"]:
        raise ValueError("Snapshot hash mismatch")
    code_hash = jobs.code_digest(jobs.LAB)
    frame = pd.read_csv(source)
    frame.index = pd.DatetimeIndex(pd.to_datetime(frame.pop("timestamp"), utc=True)).tz_localize(None)
    if frame.index.has_duplicates or not frame.index.is_monotonic_increasing:
        raise ValueError("Invalid timestamp order")
    start = pd.Timestamp(config["start"])
    stop = pd.Timestamp(config["end"]) + pd.Timedelta(days=1)
    window = frame.loc[(frame.index >= start) & (frame.index < stop)]
    frame = pd.concat([frame.loc[frame.index < start].tail(2000), window])
    base_signals = _sweep_build(frame)
    le, se, lsl, ltp, ssl, stp = base_signals
    rank = _atr_rank(frame)
    cap = pd.Series(np.select([rank < .33, rank < .67], [4., 6.], default=8.), index=frame.index)
    ltp = pd.Series(np.minimum(ltp, frame.close + (frame.close - lsl) * cap), index=frame.index)
    stp = pd.Series(np.maximum(stp, frame.close - (ssl - frame.close) * cap), index=frame.index)
    eligible = (frame.index >= start) & (frame.index < stop) & (np.arange(len(frame)) >= 519)
    signals = (le & eligible & rank.notna(), se & eligible & rank.notna(), lsl, ltp, ssl, stp)
    spec = spec_by_name("SWEEP_CORE")
    plan = [(FILL_BAR_SL_FIRST, 1.), (FILL_BAR_SL_FIRST, 2.),
            (FILL_BAR_SL_FIRST, 3.), (FILL_1M_THEN_SL_FIRST, 1.)]
    records, scenarios = [], []
    for mode, factor in plan:
        inst = replace(INSTRUMENTS["NASDAQ100"],
                       cost_per_side=INSTRUMENTS["NASDAQ100"].cost_per_side * config["cost_factor"] * factor)
        rows = reference_trades(frame, signals, inst, spec.min_rr, spec.max_rr, spec.max_hold, mode)
        ref = pd.Series([r["r"] for r in rows], index=pd.DatetimeIndex([r["signal_time"] for r in rows]))
        actual = simulate_trades(frame, *signals, inst, min_rr=spec.min_rr,
                                 max_rr=spec.max_rr, max_hold=spec.max_hold, fill_mode=mode)
        matched = list(actual.index) == list(ref.index)
        error = float(np.max(np.abs(actual.to_numpy() - ref.to_numpy()))) if matched and len(ref) else None
        passed = matched and (error is None or error <= 1e-10)
        scenarios.append({"mode": mode, "cost_multiplier": factor, **_summary(actual),
                          "reference_matched": passed, "max_abs_r_difference": error})
        records.extend([{**row, "mode": mode, "cost_multiplier": factor} for row in rows])
    prefix_checks = []
    for count in (520, 1000, 5000, 10000, 20000, len(frame) - 100):
        if not 0 < count < len(frame):
            continue
        partial = list(_sweep_build(frame.iloc[:count])) + [_atr_rank(frame.iloc[:count])]
        full = list(base_signals) + [rank]
        diffs = [int((~np.isclose(a.iloc[:count].to_numpy(dtype=float), b.to_numpy(dtype=float), equal_nan=True)).sum())
                 for a, b in zip(full, partial)]
        prefix_checks.append({"bars": count, "difference_cells": diffs})
    baseline = {t["entry_time"]: t["r"] for t in original["trades"]}
    new_rows = [r for r in records if r["mode"] == FILL_BAR_SL_FIRST and r["cost_multiplier"] == 1]
    changes = [{"signal_time": r["signal_time"], "old_r": baseline.get(r["signal_time"]),
                "new_r": r["r"], "exit_reason": r["reason"]}
               for r in new_rows if r["signal_time"] not in baseline or
               abs(r["r"] - baseline[r["signal_time"]]) > 1e-10]
    panel = jobs.execute(config)
    panel_series = pd.Series([r["r"] for r in panel["trades"]],
                             index=pd.DatetimeIndex([r["entry_time"] for r in panel["trades"]]))
    ref_base = pd.Series([r["r"] for r in new_rows], index=pd.DatetimeIndex([r["signal_time"] for r in new_rows]))
    panel_pass = list(panel_series.index) == list(ref_base.index) and np.allclose(panel_series, ref_base, rtol=0, atol=1e-10)
    costs = [s["sum_r"] for s in scenarios[:3]]
    passed = (all(s["reference_matched"] for s in scenarios) and panel_pass and
              costs[0] >= costs[1] >= costs[2] and not any(any(p["difference_cells"]) for p in prefix_checks))
    report = {"created_at": jobs.utc_now(), "historical_diagnostic_only": True,
              "saved_job": str(saved_job.resolve()), "saved_job_sha256": hashlib.sha256(saved_job.read_bytes()).hexdigest(),
              "snapshot": str(source.resolve()), "data_sha256": data_hash,
              "code_sha256": code_hash, "config": config, "declared_scenarios": plan,
              "original_metrics": original["metrics"], "scenarios": scenarios,
              "changes_vs_saved_job": changes,
              "original_only_signals": sorted(set(baseline) - {r["signal_time"] for r in new_rows}),
              "prefix_checks": prefix_checks, "panel_reference_matched": bool(panel_pass),
              "cost_stress_monotone": costs[0] >= costs[1] >= costs[2], "passed": bool(passed),
              "limits": ["Shared signal generation; independent execution only, not MT5 tick parity.",
                         "Same previously seen snapshot; not new OOS or forward.",
                         "Fixed proportional costs, no dynamic bid/ask or liquidity model.",
                         "1m scenario has no minute data; unresolved simultaneous touches use SL.",
                         "OHLC stop-gap open is a proxy, not a guaranteed broker fill."]}
    if jobs.code_digest(jobs.LAB) != code_hash or hashlib.sha256(source.read_bytes()).hexdigest() != data_hash:
        raise RuntimeError("Inputs changed during audit")
    output.mkdir(parents=True, exist_ok=False)
    (output / "audit.json").write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")
    pd.DataFrame(records).to_csv(output / "trades.csv", index=False)
    examples = new_rows[:10]  # chronological selection, no outcome-based cherry-picking
    lines = ["# First ten chronological trades — independent execution trace", "",
             "Hypothetical OHLC replay; not broker fills. Times are UTC bar labels; default entry occurs at signal-bar close.", "",
             "| Signal bar (UTC) | Side | Entry | Stop | Target | Exit bar (UTC) | Exit | Reason | Gross R | Cost R | Net R |",
             "|---|---|---:|---:|---:|---|---:|---|---:|---:|---:|"]
    for r in examples:
        lines.append(f"| {r['signal_time']} | {r['direction']} | {r['entry']:.3f} | {r['stop']:.3f} | {r['target']:.3f} | {r['exit_time']} | {r['exit']:.3f} | {r['reason']} | {r['gross_r']:.6f} | {r['cost_r']:.6f} | {r['r']:.6f} |")
    (output / "examples.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("saved_job", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = audit(args.saved_job, args.output)
    print(json.dumps({k: report[k] for k in ("passed", "scenarios", "changes_vs_saved_job")}, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
