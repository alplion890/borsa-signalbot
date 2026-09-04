"""Gercek emir yolu, risk politikasini TEK kaynaktan almali.

2026-08-21'de bulundu: `order_executor` kendi `ExecConfig`'inde risk %1.5,
sweep %2.25, gunluk DD %4.5 tutuyordu; `signalbot/risk.py`'deki faz profili,
PAPER korumasi, toplam acik risk tavani ve haftalik stop emir yoluna hic
ulasmiyordu. Whitelist'te ayni hata olmustu (iki kopya, biri guncellendi).

Bu testler kaymanin sessizce geri gelmesini engeller.
"""
from __future__ import annotations

import sys
from types import SimpleNamespace

import pandas as pd
import pytest

if "MetaTrader5" not in sys.modules:  # gercek paket yalnizca Windows'ta
    sys.modules["MetaTrader5"] = SimpleNamespace(
        ORDER_TYPE_BUY=0, ORDER_TYPE_SELL=1, TRADE_ACTION_DEAL=1,
        ORDER_TIME_GTC=0, ORDER_FILLING_IOC=1, TRADE_RETCODE_DONE=10009,
    )

from unittest.mock import patch

from intraday.forward_ea.order_executor import ExecConfig, OrderExecutor
from intraday.forward_ea.positions import PaperPosition
from intraday.signalbot.risk import live_module_names, profile_for

LIVE = sorted(live_module_names())[0]
PAPER = "GOLD_NY_ORB_TREND"


class SahteMT5:
    ORDER_TYPE_BUY = 0
    ORDER_TYPE_SELL = 1
    TRADE_ACTION_DEAL = 1
    ORDER_TIME_GTC = 0
    ORDER_FILLING_IOC = 1
    TRADE_RETCODE_DONE = 10009

    def __init__(self, equity: float = 100_000.0):
        self.account_info_data = SimpleNamespace(
            balance=100_000.0, equity=equity, trade_allowed=True,
            login=1, server="Demo")
        self.terminal_info_data = SimpleNamespace(trade_allowed=True, connected=True)
        self.positions_data: list = []
        self.gonderilen: list = []

    def account_info(self):
        return self.account_info_data

    def terminal_info(self):
        return self.terminal_info_data

    def symbol_select(self, name, select):
        return True

    def symbol_info(self, name):
        return SimpleNamespace(point=0.01, digits=2, volume_min=0.01,
                               volume_step=0.01, volume_max=1000.0,
                               trade_tick_value=1.0, trade_tick_size=0.01,
                               trade_contract_size=100.0)

    def symbol_info_tick(self, name):
        return SimpleNamespace(bid=2399.5, ask=2400.5)

    def positions_get(self, symbol=None):
        if symbol is None:
            return tuple(self.positions_data)
        return tuple(p for p in self.positions_data if p.symbol == symbol)

    def order_send(self, request):
        self.gonderilen.append(request)
        return SimpleNamespace(retcode=10009, order=1, comment="OK", deal=1)


def _pozisyon(modul: str = LIVE, weight: float = 1.0) -> PaperPosition:
    return PaperPosition(
        module=modul, symbol="XAUUSD", direction=1,
        entry_time=pd.Timestamp("2026-08-21 14:00:00"),
        entry=2400.0, sl=2390.0, tp=2420.0, weight=weight,
        max_hold_bars=48, cost_per_side=0.00012)


@pytest.fixture
def istemci():
    return SahteMT5()


def test_ExecConfig_ARTIK_risk_alani_TASIMAZ():
    """Ikinci bir politika kaynagi olusturmak derlenmemeli bile."""
    alanlar = ExecConfig().__dataclass_fields__
    for yasak in ("risk_pct", "sweep_risk_pct", "max_risk_pct", "daily_dd_halt_pct"):
        assert yasak not in alanlar, f"{yasak} geri geldi -- ikinci politika kaynagi"


@patch("intraday.forward_ea.order_executor.mt5_io.resolve", return_value="XAUUSD")
def test_sweep_ARTIK_ozel_carpan_ALMAZ(_resolve, istemci):
    """Eski kod modul adinda 'SWEEP' arayip %2.25 veriyordu."""
    sweep = [m for m in live_module_names() if "SWEEP" in m]
    if not sweep:
        pytest.skip("canli listede sweep modulu yok")
    ex = OrderExecutor(client=istemci, phase="bnpl_challenge")
    _, profil = profile_for("bnpl_challenge")

    ex.open_for_signal(_pozisyon(sweep[0]), 100_000.0)
    assert istemci.gonderilen, "emir gonderilmedi"
    lot_sweep = istemci.gonderilen[-1]["volume"]

    istemci.gonderilen.clear()
    digerleri = [m for m in live_module_names() if "SWEEP" not in m]
    if not digerleri:
        pytest.skip("canli listede sweep-disi modul yok (NQ_ORB 2026-09-04'te dusuruldu)")
    ex.open_for_signal(_pozisyon(digerleri[0]), 100_000.0)
    lot_diger = istemci.gonderilen[-1]["volume"]

    assert lot_sweep == lot_diger, (
        f"sweep hala farkli boyutlaniyor: {lot_sweep} vs {lot_diger}")


@patch("intraday.forward_ea.order_executor.mt5_io.resolve", return_value="XAUUSD")
def test_PAPER_modul_gercek_emir_ALAMAZ(_resolve, istemci):
    ex = OrderExecutor(client=istemci, live_modules={PAPER}, phase="bnpl_challenge")
    sonuc = ex.open_for_signal(_pozisyon(PAPER), 100_000.0)
    assert sonuc["action"] == "skip"
    assert "PAPER" in sonuc["reason"]
    assert not istemci.gonderilen


@patch("intraday.forward_ea.order_executor.mt5_io.resolve", return_value="XAUUSD")
def test_kazanc_sonrasi_BOOST_gercek_emirde_kullanilmaz(_resolve, istemci):
    """Politikada kazanc sonrasi %3 var; otomatik emir kendi kaldiracini artirmaz."""
    from intraday.signalbot.risk import risk_plan

    plan = risk_plan(phase="bnpl_challenge", balance=100_000.0, module_name=LIVE,
                     module_weight=1.0, symbol_key="XAUUSD", entry=2400.0, sl=2390.0)
    assert plan.winner_usd > plan.normal_usd, "test varsayimi: boost var"

    ex = OrderExecutor(client=istemci, phase="bnpl_challenge")
    ex.open_for_signal(_pozisyon(), 100_000.0)
    lot = istemci.gonderilen[-1]["volume"]
    beklenen = ex.lot_for("XAUUSD", 2400.0, 2390.0, plan.normal_usd)
    assert lot == beklenen


@patch("intraday.forward_ea.order_executor.mt5_io.resolve", return_value="XAUUSD")
def test_gunluk_stop_PROFILDEN_gelir(_resolve):
    _, profil = profile_for("bnpl_challenge")
    esik = profil.daily_stop_pct
    istemci = SahteMT5(equity=100_000.0)
    ex = OrderExecutor(client=istemci, phase="bnpl_challenge")
    ex._get_day_start_equity()  # gun basi equity'yi 100k olarak kilitle

    istemci.account_info_data.equity = 100_000.0 * (1 - esik - 0.005)
    halt, sebep = ex._daily_dd_halt()
    assert halt, f"gunluk stop tetiklenmedi (esik {esik:.1%})"
    assert "Gunluk stop" in sebep


@patch("intraday.forward_ea.order_executor.mt5_io.resolve", return_value="XAUUSD")
def test_haftalik_stop_ENGELLER(_resolve):
    _, profil = profile_for("bnpl_challenge")
    if profil.weekly_stop_pct <= 0:
        pytest.skip("profilde haftalik stop yok")
    istemci = SahteMT5(equity=100_000.0)
    ex = OrderExecutor(client=istemci, phase="bnpl_challenge")
    ex._get_week_start_equity()

    # Gunluk esigi asmadan haftalik esigi as: gun basi equity'yi bugune esitle
    istemci.account_info_data.equity = 100_000.0 * (1 - profil.weekly_stop_pct - 0.005)
    ex._day_start_equity.clear()
    ex._get_day_start_equity()

    halt, sebep = ex._weekly_dd_halt()
    assert halt and "Haftalik stop" in sebep


@patch("intraday.forward_ea.order_executor.mt5_io.resolve", return_value="XAUUSD")
def test_toplam_acik_risk_TAVANI_uygulanir(_resolve, istemci):
    from intraday.forward_ea.order_executor import MAGIC
    from intraday.signalbot.risk import risk_plan

    plan = risk_plan(phase="bnpl_challenge", balance=100_000.0, module_name=LIVE,
                     module_weight=1.0, symbol_key="XAUUSD", entry=2400.0, sl=2390.0)
    kac = int(plan.max_open_risk_pct / plan.normal_pct) + 1
    istemci.positions_data = [
        SimpleNamespace(magic=MAGIC, symbol="XAUUSD", comment="x", ticket=i)
        for i in range(kac)
    ]
    ex = OrderExecutor(client=istemci, phase="bnpl_challenge")
    sonuc = ex.open_for_signal(_pozisyon(), 100_000.0)
    assert sonuc["action"] == "skip"
    assert "Toplam acik risk" in sonuc["reason"]
    assert not istemci.gonderilen


@patch("intraday.forward_ea.order_executor.mt5_io.resolve", return_value="XAUUSD")
def test_funded_fazi_daha_kucuk_lot_verir(_resolve):
    """Faz farkindaligi yoktu: funded %0.5 profili emir yoluna hic ulasmiyordu."""
    a, b = SahteMT5(), SahteMT5()
    OrderExecutor(client=a, phase="bnpl_challenge").open_for_signal(_pozisyon(), 100_000.0)
    OrderExecutor(client=b, phase="bnpl_funded").open_for_signal(_pozisyon(), 100_000.0)
    assert a.gonderilen and b.gonderilen
    assert b.gonderilen[-1]["volume"] < a.gonderilen[-1]["volume"]
