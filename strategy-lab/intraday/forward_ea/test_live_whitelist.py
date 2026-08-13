"""Gercek emir atabilen modul listesi TEK kaynaktan gelmeli.

Neden ayri dosya: bu invaryant iki modul arasinda (order_executor <-> risk).
Iki yerde elle tutulan liste 2026-08-06'da kaydi ve kimse fark etmedi --
risk.py duzeltildi, order_executor duzeltilmedi. Sonuc: elenmis GOLD gercek
emir atabiliyordu, en kanitli SWEEP_CORE atamiyordu.

Ayni hatanin ucuncu ornegi (bkz risk tier'i ters bagliydi, notify aday
siziyordu). Kalip ayni: ayni gercegin iki kopyasi.
"""
from __future__ import annotations

import sys
from types import SimpleNamespace

# order_executor MT5 paketini import ediyor; bu testler terminal gerektirmez.
# Yalnizca paket yoksa yer tutucu konur (Windows disi / venv disi kosumlar icin).
if "MetaTrader5" not in sys.modules:
    try:
        import MetaTrader5  # noqa: F401
    except ModuleNotFoundError:
        sys.modules["MetaTrader5"] = SimpleNamespace(
            initialize=lambda *a, **k: False, shutdown=lambda: None,
        )

from ..signalbot import risk
from ..signalbot.risk import Tier, tier_of
from . import order_executor as oe

# Karar Kurali (vault: "Borsa - Karar Kurali (baslama ve durma)", madde 2):
# girilecek SADECE bu ikisi.
KARAR_KURALI_IKILI = {"NQ_ORB_STRONG_TREND", "SWEEP_CORE_AVOID_MID_VWAP"}


def test_whitelist_matches_karar_kurali() -> None:
    assert oe.LIVE_MODULES == KARAR_KURALI_IKILI


def test_whitelist_cannot_drift_from_risk_tiers() -> None:
    """Iki liste ayni gercegi anlatiyor; kopya tutulursa yine kayar."""
    assert oe.LIVE_MODULES == set(risk.live_module_names())


def test_every_live_module_is_live_tier_in_risk() -> None:
    for name in oe.LIVE_MODULES:
        assert tier_of(name) is Tier.LIVE, f"{name} risk.py'de LIVE degil"


def test_eliminated_gold_cannot_place_real_orders() -> None:
    """GOLD_NY_ORB_TREND elendi: forward exp_R -0.152, 18 islem, PSR 0.203."""
    assert "GOLD_NY_ORB_TREND" not in oe.LIVE_MODULES


def test_strongest_module_can_place_real_orders() -> None:
    """SWEEP_CORE portfoyun kaninin neredeyse tamamini uretti (PSR 0.907)."""
    assert "SWEEP_CORE_AVOID_MID_VWAP" in oe.LIVE_MODULES


def test_no_candidate_can_ever_place_real_orders() -> None:
    assert not any(n.startswith("CAND_") for n in oe.LIVE_MODULES)
