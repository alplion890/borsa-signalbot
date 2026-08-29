"""Maven BNPL challenge/funded risk kilitleri + LIVE/PAPER tier eslemesi."""
from __future__ import annotations
import math
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

# LIVE = gercek para. Uyelik forward test KANITIYLA kazanilir, backtest yetmez.
# 2026-08-06 revizyonu (97 islemlik defter):
#   GOLD_NY_ORB_TREND  CIKARILDI -- Elenmis modul en yuksek riski aliyordu.
#   SWEEP_CORE         EKLENDI   -- yanlis tarafta durdugu icin yarim riskle
#                      calisiyordu.
#
# UYARI: bu satirlarda EskiDEN forward rakamlari yaziliydi (gold -0.152/18 islem,
# sweep +1.206). O sayilar BACKFILL KIRLI defterden geliyordu; 2026-08-21'de
# defter temizlenince degistiler. Guncel forward icin tek kaynak:
#   python -m intraday.forward_ea.ledger  (veya birlesik_forward)
# Yorumda sayi dondurmak, sayi degisince yalana donusuyor -- o yuzden cikarildi.
#                      Yanlis tarafta durdugu icin yarim riskle calisiyordu.
# EUR/GBP London PAPER kalir: Persembe filtresi 2026-08-05'te kaldirilinca
# config degisti, onceki 6 islem gecersiz -> su an kanitsiz (kullanici karari).
_LIVE_MODULES = {"NQ_ORB_STRONG_TREND", "SWEEP_CORE_AVOID_MID_VWAP"}


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
    # %1.5 normal, onceki KAPANAN islem kazandiysa %3 (anti-martingale).
    # Kullanici karari 2026-08-06: hiz ugruna yuksek varyans BILINCLI kabul.
    #
    # Olculen takas (40k Monte Carlo, defterden bootstrap R, eslesmis cekilis):
    #             gecme%  patlama%  medyan sure  p90 sure  p95 en dip
    #   sabit %1   96.5     3.5      2.7 hafta   9.4 hf     -8.9%
    #   %1.5->%3   84.8    15.2      1.2 hafta   4.2 hf    -10.9%
    # Yani 1.5 hafta hiz, +11.7 puan patlama olasiligina mal oluyor.
    # p95 en dip -%10.9: en kotu %5 senaryoda statik dip ZATEN asiliyor.
    # PAPER moduller 0.0 -> gercek para yok, sadece defter kaydi.
    "bnpl_challenge": RiskProfile(
        "BNPL challenge hizli",
        0.015, 0.030, 0.030,
        0.030, 0.045, 0.075,
        None, None, None,
        0.0, 0.0, 0.0,
    ),
    # Maven BNPL funded: 4% daily DD, 8% trailing DD, 20% consistency.
    # Challenge gecilir gecilmez BURAYA gecilir: %0.5. Funded'da %1 ile calisan
    # hesaplarin yarisi patliyor; sermayeyi korumak hizdan onceliklidir.
    "bnpl_funded": RiskProfile(
        "BNPL funded koruma %0.5",
        0.0050, 0.0050, 0.0050,
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


def live_module_names() -> frozenset[str]:
    """Gercek para yetkisi olan moduller -- TEK kaynak.

    order_executor bu listeyi kendi kopyasinda tutuyordu ve 2026-08-06'da
    kaydi: burasi duzeltilirken orasi unutuldu, elenmis GOLD gercek emir
    atabilir halde kaldi. Kopya yerine buradan turetilir.
    """
    return frozenset(_LIVE_MODULES)


def risk_dollars(phase: str, balance: float) -> float:
    _, profile = profile_for(phase)
    return round(balance * profile.normal_pct, 2)


def lot_for(symbol_key: str, entry: float, sl: float, risk_usd: float) -> float:
    dist = abs(entry - sl)
    if dist <= 0 or risk_usd <= 0:
        return 0.0
    vpp = _VALUE_PER_POINT[symbol_key]
    raw_lot = risk_usd / (dist * vpp)
    # Never round upward through the configured dollar-risk ceiling.
    lot = math.floor((raw_lot + 1e-12) * 100) / 100
    return round(lot, 2) if lot >= 0.01 else 0.0


def risk_plan(*, phase: str, balance: float, module_name: str, module_weight: float,
              symbol_key: str, entry: float, sl: float) -> RiskPlan:
    """Return the locked BNPL phase plan, respecting weights and hard caps.

    Portfolio weights reduce/increase allocation, but no single signal may
    exceed the phase cap. The old 1.5x sweep-core multiplier was removed on
    2026-08-06: risk is now flat per phase, sized by evidence tier only.
    """
    profile_key, profile = profile_for(phase)
    multiplier = float(module_weight)
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
