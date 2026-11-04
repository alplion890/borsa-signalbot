"""Exploratory delayed Fed futures-shock study; not an FTMO execution backtest.

Run with the bundled Python (pandas/openpyxl installed):
    python -m intraday.rate_surprise_pilot
See outputs/intraday/rate_event_research/PROTOCOL.md before interpreting results.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs/intraday/rate_event_research"
CACHE = ROOT / "outputs/intraday/cache/history"
SYMBOLS = ("EURUSD", "GBPUSD")


def utc_event_time(value: object) -> pd.Timestamp:
    """USMPD date_time is explicitly Eastern Time, including DST."""
    return pd.Timestamp(value).tz_localize("America/New_York").tz_convert("UTC")


def period(timestamp: pd.Timestamp) -> str:
    if timestamp.year <= 2021:
        return "development"
    if timestamp.year <= 2024:
        return "selection"
    return "holdout"


def load_prices(symbol: str) -> tuple[pd.DataFrame, list[dict]]:
    frames, sources = [], []
    for path in sorted(CACHE.glob(f"{symbol}_5m_*.csv")):
        raw = path.read_bytes()
        frame = pd.read_csv(path, parse_dates=["timestamp"])
        frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True)
        frames.append(frame.set_index("timestamp")[["open"]])
        sources.append({"path": str(path.relative_to(ROOT)),
                        "sha256": hashlib.sha256(raw).hexdigest()})
    if not frames:
        raise ValueError(f"No history for {symbol}")
    prices = pd.concat(frames).sort_index()
    if prices.index.has_duplicates:
        duplicates = prices[prices.index.duplicated(keep=False)]
        if duplicates.groupby(level=0)["open"].nunique(dropna=False).gt(1).any():
            raise ValueError(f"Conflicting duplicate opens for {symbol}")
        # Yearly downloads overlap at their boundary; identical opens are one bar.
        prices = prices[~prices.index.duplicated(keep="first")]
    if not np.isfinite(prices["open"]).all() or (prices["open"] <= 0).any():
        raise ValueError(f"Invalid open prices for {symbol}")
    return prices, sources


def trade_returns(entry: float, exit_price: float, direction: int) -> dict:
    gross = direction * (exit_price / entry - 1) * 10000
    return {"gross_bps": gross,
            "assumed_1pip_bps": gross - 0.0001 / entry * 10000,
            "assumed_2pip_bps": gross - 0.0002 / entry * 10000}


def run() -> dict:
    prices, inputs = {}, []
    for symbol in SYMBOLS:
        prices[symbol], source = load_prices(symbol)
        inputs.extend(source)
    book = OUT / "fed_usmpd.xlsx"
    events = pd.read_excel(book, sheet_name="Statements")
    inputs.append({"path": str(book.relative_to(ROOT)),
                   "sha256": hashlib.sha256(book.read_bytes()).hexdigest()})
    trades, excluded = [], []
    for _, event in events.iterrows():
        release = utc_event_time(event["date_time"])
        if release.year < 2012:
            continue
        reason = None
        shock = event["MP1"]
        if event["Unscheduled"] != 0:
            reason = "unscheduled"
        elif pd.isna(shock) or not np.isfinite(shock) or shock == 0:
            reason = "missing_or_zero_MP1"
        entry_time = release + pd.Timedelta(minutes=30)
        close = release.tz_convert("America/New_York").normalize() + pd.Timedelta(hours=17)
        # Meetings in this cohort never occur on a DST-change Sunday.
        exits = {"24H": entry_time + pd.Timedelta(hours=24),
                 "CLOSE": close.tz_convert("UTC")}
        required = [entry_time, *exits.values()]
        if any(t.minute % 5 or t.second for t in required):
            reason = reason or "off_grid_timestamp"
        if exits["CLOSE"] <= entry_time:
            reason = reason or "close_before_entry"
        if any(any(t not in prices[s].index for t in required) for s in SYMBOLS):
            reason = reason or "missing_exact_bar_in_paired_cohort"
        if reason:
            excluded.append({"event_id": release.isoformat(), "reason": reason})
            continue
        for symbol in SYMBOLS:
            entry = float(prices[symbol].loc[entry_time, "open"])
            direction = -int(np.sign(shock))  # Both pairs quote USD.
            for hold, exit_time in exits.items():
                exit_price = float(prices[symbol].loc[exit_time, "open"])
                trades.append({"event_id": release.isoformat(), "symbol": symbol,
                               "period": period(release), "hold": hold,
                               "mp1_percentage_points": float(shock),
                               "direction": direction,
                               "signal_window_end": (release + pd.Timedelta(minutes=20)).isoformat(),
                               "entry_at": entry_time.isoformat(), "exit_at": exit_time.isoformat(),
                               "entry": entry, "exit": exit_price,
                               **trade_returns(entry, exit_price, direction)})
    if not trades:
        raise ValueError("No paired eligible events; no performance report produced")
    frame = pd.DataFrame(trades)
    metrics = ["gross_bps", "assumed_1pip_bps", "assumed_2pip_bps"]
    portfolio = frame.groupby(["event_id", "period", "hold"], as_index=False)[metrics].mean()
    selection = portfolio[portfolio.period == "selection"].groupby("hold").gross_bps.mean()
    if set(selection.index) != {"24H", "CLOSE"}:
        raise ValueError("Both selection-period holds required")
    chosen = "24H" if selection["24H"] > selection["CLOSE"] else "CLOSE"
    summary = []
    for (split, hold), group in portfolio.groupby(["period", "hold"]):
        summary.append({"period": split, "hold": hold, "n_independent_events": len(group),
                        "gross_positive_fraction": float((group.gross_bps > 0).mean()),
                        **{f"mean_{m}": float(group[m].mean()) for m in metrics}})
    report = {"study": "FED_MP1_DELAY30_EXPLORATORY_PROXY",
              "not_full_requested_strategy": True, "ftmo_compliant_test": False,
              "selected_hold_using_2022_2024_only": chosen,
              "selection_metric": "equal_weight_event_mean_gross_bps",
              "summary": summary, "inputs": inputs,
              "code_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "protocol_sha256": hashlib.sha256((OUT / "PROTOCOL.md").read_bytes()).hexdigest(),
              "limits": ["MP1 futures shock, not survey consensus or text tone",
                         "Retrospective research data; no live signal feed established",
                         "Gross returns and hypothetical pip-cost sensitivities only",
                         "No swap, measured spread/slippage, stop, sizing, or FTMO rule simulation",
                         "Two FX legs share each Fed shock; event is the observation unit"]}
    frame.to_csv(OUT / "pilot_trades.csv", index=False)
    portfolio.to_csv(OUT / "pilot_event_portfolio.csv", index=False)
    pd.DataFrame(excluded).to_csv(OUT / "pilot_exclusions.csv", index=False)
    pd.DataFrame(summary).to_csv(OUT / "pilot_summary.csv", index=False)
    (OUT / "pilot_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


if __name__ == "__main__":
    result = run()
    print(json.dumps({k: result[k] for k in ["study", "selected_hold_using_2022_2024_only", "summary"]}, indent=2))
