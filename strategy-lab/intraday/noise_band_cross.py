"""Noise Band cross-index replication (SP500, US30, US2000) vs NQ.

Preregistered: HANDOFF/noise_band_capraz_endeks_onkayit_2026-11-17.md.

    python -m intraday.noise_band_cross
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from .history_fetch import load_history
from .noise_band_14y import daily_net, summary
from .noise_band_research import simulate

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "outputs" / "intraday" / "noise_band" / "cross"
PROFILE = ROOT / "outputs" / "intraday" / "mt5_bridge" / "reality_profile.csv"
SYMBOLS = ("SP500", "US30", "US2000")
SPLIT = "2022-01-01"
ALPHA_LO = 0.05 / 3 / 2  # Bonferroni, two-sided -> 0.0083 quantile


def ci(daily: pd.Series, reps: int = 10_000) -> list[float]:
    rng = np.random.default_rng(20261117)
    n = len(daily)
    starts = rng.integers(0, n, size=(reps, (n + 4) // 5))
    idx = ((starts[:, :, None] + np.arange(5)) % n).reshape(reps, -1)[:, :n]
    means = daily.to_numpy()[idx].mean(axis=1)
    return (np.quantile(means, [ALPHA_LO, 1 - ALPHA_LO]) * 10_000).tolist()


def run_symbol(sym: str, cost: float) -> tuple[dict, pd.Series, pd.DataFrame]:
    frame = load_history(sym, "5m", start_year=2012)
    frame.index = pd.to_datetime(frame.index, utc=True)
    trades, dates = simulate(frame)
    res = {"trades": len(trades), "days": len(dates), "active_days": int(trades.date.nunique()),
           "cost_central": cost}
    central = None
    for label, c in (("zero", 0.0), ("central", cost), ("pessimistic", 2 * cost)):
        d = daily_net(trades, dates, c)
        is_ = d.index < SPLIT
        res[label] = {"all": summary(d), "ci_bonf_bp": ci(d),
                      "2012-21": summary(d[is_]), "2022+": summary(d[~is_]),
                      "yearly_pct": {y: float(((1 + g).prod() - 1) * 100)
                                     for y, g in d.groupby(d.index.str[:4])}}
        if label == "central":
            central = d
    c = res["central"]
    res["PASS"] = bool(c["ci_bonf_bp"][0] > 0 and c["2012-21"]["mean_daily_bp"] > 0
                       and c["2022+"]["mean_daily_bp"] > 0
                       and res["pessimistic"]["all"]["mean_daily_bp"] > 0)
    return res, central, trades


def overlap(nq_tr: pd.DataFrame, tr: pd.DataFrame) -> float:
    a = nq_tr.groupby("date").direction.first()
    b = tr.groupby("date").direction.first()
    common = a.index.intersection(b.index)
    return float((a[common] == b[common]).mean() * 100) if len(common) else np.nan


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    prof = pd.read_csv(PROFILE).set_index("symbol")
    nq_res, nq_d, nq_tr = run_symbol("NASDAQ100", float(prof.loc["NASDAQ100", "real_cost_per_side_central"]))
    out = {"NASDAQ100_ref": {"mean_daily_bp": nq_res["central"]["all"]["mean_daily_bp"]}}
    for sym in SYMBOLS:
        res, d, tr = run_symbol(sym, float(prof.loc[sym, "real_cost_per_side_central"]))
        both = pd.concat([nq_d, d], axis=1, join="inner").dropna()
        res["corr_daily_with_NQ"] = float(both.corr().iloc[0, 1])
        res["same_day_same_dir_pct"] = overlap(nq_tr, tr)
        tr.to_csv(OUT / f"trades_{sym}.csv", index=False)
        out[sym] = res
        c = res["central"]
        print(f"{sym}: n={res['trades']} PASS={res['PASS']} corrNQ={res['corr_daily_with_NQ']:.2f} "
              f"ayni_yon%={res['same_day_same_dir_pct']:.0f}")
        for m in ("zero", "central", "pessimistic"):
            a = res[m]
            print(f"  {m:11s} {a['all']['mean_daily_bp']:+.2f}bp/gun yil%{a['all']['ann_pct_approx']:+.1f} "
                  f"DD%{a['all']['max_daily_close_drawdown_pct']:.1f} CIbonf {[round(x, 2) for x in a['ci_bonf_bp']]} "
                  f"IS {a['2012-21']['mean_daily_bp']:+.2f} OOS {a['2022+']['mean_daily_bp']:+.2f}")
        print("  yillik(merkez):", {k: round(v, 1) for k, v in c["yearly_pct"].items()})
    (OUT / "result.json").write_text(json.dumps(out, indent=2), encoding="utf8")


if __name__ == "__main__":
    main()
