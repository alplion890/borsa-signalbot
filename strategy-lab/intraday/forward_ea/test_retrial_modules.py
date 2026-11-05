"""Forward re-trial candidates must match the preregistered archived definition.

Prereg: HANDOFF/edge_yeniden_yargilama_onkayit_2026-11-05.md (commit 36a8e4c).
"""
from __future__ import annotations

from . import modules


def test_nq_orb_retrial_uses_archived_definition(monkeypatch):
    seen = {}

    def fake_orb(case, adx_min):
        seen["case"], seen["adx_min"] = case, adx_min
        return lambda _frame: None

    monkeypatch.setattr(modules, "_orb_detector", fake_orb)
    mod = {m.name: m for m in modules.candidate_modules()}["CAND_RT_NQ_ORB"]
    assert (mod.symbol_key, mod.tf, mod.weight, mod.max_hold_bars) == \
        ("NASDAQ100", "5m", 0.0, 48)
    assert seen["case"] == modules.ORBCase(
        "NASDAQ100", 14.5, 15, 20.5, "retest", "none", 1.5, "other_side", 1.0, 48)
    assert seen["adx_min"] == 28.0


def test_retrial_candidate_never_reaches_telegram_list():
    assert "CAND_RT_NQ_ORB" not in {m.name for m in modules.default_modules()}
