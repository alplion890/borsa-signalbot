"""Meta-label test: can entry-time market conditions separate losing signals?

Preregistered: HANDOFF/meta_label_onkayit_2026-11-16.md (commit 34a3587).
IS 2012-2021 picks the rule; OOS 2022+ judges it once. Costs: Maven-measured.

    python -m intraday.meta_label_lab
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

from . import live_cost_check as lcc
from .config import INSTRUMENTS
from .data_quality import clean
from .event_calendar import all_events
from .hierarchical_edge_lab import hourly_ema_trend
from .history_fetch import load_history
from .honest_engine import simulate_trades
from .indicators import adx, atr
from .long_history_ab import _atr_rank, spec_by_name

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "outputs" / "intraday" / "meta_label"
OOS_START = pd.Timestamp("2022-01-01")
FEATURES = ("atr_rank", "adx", "eff20", "rel_vol", "bar_atr", "event_day",
            "hour", "gap", "with_trend")
BINARY = {"event_day", "with_trend"}
MODULES = ("SWEEP_CORE", "NQ_ORB", "GOLD_ORB", "EUR_LONDON", "GBP_LONDON")
N_PERM = 10_000
RNG = np.random.default_rng(20261116)


@dataclass(frozen=True)
class Trades:
    """Per-trade frame: r0 (zero cost), cost_r (measured central), features."""
    module: str
    frame: pd.DataFrame


def _daily_atr_rank(df: pd.DataFrame) -> pd.Series:
    d = df.resample("1D").agg({"high": "max", "low": "min", "close": "last"}).dropna()
    rank = (atr(d, 14) / d["close"]).rolling(100, min_periods=50).rank(pct=True).shift(1)
    days = pd.Series(df.index.normalize(), index=df.index)
    return days.map(rank)


def _gap(df: pd.DataFrame) -> pd.Series:
    d = df.resample("1D").agg({"open": "first", "high": "max", "low": "min",
                               "close": "last"}).dropna()
    g = ((d["open"] - d["close"].shift(1)).abs() / atr(d, 14).shift(1))
    days = pd.Series(df.index.normalize(), index=df.index)
    return days.map(g)


def feature_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Every column is known when the signal bar closes."""
    a = atr(df, 14)
    step = df["close"].diff().abs()
    eff = (df["close"] - df["close"].shift(20)).abs() / step.rolling(20).sum()
    event_days = {e.gun for e in all_events()}
    return pd.DataFrame({
        "atr_rank": _daily_atr_rank(df),
        "adx": adx(df, 14),
        "eff20": eff,
        "rel_vol": df["volume"] / df["volume"].rolling(20).median().replace(0, np.nan),
        "bar_atr": (df["high"] - df["low"]) / a,
        "event_day": pd.Series(df.index.date, index=df.index).isin(event_days).astype(int),
        "hour": df.index.hour,
        "gap": _gap(df),
        "trend_1h": hourly_ema_trend(df),
    }, index=df.index)


def _sweep_inputs(df: pd.DataFrame, spec) -> tuple:
    le, se, lsl, ltp, ssl, stp = spec.build(df)
    rank = _atr_rank(df)
    cap = pd.Series(np.select([rank < .33, rank < .67], [4., 6.], default=8.), index=df.index)
    ltp = pd.Series(np.minimum(ltp, df.close + (df.close - lsl) * cap), index=df.index)
    stp = pd.Series(np.maximum(stp, df.close - (ssl - df.close) * cap), index=df.index)
    ok = rank.notna()
    return le & ok, se & ok, lsl, ltp, ssl, stp


def module_trades(name: str) -> Trades:
    spec = spec_by_name(name)
    df = clean(load_history(spec.symbol, spec.tf, start_year=2012))
    sig = _sweep_inputs(df, spec) if spec.adaptive_rr else spec.build(df)
    le, se, lsl, ltp, ssl, stp = sig
    r0 = simulate_trades(df, le, se, lsl, ltp, ssl, stp, lcc.zero(spec.symbol),
                         min_rr=spec.min_rr, max_rr=spec.max_rr, max_hold=spec.max_hold)
    idx = r0.index
    long_ = le.reindex(idx).fillna(False).astype(bool)
    entry = df["close"].reindex(idx)
    risk = np.where(long_, entry - lsl.reindex(idx), ssl.reindex(idx) - entry)
    full, _ = lcc.pts(spec.symbol)
    f = feature_frame(df).reindex(idx)
    f["with_trend"] = (np.sign(f.pop("trend_1h")) == np.where(long_, 1, -1)).astype(int)
    f["r0"] = r0.values
    f["cost_r"] = 2 * full / risk
    return Trades(name, f.dropna())


def _perm_p(r: np.ndarray, keep: np.ndarray) -> float:
    """One-sided: is mean(kept) above what random keep-sets of same size give?"""
    obs = r[keep].mean()
    k = int(keep.sum())
    sims = np.array([r[RNG.permutation(len(r))[:k]].mean() for _ in range(N_PERM)])
    return float((np.sum(sims >= obs) + 1) / (N_PERM + 1))


def _evaluate(t: pd.DataFrame, keep: pd.Series, label: str) -> dict:
    o = t.index >= OOS_START
    r_c = (t["r0"] - t["cost_r"]).to_numpy()
    r_h = (t["r0"] - 2 * t["cost_r"]).to_numpy()
    k, oo = keep.to_numpy(), o
    ko = k & oo
    return {
        "rule": label,
        "is_n_all": int((~oo).sum()), "is_exp_all": float(r_c[~oo].mean()),
        "is_n_keep": int((k & ~oo).sum()), "is_exp_keep": float(r_c[k & ~oo].mean()) if (k & ~oo).any() else np.nan,
        "oos_n_all": int(oo.sum()), "oos_exp_all": float(r_c[oo].mean()),
        "oos_n_keep": int(ko.sum()),
        "oos_days_keep": int(pd.Index(t.index[ko].date).nunique()),
        "oos_keep_zero": float(t["r0"].to_numpy()[ko].mean()) if ko.any() else np.nan,
        "oos_keep_central": float(r_c[ko].mean()) if ko.any() else np.nan,
        "oos_keep_high": float(r_h[ko].mean()) if ko.any() else np.nan,
        "oos_p": _perm_p(r_c[oo], k[oo]) if 0 < ko.sum() < oo.sum() else np.nan,
    }


def single_feature_rules(t: pd.DataFrame) -> list[dict]:
    """Test A: skip the IS-worst tercile (or binary value) of each feature."""
    rows, is_ = [], t.index < OOS_START
    r_c = t["r0"] - t["cost_r"]
    for feat in FEATURES:
        if feat in BINARY:
            bucket = t[feat].astype(int)
        else:
            edges = t.loc[is_, feat].quantile([1 / 3, 2 / 3]).to_numpy()
            bucket = pd.Series(np.digitize(t[feat], edges), index=t.index)
        worst = r_c[is_].groupby(bucket[is_]).mean().idxmin()
        rows.append(_evaluate(t, bucket != worst, f"A:{feat}!={worst}"))
    return rows


def model_rule(t: pd.DataFrame) -> dict:
    """Test B: logistic regression on all features, IS-median threshold."""
    is_ = t.index < OOS_START
    x = t[list(FEATURES)].to_numpy(float)
    y = (t["r0"] - t["cost_r"] > 0).astype(int).to_numpy()
    sc = StandardScaler().fit(x[is_])
    m = LogisticRegression(C=1.0, max_iter=1000).fit(sc.transform(x[is_]), y[is_])
    p = m.predict_proba(sc.transform(x))[:, 1]
    keep = pd.Series(p >= np.median(p[is_]), index=t.index)
    row = _evaluate(t, keep, "B:logit")
    row["coef"] = dict(zip(FEATURES, np.round(m.coef_[0], 3).tolist()))
    return row


def holm(pvals: list[float]) -> list[float]:
    p = np.asarray(pvals, float)
    order = np.argsort(p)
    adj = np.empty_like(p)
    running = 0.0
    for rank, i in enumerate(order):
        running = max(running, min(1.0, (len(p) - rank) * p[i]))
        adj[i] = running
    return adj.tolist()


def passes(row: dict) -> bool:
    return (row["oos_keep_central"] > 0 and row["oos_keep_central"] > row["oos_exp_all"]
            and row["p_holm"] < 0.05 and row["oos_n_keep"] >= 30 and row["oos_keep_high"] > 0)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    a_rows, b_rows = [], []
    for name in MODULES:
        t = module_trades(name).frame
        t.to_csv(OUT / f"trades_{name}.csv")
        a_rows += [{"module": name, **r} for r in single_feature_rules(t)]
        b_rows.append({"module": name, **model_rule(t)})
    for rows in (a_rows, b_rows):
        adj = holm([r["oos_p"] if np.isfinite(r["oos_p"]) else 1.0 for r in rows])
        for r, q in zip(rows, adj):
            r["p_holm"] = q
            r["PASS"] = passes(r)
    res = pd.DataFrame(a_rows + b_rows)
    res.drop(columns=["coef"], errors="ignore").to_csv(OUT / "results.csv", index=False)
    (OUT / "model_coefs.json").write_text(json.dumps(
        {r["module"]: r["coef"] for r in b_rows}, indent=2), encoding="utf8")
    pd.set_option("display.width", 260)
    cols = ["module", "rule", "is_exp_all", "is_exp_keep", "oos_n_all", "oos_exp_all",
            "oos_n_keep", "oos_keep_zero", "oos_keep_central", "oos_keep_high", "oos_p", "p_holm", "PASS"]
    print(res[cols].round(3).to_string(index=False))


if __name__ == "__main__":
    main()
