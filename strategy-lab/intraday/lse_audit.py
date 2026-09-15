"""LSE 15dk arsivini mevcut veriyle karsilastir ve SWEEP'i PAPER denetle."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from .adx_lab import _make_signals
from .config import INSTRUMENTS
from .history_fetch import load_history as load_existing
from .honest_engine import metrics, simulate_trades
from .lse_data import HISTORY_CACHE, download_history, load_history


OUT = Path(__file__).resolve().parent.parent / "outputs" / "intraday" / "lse_audit"


def _utc(frame: pd.DataFrame) -> pd.DataFrame:
    frame = frame.copy().sort_index()
    index = pd.DatetimeIndex(frame.index)
    frame.index = index.tz_localize("UTC") if index.tz is None else index.tz_convert("UTC")
    return frame[~frame.index.duplicated(keep="last")]


def _existing_15m(symbol: str) -> pd.DataFrame:
    if symbol == "NASDAQ100":
        return _utc(load_existing(symbol, "15m", start_year=2016))
    five = _utc(load_existing(symbol, "5m", start_year=2012))
    return five.resample("15min", label="left", closed="left").agg({
        "open": "first", "high": "max", "low": "min", "close": "last",
        "volume": "sum",
    }).dropna(subset=["open", "high", "low", "close"])


def compare_frames(lse: pd.DataFrame, existing: pd.DataFrame) -> dict:
    lse, existing = _utc(lse), _utc(existing)
    joined = lse.add_prefix("lse_").join(existing.add_prefix("old_"), how="inner")
    lret = joined["lse_close"].pct_change()
    oret = joined["old_close"].pct_change()
    valid = lret.notna() & oret.notna()
    price_ratio = joined["lse_close"] / joined["old_close"]
    lv = joined["lse_volume"]
    ov = joined["old_volume"]
    volume_valid = (lv > 0) & (ov > 0)
    dislocation = valid & ((lret - oret).abs() > .005)
    calm = valid & (lret.abs() < .01) & (oret.abs() < .01)
    lse_window = lse.loc[joined.index.min():joined.index.max()] if len(joined) else lse.iloc[0:0]
    old_window = existing.loc[joined.index.min():joined.index.max()] if len(joined) else existing.iloc[0:0]
    return {
        "lse_bars_in_overlap_window": int(len(lse_window)),
        "existing_bars_in_overlap_window": int(len(old_window)),
        "aligned_bars": int(len(joined)),
        "overlap_start": joined.index.min().isoformat() if len(joined) else None,
        "overlap_end": joined.index.max().isoformat() if len(joined) else None,
        "return_correlation": float(lret[valid].corr(oret[valid])) if valid.sum() > 2 else None,
        "return_correlation_excluding_1pct_jumps": (
            float(lret[calm].corr(oret[calm])) if calm.sum() > 2 else None
        ),
        "median_abs_return_diff_bps": (
            float((lret[valid] - oret[valid]).abs().median() * 10_000)
            if valid.any() else None
        ),
        "median_price_ratio": float(price_ratio.median()) if len(joined) else None,
        "price_ratio_iqr": (
            float(price_ratio.quantile(.75) - price_ratio.quantile(.25))
            if len(joined) else None
        ),
        "volume_correlation": (
            float(lv[volume_valid].corr(ov[volume_valid]))
            if volume_valid.sum() > 2 else None
        ),
        "return_dislocations_over_50bps": int(dislocation.sum()),
        "largest_dislocations": [
            {
                "timestamp": ts.isoformat(),
                "lse_return_pct": round(float(lret.loc[ts] * 100), 4),
                "existing_return_pct": round(float(oret.loc[ts] * 100), 4),
            }
            for ts in (lret - oret).abs().loc[dislocation].nlargest(5).index
        ],
    }


def sweep_results(frame: pd.DataFrame) -> dict:
    """Canli dedektorun kurallarini tek seri simulasyonuna uygular."""
    frame = _utc(frame)
    le, se, lsl, ltp, ssl, stp, atr_s = _make_signals(frame, 25.0)
    allowed = frame.index.dayofweek != 2
    le, se = le & allowed, se & allowed
    rank = (atr_s / frame["close"]).rolling(500, min_periods=100).rank(pct=True)
    max_rr = pd.Series(np.select(
        [rank < .33, rank < .67], [4.0, 6.0], default=8.0,
    ), index=frame.index)

    long_risk = frame["close"] - lsl
    short_risk = ssl - frame["close"]
    long_raw_rr = (ltp - frame["close"]) / long_risk
    short_raw_rr = (frame["close"] - stp) / short_risk
    le = le & (long_risk > 0) & (long_raw_rr >= 2.0) & rank.notna()
    se = se & (short_risk > 0) & (short_raw_rr >= 2.0) & rank.notna()
    ltp_adj = frame["close"] + np.minimum(long_raw_rr, max_rr) * long_risk
    stp_adj = frame["close"] - np.minimum(short_raw_rr, max_rr) * short_risk

    r = simulate_trades(
        frame, le, se, lsl, ltp_adj, ssl, stp_adj,
        INSTRUMENTS["NASDAQ100"], min_rr=2.0, max_rr=8.0,
    )
    result = metrics(r)
    result.update({
        "start": frame.index.min().isoformat(),
        "end": frame.index.max().isoformat(),
        "total_r": float(r.sum()),
        "note": "PAPER kaynak denetimi; LIVE statu/risk degistirmez",
    })
    return result


def run(download: bool, start_year: int, end_year: int) -> dict:
    symbols = ("NASDAQ100", "EURUSD", "GBPUSD")
    if download:
        for symbol in symbols:
            download_history(
                symbol, "15m", start_year, end_year,
                on_progress=print,
            )
    report: dict[str, object] = {"scope": f"{start_year}-{end_year}", "symbols": {}}
    for symbol in symbols:
        lse = load_history(symbol, cache_dir=HISTORY_CACHE)
        old = _existing_15m(symbol)
        report["symbols"][symbol] = compare_frames(lse, old)
    lse_nq = load_history("NASDAQ100", cache_dir=HISTORY_CACHE)
    old_nq = _existing_15m("NASDAQ100")
    common_start = max(lse_nq.index.min(), old_nq.index.min())
    common_end = min(lse_nq.index.max(), old_nq.index.max())
    report["sweep_paper_check"] = {
        "lse_nq_futures": sweep_results(lse_nq.loc[common_start:common_end]),
        "existing_nasdaq_index": sweep_results(old_nq.loc[common_start:common_end]),
    }
    OUT.mkdir(parents=True, exist_ok=True)
    target = OUT / "report.json"
    target.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--download", action="store_true")
    parser.add_argument("--from", dest="start", type=int, default=2021)
    parser.add_argument("--to", dest="end", type=int, default=pd.Timestamp.utcnow().year)
    args = parser.parse_args()
    print(json.dumps(run(args.download, args.start, args.end), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

