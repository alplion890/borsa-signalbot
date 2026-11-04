"""Mevcut tarihsel moduller icin gecikmeli reel faiz ve dolar yonu A/B.

Kurallar sabittir: 5 is gunluk degisim, reel faizde 2 is gunu ve DXY'de
1 is gunu gecikme. Gun ici yayin saati bilinmeyen gunluk kapanislar ayni gun
isleme sokulmaz. FRED vintage kullanilmadigindan sonradan yapilan olasi seri
revizyonlari ayrica denetlenmelidir. Haber surprizi/canliya alma testi degildir.

Calistir: python -m intraday.macro_context_ab [--refresh] [--modules NQ_ORB GOLD_ORB EUR_LONDON GBP_LONDON]
"""
from __future__ import annotations

import argparse
import json
from dataclasses import replace
from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf

from .history_fetch import load_history
from .long_history_ab import run_spec, spec_by_name, summarize

OUT = Path(__file__).resolve().parent.parent / "outputs" / "intraday" / "macro_context_ab"


def _sources(refresh: bool) -> tuple[pd.Series, pd.Series]:
    OUT.mkdir(parents=True, exist_ok=True)
    fred_path = OUT / "DFII10_fred.csv"
    dxy_path = OUT / "DXY_yahoo.csv"
    if refresh or not fred_path.exists():
        pd.read_csv("https://fred.stlouisfed.org/graph/fredgraph.csv?id=DFII10").to_csv(
            fred_path, index=False
        )
    if refresh or not dxy_path.exists():
        raw = yf.Ticker("DX-Y.NYB").history(
            start="2012-01-01", interval="1d", auto_adjust=False
        )
        if raw.empty:
            raise RuntimeError("Yahoo DXY gunluk verisi bos geldi")
        pd.DataFrame({"date": raw.index.date, "close": raw["Close"].to_numpy()}).to_csv(
            dxy_path, index=False
        )
    fred = pd.read_csv(fred_path, parse_dates=["observation_date"])
    dxy = pd.read_csv(dxy_path, parse_dates=["date"])
    real = pd.to_numeric(fred["DFII10"], errors="coerce")
    real.index = pd.DatetimeIndex(fred["observation_date"])
    dollar = pd.to_numeric(dxy["close"], errors="coerce")
    dollar.index = pd.DatetimeIndex(dxy["date"])
    return real.sort_index(), dollar.sort_index()


def delayed_change(series: pd.Series, dates: pd.DatetimeIndex, lag: int) -> pd.Series:
    """Trade gununde bilinen en son gunluk kapanisin 5 is gunluk farki."""
    calendar = pd.date_range(
        min(series.index.min(), dates.min()) - pd.Timedelta(days=14),
        max(series.index.max(), dates.max()), freq="B"
    )
    # Tatillerde en fazla uc is gunu geriye bak; uzun veri deliklerini gecersiz say.
    daily = series.reindex(calendar).ffill(limit=3)
    change = daily.shift(lag) - daily.shift(lag + 5)
    return change.reindex(dates.normalize()).set_axis(dates)


def _summary(r: pd.Series) -> dict:
    base = summarize(r)
    if not len(r):
        return base | {"max_drawdown_R": None, "positive_years": 0, "years": 0}
    equity = r.cumsum()
    annual = r.groupby(r.index.year).sum()
    return base | {
        "max_drawdown_R": float((equity - equity.cummax().clip(lower=0)).min()),
        "positive_years": int((annual > 0).sum()), "years": int(len(annual)),
    }


def _weekly_delta_ci(base: pd.Series, candidate: pd.Series, seed: int = 817) -> list[float]:
    start = min(base.index.min(), candidate.index.min()).normalize()
    end = max(base.index.max(), candidate.index.max()).normalize()
    weeks = pd.date_range(start, end + pd.Timedelta(days=7), freq="W")
    a = base.resample("W").sum().reindex(weeks, fill_value=0.0)
    b = candidate.resample("W").sum().reindex(weeks, fill_value=0.0)
    diff = (b - a).to_numpy()
    if len(diff) < 2:
        return [float("nan"), float("nan")]
    rng = np.random.default_rng(seed)
    draws = rng.choice(diff, size=(5000, len(diff)), replace=True).mean(axis=1)
    return [float(v) for v in np.quantile(draws, [0.025, 0.975])]


def gbp_causal_build(frame: pd.DataFrame) -> tuple:
    """Match the live range-rank at each signal using only then-known closes."""
    from .long_history_ab import _GBP_LONDON
    from .internet_seed_strategies import _build_london
    le, se, *levels = _build_london(frame, _GBP_LONDON)
    dates = frame.index.normalize()
    h = frame.index.hour + frame.index.minute / 60.0
    window = (h >= _GBP_LONDON.range_start) & (h < _GBP_LONDON.range_end)
    high = frame.high.where(window).groupby(dates).max()
    low = frame.low.where(window).groupby(dates).min()
    width = high - low
    past_ranges = width / frame.close.groupby(dates).last()
    ok = pd.Series(False, index=frame.index)
    for i in np.flatnonzero((le | se).to_numpy()):
        date = dates[i]
        pos = past_ranges.index.get_loc(date)
        previous = past_ranges.iloc[max(0, pos - 19):pos].dropna()
        current = width.loc[date] / frame.close.iloc[i]
        if len(previous) < 9 or not np.isfinite(current):
            continue
        rank = (1 + (previous < current).sum() + 0.5 * (previous == current).sum()) / (len(previous) + 1)
        ok.iloc[i] = 0.33 < rank <= 0.67
    return le & ok, se & ok, *levels


def run(refresh: bool = False, module: str = "SWEEP_CORE") -> dict:
    real, dxy = _sources(refresh)
    spec = spec_by_name(module)
    out = OUT if module == "SWEEP_CORE" else OUT / module
    out.mkdir(parents=True, exist_ok=True)
    if module == "GBP_LONDON":
        # The historical mirror normalizes the range by the day's LAST close.
        # Use the signal close for today and already-known closes for past days.
        spec = replace(spec, build=gbp_causal_build)
    df = load_history(spec.symbol, spec.tf, start_year=2012)
    dates = pd.DatetimeIndex(df.index.normalize().unique())
    rc = delayed_change(real, dates, lag=2)
    dc = delayed_change(dxy, dates, lag=1)
    daily = pd.DataFrame({"real_5d": rc, "dxy_5d": dc}, index=dates)
    daily["valid"] = daily.notna().all(axis=1)
    daily.to_csv(out / "daily_features.csv", index_label="trade_date_utc")
    aligned = daily.reindex(df.index.normalize()).set_axis(df.index)
    coverage = aligned["valid"].fillna(False).astype(bool)
    real_long = coverage & (aligned["real_5d"] <= 0)
    real_short = coverage & (aligned["real_5d"] >= 0)
    dxy_long = coverage & (aligned["dxy_5d"] <= 0)
    dxy_short = coverage & (aligned["dxy_5d"] >= 0)
    masks = {
        "baseline": (coverage, coverage),
        "real_yield": (real_long, real_short),
        "dxy": (dxy_long, dxy_short),
        "both": (real_long & dxy_long, real_short & dxy_short),
    }
    results: dict[str, pd.Series] = {}
    for name, (long_mask, short_mask) in masks.items():
        def filtered(frame: pd.DataFrame, lm=long_mask, sm=short_mask):
            le, se, lsl, ltp, ssl, stp = spec.build(frame)
            return le & lm, se & sm, lsl, ltp, ssl, stp
        results[name] = run_spec(replace(spec, build=filtered), df)
    for name, r in results.items():
        r.rename("R").to_csv(out / f"trades_{name}.csv", index_label="entry_utc")
    report = {
        "hypothesis": f"{module}: 5 is gunluk ABD reel faiz ve/veya DXY dususu long, yukselisi short icin onay",
        "module": module, "symbol": spec.symbol, "timeframe": spec.tf,
        "scope": "Historical long_history_ab definitions; not proof of current forward module parity",
        "gbp_correction": "current range normalized by signal close; past 19 dates use already-known day closes" if module == "GBP_LONDON" else None,
        "data": {"nq_first": str(df.index.min()), "nq_last": str(df.index.max()),
                 "bars": len(df), "valid_days": int(daily["valid"].sum()),
                 "all_days": len(daily), "real_source": "FRED DFII10 daily; 2 business-day lag",
                 "dxy_source": "Yahoo DX-Y.NYB daily; 1 business-day lag"},
        "variants": {},
    }
    for name, r in results.items():
        variants = report["variants"]
        variants[name] = {"full": _summary(r)}
        for label, lo, hi in (("2012_2021", 2012, 2021), ("2022_2026", 2022, 2026)):
            part = r[(r.index.year >= lo) & (r.index.year <= hi)]
            variants[name][label] = _summary(part)
        if name != "baseline" and len(r) and len(results["baseline"]):
            variants[name]["weekly_delta_R_ci95"] = _weekly_delta_ci(results["baseline"], r)
    (out / "report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    return report


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--refresh", action="store_true")
    p.add_argument("--modules", nargs="+", default=["SWEEP_CORE"],
                   choices=["SWEEP_CORE", "NQ_ORB", "GOLD_ORB", "EUR_LONDON", "GBP_LONDON"])
    args = p.parse_args()
    for i, module in enumerate(args.modules):
        report = run(args.refresh and i == 0, module)
        print(json.dumps(report, indent=2, ensure_ascii=False, default=str), flush=True)


if __name__ == "__main__":
    main()
