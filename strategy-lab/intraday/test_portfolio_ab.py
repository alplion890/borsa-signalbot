"""Portfoy kompozisyonu olcumunun cekirdek mantigi.

Spec: docs/superpowers/specs/2026-08-14-portfoy-kompozisyonu-design.md

Burada test edilen iki sey, yanlis olursa KARARI sessizce degistirir:
  1. Tek-slot filtresi -- uygulanmazsa cok sembollu portfoyler sisirilir.
  2. Faz kurallari -- yanlis esik/risk, patlama olasiligini kaydirir.
Rapor/ciktilama katmani test edilmiyor (proje konvansiyonu: lab scriptleri).
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from . import portfolio_ab as pa


def _trades(rows: list[tuple[str, str]]) -> pd.DataFrame:
    return pd.DataFrame({
        "entry_time": pd.to_datetime([r[0] for r in rows]),
        "exit_time": pd.to_datetime([r[1] for r in rows]),
        "r": np.arange(len(rows), dtype=float),
    })


# --- 1. tek-slot filtresi ---------------------------------------------------


def test_non_overlapping_trades_all_kept() -> None:
    df = _trades([("2026-01-01 10:00", "2026-01-01 11:00"),
                  ("2026-01-01 12:00", "2026-01-01 13:00")])
    assert len(pa.one_slot(df)) == 2


def test_overlapping_trade_is_dropped() -> None:
    """Ikinci islem birincisi acikken basliyor -> alinmaz."""
    df = _trades([("2026-01-01 10:00", "2026-01-01 14:00"),
                  ("2026-01-01 11:00", "2026-01-01 12:00")])
    kept = pa.one_slot(df)
    assert len(kept) == 1
    assert kept.iloc[0]["r"] == 0.0, "ilk gelen tutulmali"


def test_trade_starting_exactly_at_previous_exit_is_kept() -> None:
    df = _trades([("2026-01-01 10:00", "2026-01-01 11:00"),
                  ("2026-01-01 11:00", "2026-01-01 12:00")])
    assert len(pa.one_slot(df)) == 2


def test_unsorted_input_is_ordered_before_filtering() -> None:
    """Defter modul bazinda birlestirilince sira bozulur; filtre once siralamali."""
    df = _trades([("2026-01-01 12:00", "2026-01-01 13:00"),
                  ("2026-01-01 10:00", "2026-01-01 11:00")])
    kept = pa.one_slot(df)
    assert len(kept) == 2
    assert list(kept["entry_time"]) == sorted(kept["entry_time"])


def test_third_trade_after_long_first_is_kept() -> None:
    """Uzun bir islem iki adayi birden yerse, sonraki yine alinabilmeli."""
    df = _trades([("2026-01-01 10:00", "2026-01-01 20:00"),
                  ("2026-01-01 11:00", "2026-01-01 12:00"),
                  ("2026-01-01 21:00", "2026-01-01 22:00")])
    kept = pa.one_slot(df)
    assert len(kept) == 2
    assert list(kept["r"]) == [0.0, 2.0]


# --- 2. challenge fazi ------------------------------------------------------


def test_challenge_passes_on_winning_pool() -> None:
    """+2R'lik islemler %1.5 riskle: 2 islemde +%4'u gecer."""
    R = np.array([2.0])
    passed = pa.simulate_challenge(R, n_paths=50, rng=np.random.default_rng(0))
    assert passed.all()


def test_challenge_stops_on_losing_pool() -> None:
    R = np.array([-1.0])
    passed = pa.simulate_challenge(R, n_paths=50, rng=np.random.default_rng(0))
    assert not passed.any()


def test_risk_doubles_after_a_win() -> None:
    """Kural: onceki kapanan islem kazandiysa risk %3.

    Ilk islem +1R -> %1.5 kazanc (eq 1.015). Ikinci islem de +1R ama artik
    risk %3 -> eq 1.015*1.03. Tek islemlik %1.5'ten buyuk olmali.
    """
    eq = pa.challenge_equity_after(np.array([1.0, 1.0]))
    assert eq == pytest.approx(1.015 * 1.03)


def test_risk_stays_low_after_a_loss() -> None:
    eq = pa.challenge_equity_after(np.array([-1.0, 1.0]))
    assert eq == pytest.approx(0.985 * 1.015)


# --- 3. funded fazi ---------------------------------------------------------


def test_funded_survives_winning_pool() -> None:
    R = np.array([2.0])
    alive = pa.simulate_funded(R, trades_per_day=1.0, n_days=60,
                               n_paths=50, rng=np.random.default_rng(0))
    assert alive.all()


def test_funded_blown_by_trailing_drawdown() -> None:
    """Surekli kaybeden havuz %8 trailing DD'ye carpmali."""
    R = np.array([-1.0])
    alive = pa.simulate_funded(R, trades_per_day=4.0, n_days=252,
                               n_paths=50, rng=np.random.default_rng(0))
    assert not alive.any()


def test_funded_trailing_drawdown_measured_from_peak_not_start() -> None:
    """Once +%10 yapip sonra tepeden %8 geri veren hesap OLMELI.

    Statik limit olsaydi hayatta kalirdi (hesap hala baslangicin USTUNDE).
    Bu ayrim Maven'in en tehlikeli kurali; yanlis uygulanirsa patlama olasiligi
    sistematik olarak dusuk cikar.

    Gunler tek tek -%4 limitinin ustunde tutuldu ki bu test SADECE trailing
    kuralini olcsun -- yoksa gunluk limit yuzunden dogru sonucu yanlis sebeple
    verirdi.
    """
    kill = np.array([+0.10, -0.03, -0.03, -0.03])   # tepe 1.10 -> 1.01, fark 0.09
    live = np.array([+0.10, -0.03, -0.03])          # tepe 1.10 -> 1.04, fark 0.06
    assert pa.funded_path_survives(kill) is False
    assert pa.funded_path_survives(live) is True


def test_funded_blown_by_daily_loss_limit() -> None:
    """Tek gunde -%4 -> o gun hesap biter (trailing DD'ye bakilmaksizin)."""
    assert pa.funded_path_survives(np.array([-0.045])) is False
    assert pa.funded_path_survives(np.array([-0.035])) is True
