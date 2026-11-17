"""Prop-account fit: does a strategy pass the Maven challenge and reach a first payout?

Input is a daily P&L series in account-fraction units at a "unit" size
(R-based strategies: daily sum of R; notional strategies: daily return at 1x).
The series is scaled by a sizing factor and replayed from every historical
start day (real order, no shuffling), so streaks and regimes are preserved.

Rules (Maven BNPL 1-step, vault "Borsa - Maven Fon Kurallari"; verify before use):
  challenge: +4% target, 10% static drawdown, no daily limit, no consistency
  funded:    8% trailing drawdown on equity peak, 4% daily loss, 20% consistency
             (best day <= 20% of cycle profit), no waiting period; after the first
             withdrawal the floor locks at the initial balance (Maven BNPL FAQ, 2026-11-17)
Closed-balance approximation: intraday floating loss is not modelled.

    python -m intraday.prop_fit
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "outputs" / "intraday" / "prop_fit"


@dataclass(frozen=True)
class Rules:
    target: float = 0.04
    static_dd: float = 0.10
    trail_dd: float = 0.08
    daily_limit: float = 0.04
    consistency: float = 0.20
    min_trade_days: int = 0           # BNPL FAQ lists no minimum-days rule (Standard accounts have one)
    first_payout_min_days: int = 0    # BNPL FAQ: no fixed payout waiting period (Standard: 10 business days)
    horizon_days: int = 252
    challenge_trailing: bool = False  # Maven BNPL FAQ (verified 2026-11-17): phase-1 10% static
    funded_trailing: bool = True
    min_payout_profit: float = 0.004  # Maven minimum withdrawal $20 on $5K
    lock_after_withdraw: bool = True  # BNPL FAQ: after first withdrawal the drawdown floor = initial balance
    withdraw_frac: float = 1.0        # share of profit above initial balance withdrawn at each payout
    account_usd: float = 5000.0
    split: float = 0.80


# Rule ablation: remove one Maven funded rule at a time to see which one kills the edge.
OFF = 1e9
ABLATIONS: dict[str, dict] = {
    "maven": {},
    "no_consistency": {"consistency": OFF},
    "static_8": {"funded_trailing": False},
    "no_daily": {"daily_limit": OFF},
    "static_10_daily_5_no_cons": {"funded_trailing": False, "trail_dd": 0.10, "daily_limit": 0.05,
                                  "consistency": OFF, "lock_after_withdraw": False},
}


def challenge(daily: np.ndarray, start: int, rules: Rules) -> tuple[int, int]:
    """Return (outcome, days): 1 pass, -1 fail, 0 unresolved within horizon."""
    bal, peak = 0.0, 0.0
    end = min(start + rules.horizon_days, len(daily))
    for i in range(start, end):
        bal += daily[i]
        peak = max(peak, bal) if rules.challenge_trailing else 0.0
        if bal <= peak - rules.static_dd:
            return -1, i - start + 1
        if bal >= rules.target:
            return 1, i - start + 1
    return 0, end - start


def funded(daily: np.ndarray, traded: np.ndarray, start: int, rules: Rules) -> tuple[int, int, float]:
    """Return (outcome, days, payout_profit): 1 first payout, -1 breach, 0 unresolved."""
    bal, peak, best, ndays = 0.0, 0.0, 0.0, 0
    end = min(start + rules.horizon_days, len(daily))
    for i in range(start, end):
        d = daily[i]
        if d <= -rules.daily_limit:
            return -1, i - start + 1, 0.0
        bal += d
        peak = max(peak, bal) if rules.funded_trailing else 0.0
        if bal <= peak - rules.trail_dd:
            return -1, i - start + 1, 0.0
        best = max(best, d)
        ndays += int(traded[i])
        days = i - start + 1
        if (days >= rules.first_payout_min_days and ndays >= rules.min_trade_days
                and bal >= rules.min_payout_profit and best <= rules.consistency * bal):
            return 1, days, bal
    return 0, end - start, 0.0


def funded_path(c: np.ndarray, lo: np.ndarray, hi: np.ndarray, traded: np.ndarray,
                start: int, rules: Rules) -> tuple[float, bool, int]:
    """One funded year, withdrawing every eligible cycle.

    c/lo/hi: day close P&L and intraday worst/best P&L (account fraction, vs start-of-day balance).
    Before the first withdrawal the floor trails the equity peak (or is static); after it, with
    lock_after_withdraw, the floor is the initial balance (bal = 0). Returns (withdrawn, breached, payouts).
    """
    paid, bal, peak, best, ndays, cyc, cyc0, locked, n = 0.0, 0.0, 0.0, 0.0, 0, 0, 0.0, False, 0

    def floor() -> float:
        return 0.0 if locked else (peak if rules.funded_trailing else 0.0) - rules.trail_dd

    for i in range(start, min(start + rules.horizon_days, len(c))):
        if lo[i] <= -rules.daily_limit or bal + lo[i] <= floor():
            return paid, True, n
        if rules.funded_trailing and not locked:
            peak = max(peak, bal + hi[i])
        bal += c[i]
        if bal <= floor():
            return paid, True, n
        best, ndays, cyc = max(best, c[i]), ndays + int(traded[i]), cyc + 1
        profit, amount = bal - cyc0, rules.withdraw_frac * bal
        if (cyc >= rules.first_payout_min_days and ndays >= rules.min_trade_days
                and amount >= rules.min_payout_profit and profit > 0 and best <= rules.consistency * profit):
            paid, bal, n = paid + amount, bal - amount, n + 1
            locked = locked or rules.lock_after_withdraw
            peak, cyc0, best, ndays, cyc = bal, bal, 0.0, 0, 0
    return paid, False, n


def funded_year(daily: np.ndarray, traded: np.ndarray, start: int, rules: Rules) -> tuple[float, bool]:
    """Closed-balance version of funded_path (intraday floating P&L not modelled)."""
    paid, breached, _ = funded_path(daily, np.minimum(daily, 0.0), np.maximum(daily, 0.0), traded, start, rules)
    return paid, breached


def yearly_ev(daily: pd.Series, traded: pd.Series, scale: float, rules: Rules = Rules()) -> dict:
    x, t = daily.to_numpy() * scale, traded.to_numpy()
    res = np.array([funded_year(x, t, s, rules) for s in range(0, max(len(x) - 20, 1))])
    usd = res[:, 0] * rules.account_usd * rules.split
    return {"ev_usd_year": float(usd.mean()), "median_usd_year": float(np.median(usd)),
            "breach_pct": float(res[:, 1].mean() * 100)}


def evaluate(daily: pd.Series, traded: pd.Series, scale: float, rules: Rules = Rules()) -> dict:
    x = daily.to_numpy() * scale
    t = traded.to_numpy()
    starts = range(0, max(len(x) - 20, 1))
    ch = np.array([challenge(x, s, rules) for s in starts])
    fu = np.array([funded(x, t, s, rules) for s in starts])
    passed, failed = ch[:, 0] == 1, ch[:, 0] == -1
    paid = fu[:, 0] == 1
    return {"scale": scale, "starts": len(ch),
            "challenge_pass_pct": float(passed.mean() * 100), "challenge_fail_pct": float(failed.mean() * 100),
            "challenge_median_days": float(np.median(ch[passed, 1])) if passed.any() else None,
            "funded_payout_pct": float(paid.mean() * 100), "funded_breach_pct": float((fu[:, 0] == -1).mean() * 100),
            "funded_median_days": float(np.median(fu[paid, 1])) if paid.any() else None,
            "funded_median_payout_pct": float(np.median(fu[paid, 2]) * 100) if paid.any() else None,
            "funded_ev_usd": float(fu[:, 2].mean() * rules.account_usd * rules.split),
            "both_pct": float(passed.mean() * paid.mean() * 100)}


def to_calendar(by_date: pd.Series) -> tuple[pd.Series, pd.Series]:
    """Daily P&L on every weekday between first and last date (no-trade days = 0)."""
    idx = pd.to_datetime(by_date.index)
    s = pd.Series(by_date.to_numpy(), index=idx).groupby(level=0).sum()
    cal = pd.bdate_range(s.index.min(), s.index.max())
    traded = pd.Series(cal.isin(s.index), index=cal)
    return s.reindex(cal, fill_value=0.0), traded


def r_strategy(dates: pd.Series, r: pd.Series) -> pd.Series:
    return pd.Series(r.to_numpy(), index=pd.to_datetime(dates).dt.normalize()).groupby(level=0).sum()


def load_sources() -> dict[str, tuple[pd.Series, str]]:
    """Daily unit P&L per strategy at Maven measured central cost."""
    from .noise_band_14y import daily_net

    prof = pd.read_csv(ROOT / "outputs/intraday/mt5_bridge/reality_profile.csv").set_index("symbol")
    nq_cost = float(prof.loc["NASDAQ100", "real_cost_per_side_central"])
    out: dict[str, tuple[pd.Series, str]] = {}

    sw = pd.read_csv(ROOT / "outputs/intraday/meta_label/trades_SWEEP_CORE.csv")
    sw_r = sw["r0"] - sw["cost_r"] * (nq_cost / 0.00009)  # config 0.9bp -> measured, same fraction model
    out["SWEEP"] = (r_strategy(sw["timestamp"], sw_r), "R")

    nb = pd.read_csv(ROOT / "outputs/intraday/noise_band/14y/trades.csv")
    nb_res = json.loads((ROOT / "outputs/intraday/noise_band/14y/result.json").read_text())
    dates = pd.bdate_range(nb_res["first"], nb_res["last"]).strftime("%Y-%m-%d")
    nb_daily = daily_net(nb, pd.Index(dates), nq_cost)
    out["NOISE_BAND"] = (pd.Series(nb_daily.to_numpy(), index=pd.to_datetime(nb_daily.index)), "notional")

    em = pd.read_csv(ROOT / "outputs/intraday/ema12_first5m/14y/trades.csv")
    em = em[em["risk"] >= 1]
    em_r = em["r_gross"] - 2 * nq_cost * em["entry"] / em["risk"]
    out["EMA12"] = (r_strategy(em["date"], em_r), "R")

    from .fx_fix_btc_hours import btc_daily
    bt = btc_daily(float(prof.loc["BTCUSDT", "real_cost_per_side_central"]))["H6_btc_21_23"]
    out["BTC_21_23"] = (pd.Series(bt.to_numpy(), index=pd.to_datetime(bt.index)), "notional")
    return out


# Default size per edge for the ablation table (R: risk fraction; notional: leverage multiple).
ABLATION_SCALE = {"SWEEP": 0.005, "NOISE_BAND": 1.0, "EMA12": 0.0025, "BTC_21_23": 0.5}


def ablation(sources: dict[str, tuple[pd.Series, str]]) -> pd.DataFrame:
    """Funded payout % per edge under Maven rules and with one rule removed at a time."""
    rows = []
    for name, (by_date, unit) in sources.items():
        for period, s in (("all", by_date), ("2022+", by_date[by_date.index >= "2022-01-01"])):
            daily, traded = to_calendar(s) if unit == "R" or name != "BTC_21_23" else (
                s, pd.Series(True, index=s.index))
            row = {"strategy": name, "period": period, "scale": ABLATION_SCALE[name]}
            for label, kw in ABLATIONS.items():
                res = evaluate(daily, traded, ABLATION_SCALE[name], Rules(**kw))
                row[f"{label}_payout"] = round(res["funded_payout_pct"], 1)
                row[f"{label}_breach"] = round(res["funded_breach_pct"], 1)
                if label == "maven":
                    row["challenge_pass"] = round(res["challenge_pass_pct"], 1)
                    row["challenge_fail"] = round(res["challenge_fail_pct"], 1)
            gains = {k: row[f"{k}_payout"] - row["maven_payout"] for k in ABLATIONS if k != "maven"}
            row["binding_rule"] = max(gains, key=gains.get) if max(gains.values()) >= 5 else "none"
            rows.append(row)
    return pd.DataFrame(rows)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    rules = Rules()
    sources = load_sources()
    abl = ablation(sources)
    abl.to_csv(OUT / "rule_ablation.csv", index=False)
    print(abl.to_string(index=False))
    rows = []
    for name, (by_date, unit) in sources.items():
        for period, s in (("all", by_date), ("2022+", by_date[by_date.index >= "2022-01-01"])):
            daily, traded = to_calendar(s)
            scales = (0.0025, 0.005, 0.0075, 0.01, 0.015) if unit == "R" else (0.5, 1.0, 1.5, 2.0, 3.0)
            for sc in scales:
                res = evaluate(daily, traded, sc, rules)
                rows.append({"strategy": name, "period": period, "unit": unit, **res})
                print(f"{name:10s} {period:5s} {'risk%' if unit == 'R' else 'kald.'} "
                      f"{sc * 100 if unit == 'R' else sc:>5} | challenge gec %{res['challenge_pass_pct']:5.1f} "
                      f"patla %{res['challenge_fail_pct']:5.1f} medyan {res['challenge_median_days']} gun | "
                      f"payout %{res['funded_payout_pct']:5.1f} ihlal %{res['funded_breach_pct']:5.1f} "
                      f"medyan {res['funded_median_days']} gun kar%{res['funded_median_payout_pct']}")
    pd.DataFrame(rows).to_csv(OUT / "baseline.csv", index=False)
    (OUT / "rules.json").write_text(json.dumps(asdict(rules), indent=2), encoding="utf8")


if __name__ == "__main__":
    main()
