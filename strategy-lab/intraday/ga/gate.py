"""Overfit gate'i GA fitness + hard-filter olarak sarmalar.

Mevcut overfit_validation gate kriterleri (PROJECT_STATUS Adim B):
    exp_r >= GATE_EXP        (yuksek-frekans portfoyu icin gevsetilebilir)
    trades_per_week >= 2.5
    pass_pct >= 32
    total_dd_pct <= 8
    positive_years >= 4
    min_year_R > 0

GA fitness'i bu kriterleri SERT esik degil, ceza olarak kullanir: gate'i gecen
adaylar pass_pct ile odullenir; her ihlal agir ceza yer. Boylece GA gate-gecen
bolgeye dogru evrilir ama curve-fit kose cozumlerden kacinir.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from ..regime_router_quality_lift_scan import (
    _challenge, _metrics, _weeks, _window_summary, _year_stats,
)


@dataclass(frozen=True)
class GateConfig:
    exp_r: float = 0.10          # yuksek-frekans portfoyu icin 0.14'ten gevsetildi
    trades_per_week: float = 2.5
    pass_pct: float = 32.0
    total_dd_pct: float = 8.0
    positive_years: int = 4
    min_year_R: float = 0.0


def evaluate_ledger(ledger: pd.DataFrame) -> dict:
    """Bir portfoy ledger'indan gate metriklerini hesapla."""
    m = _metrics(ledger["weighted_r"])
    m["trades_per_week"] = m["trades"] / _weeks(ledger.index)
    w = _challenge(ledger)
    m.update(_window_summary(w))
    m.update(_year_stats(ledger))
    return m


def gate_status(metrics: dict, cfg: GateConfig) -> tuple[bool, list[str]]:
    """(gecti_mi, ihlaller). Bos liste = temiz gecis."""
    fails = []
    if metrics["exp_r"] < cfg.exp_r:
        fails.append(f"exp_r {metrics['exp_r']:.3f}<{cfg.exp_r}")
    if metrics["trades_per_week"] < cfg.trades_per_week:
        fails.append(f"tpw {metrics['trades_per_week']:.2f}<{cfg.trades_per_week}")
    if metrics["pass_pct"] < cfg.pass_pct:
        fails.append(f"pass {metrics['pass_pct']:.1f}<{cfg.pass_pct}")
    if metrics["total_dd_pct"] > cfg.total_dd_pct:
        fails.append(f"totalDD {metrics['total_dd_pct']:.1f}>{cfg.total_dd_pct}")
    if metrics["positive_years"] < cfg.positive_years:
        fails.append(f"posYears {metrics['positive_years']}<{cfg.positive_years}")
    if metrics["min_year_R"] <= cfg.min_year_R:
        fails.append(f"minYearR {metrics['min_year_R']:.2f}<=0")
    return (len(fails) == 0, fails)


def fitness(metrics: dict, cfg: GateConfig) -> float:
    """GA fitness: pass_pct temel; her gate ihlali agir ceza.

    Gate-gecen aday her zaman gate-kalandan yuksek skorlu olur (taban ofset).
    Geceler arasinda pass_pct + hafif DD-marji ile siralanir.
    """
    passed, fails = gate_status(metrics, cfg)
    if not np.isfinite(metrics.get("pass_pct", np.nan)):
        return float("-inf")
    base = metrics["pass_pct"]
    dd_margin = max(0.0, cfg.total_dd_pct - metrics["total_dd_pct"])  # bos DD odulu
    if passed:
        return 1000.0 + base + dd_margin * 0.5
    # gate-kaldi: pass'i tut ama her ihlal icin -50
    return base - 50.0 * len(fails)
