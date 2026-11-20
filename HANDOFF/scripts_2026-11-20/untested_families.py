"""Untested families H1-H4 (prereg HANDOFF/denenmemis_aileler_onkayit_2026-11-20.md).

Input: outputs/intraday/untested_families/{close.csv, us_legs.csv} from multi_panel.py.
Every rule below is the source paper's headline variant; no parameter is chosen on this data.
Run from strategy-lab: python ../HANDOFF/scripts_2026-11-20/untested_families.py
"""
from __future__ import annotations

import json
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd

D = Path("outputs/intraday/untested_families")
START, END = "2013-01-01", "2026-08-28"
BLOCKS = {"2013-17": ("2013-01-01", "2017-12-31"), "2018-21": ("2018-01-01", "2021-12-31"),
          "2022-23": ("2022-01-01", "2023-12-31"), "2024-26": ("2024-01-01", END)}
FX = ["AUDUSD", "EURUSD", "GBPUSD", "USDCAD", "USDCHF", "USDJPY"]
IDX = ["NASDAQ100", "SP500", "US30", "US2000", "UK100", "FRA40", "JAP225"]
COST_NAME = {"BTCUSD": "BTCUSDT"}


def costs() -> pd.Series:
    p = pd.read_csv("outputs/intraday/mt5_bridge/reality_profile.csv").set_index("symbol")
    return p["real_cost_per_side_central"]


def load() -> tuple[pd.DataFrame, pd.DataFrame]:
    px = pd.read_csv(D / "close.csv", index_col=0, parse_dates=True)
    legs = pd.read_csv(D / "us_legs.csv", index_col=0, header=[0, 1], parse_dates=True)
    return px, legs


def ewma_vol(r: pd.DataFrame) -> pd.DataFrame:
    """MOP 2012: exponentially weighted daily variance, center of mass 60 days, annualized (261). Known at t (uses r up to t)."""
    return np.sqrt(r.pow(2).ewm(com=60, min_periods=60).mean() * 261)


def month_ends(idx: pd.DatetimeIndex) -> pd.DatetimeIndex:
    s = pd.Series(idx, index=idx)
    return pd.DatetimeIndex(s.groupby([idx.year, idx.month]).last().to_numpy())


def hold_monthly(w_me: pd.DataFrame, idx: pd.DatetimeIndex) -> pd.DataFrame:
    """Weights decided at month-end close t apply to returns from t+1 onward (no look-ahead)."""
    return w_me.reindex(idx).ffill().shift(1)


def net(w: pd.DataFrame, r: pd.DataFrame, cost: pd.Series, cmult: float) -> pd.Series:
    c = pd.Series({k: cost[COST_NAME.get(k, k)] for k in w.columns}) * cmult
    gross = (w * r).sum(axis=1)
    turn = w.fillna(0).diff().abs().mul(c, axis=1).sum(axis=1)
    return gross - turn


def h1_tsmom(px: pd.DataFrame) -> pd.DataFrame:
    """MOP 2012: sign of past 12-month return; size 40%/sigma_ex-ante; monthly; equal weight across available assets."""
    r = px.pct_change(fill_method=None)
    vol = ewma_vol(r)
    me = month_ends(px.index)
    ret12 = px / px.shift(252) - 1
    w = (np.sign(ret12) * 0.40 / vol).loc[me]
    n = w.notna().sum(axis=1).replace(0, np.nan)
    return hold_monthly(w.div(n, axis=0), px.index)


def _xs_class(px: pd.DataFrame, cols: list[str], me: pd.DatetimeIndex) -> pd.DataFrame:
    """AMP 2013: rank of 12-1 month return, weights = c*(rank - mean rank), sum|w| = 2 (long $1 / short $1)."""
    sub = px[cols]
    mom = (sub.shift(21) / sub.shift(252) - 1).loc[me]
    rk = mom.rank(axis=1)
    dev = rk.sub(rk.mean(axis=1), axis=0)
    return dev.div(dev.abs().sum(axis=1) / 2, axis=0)


def h2_xsmom(px: pd.DataFrame) -> pd.DataFrame:
    """Within FX and within indices; classes combined with equal ex-ante vol (10% annual each), monthly."""
    r = px.pct_change(fill_method=None)
    me = month_ends(px.index)
    out = []
    for cols in (FX, IDX):
        w = _xs_class(px, cols, me)
        wd = hold_monthly(w, px.index)
        pr = (wd * r[cols]).sum(axis=1)
        v = np.sqrt(pr.pow(2).ewm(com=60, min_periods=60).mean() * 261)
        scale = (0.10 / v).reindex(me).reindex(px.index).ffill().shift(1)  # scale fixed at month-end, known then
        out.append(wd.mul(scale, axis=0) / 2)
    return pd.concat(out, axis=1).reindex(columns=px.columns).fillna(0)


def h3_pairs(px: pd.DataFrame) -> pd.DataFrame:
    """Gatev-Goetzmann-Rouwenhorst 2006: 12m formation (normalized prices, min SSD), top-5 pairs (within class),
    trade 6m: open when |spread| > 2 formation-sd, close at zero crossing or end of period; $1 long / $1 short per pair."""
    w = pd.DataFrame(0.0, index=px.index, columns=px.columns)
    dates = px.loc[START:END].index
    starts = pd.date_range(dates[0], dates[-1], freq="6MS")
    for s in starts:
        f0, f1 = s - pd.DateOffset(months=12), s
        form = px.loc[f0:f1 - pd.Timedelta(days=1)]
        trade = px.loc[f1:f1 + pd.DateOffset(months=6) - pd.Timedelta(days=1)]
        if len(form) < 200 or trade.empty:
            continue
        cand = []
        for cols in (FX, IDX):
            ok = [c for c in cols if form[c].notna().all() and trade[c].notna().any()]
            for a, b in combinations(ok, 2):
                na, nb = form[a] / form[a].iloc[0], form[b] / form[b].iloc[0]
                cand.append((float(((na - nb) ** 2).sum()), a, b, float((na - nb).std())))
        for _, a, b, sd in sorted(cand)[:5]:
            base_a, base_b = trade[a].dropna().iloc[0], trade[b].dropna().iloc[0]
            spread = (trade[a] / base_a - trade[b] / base_b).ffill()
            pos = 0.0
            for t, x in spread.items():
                if pos == 0 and abs(x) > 2 * sd:
                    pos = -np.sign(x)
                elif pos != 0 and np.sign(x) == pos:   # crossed zero
                    pos = 0.0
                w.loc[t, a] += pos / 5
                w.loc[t, b] -= pos / 5
        last = trade.index[-1]
        w.loc[last, :] = w.loc[last, :]  # positions end with the period (next period rebuilt from zero)
    return w.shift(1)  # decided at close t, held from t+1


def h4_overnight_mr(legs: pd.DataFrame, cost: pd.Series, cmult: float) -> pd.Series:
    """Quant Returns: demean overnight (NY close->open) returns across US indices; weight = -(r_i - mean), gross 2;
    enter at NY open, exit at NY close (signal known at the open)."""
    on = legs.xs("overnight", axis=1, level=1)
    day = legs.xs("day", axis=1, level=1)
    dev = on.sub(on.mean(axis=1), axis=0)
    w = -dev.div(dev.abs().sum(axis=1) / 2, axis=0)
    c = pd.Series({k: cost[k] for k in w.columns}) * cmult
    return (w * day).sum(axis=1) - w.abs().mul(2 * c, axis=1).sum(axis=1)


def boot_p(x: pd.Series, reps: int = 10000, block: int = 20, seed: int = 20261120) -> float:
    """One-sided p for mean > 0, circular block bootstrap of the demeaned series."""
    a = x.to_numpy() - x.mean()
    n = len(a)
    rng = np.random.default_rng(seed)
    st = rng.integers(0, n, size=(reps, n // block + 1))
    ix = ((st[:, :, None] + np.arange(block)) % n).reshape(reps, -1)[:, :n]
    return float((a[ix].mean(axis=1) >= x.mean()).mean())


def stats(x: pd.Series) -> dict:
    x = x.loc[START:END].dropna()
    sr = x.mean() / x.std() * np.sqrt(261) if x.std() > 0 else 0.0
    blk = {k: float(x.loc[a:b].mean() * 1e4) for k, (a, b) in BLOCKS.items()}
    return dict(n=len(x), ann_pct=float(x.mean() * 261 * 100), sharpe=float(sr),
                blocks_bp=blk, pos_blocks=int(sum(v > 0 for v in blk.values())))


def main() -> None:
    px, legs = load()
    cost = costs()
    r = px.pct_change(fill_method=None)
    weights = {"H1_TSMOM": h1_tsmom(px), "H2_XSMOM": h2_xsmom(px), "H3_PAIRS": h3_pairs(px)}
    res = {}
    for name, w in weights.items():
        res[name] = {f"c{m:g}": stats(net(w, r, cost, m)) for m in (0.0, 1.0, 2.0)}
        res[name]["p_1x"] = boot_p(net(w, r, cost, 1.0).loc[START:END].dropna())
        res[name]["avg_gross_lev"] = float(w.abs().sum(axis=1).loc[START:END].mean())
    res["H4_ON_MR"] = {f"c{m:g}": stats(h4_overnight_mr(legs, cost, m)) for m in (0.0, 1.0, 2.0)}
    res["H4_ON_MR"]["p_1x"] = boot_p(h4_overnight_mr(legs, cost, 1.0).loc[START:END].dropna())
    # Holm across the four primary tests
    ps = sorted((res[k]["p_1x"], k) for k in ("H1_TSMOM", "H2_XSMOM"))   # primary only (prereg addendum)
    for k in ("H3_PAIRS", "H4_ON_MR"):
        res[k]["holm_threshold"], res[k]["holm_sig"] = float("nan"), False   # exploratory
    for i, (p, k) in enumerate(ps):
        res[k]["holm_threshold"] = 0.05 / (len(ps) - i)
    rejected = True
    for p, k in ps:
        ok = rejected and p <= res[k]["holm_threshold"]
        res[k]["holm_sig"] = bool(ok)
        rejected = ok
    for k, v in res.items():
        v["PASS"] = bool(v["holm_sig"] and v["c1"]["pos_blocks"] >= 3 and v["c2"]["ann_pct"] > 0)
    (D / "result.json").write_text(json.dumps(res, indent=1))
    for k, v in res.items():
        print(f"\n{k}: PASS={v['PASS']} p1x={v['p_1x']:.4f} holm<= {v['holm_threshold']:.4f}"
              + (f" lev {v['avg_gross_lev']:.2f}" if "avg_gross_lev" in v else ""))
        for c in ("c0", "c1", "c2"):
            s = v[c]
            print(f"  {c}: yil %{s['ann_pct']:+.2f} SR {s['sharpe']:+.2f} n{s['n']} bloklar(bp/gun) "
                  + " ".join(f"{b}:{x:+.2f}" for b, x in s["blocks_bp"].items()) + f" pozitif {s['pos_blocks']}/4")


if __name__ == "__main__":
    main()
