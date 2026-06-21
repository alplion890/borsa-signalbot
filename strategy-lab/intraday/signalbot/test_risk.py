from intraday.signalbot.risk import lot_for, risk_dollars, risk_plan, Tier, tier_of


def test_risk_dollars_challenge():
    assert risk_dollars("challenge", 5000) == 75.0


def test_risk_dollars_funded():
    assert risk_dollars("funded", 5000) == 17.5


def test_lot_for_xauusd():
    lot = lot_for("XAUUSD", 4225, 4214, 75)
    assert lot > 0


def test_tier_gold_ny_orb_trend_is_live():
    assert tier_of("GOLD_NY_ORB_TREND") is Tier.LIVE


def test_tier_nq_orb_strong_trend_is_live():
    assert tier_of("NQ_ORB_STRONG_TREND") is Tier.LIVE


def test_tier_sweep_core_is_paper():
    assert tier_of("SWEEP_CORE_AVOID_MID_VWAP") is Tier.PAPER


def test_tier_eur_london_is_paper():
    assert tier_of("EUR_LONDON_FADE_EMA") is Tier.PAPER


def test_challenge_winner_plan_is_1_5_to_3():
    plan = risk_plan(
        phase="challenge", balance=5000, module_name="GOLD_NY_ORB_TREND",
        module_weight=1.0, symbol_key="XAUUSD", entry=3000, sl=2990,
    )
    assert plan.normal_usd == 75
    assert plan.winner_usd == 150


def test_btc_weight_reduces_risk():
    plan = risk_plan(
        phase="challenge", balance=5000, module_name="BTCUSDT_OF_ABSORPTION",
        module_weight=0.11, symbol_key="BTC", entry=100000, sl=99000,
    )
    assert plan.normal_usd == 4.12
    assert plan.winner_usd == 4.12


def test_challenge_paper_modules_are_capped_at_point_75_percent():
    plan = risk_plan(
        phase="bnpl_challenge", balance=5000, module_name="SWEEP_ES_DIV",
        module_weight=2.0, symbol_key="NASDAQ100", entry=20000, sl=19950,
    )
    assert plan.normal_usd == 37.5
    assert plan.winner_usd == 37.5
    assert plan.normal_pct == 0.0075


def test_funded_live_has_no_winner_boost_and_half_percent_cap():
    plan = risk_plan(
        phase="bnpl_funded", balance=5000, module_name="GOLD_NY_ORB_TREND",
        module_weight=2.0, symbol_key="XAUUSD", entry=3000, sl=2990,
    )
    assert plan.normal_usd == 25.0
    assert plan.winner_usd == 25.0
    assert plan.max_open_risk_pct == 0.005
    assert plan.daily_profit_cap_pct == 0.005


def test_funded_paper_modules_are_observation_only():
    plan = risk_plan(
        phase="bnpl_funded", balance=5000, module_name="SWEEP_ES_DIV",
        module_weight=2.0, symbol_key="NASDAQ100", entry=20000, sl=19950,
    )
    assert plan.normal_usd == 0.0
    assert plan.normal_lot == 0.0
    assert plan.real_money_allowed is False
