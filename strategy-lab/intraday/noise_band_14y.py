"""Noise Band on 14y Dukascopy NQ 5m with Maven-measured cost.

Preregistered: HANDOFF/noise_band_14y_onkayit_2026-11-17.md. Rules are the
unchanged `noise_band_research.simulate`.

    python -m intraday.noise_band_14y
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from .history_fetch import load_history
from .noise_band_research import simulate, stats

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "outputs" / "intraday" / "noise_band" / "14y"
PROFILE = ROOT / "outputs" / "intraday" / "mt5_bridge" / "reality_profile.csv"
SPLIT = "2022-01-01"


def daily_net(trades: pd.DataFrame, dates: list[str], cost: float) -> pd.Series:
    daily = pd.Series(0.0, index=dates)
    if not trades.empty:
        ratio = trades.exit / trades.entry
        net = trades.direction * (ratio - 1) - cost * (1 + ratio)
        daily.update(net.groupby(trades.date).sum())
    return daily


def block_ci(daily: pd.Series, seed: int = 20261117, reps: int = 10_000) -> list[float]:
    rng = np.random.default_rng(seed)
    n = len(daily)
    starts = rng.integers(0, n, size=(reps, (n + 4) // 5))
    idx = ((starts[:, :, None] + np.arange(5)) % n).reshape(reps, -1)[:, :n]
    means = daily.to_numpy()[idx].mean(axis=1)
    return (np.quantile(means, [0.025, 0.975]) * 10_000).tolist()


def summary(daily: pd.Series) -> dict:
    s = stats(daily)
    s["ann_pct_approx"] = float(daily.mean() * 252 * 100)
    return s


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    frame = load_history("NASDAQ100", "5m", start_year=2012)
    frame.index = pd.to_datetime(frame.index, utc=True)
    trades, dates = simulate(frame)
    central = float(pd.read_csv(PROFILE).set_index("symbol").loc["NASDAQ100", "real_cost_per_side_central"])
    result = {"trades": len(trades), "days": len(dates), "first": dates[0], "last": dates[-1],
              "active_days": int(trades.date.nunique()), "cost_central": central}
    for label, cost in (("zero", 0.0), ("central", central), ("pessimistic", 2 * central)):
        d = daily_net(trades, dates, cost)
        is_ = d.index < SPLIT
        result[label] = {"all": summary(d), "ci95_bp": block_ci(d),
                         "2012-21": summary(d[is_]), "2022+": summary(d[~is_]),
                         "yearly_pct": {y: float(((1 + g).prod() - 1) * 100)
                                        for y, g in d.groupby(d.index.str[:4])}}
    c = result["central"]
    result["PASS"] = bool(c["ci95_bp"][0] > 0 and c["2012-21"]["mean_daily_bp"] > 0
                          and c["2022+"]["mean_daily_bp"] > 0
                          and result["pessimistic"]["all"]["mean_daily_bp"] > 0)
    trades.to_csv(OUT / "trades.csv", index=False)
    (OUT / "result.json").write_text(json.dumps(result, indent=2), encoding="utf8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
