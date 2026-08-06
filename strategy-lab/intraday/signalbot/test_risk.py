from intraday.signalbot.risk import lot_for, risk_dollars, risk_plan, Tier, tier_of


def test_risk_dollars_challenge():
    assert risk_dollars("challenge", 5000) == 75.0


def test_risk_dollars_funded():
    assert risk_dollars("funded", 5000) == 25.0


def test_lot_for_xauusd():
    lot = lot_for("XAUUSD", 4225, 4214, 75)
    assert lot > 0


def test_lot_never_rounds_above_dollar_risk_or_forces_minimum():
    assert lot_for("BTC", 100000, 99000, 4.12) == 0.0
    assert lot_for("XAUUSD", 3000, 2991, 50) == 0.05


def test_tier_is_the_forward_proven_pair():
    """Gercek para sadece forward defterinde kaniti olan ikiliye acilir."""
    assert tier_of("NQ_ORB_STRONG_TREND") is Tier.LIVE
    assert tier_of("SWEEP_CORE_AVOID_MID_VWAP") is Tier.LIVE


def test_tier_gold_is_paper_after_negative_forward_evidence():
    """GOLD forward'da -0.152 exp_R verdi (18 islem) -> gercek para YOK."""
    assert tier_of("GOLD_NY_ORB_TREND") is Tier.PAPER


def test_tier_london_modules_are_paper_until_reproven():
    """Persembe filtresi kalkinca config degisti; onceki ornekler gecersiz."""
    assert tier_of("EUR_LONDON_FADE_EMA") is Tier.PAPER
    assert tier_of("GBP_LONDON_STRONG_TREND") is Tier.PAPER


def test_challenge_live_risk_is_1_5_then_3_after_a_winner():
    """Anti-martingale: kazanandan sonra risk iki katina cikar."""
    plan = risk_plan(
        phase="challenge", balance=5000, module_name="SWEEP_CORE_AVOID_MID_VWAP",
        module_weight=1.0, symbol_key="NASDAQ100", entry=20000, sl=19950,
    )
    assert plan.normal_pct == 0.015
    assert plan.normal_usd == 75.0
    assert plan.winner_usd == 150.0


def test_challenge_live_never_exceeds_cap_even_with_high_weight():
    """Agirlik ne olursa olsun tek islem %3 tavanini asamaz."""
    plan = risk_plan(
        phase="challenge", balance=5000, module_name="NQ_ORB_STRONG_TREND",
        module_weight=4.0, symbol_key="NASDAQ100", entry=20000, sl=19950,
    )
    assert plan.normal_pct == 0.030
    assert plan.winner_pct == 0.030


def test_challenge_paper_modules_are_observation_only():
    """Gold/EUR/GBP/BTC: Telegram'a duser ama gercek para ayrilmaz."""
    for name, symbol, entry, sl in (
        ("GOLD_NY_ORB_TREND", "XAUUSD", 3000, 2990),
        ("EUR_LONDON_FADE_EMA", "EURUSD", 1.10, 1.099),
        ("BTCUSDT_OF_ABSORPTION", "BTC", 100000, 99000),
    ):
        plan = risk_plan(
            phase="challenge", balance=5000, module_name=name,
            module_weight=1.0, symbol_key=symbol, entry=entry, sl=sl,
        )
        assert plan.normal_usd == 0.0, name
        assert plan.real_money_allowed is False, name


def test_funded_live_drops_to_half_percent():
    plan = risk_plan(
        phase="bnpl_funded", balance=5000, module_name="SWEEP_CORE_AVOID_MID_VWAP",
        module_weight=2.0, symbol_key="NASDAQ100", entry=20000, sl=19950,
    )
    assert plan.normal_pct == 0.005
    assert plan.normal_usd == 25.0
    assert plan.winner_usd == 25.0
    assert plan.max_open_risk_pct == 0.005
    assert plan.daily_profit_cap_pct == 0.005


def test_funded_paper_modules_are_observation_only():
    plan = risk_plan(
        phase="bnpl_funded", balance=5000, module_name="GOLD_NY_ORB_TREND",
        module_weight=2.0, symbol_key="XAUUSD", entry=3000, sl=2990,
    )
    assert plan.normal_usd == 0.0
    assert plan.normal_lot == 0.0
    assert plan.real_money_allowed is False
