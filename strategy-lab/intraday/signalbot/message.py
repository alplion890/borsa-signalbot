"""Telegram mesaji — sade Turkce duz yazi, emoji/sembol yigini yok."""
from __future__ import annotations
from .risk import RiskPlan, Tier

_HUMAN = {
    "GOLD_NY_ORB_TREND": "Gold ORB",
    "NQ_ORB_STRONG_TREND": "NQ ORB",
    "SWEEP_CORE_AVOID_MID_VWAP": "NQ sweep",
    "EUR_LONDON_FADE_EMA": "EUR London fade",
    "GBP_LONDON_STRONG_TREND": "GBP London trend",
    "SWEEP_ES_DIV": "NQ ES uyumsuzluk",
    "BTCUSDT_OF_ABSORPTION": "BTC absorption",
}


def format_signal(*, tier: Tier, module: str, symbol_key: str, direction: int,
                  entry: float, sl: float, tp: float, lot: float,
                  risk_usd: float, trt_time: str,
                  risk_plan: RiskPlan | None = None) -> str:
    yon = "long" if direction == 1 else "short"
    ad = _HUMAN.get(module, module)
    if risk_plan is None:
        risk_text = f"Risk {risk_usd:g} dolar yani lot {lot:g}."
    elif abs(risk_plan.normal_lot - risk_plan.winner_lot) < 1e-9:
        risk_text = (
            f"Risk yuzde {risk_plan.normal_pct * 100:g} yani "
            f"{risk_plan.normal_usd:g} dolar ve lot {risk_plan.normal_lot:g}."
        )
    else:
        risk_text = (
            f"Normal risk {risk_plan.normal_usd:g} dolar lot {risk_plan.normal_lot:g}. "
            f"Onceki kapanan islem kazandiysa {risk_plan.winner_usd:g} dolar "
            f"lot {risk_plan.winner_lot:g}."
        )
    common_tail = (
        f"{risk_text} Saat {trt_time}. Acik islemin varsa veya fiyat giristen "
        "uzaklastiysa alma."
    )
    if tier is Tier.LIVE:
        return (
            f"{ad} {yon} sinyali geldi. Yaklasik {entry:g} ten gir, "
            f"stop {sl:g}, hedef {tp:g}. {common_tail} "
            "Retest girisi bekle, kirilimi kovalama."
        )
    return (
        f"Paper sinyali {ad} {yon}. Once chart ac ve setupi teyit et. "
        f"Yaklasik {entry:g} ten gir, stop {sl:g}, hedef {tp:g}. {common_tail}"
    )
