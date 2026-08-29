"""Maven 5K Buy Now Pay Later challenge simulator.

Official evaluation rules verified on 2026-06-19:
  - 4% profit target
  - no daily drawdown
  - 10% static maximum drawdown from initial balance
  - no minimum trading days
  - no consistency rule
  - no stated maximum trading days

The input is the fixed seven-module final router ledger. Each row is one
completed trade expressed in weighted R. Challenge paths start on every
calendar day for which at least ``min_history_days`` remain.

VectorBT is used to independently reconstruct each synthetic account equity
curve and calculate portfolio-level return/drawdown. Maven pass/fail stopping
logic remains explicit because it is rule-specific.

Run from ``strategy-lab``:
    python -m intraday.challenge_sim
"""
from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable

import numpy as np
import pandas as pd

from .signalbot.risk import live_module_names

OUT = Path(__file__).resolve().parent.parent / "outputs" / "intraday"
DEFAULT_LEDGER = OUT / "regime_router_final_validation_ledger.csv"


@dataclass(frozen=True)
class MavenRules:
    account_size: float = 5_000.0
    target_pct: float = 0.04
    max_drawdown_pct: float = 0.10
    daily_drawdown_pct: float | None = None
    min_trading_days: int = 0
    max_trading_days: int | None = None
    upfront_fee_usd: float = 5.0
    pay_after_pass_usd: float = 69.0

    @property
    def target_balance(self) -> float:
        return self.account_size * (1.0 + self.target_pct)

    @property
    def breach_balance(self) -> float:
        return self.account_size * (1.0 - self.max_drawdown_pct)


@dataclass(frozen=True)
class RiskPolicy:
    name: str
    base_risk: float
    winner_risk: float | None = None
    sweep_multiplier: float = 1.0
    risk_cap: float = 0.03

    def risk_for(self, module: str, previous_win: bool) -> float:
        risk = self.winner_risk if previous_win and self.winner_risk is not None else self.base_risk
        if module == "SWEEP_CORE_AVOID_MID_VWAP":
            risk *= self.sweep_multiplier
        return min(float(risk), self.risk_cap)


DEFAULT_POLICIES = (
    RiskPolicy("fixed_0.50", 0.005),
    RiskPolicy("fixed_0.75", 0.0075),
    RiskPolicy("fixed_1.00", 0.010),
    RiskPolicy("fixed_1.25", 0.0125),
    RiskPolicy("fixed_1.50", 0.015),
    RiskPolicy("current_1.5_to_3_sweep", 0.015, 0.030, 1.5, 0.030),
)


def load_final_ledger(path: Path = DEFAULT_LEDGER) -> pd.DataFrame:
    df = pd.read_csv(path)
    time_col = "timestamp" if "timestamp" in df.columns else df.columns[0]
    df[time_col] = pd.to_datetime(df[time_col], errors="coerce", utc=True)
    df = df.dropna(subset=[time_col]).set_index(time_col).sort_index()
    required = {"module", "weighted_r"}
    missing = required.difference(df.columns)
    if missing:
        raise ValueError(f"ledger missing columns: {sorted(missing)}")
    df["weighted_r"] = pd.to_numeric(df["weighted_r"], errors="coerce")
    return df.dropna(subset=["weighted_r"])


def _vectorbt_metrics(equity: pd.Series, initial_cash: float) -> tuple[float, float]:
    """Return total return and max drawdown from a synthetic VectorBT portfolio."""
    if equity.empty:
        return 0.0, 0.0
    try:
        import vectorbt as vbt
    except ImportError as exc:
        raise RuntimeError("vectorbt is required; install strategy-lab/requirements.txt") from exc

    synthetic_price = equity / initial_cash
    portfolio = vbt.Portfolio.from_holding(
        synthetic_price,
        init_cash=initial_cash,
        size=initial_cash,
        freq="1D",
    )
    total_return_attr = portfolio.total_return
    max_drawdown_attr = portfolio.max_drawdown
    total_return = float(total_return_attr() if callable(total_return_attr) else total_return_attr)
    max_drawdown = abs(
        float(max_drawdown_attr() if callable(max_drawdown_attr) else max_drawdown_attr)
    )
    return total_return, max_drawdown


def simulate_path(
    trades: pd.DataFrame,
    start: pd.Timestamp,
    policy: RiskPolicy,
    rules: MavenRules = MavenRules(),
    horizon_days: int | None = None,
    validate_vectorbt: bool = True,
) -> dict:
    end = trades.index.max() if horizon_days is None else start + pd.Timedelta(days=horizon_days)
    sub = trades.loc[start:end]
    balance = rules.account_size
    previous_win = False
    result = "open"
    finish_ts = pd.NaT
    equity_values: list[float] = []
    equity_index: list[pd.Timestamp] = []
    used_trades = 0

    for ts, row in sub.iterrows():
        risk = policy.risk_for(str(row["module"]), previous_win)
        outcome_r = float(row["weighted_r"])
        balance *= 1.0 + outcome_r * risk
        used_trades += 1
        equity_values.append(balance)
        equity_index.append(ts)

        if balance <= rules.breach_balance:
            result = "max_drawdown"
            finish_ts = ts
            break
        if balance >= rules.target_balance:
            result = "pass"
            finish_ts = ts
            break
        previous_win = outcome_r > 0

    equity = pd.Series(equity_values, index=pd.DatetimeIndex(equity_index), dtype=float)
    if validate_vectorbt and not equity.empty:
        vbt_return, vbt_max_dd = _vectorbt_metrics(equity, rules.account_size)
    else:
        vbt_return = balance / rules.account_size - 1.0
        running_peak = pd.concat(
            [pd.Series([rules.account_size]), equity.reset_index(drop=True)]
        ).cummax()
        path = pd.concat([pd.Series([rules.account_size]), equity.reset_index(drop=True)])
        vbt_max_dd = float(((running_peak - path) / running_peak).max())

    elapsed_to = finish_ts if pd.notna(finish_ts) else min(end, trades.index.max())
    elapsed_days = max(0.0, (elapsed_to - start).total_seconds() / 86_400.0)
    return {
        "start": start,
        "result": result,
        "finish": finish_ts,
        "days": elapsed_days,
        "trades": used_trades,
        "final_balance": balance,
        "return_pct": vbt_return * 100.0,
        "max_drawdown_pct": vbt_max_dd * 100.0,
    }


def simulate_rolling_starts(
    trades: pd.DataFrame,
    policy: RiskPolicy,
    rules: MavenRules = MavenRules(),
    horizon_days: int = 180,
    start_frequency: str = "7D",
    validate_vectorbt: bool = True,
) -> pd.DataFrame:
    first = trades.index.min().normalize()
    last = (trades.index.max() - pd.Timedelta(days=horizon_days)).normalize()
    starts = pd.date_range(first, last, freq=start_frequency, tz=trades.index.tz)
    rows = [
        simulate_path(
            trades,
            start,
            policy,
            rules=rules,
            horizon_days=horizon_days,
            validate_vectorbt=validate_vectorbt,
        )
        for start in starts
    ]
    return pd.DataFrame(rows)


def summarize(paths: pd.DataFrame, policy: RiskPolicy, horizon_days: int) -> dict:
    if paths.empty:
        return {"policy": policy.name, "horizon_days": horizon_days, "starts": 0}
    result_pct = paths["result"].value_counts(normalize=True).mul(100.0)
    passed = paths[paths["result"] == "pass"]
    return {
        "policy": policy.name,
        "horizon_days": horizon_days,
        "starts": int(len(paths)),
        "pass_pct": float(result_pct.get("pass", 0.0)),
        "fail_pct": float(result_pct.get("max_drawdown", 0.0)),
        "open_pct": float(result_pct.get("open", 0.0)),
        "median_pass_days": float(passed["days"].median()) if len(passed) else np.nan,
        "p75_pass_days": float(passed["days"].quantile(0.75)) if len(passed) else np.nan,
        "median_pass_trades": float(passed["trades"].median()) if len(passed) else np.nan,
        "median_max_drawdown_pct": float(paths["max_drawdown_pct"].median()),
        "p95_max_drawdown_pct": float(paths["max_drawdown_pct"].quantile(0.95)),
    }


def run_scan(
    trades: pd.DataFrame,
    policies: tuple[RiskPolicy, ...] = DEFAULT_POLICIES,
    horizons: tuple[int, ...] = (30, 60, 90, 180),
    rules: MavenRules = MavenRules(),
    start_frequency: str = "7D",
    validate_vectorbt: bool = True,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    summaries = []
    paths = []
    for policy in policies:
        for horizon in horizons:
            result = simulate_rolling_starts(
                trades,
                policy,
                rules=rules,
                horizon_days=horizon,
                start_frequency=start_frequency,
                validate_vectorbt=validate_vectorbt,
            )
            result.insert(0, "policy", policy.name)
            result.insert(1, "horizon_days", horizon)
            paths.append(result)
            summaries.append(summarize(result, policy, horizon))
    return pd.DataFrame(summaries), pd.concat(paths, ignore_index=True)


def compare_bot_portfolios(
    trades: pd.DataFrame,
    policy: RiskPolicy = RiskPolicy("fixed_1.00", 0.01),
    horizons: tuple[int, ...] = (30, 60, 90, 180),
    rules: MavenRules = MavenRules(),
    start_frequency: str = "7D",
    validate_vectorbt: bool = True,
) -> pd.DataFrame:
    portfolios = {
        "all_7": trades,
        "phase1_5": trades[
            ~trades["module"].isin(["SWEEP_ES_DIV", "BTCUSDT_OF_ABSORPTION"])
        ],
        # CANLI portfoy risk.py'den TURER, sabit yazilmaz. 2026-08-28 denetiminde
        # bulundu: burasi "forward_verified_2" adiyla GOLD+NQ_ORB'u sabitliyordu.
        # Etiket 2026-08-06'da dogruydu; sonra defter backfill'den temizlendi,
        # GOLD emekli oldu, NQ_ORB dusurme esigine 3 islem kaldi -- yani
        # "forward dogrulanmis" denen kume defterdeki en kotu iki modulu
        # gosterir olmustu. Sabit liste tier degisince sessizce yanlislasiyor.
        "canli_tier": trades[trades["module"].isin(live_module_names())],
    }
    rows = []
    for name, portfolio_trades in portfolios.items():
        summary, _ = run_scan(
            portfolio_trades,
            policies=(policy,),
            horizons=horizons,
            rules=rules,
            start_frequency=start_frequency,
            validate_vectorbt=validate_vectorbt,
        )
        summary.insert(0, "portfolio", name)
        summary.insert(1, "trade_count", len(portfolio_trades))
        rows.append(summary)
    return pd.concat(rows, ignore_index=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Maven 5K Pay After Pass simulator")
    parser.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER)
    parser.add_argument("--start-frequency", default="7D")
    parser.add_argument("--no-vectorbt-validation", action="store_true")
    args = parser.parse_args()

    rules = MavenRules()
    trades = load_final_ledger(args.ledger)
    summary, paths = run_scan(
        trades,
        rules=rules,
        start_frequency=args.start_frequency,
        validate_vectorbt=not args.no_vectorbt_validation,
    )
    comparison = compare_bot_portfolios(
        trades,
        rules=rules,
        start_frequency=args.start_frequency,
        validate_vectorbt=not args.no_vectorbt_validation,
    )

    summary_path = OUT / "maven_5k_challenge_summary.csv"
    paths_path = OUT / "maven_5k_challenge_paths.csv"
    comparison_path = OUT / "maven_5k_portfolio_comparison.csv"
    card_path = OUT / "maven_5k_challenge_run_card.json"
    summary.to_csv(summary_path, index=False)
    paths.to_csv(paths_path, index=False)
    comparison.to_csv(comparison_path, index=False)
    card_path.write_text(
        json.dumps(
            {
                "verified_date": "2026-06-19",
                "rules": asdict(rules),
                "modules": sorted(trades["module"].unique().tolist()),
                "trade_count": int(len(trades)),
                "first_trade": str(trades.index.min()),
                "last_trade": str(trades.index.max()),
                "vectorbt_validated": not args.no_vectorbt_validation,
                "source_urls": [
                    "https://maventrading.com/buy-now-pay-later",
                    "https://maventrading.com/faqs",
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    cols = [
        "policy",
        "horizon_days",
        "pass_pct",
        "fail_pct",
        "open_pct",
        "median_pass_days",
        "p75_pass_days",
        "median_pass_trades",
        "p95_max_drawdown_pct",
    ]
    print("\nMAVEN 5K PAY AFTER PASS - 7 MODULE FINAL ROUTER")
    print(f"Rules: target ${rules.target_balance:,.0f}, breach ${rules.breach_balance:,.0f}, daily DD none")
    print(summary[cols].to_string(index=False, float_format=lambda x: f"{x:.2f}"))
    print(f"\nsummary: {summary_path}")
    print(f"paths:   {paths_path}")
    print(f"compare: {comparison_path}")
    print(f"card:    {card_path}")


if __name__ == "__main__":
    main()
