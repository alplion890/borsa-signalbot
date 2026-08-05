"""Regime router portfolio built from existing trade ledgers.

This is the next step after the autopsy:
  - keep the high-quality sweep edge as the core,
  - add only regime-positive complementary modules,
  - evaluate static vs online guarded routing,
  - simulate prop-style 30-day calendar windows.

It does not redownload market data and does not rerun indicator grids.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

OUT = Path(__file__).resolve().parent.parent / "outputs" / "intraday"


@dataclass(frozen=True)
class ModuleSpec:
    name: str
    source: str
    setup_contains: str | None = None
    filters: tuple[tuple[str, object, str], ...] = ()  # (column, value, op)
    weight: float = 1.0


def _load_ledger(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    time_col = "timestamp" if "timestamp" in df.columns else df.columns[0]
    df[time_col] = pd.to_datetime(df[time_col], errors="coerce")
    df = df.dropna(subset=[time_col]).set_index(time_col).sort_index()
    df["r"] = pd.to_numeric(df["r"], errors="coerce")
    df = df.dropna(subset=["r"])
    if "setup" not in df.columns:
        df["setup"] = "NQ sweep"
    return df


def _metrics(r: pd.Series) -> dict:
    r = pd.to_numeric(r, errors="coerce").dropna()
    n = len(r)
    if n == 0:
        return {"trades": 0, "exp_r": np.nan, "win_rate": np.nan, "pf": np.nan, "total_R": 0.0}
    wins = r[r > 0]
    losses = r[r < 0]
    gross_win = float(wins.sum())
    gross_loss = float(-losses.sum())
    return {
        "trades": int(n),
        "exp_r": round(float(r.mean()), 3),
        "win_rate": round(float((r > 0).mean() * 100), 1),
        "pf": round(gross_win / gross_loss, 3) if gross_loss > 0 else np.inf,
        "total_R": round(float(r.sum()), 2),
    }


def _calendar_windows(
    r: pd.Series,
    target: float = 0.10,
    daily_dd: float = 0.05,
    total_dd: float = 0.10,
    days: int = 30,
    min_trading_days: int = 4,
    risk_base: float = 0.01,
    risk_boost: float | None = 0.02,
) -> pd.DataFrame:
    if r.empty:
        return pd.DataFrame()
    r = r.sort_index()
    first_day = r.index[0].normalize()
    last_start = (r.index[-1] - pd.Timedelta(days=days)).normalize()
    starts = pd.date_range(first_day, last_start, freq="D")
    rows = []
    for start in starts:
        end = start + pd.Timedelta(days=days)
        sub = r.loc[start:end]
        eq = 1.0
        peak = 1.0
        prev_win = False
        trading_days: set[pd.Timestamp] = set()
        day_start = None
        day_start_eq = eq
        result = "timeout"
        pass_day = np.nan
        for ts, ri in sub.items():
            day = ts.normalize()
            if day_start is None or day != day_start:
                day_start = day
                day_start_eq = eq
            trading_days.add(day)
            risk = risk_boost if (risk_boost is not None and prev_win) else risk_base
            eq *= 1.0 + float(ri) * risk
            peak = max(peak, eq)
            if eq <= day_start_eq - daily_dd:
                result = "daily_dd"
                break
            if eq <= 1.0 - total_dd:
                result = "total_dd"
                break
            if eq >= 1.0 + target and len(trading_days) >= min_trading_days:
                result = "pass"
                pass_day = float((ts.normalize() - start).days)
                break
            prev_win = float(ri) > 0
        rows.append({
            "start": start,
            "result": result,
            "trades": int(len(sub)),
            "trading_days": int(len(trading_days)),
            "final_eq": eq,
            "pass_day": pass_day,
        })
    return pd.DataFrame(rows)


def _apply_filters(df: pd.DataFrame, spec: ModuleSpec) -> pd.DataFrame:
    out = df.copy()
    if spec.setup_contains:
        out = out[out["setup"].astype(str).str.contains(spec.setup_contains, regex=False, na=False)]
    for col, value, op in spec.filters:
        if col not in out.columns:
            return out.iloc[0:0]
        if op == "==":
            out = out[out[col] == value]
        elif op == "!=":
            out = out[out[col] != value]
        else:
            raise ValueError(f"Unsupported op: {op}")
    out = out.copy()
    out["module"] = spec.name
    out["module_weight"] = spec.weight
    out["weighted_r"] = out["r"] * spec.weight
    return out


def _guard_online(module_trades: pd.DataFrame, window: int = 20, min_prior: int = 20, floor: float = -0.05) -> pd.DataFrame:
    """Online kill switch: after enough trades, require prior rolling expectancy."""
    kept = []
    for _, sub in module_trades.sort_index().groupby("module", sort=False):
        sub = sub.sort_index().copy()
        prior_roll = sub["weighted_r"].shift(1).rolling(window, min_periods=min_prior).mean()
        sub["prior_roll_exp"] = prior_roll
        sub["guard_pass"] = prior_roll.isna() | (prior_roll >= floor)
        kept.append(sub[sub["guard_pass"]])
    return pd.concat(kept).sort_index() if kept else module_trades.iloc[0:0]


def _dedupe_router_trades(trades: pd.DataFrame) -> pd.DataFrame:
    """Keep one trade per timestamp; prefer higher module priority/weight."""
    if trades.empty:
        return trades
    priority = {
        "SWEEP_ES_DIV": 1,
        "NQ_ORB_STRONG_TREND": 2,
        "EUR_LONDON_FADE_EMA": 3,
        "GBP_LONDON_STRONG_TREND": 4,
    }
    out = trades.copy()
    out["priority"] = out["module"].map(priority).fillna(9)
    out = out.sort_values(["priority", "module_weight"], ascending=[True, False])
    out = out[~out.index.duplicated(keep="first")].sort_index()
    return out


def _summary(name: str, trades: pd.DataFrame) -> dict:
    r = trades["weighted_r"].sort_index() if not trades.empty else pd.Series(dtype=float)
    m = _metrics(r)
    weeks = max((r.index[-1] - r.index[0]).days / 7, 1e-9) if len(r) else 1.0
    years = []
    if len(r):
        for year, sub in r.groupby(r.index.year):
            ym = _metrics(sub)
            ym["year"] = int(year)
            years.append(ym)
    year_df = pd.DataFrame(years)
    windows_1_2 = _calendar_windows(r, risk_base=0.01, risk_boost=0.02)
    windows_15_3 = _calendar_windows(r, risk_base=0.015, risk_boost=0.03)
    def pass_stats(w: pd.DataFrame) -> dict:
        if w.empty:
            return {"pass": 0.0, "daily": 0.0, "total": 0.0, "timeout": 100.0, "median_trades": 0.0}
        vc = w["result"].value_counts(normalize=True) * 100
        return {
            "pass": round(float(vc.get("pass", 0.0)), 2),
            "daily": round(float(vc.get("daily_dd", 0.0)), 2),
            "total": round(float(vc.get("total_dd", 0.0)), 2),
            "timeout": round(float(vc.get("timeout", 0.0)), 2),
            "median_trades": round(float(w["trades"].median()), 1),
        }
    s12 = pass_stats(windows_1_2)
    s153 = pass_stats(windows_15_3)
    return {
        "router": name,
        **m,
        "trades_per_week": round(m["trades"] / weeks, 3),
        "positive_years": int((year_df["total_R"] > 0).sum()) if not year_df.empty else 0,
        "min_year_R": round(float(year_df["total_R"].min()), 2) if not year_df.empty else np.nan,
        "pass_1_2": s12["pass"],
        "daily_1_2": s12["daily"],
        "timeout_1_2": s12["timeout"],
        "median_trades_1_2": s12["median_trades"],
        "pass_1_5_3": s153["pass"],
        "daily_1_5_3": s153["daily"],
        "timeout_1_5_3": s153["timeout"],
        "median_trades_1_5_3": s153["median_trades"],
    }


def _reweight_modules(all_trades: pd.DataFrame, weights: dict[str, float]) -> pd.DataFrame:
    out = all_trades.copy()
    out["module_weight"] = out["module"].map(weights).astype(float)
    out["weighted_r"] = out["r"] * out["module_weight"]
    return _dedupe_router_trades(out)


def _weight_scan(all_trades: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for nq_w in (0.20, 0.30, 0.35, 0.45, 0.55, 0.70):
        for eur_w in (0.00, 0.20, 0.30, 0.45, 0.60):
            for gbp_w in (0.00, 0.15, 0.25, 0.35, 0.50):
                weights = {
                    "SWEEP_ES_DIV": 1.0,
                    "NQ_ORB_STRONG_TREND": nq_w,
                    "EUR_LONDON_FADE_EMA": eur_w,
                    "GBP_LONDON_STRONG_TREND": gbp_w,
                }
                ledger = _reweight_modules(all_trades, weights)
                s = _summary("weight_scan", ledger)
                s.update({
                    "sweep_w": 1.0,
                    "nq_w": nq_w,
                    "eur_w": eur_w,
                    "gbp_w": gbp_w,
                })
                rows.append(s)
    res = pd.DataFrame(rows)
    # Keep sane candidates first: enough frequency, all years positive, daily DD not silly.
    res["score"] = (
        res["pass_1_5_3"] * 1.5
        + res["exp_r"] * 100
        + res["pf"] * 3
        + res["min_year_R"] * 0.5
        - res["daily_1_5_3"] * 1.5
        - (res["trades_per_week"] - 5.0).abs() * 2.0
    )
    return res.sort_values("score", ascending=False)


def main() -> None:
    sweep = _load_ledger(OUT / "sweep_regime_ledger.csv")
    internet = _load_ledger(OUT / "internet_seed_regime_ledgers.csv")
    divergence = _load_ledger(OUT / "intermarket_divergence_ledger.csv")
    sources = {"sweep": sweep, "internet": internet, "divergence": divergence}

    specs = [
        ModuleSpec(
            name="SWEEP_ES_DIV",
            source="divergence",
            weight=1.0,
        ),
        ModuleSpec(
            name="NQ_ORB_STRONG_TREND",
            source="internet",
            setup_contains="NASDAQ100 ORB open=14.5 range=15 retest none rr=1.5 sl=other_side hold=48",
            filters=(("adx_regime", "strong_trend", "=="),),
            weight=0.35,
        ),
        ModuleSpec(
            name="EUR_LONDON_FADE_EMA",
            source="internet",
            setup_contains="EURUSD London range=2.0-7.0 none rr=1.0 sl=other_side hold=48",
            filters=(("ema_aligned", False, "=="),),
            weight=0.30,
        ),
        ModuleSpec(
            name="GBP_LONDON_STRONG_TREND",
            source="internet",
            setup_contains="GBPUSD London range=2.0-7.0 none rr=2.0 sl=other_side hold=48",
            filters=(("adx_regime", "strong_trend", "=="),),
            weight=0.25,
        ),
    ]

    modules = []
    module_rows = []
    for spec in specs:
        mod = _apply_filters(sources[spec.source], spec)
        modules.append(mod)
        raw_m = _metrics(mod["r"]) if not mod.empty else _metrics(pd.Series(dtype=float))
        weighted_m = _metrics(mod["weighted_r"]) if not mod.empty else raw_m
        module_rows.append({
            "module": spec.name,
            "source": spec.source,
            "weight": spec.weight,
            "trades": raw_m["trades"],
            "raw_exp_r": raw_m["exp_r"],
            "raw_pf": raw_m["pf"],
            "weighted_exp_r": weighted_m["exp_r"],
            "weighted_total_R": weighted_m["total_R"],
        })

    all_trades = pd.concat(modules).sort_index()
    static = _dedupe_router_trades(all_trades)
    guarded = _dedupe_router_trades(_guard_online(all_trades, window=20, min_prior=20, floor=-0.05))
    scan = _weight_scan(all_trades)
    best = scan.iloc[0]
    best_weights = {
        "SWEEP_ES_DIV": 1.0,
        "NQ_ORB_STRONG_TREND": float(best["nq_w"]),
        "EUR_LONDON_FADE_EMA": float(best["eur_w"]),
        "GBP_LONDON_STRONG_TREND": float(best["gbp_w"]),
    }
    best_weighted = _reweight_modules(all_trades, best_weights)

    summaries = pd.DataFrame([
        _summary("static_regime_router", static),
        _summary("online_guarded_router", guarded),
        _summary("best_weight_scan_router", best_weighted),
    ])

    module_df = pd.DataFrame(module_rows)
    static_ledger = static[["module", "setup", "r", "weighted_r", "module_weight"]].copy()
    guarded_ledger = guarded[["module", "setup", "r", "weighted_r", "module_weight"]].copy()
    years = []
    for name, ledger in (("static_regime_router", static), ("online_guarded_router", guarded)):
        for year, sub in ledger["weighted_r"].groupby(ledger.index.year):
            row = {"router": name, "year": int(year)}
            row.update(_metrics(sub))
            years.append(row)
    for year, sub in best_weighted["weighted_r"].groupby(best_weighted.index.year):
        row = {"router": "best_weight_scan_router", "year": int(year)}
        row.update(_metrics(sub))
        years.append(row)
    years_df = pd.DataFrame(years)

    module_path = OUT / "regime_router_modules.csv"
    summary_path = OUT / "regime_router_summary.csv"
    years_path = OUT / "regime_router_years.csv"
    static_path = OUT / "regime_router_static_ledger.csv"
    guarded_path = OUT / "regime_router_guarded_ledger.csv"
    best_path = OUT / "regime_router_best_weighted_ledger.csv"
    scan_path = OUT / "regime_router_weight_scan.csv"
    module_df.to_csv(module_path, index=False)
    summaries.to_csv(summary_path, index=False)
    years_df.to_csv(years_path, index=False)
    static_ledger.to_csv(static_path)
    guarded_ledger.to_csv(guarded_path)
    best_weighted[["module", "setup", "r", "weighted_r", "module_weight"]].to_csv(best_path)
    scan.to_csv(scan_path, index=False)

    print("\nREGIME ROUTER FACTORY")
    print(f"modules: {module_path}")
    print(f"summary: {summary_path}")
    print(f"years:   {years_path}")
    print(f"static:  {static_path}")
    print(f"guarded: {guarded_path}")
    print(f"best:    {best_path}")
    print(f"weights: {scan_path}")
    print("\nMODULES")
    print(module_df.to_string(index=False))
    print("\nSUMMARY")
    print(summaries.to_string(index=False))
    print("\nYEARS")
    print(years_df.to_string(index=False))
    print("\nTOP WEIGHT SCAN")
    cols = [
        "nq_w", "eur_w", "gbp_w", "trades", "trades_per_week", "exp_r",
        "pf", "total_R", "positive_years", "min_year_R", "pass_1_2",
        "pass_1_5_3", "daily_1_5_3", "timeout_1_5_3", "score",
    ]
    print(scan[cols].head(20).to_string(index=False))


if __name__ == "__main__":
    main()
