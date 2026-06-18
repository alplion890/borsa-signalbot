"""Maven challenge risk/lot hesabi + LIVE/PAPER tier eslemesi."""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum

_RISK_PCT = {"challenge": 0.015, "funded": 0.005}
_WINNER_RISK_PCT = {"challenge": 0.030, "funded": 0.0075}
_RISK_CAP = {"challenge": 0.030, "funded": 0.0075}

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
class RiskPlan:
    normal_pct: float
    winner_pct: float
    normal_usd: float
    winner_usd: float
    normal_lot: float
    winner_lot: float


def tier_of(module_name: str) -> Tier:
    return Tier.LIVE if module_name in _LIVE_MODULES else Tier.PAPER


def risk_dollars(phase: str, balance: float) -> float:
    return round(balance * _RISK_PCT[phase], 2)


def lot_for(symbol_key: str, entry: float, sl: float, risk_usd: float) -> float:
    dist = abs(entry - sl)
    if dist <= 0:
        return 0.0
    vpp = _VALUE_PER_POINT[symbol_key]
    return max(0.01, round(risk_usd / (dist * vpp), 2))


def risk_plan(*, phase: str, balance: float, module_name: str, module_weight: float,
              symbol_key: str, entry: float, sl: float) -> RiskPlan:
    """Return the 1.5% -> 3% plan, respecting module weights and hard cap.

    Sweep core gets the historical 1.5x base multiplier. Portfolio weights
    reduce/increase allocation, but no single signal may exceed the phase cap.
    """
    multiplier = float(module_weight)
    if module_name == _SWEEP_MODULE:
        multiplier *= 1.5
    normal_pct = min(_RISK_PCT[phase] * multiplier, _RISK_CAP[phase])
    winner_pct = min(_WINNER_RISK_PCT[phase] * multiplier, _RISK_CAP[phase])
    normal_usd = round(balance * normal_pct, 2)
    winner_usd = round(balance * winner_pct, 2)
    return RiskPlan(
        normal_pct=normal_pct,
        winner_pct=winner_pct,
        normal_usd=normal_usd,
        winner_usd=winner_usd,
        normal_lot=lot_for(symbol_key, entry, sl, normal_usd),
        winner_lot=lot_for(symbol_key, entry, sl, winner_usd),
    )
