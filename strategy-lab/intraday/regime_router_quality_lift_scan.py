"""Quality-lift scan for the live regime router.

The finalist passes the raw-OHLC parity check, but it times out too often
because helper modules add many low-expectancy trades. This scan tests the five
practical fixes:

  1. remove or filter GBP London,
  2. add stricter NQ ORB regime filters,
  3. re-check EUR London fade filters/weights,
  4. loosen/tighten sweep selection,
  5. keep only candidates near >=3 trades/week with materially higher exp_r.
"""
from __future__ import annotations

import itertools
from pathlib import Path

import numpy as np
import pandas as pd

OUT = Path(__file__).resolve().parent.parent / "outputs" / "intraday"

SWEEP = "SWEEP_CORE_AVOID_MID_VWAP"
NQ = "NQ_ORB_STRONG_TREND"
EUR = "EUR_LONDON_FADE_EMA"
GBP = "GBP_LONDON_STRONG_TREND"

PRIORITY = {SWEEP: 1, NQ: 2, EUR: 3, GBP: 4}


def _load_time_csv(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    time_col = "timestamp" if "timestamp" in df.columns else df.columns[0]
    df[time_col] = pd.to_datetime(df[time_col], errors="coerce")
    df = df.dropna(subset=[time_col]).set_index(time_col).sort_index()
    df["r"] = pd.to_numeric(df["r"], errors="coerce")
    return df.dropna(subset=["r"])


def _metrics(r: pd.Series) -> dict:
    r = pd.to_numeric(r, errors="coerce").dropna()
    n = len(r)
    if n == 0:
        return {
            "trades": 0,
            "exp_r": np.nan,
            "win_rate": np.nan,
            "avg_win_r": np.nan,
            "avg_loss_r": np.nan,
            "pf": np.nan,
            "total_R": 0.0,
        }
    wins = r[r > 0]
    losses = r[r < 0]
    gross_win = float(wins.sum())
    gross_loss = float(-losses.sum())
    return {
        "trades": int(n),
        "exp_r": float(r.mean()),
        "win_rate": float((r > 0).mean() * 100.0),
        "avg_win_r": float(wins.mean()) if len(wins) else 0.0,
        "avg_loss_r": float(losses.mean()) if len(losses) else 0.0,
        "pf": gross_win / gross_loss if gross_loss > 0 else np.inf,
        "total_R": float(r.sum()),
    }


def _weeks(index: pd.DatetimeIndex) -> float:
    return max((index[-1] - index[0]).days / 7.0, 1e-9) if len(index) else 1.0


def _dedupe(trades: pd.DataFrame) -> pd.DataFrame:
    if trades.empty:
        return trades
    out = trades.copy()
    out["priority"] = out["module"].map(PRIORITY).fillna(9)
    out = out.sort_values(["priority", "weight"], ascending=[True, False])
    return out[~out.index.duplicated(keep="first")].sort_index()


def _with_module(df: pd.DataFrame, module: str, label: str, weight: float) -> pd.DataFrame:
    out = df.copy()
    out["module"] = module
    out["variant"] = label
    out["weight"] = weight
    out["weighted_r"] = out["r"] * weight
    return out


def _single_and_pair_variants(
    base: pd.DataFrame,
    module: str,
    setup_filter: str,
    min_trades: int,
    top_n: int,
) -> list[dict]:
    setup_names = sorted(
        base.loc[
            base["setup"].astype(str).str.contains(setup_filter, regex=False, na=False),
            "setup",
        ].dropna().unique()
    )
    cols = ["adx_regime", "atr_regime", "range_regime", "ema_aligned", "dow", "dir"]
    variants: list[dict] = []

    def add(label: str, df: pd.DataFrame) -> None:
        if len(df) < min_trades:
            return
        m = _metrics(df["r"])
        tpw = m["trades"] / _weeks(df.index)
        if m["exp_r"] <= -0.02:
            return
        variants.append({
            "module": module,
            "label": label,
            "df": df,
            "trades": m["trades"],
            "exp_r": m["exp_r"],
            "pf": m["pf"],
            "tpw": tpw,
            "score": m["exp_r"] * 100.0 + min(tpw, 3.0) * 4.0 + min(m["pf"], 3.0),
        })

    for setup in setup_names:
        src = base[base["setup"] == setup].copy()
        setup_label = setup.replace("NASDAQ100 ", "NQ ").replace(" sl=other_side", "")
        add(f"{setup_label}|all", src)

        filters = []
        for col in cols:
            if col not in src.columns:
                continue
            for val in sorted(src[col].dropna().unique(), key=lambda x: str(x)):
                allow = src[src[col] == val]
                avoid = src[src[col] != val]
                filters.append((f"{col}={val}", allow))
                filters.append((f"{col}!={val}", avoid))
                add(f"{setup_label}|{col}={val}", allow)
                add(f"{setup_label}|{col}!={val}", avoid)

        # Pair allows only. Avoid-pair filters get too curve-fitty too quickly.
        allow_filters = [(name, df) for name, df in filters if "!=" not in name]
        for (name_a, df_a), (name_b, _) in itertools.combinations(allow_filters, 2):
            col_a = name_a.split("=")[0]
            col_b = name_b.split("=")[0]
            if col_a == col_b:
                continue
            val_b = name_b.split("=", 1)[1]
            pair = df_a[df_a[col_b].astype(str) == val_b]
            add(f"{setup_label}|{name_a}&{name_b}", pair)

    deduped = {}
    for item in sorted(variants, key=lambda x: x["score"], reverse=True):
        deduped.setdefault(item["label"], item)
    out = list(deduped.values())
    out = sorted(out, key=lambda x: x["score"], reverse=True)[:top_n]
    return out


def _sweep_variants(sweep: pd.DataFrame) -> list[dict]:
    variants: list[dict] = []

    def add(label: str, df: pd.DataFrame) -> None:
        if len(df) < 8:
            return
        m = _metrics(df["r"])
        variants.append({
            "module": SWEEP,
            "label": label,
            "df": df,
            "trades": m["trades"],
            "exp_r": m["exp_r"],
            "pf": m["pf"],
            "tpw": m["trades"] / _weeks(df.index),
            "score": m["exp_r"] * 100.0 + min(m["trades"] / _weeks(df.index), 1.0) * 8.0,
        })

    current = sweep[sweep["vwap_dist_regime"] != "mid_vwap_dist"]
    add("sweep|current_avoid_mid_vwap", current)
    add("sweep|all_filtered", sweep)
    for col in ["adx_regime", "atr_regime", "vwap_dist_regime", "bar_range_regime", "dir", "dow"]:
        for val in sorted(sweep[col].dropna().unique(), key=lambda x: str(x)):
            add(f"sweep|{col}={val}", sweep[sweep[col] == val])
            add(f"sweep|{col}!={val}", sweep[sweep[col] != val])
    out = sorted(variants, key=lambda x: x["score"], reverse=True)
    keep = {"sweep|current_avoid_mid_vwap", "sweep|all_filtered"}
    selected = []
    seen = set()
    for item in out:
        if item["label"] in keep or len(selected) < 8:
            if item["label"] not in seen:
                selected.append(item)
                seen.add(item["label"])
    return selected[:10]


def _risk(state: dict, module: str) -> float:
    base = 0.03 if int(state["win_streak"]) >= 1 else 0.015
    if module == SWEEP:
        return min(base * 1.5, 0.03)
    return base


def _challenge(df: pd.DataFrame, days: int = 30) -> pd.DataFrame:
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
        risks = []
        for ts, row in sub.iterrows():
            day = ts.normalize()
            if day_start is None or day != day_start:
                day_start = day
                day_start_eq = state["eq"]
            trading_days.add(day)
            rv = float(row["weighted_r"])
            risk = _risk(state, str(row["module"]))
            risks.append(risk)
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


def _window_summary(w: pd.DataFrame) -> dict:
    vc = w["result"].value_counts(normalize=True) * 100.0
    passed = w[w["result"] == "pass"]
    return {
        "pass_pct": float(vc.get("pass", 0.0)),
        "daily_dd_pct": float(vc.get("daily_dd", 0.0)),
        "total_dd_pct": float(vc.get("total_dd", 0.0)),
        "timeout_pct": float(vc.get("timeout", 0.0)),
        "median_pass_day": float(passed["pass_day"].median()) if len(passed) else np.nan,
        "mean_pass_day": float(passed["pass_day"].mean()) if len(passed) else np.nan,
        "median_trades_30d": float(w["trades"].median()),
        "median_final_eq": float(w["final_eq"].median()),
        "avg_window_risk_pct": float(w["avg_risk_pct"].mean()),
    }


def _year_stats(df: pd.DataFrame) -> dict:
    totals = df["weighted_r"].groupby(df.index.year).sum()
    return {
        "positive_years": int((totals > 0).sum()),
        "min_year_R": float(totals.min()) if len(totals) else np.nan,
        "years": ";".join(f"{int(y)}:{v:.2f}" for y, v in totals.items()),
    }


def _combo_metrics(parts: list[pd.DataFrame]) -> tuple[pd.DataFrame, dict]:
    ledger = _dedupe(pd.concat(parts).sort_index())
    m = _metrics(ledger["weighted_r"])
    m["trades_per_week"] = m["trades"] / _weeks(ledger.index)
    m.update(_year_stats(ledger))
    return ledger, m


def main() -> None:
    sweep = _load_time_csv(OUT / "sweep_regime_ledger.csv")
    sweep["setup"] = "NQ sweep"
    internet = _load_time_csv(OUT / "internet_seed_regime_ledgers.csv")

    sweep_vars = _sweep_variants(sweep)
    nq_vars = _single_and_pair_variants(internet, NQ, "NASDAQ100 ORB", 80, 5)
    eur_vars = _single_and_pair_variants(internet, EUR, "EURUSD London", 35, 4)
    gbp_vars = _single_and_pair_variants(internet, GBP, "GBPUSD London", 35, 3)
    gbp_vars = [{"module": GBP, "label": "GBP_OFF", "df": internet.iloc[0:0], "trades": 0, "exp_r": 0.0, "pf": np.nan, "tpw": 0.0, "score": 999.0}] + gbp_vars

    variant_rows = []
    for group, vars_ in [("sweep", sweep_vars), ("nq", nq_vars), ("eur", eur_vars), ("gbp", gbp_vars)]:
        for v in vars_:
            variant_rows.append({
                "group": group,
                "label": v["label"],
                "trades": v["trades"],
                "trades_per_week": v["tpw"],
                "exp_r": v["exp_r"],
                "pf": v["pf"],
            })
    pd.DataFrame(variant_rows).to_csv(OUT / "regime_router_quality_lift_variants.csv", index=False)

    weight_grid = {
        SWEEP: [1.0],
        NQ: [0.70, 1.0],
        EUR: [0.60, 1.0],
        GBP: [0.0, 0.25],
    }

    fast_rows = []
    for sv, nv, ev, gv in itertools.product(sweep_vars, nq_vars, eur_vars, gbp_vars):
        for nw, ew, gw in itertools.product(weight_grid[NQ], weight_grid[EUR], weight_grid[GBP]):
            if gv["label"] == "GBP_OFF" and gw != 0.0:
                continue
            parts = [
                _with_module(sv["df"], SWEEP, sv["label"], 1.0),
                _with_module(nv["df"], NQ, nv["label"], nw),
                _with_module(ev["df"], EUR, ev["label"], ew),
            ]
            if gv["label"] != "GBP_OFF" and gw > 0:
                parts.append(_with_module(gv["df"], GBP, gv["label"], gw))
            ledger, m = _combo_metrics(parts)
            if m["trades_per_week"] < 2.5:
                continue
            fast_rows.append({
                "sweep_variant": sv["label"],
                "nq_variant": nv["label"],
                "eur_variant": ev["label"],
                "gbp_variant": gv["label"] if gw > 0 else "GBP_OFF",
                "sweep_w": 1.0,
                "nq_w": nw,
                "eur_w": ew,
                "gbp_w": gw if gv["label"] != "GBP_OFF" else 0.0,
                **m,
                "pre_score": (
                    m["exp_r"] * 180.0
                    + min(m["trades_per_week"], 5.0) * 3.0
                    + min(m["pf"], 2.5) * 5.0
                    + m["min_year_R"] * 0.5
                ),
            })

    fast = pd.DataFrame(fast_rows).sort_values("pre_score", ascending=False)
    fast.to_csv(OUT / "regime_router_quality_lift_fast_scan.csv", index=False)

    challenge_rows = []
    eval_rows = fast.head(60).to_dict("records")
    for row in eval_rows:
        sv = next(v for v in sweep_vars if v["label"] == row["sweep_variant"])
        nv = next(v for v in nq_vars if v["label"] == row["nq_variant"])
        ev = next(v for v in eur_vars if v["label"] == row["eur_variant"])
        gv = next((v for v in gbp_vars if v["label"] == row["gbp_variant"]), gbp_vars[0])
        parts = [
            _with_module(sv["df"], SWEEP, sv["label"], row["sweep_w"]),
            _with_module(nv["df"], NQ, nv["label"], row["nq_w"]),
            _with_module(ev["df"], EUR, ev["label"], row["eur_w"]),
        ]
        if row["gbp_variant"] != "GBP_OFF" and row["gbp_w"] > 0:
            parts.append(_with_module(gv["df"], GBP, gv["label"], row["gbp_w"]))
        ledger, m = _combo_metrics(parts)
        windows = _challenge(ledger)
        ws = _window_summary(windows)
        challenge_rows.append({
            **{k: row[k] for k in [
                "sweep_variant", "nq_variant", "eur_variant", "gbp_variant",
                "sweep_w", "nq_w", "eur_w", "gbp_w",
            ]},
            **m,
            **ws,
            "score": (
                ws["pass_pct"] * 1.7
                + m["exp_r"] * 160.0
                - ws["daily_dd_pct"] * 2.0
                - ws["total_dd_pct"] * 1.5
                + min(m["trades_per_week"], 4.5) * 3.0
                + m["min_year_R"] * 0.35
            ),
        })

    res = pd.DataFrame(challenge_rows).sort_values(["score", "pass_pct"], ascending=False)
    res.to_csv(OUT / "regime_router_quality_lift_scan.csv", index=False)
    if not res.empty:
        best = res.iloc[0]
        pd.DataFrame([best]).to_csv(OUT / "regime_router_quality_lift_best_summary.csv", index=False)

    cols = [
        "score", "pass_pct", "timeout_pct", "daily_dd_pct", "total_dd_pct",
        "trades", "trades_per_week", "exp_r", "win_rate", "avg_win_r",
        "avg_loss_r", "pf", "total_R", "min_year_R", "median_trades_30d",
        "sweep_variant", "nq_variant", "eur_variant", "gbp_variant",
        "nq_w", "eur_w", "gbp_w",
    ]
    print("\nQUALITY LIFT SCAN")
    print(f"variants: {OUT / 'regime_router_quality_lift_variants.csv'}")
    print(f"fast:     {OUT / 'regime_router_quality_lift_fast_scan.csv'}")
    print(f"scan:     {OUT / 'regime_router_quality_lift_scan.csv'}")
    print(f"best:     {OUT / 'regime_router_quality_lift_best_summary.csv'}")
    print("\nTOP 20")
    print(res[cols].head(20).to_string(index=False))


if __name__ == "__main__":
    main()
