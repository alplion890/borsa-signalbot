"""Baltussen et al. (2021) rROD last-30-minute momentum on NQ and XAU.

Preregistered: HANDOFF/baltussen_son30dk_onkayit_2026-11-17.md.

    python -m intraday.last30_momentum
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from .history_fetch import load_history
from .noise_band_14y import summary

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "outputs" / "intraday" / "last30_momentum"
PROFILE = ROOT / "outputs" / "intraday" / "mt5_bridge" / "reality_profile.csv"
SPLIT = "2022-01-01"
# symbol -> (entry bar HH:MM, last bar HH:MM) in New York time
MARKETS = {"NASDAQ100": ("15:30", "15:55"), "XAUUSD": ("13:00", "13:25")}


def trades_for(frame: pd.DataFrame, entry_hm: str, last_hm: str) -> pd.DataFrame:
    idx = pd.to_datetime(frame.index, utc=True).tz_convert("America/New_York")
    f = frame.set_axis(idx)
    hm = f.index.strftime("%H:%M")
    day = f.index.normalize()
    entry = f["open"][hm == entry_hm].groupby(day[hm == entry_hm]).first()
    close = f["close"][hm == last_hm].groupby(day[hm == last_hm]).first()
    d = pd.DataFrame({"entry": entry, "close": close}).dropna()
    d = d[d.index.weekday < 5]
    d["prev_close"] = d["close"].shift(1)
    d = d.dropna()
    d["dir"] = np.sign(d["entry"] / d["prev_close"] - 1)
    d = d[d["dir"] != 0]
    d["gross"] = d["dir"] * (d["close"] / d["entry"] - 1)
    d.index = d.index.strftime("%Y-%m-%d")
    return d


def evaluate(t: pd.DataFrame, central: float) -> dict:
    out = {"trades": len(t), "first": t.index[0], "last": t.index[-1],
           "win_pct": float((t.gross > 0).mean() * 100), "cost_central": central}
    for label, cost in (("zero", 0.0), ("central", central), ("pessimistic", 2 * central)):
        d = t["gross"] - cost * (1 + t["close"] / t["entry"])
        is_ = d.index < SPLIT
        lo, hi = _ci975(d)
        out[label] = {"all": summary(d), "ci975_bp": [lo, hi],
                      "2012-21": summary(d[is_]), "2022+": summary(d[~is_]),
                      "yearly_pct": {y: float(((1 + g).prod() - 1) * 100)
                                     for y, g in d.groupby(d.index.str[:4])}}
    c = out["central"]
    out["PASS"] = bool(c["ci975_bp"][0] > 0 and c["2012-21"]["mean_daily_bp"] > 0
                       and c["2022+"]["mean_daily_bp"] > 0
                       and out["pessimistic"]["all"]["mean_daily_bp"] > 0)
    return out


def _ci975(d: pd.Series, reps: int = 10_000) -> tuple[float, float]:
    rng = np.random.default_rng(20261117)
    n = len(d)
    starts = rng.integers(0, n, size=(reps, (n + 4) // 5))
    idx = ((starts[:, :, None] + np.arange(5)) % n).reshape(reps, -1)[:, :n]
    means = d.to_numpy()[idx].mean(axis=1)
    lo, hi = np.quantile(means, [0.0125, 0.9875]) * 10_000
    return float(lo), float(hi)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    prof = pd.read_csv(PROFILE).set_index("symbol")
    res = {}
    for sym, (e, last) in MARKETS.items():
        t = trades_for(load_history(sym, "5m", start_year=2012), e, last)
        t.to_csv(OUT / f"trades_{sym}.csv")
        res[sym] = evaluate(t, float(prof.loc[sym, "real_cost_per_side_central"]))
    (OUT / "result.json").write_text(json.dumps(res, indent=2), encoding="utf8")
    for sym, r in res.items():
        print(sym, "n", r["trades"], "win%", round(r["win_pct"], 1), "PASS", r["PASS"])
        for m in ("zero", "central", "pessimistic"):
            a = r[m]
            print(f"  {m:11s} {a['all']['mean_daily_bp']:+.2f}bp/islem yil%{a['all']['ann_pct_approx']:+.1f} "
                  f"DD%{a['all']['max_daily_close_drawdown_pct']:.1f} CI97.5 {[round(x, 2) for x in a['ci975_bp']]} "
                  f"IS {a['2012-21']['mean_daily_bp']:+.2f} OOS {a['2022+']['mean_daily_bp']:+.2f}")
        print("  yillik(merkez):", {k: round(v, 1) for k, v in r["central"]["yearly_pct"].items()})


if __name__ == "__main__":
    main()
