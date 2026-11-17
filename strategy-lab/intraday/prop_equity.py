"""Equity-based prop simulation: intraday worst/best floating P&L (MAE/MFE) per day.

prop_fit uses closed daily P&L. Maven measures daily loss and trailing drawdown on
equity (open P&L included), so a trade that dips -5% intraday and closes +1% breaches
the 4% daily limit. This module rebuilds each day's (close, low, high) path from bars:
  - Noise Band: NQ 5m bars between entry and exit, trades in sequence within the day
  - BTC 21-23 UTC: 1h bars 21:00 and 22:00, exit at 23:00 open
Bar high/low order inside a bar is unknown; low is checked against the prior peak first.

    python -m intraday.prop_equity
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from .history_fetch import load_history
from .prop_fit import Rules, funded_path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "outputs" / "intraday" / "prop_fit"
PROFILE = ROOT / "outputs" / "intraday" / "mt5_bridge" / "reality_profile.csv"


def nb_paths(cost: float) -> pd.DataFrame:
    """Per-day close/low/high (fraction of notional, 1x) for Noise Band NQ."""
    t = pd.read_csv(ROOT / "outputs/intraday/noise_band/14y/trades.csv")
    bars = load_history("NASDAQ100", "5m", start_year=2012)
    ts = bars.index.to_numpy()
    lo, hi = bars["low"].to_numpy(), bars["high"].to_numpy()
    e0 = pd.to_datetime(t["entry_time"], utc=True).dt.tz_localize(None).to_numpy()
    e1 = pd.to_datetime(t["exit_time"], utc=True).dt.tz_localize(None).to_numpy()
    rows: dict[str, list[float]] = {}
    for k in range(len(t)):
        d, entry, ex = int(t["direction"].iat[k]), float(t["entry"].iat[k]), float(t["exit"].iat[k])
        a, b = np.searchsorted(ts, e0[k]), np.searchsorted(ts, e1[k])
        worst = (lo[a:b].min() if d == 1 else hi[a:b].max()) if b > a else entry
        best = (hi[a:b].max() if d == 1 else lo[a:b].min()) if b > a else entry
        realized = d * (ex / entry - 1) - cost * (1 + ex / entry)
        day = t["date"].iat[k]
        c0, l0, h0 = rows.get(day, [0.0, 0.0, 0.0])
        f_lo = d * (worst / entry - 1) - cost
        f_hi = d * (best / entry - 1) - cost
        rows[day] = [c0 + realized, min(l0, c0 + f_lo, c0 + realized), max(h0, c0 + f_hi, c0 + realized)]
    df = pd.DataFrame.from_dict(rows, orient="index", columns=["close", "low", "high"])
    df.index = pd.to_datetime(df.index)
    return df.sort_index()


def btc_paths(cost: float) -> pd.DataFrame:
    df = pd.read_csv(ROOT / "outputs/intraday/cache/binance/BTCUSDT_1h.csv", parse_dates=["ts"]).set_index("ts")
    s = df[df.index.hour == 21]
    nxt = df.reindex(s.index + pd.Timedelta(hours=1))
    ex = df["open"].reindex(s.index + pd.Timedelta(hours=2)).to_numpy()
    entry = s["open"].to_numpy()
    low = np.minimum(s["low"].to_numpy(), nxt["low"].to_numpy()) / entry - 1 - cost
    high = np.maximum(s["high"].to_numpy(), nxt["high"].to_numpy()) / entry - 1 - cost
    close = ex / entry - 1 - cost * (1 + ex / entry)
    out = pd.DataFrame({"close": close, "low": np.minimum(low, close), "high": np.maximum(high, close)},
                       index=s.index.normalize()).dropna()
    return out[~out.index.duplicated()]


def combine(parts: list[tuple[pd.DataFrame, float]]) -> pd.DataFrame:
    """Sequential (non-overlapping in time) strategies within a UTC day, each scaled."""
    idx = sorted(set().union(*[p.index for p, _ in parts]))
    close = np.zeros(len(idx))
    low = np.zeros(len(idx))
    high = np.zeros(len(idx))
    for p, k in parts:
        q = p.reindex(idx).fillna(0.0).to_numpy() * k
        low = np.minimum(low, close + q[:, 1])
        high = np.maximum(high, close + q[:, 2])
        close = close + q[:, 0]
    return pd.DataFrame({"close": close, "low": low, "high": high}, index=pd.DatetimeIndex(idx))


def run(path: pd.DataFrame, rules: Rules, equity: bool) -> dict:
    c = path["close"].to_numpy()
    lo = path["low"].to_numpy() if equity else np.minimum(c, 0) * 0 + np.where(c < 0, c, 0)
    hi = path["high"].to_numpy() if equity else np.where(c > 0, c, 0)
    n = len(c)
    ch, yr = [], []
    for s in range(0, max(n - 20, 1)):
        bal, res = 0.0, 0
        for i in range(s, min(s + rules.horizon_days, n)):
            if bal + lo[i] <= -rules.static_dd:
                res = -1
                break
            bal += c[i]
            if bal >= rules.target:
                res = 1
                break
        ch.append(res)
        paid, breach, npay = funded_path(c, lo, hi, c != 0, s, rules)
        yr.append((paid, breach, npay))
    ch, yr = np.array(ch), np.array(yr)
    return {"challenge_pass": float((ch == 1).mean() * 100), "challenge_fail": float((ch == -1).mean() * 100),
            "funded_ev_usd_year": float(yr[:, 0].mean() * rules.account_usd * rules.split),
            "funded_breach": float(yr[:, 1].mean() * 100), "payouts_per_year": float(yr[:, 2].mean())}


# Maven BNPL as verified 2026-11-17; "old model" = pre-verification assumptions (no withdrawal lock,
# 10-day wait); partial withdrawals keep a buffer above the locked floor.
RULESETS: dict[str, Rules] = {
    "maven_bnpl": Rules(),
    "maven_bnpl_withdraw75": Rules(withdraw_frac=0.75),
    "maven_bnpl_withdraw50": Rules(withdraw_frac=0.5),
    "maven_bnpl_withdraw25": Rules(withdraw_frac=0.25),
    "maven_old_model": Rules(lock_after_withdraw=False, first_payout_min_days=10),
    "no_consistency_static10": Rules(consistency=1e9, funded_trailing=False, trail_dd=0.10, daily_limit=0.05,
                                     lock_after_withdraw=False),
}


def main() -> None:
    prof = pd.read_csv(PROFILE).set_index("symbol")["real_cost_per_side_central"]
    nb, bt = nb_paths(float(prof["NASDAQ100"])), btc_paths(float(prof["BTCUSDT"]))
    nb_d = nb.reindex(pd.bdate_range(nb.index.min(), nb.index.max())).fillna(0.0)
    cases = {"NOISE_BAND x1": combine([(nb_d, 1.0)]), "BTC_21_23 x0.5": combine([(bt, 0.5)]),
             "NB x0.75 + BTC x0.35": combine([(nb_d, 0.75), (bt, 0.35)])}
    rows = []
    for name, p in cases.items():
        p = p[(p.index >= max(nb.index.min(), bt.index.min()) if "+" in name else p.index >= p.index.min())]
        for period, q in (("all", p), ("2022+", p[p.index >= "2022-01-01"])):
            for label, rules in RULESETS.items():
                for eq in (False, True):
                    if not eq and label != "maven_bnpl":
                        continue
                    r = run(q, rules, eq)
                    rows.append({"case": name, "period": period, "rules": label,
                                 "basis": "equity" if eq else "closed", **{k: round(v, 1) for k, v in r.items()}})
                    print(rows[-1])
    OUT.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(OUT / "equity_vs_closed.csv", index=False)
    worst = {"NB_worst_intraday_pct": float(nb["low"].min() * 100), "BTC_worst_intraday_pct": float(bt["low"].min() * 100)}
    (OUT / "intraday_worst.json").write_text(json.dumps(worst, indent=2), encoding="utf8")
    print(worst)


if __name__ == "__main__":
    main()
