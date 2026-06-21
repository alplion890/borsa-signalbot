"""Maven BNPL challenge/funded risk kilitleri + LIVE/PAPER tier eslemesi."""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum

# Enstruman basina 1 lot icin 1 puan hareketin $ degeri.
# LIVE moduller (Gold/NQ) dogru; FX paper -> implementer config.py'den duzeltir (~10$/pip/lot).
_VALUE_PER_POINT = {
    "XAUUSD": 100.0,    # 1 lot = 100 oz
    "NASDAQ100": 20.0,  # NQ 1 puan = 20$
    "SP500": 50.0,      # ES 1 puan = 50$
    "EURUSD": 100000.0, # FX: lot*price-move; implementer pip-degeriyle duzeltir
    "GBPUSD": 100000.0,
    "BTC": 1.0,
}

_LIVE_MODULES = {"GOLD_NY_ORB_TREND", "NQ_ORB_STRONG_TREND"}
_SWEEP_MODULE = "SWEEP_CORE_AVOID_MID_VWAP"


class Tier(str, Enum):
    LIVE = "LIVE"
    PAPER = "PAPER"


@dataclass(frozen=True)
class RiskProfile:
    name: str
    normal_pct: float
    winner_pct: float
    trade_cap_pct: float
    max_open_risk_pct: float
    daily_stop_pct: float
    weekly_stop_pct: float
    consistency_day_share_pct: float | None
    daily_profit_cap_pct: float | None
    payout_buffer_pct: float | None
    paper_normal_pct: float
    paper_winner_pct: float
    paper_cap_pct: float


_PROFILES = {
    # Maven BNPL Phase 1: 4% target, no daily DD, 10% static max DD.
    # En hizli tarihsel profil; hiz ugruna yuksek varyans bilincli kabul edilir.
    "bnpl_challenge": RiskProfile(
        "BNPL challenge hizli",
        0.015, 0.030, 0.030,
        0.030, 0.045, 0.075,
        None, None, None,
        0.0075, 0.0075, 0.0075,
    ),
    # Maven BNPL funded: 4% daily DD, 8% trailing DD, 20% consistency.
    # Kazanc sonrasi risk artisi yok; payout icin kar gunlere yayilir.
    "bnpl_funded": RiskProfile(
        "BNPL funded koruma",
        0.0035, 0.0035, 0.0050,
        0.0050, 0.010, 0.020,
        0.18, 0.0050, 0.025,
        0.0, 0.0, 0.0,
    ),
}
_ALIASES = {
    "challenge": "bnpl_challenge",
    "funded": "bnpl_funded",
}


@dataclass(frozen=True)
class RiskPlan:
    profile_key: str
    profile_name: str
    normal_pct: float
    winner_pct: float
    normal_usd: float
    winner_usd: float
    normal_lot: float
    winner_lot: float
    max_open_risk_pct: float
    daily_stop_pct: float
    weekly_stop_pct: float
    consistency_day_share_pct: float | None
    daily_profit_cap_pct: float | None
    payout_buffer_pct: float | None
    real_money_allowed: bool


def profile_for(phase: str) -> tuple[str, RiskProfile]:
    key = _ALIASES.get(phase, phase)
    if key not in _PROFILES:
        raise ValueError(
            f"bilinmeyen risk profili: {phase}; "
            f"beklenen: {', '.join(sorted(_PROFILES))}"
        )
    return key, _PROFILES[key]


def tier_of(module_name: str) -> Tier:
    return Tier.LIVE if module_name in _LIVE_MODULES else Tier.PAPER


def risk_dollars(phase: str, balance: float) -> float:
    _, profile = profile_for(phase)
    return round(balance * profile.normal_pct, 2)


def lot_for(symbol_key: str, entry: float, sl: float, risk_usd: float) -> float:
    dist = abs(entry - sl)
    if dist <= 0 or risk_usd <= 0:
        return 0.0
    vpp = _VALUE_PER_POINT[symbol_key]
    return max(0.01, round(risk_usd / (dist * vpp), 2))


def risk_plan(*, phase: str, balance: float, module_name: str, module_weight: float,
              symbol_key: str, entry: float, sl: float) -> RiskPlan:
    """Return the locked BNPL phase plan, respecting weights and hard caps.

    Sweep core gets the historical 1.5x base multiplier. Portfolio weights
    reduce/increase allocation, but no single signal may exceed the phase cap.
    """
    profile_key, profile = profile_for(phase)
    multiplier = float(module_weight)
    if module_name == _SWEEP_MODULE:
        multiplier *= 1.5
    is_live = module_name in _LIVE_MODULES
    if is_live:
        normal_pct = min(profile.normal_pct * multiplier, profile.trade_cap_pct)
        winner_pct = min(profile.winner_pct * multiplier, profile.trade_cap_pct)
    else:
        normal_pct = min(profile.paper_normal_pct * multiplier, profile.paper_cap_pct)
        winner_pct = min(profile.paper_winner_pct * multiplier, profile.paper_cap_pct)
    normal_usd = round(balance * normal_pct, 2)
    winner_usd = round(balance * winner_pct, 2)
    return RiskPlan(
        profile_key=profile_key,
        profile_name=profile.name,
        normal_pct=normal_pct,
        winner_pct=winner_pct,
        normal_usd=normal_usd,
        winner_usd=winner_usd,
        normal_lot=lot_for(symbol_key, entry, sl, normal_usd),
        winner_lot=lot_for(symbol_key, entry, sl, winner_usd),
        max_open_risk_pct=profile.max_open_risk_pct,
        daily_stop_pct=profile.daily_stop_pct,
        weekly_stop_pct=profile.weekly_stop_pct,
        consistency_day_share_pct=profile.consistency_day_share_pct,
        daily_profit_cap_pct=profile.daily_profit_cap_pct,
        payout_buffer_pct=profile.payout_buffer_pct,
        real_money_allowed=normal_pct > 0,
    )
