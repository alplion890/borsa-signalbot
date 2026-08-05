import pandas as pd

from intraday.challenge_sim import (
    MavenRules,
    RiskPolicy,
    simulate_path,
    summarize,
)


def _trades(r_values):
    idx = pd.date_range("2026-01-01", periods=len(r_values), freq="D", tz="UTC")
    return pd.DataFrame(
        {
            "module": ["GOLD_NY_ORB_TREND"] * len(r_values),
            "weighted_r": r_values,
        },
        index=idx,
    )


def test_maven_rules_match_pay_after_pass():
    rules = MavenRules()
    assert rules.target_balance == 5200.0
    assert rules.breach_balance == 4500.0
    assert rules.daily_drawdown_pct is None
    assert rules.min_trading_days == 0
    assert rules.max_trading_days is None


def test_path_passes_at_four_percent():
    result = simulate_path(
        _trades([1.0, 1.0, 1.0, 1.0]),
        pd.Timestamp("2026-01-01", tz="UTC"),
        RiskPolicy("fixed_1", 0.01),
        validate_vectorbt=False,
    )
    assert result["result"] == "pass"
    assert result["trades"] == 4


def test_path_breaches_static_ten_percent():
    result = simulate_path(
        _trades([-1.0] * 11),
        pd.Timestamp("2026-01-01", tz="UTC"),
        RiskPolicy("fixed_1", 0.01),
        validate_vectorbt=False,
    )
    assert result["result"] == "max_drawdown"


def test_no_daily_drawdown_breach():
    result = simulate_path(
        _trades([-3.0, 4.0]),
        pd.Timestamp("2026-01-01", tz="UTC"),
        RiskPolicy("fixed_1", 0.01),
        validate_vectorbt=False,
    )
    assert result["result"] != "max_drawdown"


def test_summary_reports_pass_fail_open():
    paths = pd.DataFrame(
        {
            "result": ["pass", "max_drawdown", "open", "pass"],
            "days": [10, 20, 30, 14],
            "trades": [5, 8, 9, 7],
            "max_drawdown_pct": [2.0, 10.0, 4.0, 3.0],
        }
    )
    out = summarize(paths, RiskPolicy("x", 0.01), 30)
    assert out["pass_pct"] == 50.0
    assert out["fail_pct"] == 25.0
    assert out["open_pct"] == 25.0
