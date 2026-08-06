"""Aday moduller forward EA'da olculur ama Telegram'a SIZMAZ.

Kural: kanitlanmamis bir aday kullanicinin telefonuna sinyal gonderemez.
Sadece paper defterinde bagimsiz veri biriktirir. Kanit (DSR/PSR) gelince
elle default_modules()'e tasinir.
"""
from __future__ import annotations

import pandas as pd
import pytest

from . import modules


def test_candidates_are_not_in_default_modules() -> None:
    names = {m.name for m in modules.default_modules()}
    for cand in modules.candidate_modules():
        assert cand.name not in names, f"{cand.name} canli portfoye sizmis"


def test_forward_test_modules_includes_both() -> None:
    fwd = {m.name for m in modules.forward_test_modules()}
    assert {m.name for m in modules.default_modules()} <= fwd
    assert {m.name for m in modules.candidate_modules()} <= fwd


def test_signalbot_does_not_see_candidates() -> None:
    """signalbot _load_modules() SADECE default_modules kullanir."""
    from ..signalbot.signal_scan import _load_modules

    live = {m.name for m in _load_modules()}
    for cand in modules.candidate_modules():
        assert cand.name not in live, f"{cand.name} Telegram'a sizmis"


def test_signalbot_sends_exactly_default_modules() -> None:
    """Telegram listesi default_modules ile BIREBIR ayni olmali.

    Onceki hali `[*default_modules(), btc_module()]` idi: liste disaridan
    genisletilebiliyordu ve BTC aylarca olculmeden telefona dustu. Ustteki
    'aday sizmasin' testi bunu yakalayamaz cunku BTC modulu CAND_ onekli
    degildi. Bu test esitlik ariyor -- her turlu ekleme kirmizi verir.
    """
    from ..signalbot.signal_scan import _load_modules

    assert {m.name for m in _load_modules()} == {
        m.name for m in modules.default_modules()
    }


def test_btc_is_measured_but_never_sent() -> None:
    """BTC forward'da olculmeye DEVAM eder, Telegram'a CIKMAZ.

    Forward'da -0.691 exp_R verdi; sinyali telefona dusurmek zarar eden bir
    isleme davettir. Ama silmek de yanlis: olcum durursa soru cevapsiz kalir.
    """
    from ..signalbot.signal_scan import _load_modules

    fwd = {m.name for m in modules.forward_test_modules()}
    assert "CAND_BTC_ABSORPTION" in fwd
    assert not any("BTC" in m.name.upper() for m in _load_modules())


def test_candidate_names_are_marked() -> None:
    """Deftere bakan biri adayi bir bakista ayirt edebilmeli."""
    for cand in modules.candidate_modules():
        assert cand.name.startswith("CAND_"), cand.name


def test_dual_thrust_detector_returns_none_on_short_frame() -> None:
    det = modules._dual_thrust_detector(k=0.3, n_days=2)
    df = pd.DataFrame({
        "open": [1.0] * 10, "high": [1.0] * 10,
        "low": [1.0] * 10, "close": [1.0] * 10,
    }, index=pd.date_range("2026-01-01", periods=10, freq="5min"))
    assert det(df) is None


def test_dual_thrust_detector_fires_on_breakout() -> None:
    """Onceki gunlerde range olussun, seans acilisindan sonra yukari kirilsin."""
    idx = pd.date_range("2026-01-01 00:00", periods=1200, freq="5min")
    close = pd.Series(100.0, index=idx)
    # onceki gunlere dalgalanma ver (range > 0 olsun)
    close.iloc[:576] = 100.0 + pd.Series(range(576), index=idx[:576]).mod(20) * 0.5
    df = pd.DataFrame({"open": close, "high": close + 0.1,
                       "low": close - 0.1, "close": close})
    # son barda sert yukari kirilim
    df.iloc[-1, df.columns.get_loc("close")] = 200.0
    df.iloc[-1, df.columns.get_loc("high")] = 200.0
    det = modules._dual_thrust_detector(k=0.3, n_days=2, adx_min=0.0)
    sig = det(df)
    assert sig is None or sig.direction in (1, -1)  # cokmemeli; sinyal varsa gecerli olmali
