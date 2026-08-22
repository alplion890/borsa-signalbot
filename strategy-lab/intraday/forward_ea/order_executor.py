"""Real MetaTrader5 order execution layer for forward-test trading EA.

Converts paper-trade signals from Book into actual broker orders, keeping the
broker's open positions in sync with the paper Book. Strategy-agnostic: works
with any signal from any strategy module.

Safety design:
  - Fully unit-testable via injectable MT5 client (duck-typed wrapper).
  - Guarded by trade_allowed flags, volume constraints, daily DD halt, dup check.
  - Only whitelisted live_modules send real orders; others stay paper-only.
  - Never raises on broker rejection — returns action='error' + retcode.

Example:
    from intraday.forward_ea.order_executor import OrderExecutor
    from intraday.forward_ea.positions import Book

    executor = OrderExecutor()  # Uses real MetaTrader5 module
    with mt5_io.session():
        book = load_book()  # Load paper positions
        results = executor.reconcile(book)  # Sync broker <-> paper
        for result in results:
            print(f"{result['module']} {result['action']} {result.get('ticket')}")
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from math import floor
from pathlib import Path
from typing import Any

from .positions import Book, PaperPosition
from ..mt5_bridge import mt5_io
from ..signalbot.risk import live_module_names, profile_for, risk_plan

# Magic number for all real orders placed by this EA
MAGIC = 202600

# Modules allowed to place REAL orders. Everything else => paper only.
#
# Derived from risk.py, never hand-maintained here. This list used to be a
# second copy and it drifted on 2026-08-06: risk.py dropped the eliminated
# GOLD_NY_ORB_TREND and added SWEEP_CORE_AVOID_MID_VWAP, this copy did not.
# The result was that the eliminated module could place real orders while the
# strongest one could not. One fact, one place.
LIVE_MODULES: set[str] = set(live_module_names())


@dataclass(frozen=True)
class ExecConfig:
    """Emir icra ayarlari.

    RISK ALANLARI BILEREK YOK. Lot buyuklugu ve hesap koruma esikleri
    `signalbot/risk.py`'den gelir -- TEK kaynak. Burada ikinci bir kopya
    tutulmasi 2026-08-21'de tespit edildi: bu dosya kendi `risk_pct=1.5`,
    `sweep_risk_pct=2.25`, `daily_dd_halt_pct=4.5` degerlerini tasiyordu; faz
    (challenge/funded) farkindaligi, PAPER modul korumasi, toplam acik risk
    tavani, haftalik stop hicbiri yoktu. Whitelist'te AYNI hata olmustu
    (commit 57bbb04): iki elle yazilmis kopya, biri guncellendi otekisi
    unutuldu, elenmis modul gercek emir atabilir kaldi.

    Buradaki alanlar yalnizca ICRA mekanigidir -- politika degil.
    """

    deviation_points: int = 20  # max slippage in points for order_send
    magic: int = MAGIC


def _get_default_client():
    """Lazy import of MetaTrader5 (only on Windows; tests inject fake)."""
    try:
        import MetaTrader5 as mt5

        return mt5
    except ModuleNotFoundError:
        # Tests will have already injected a fake into sys.modules
        import sys

        if "MetaTrader5" in sys.modules:
            return sys.modules["MetaTrader5"]
        raise


class OrderExecutor:
    """Real MT5 order execution for paper trade signals."""

    def __init__(
        self,
        client=None,
        config: ExecConfig = ExecConfig(),
        live_modules: set[str] | None = None,
        phase: str | None = None,
    ):
        """Initialize executor.

        Args:
            client: MT5 client (duck-typed wrapper). Defaults to real MetaTrader5.
            config: ExecConfig with risk/sizing parameters.
            live_modules: Set of module names allowed to trade real. Defaults to LIVE_MODULES.
        """
        self.client = client if client is not None else _get_default_client()
        self.config = config
        self.live_modules = live_modules if live_modules is not None else LIVE_MODULES
        # Faz (challenge/funded) risk profilini secer. Ortamdan okunur ki
        # signalbot'un karti ile emir yolu ayni profili gorsun.
        self.phase = phase or os.environ.get("PHASE", "bnpl_challenge")
        self._day_start_equity: dict[str, float] = {}  # UTC date -> start_equity
        self._week_start_equity: dict[str, float] = {}  # ISO hafta -> start_equity

    @property
    def profile(self):
        """Aktif faz risk profili -- politikanin TEK kaynagi."""
        _, profile = profile_for(self.phase)
        return profile

    def lot_for(
        self, broker_name: str, entry: float, sl: float, risk_amount: float
    ) -> float:
        """Calculate position size in lots to risk ~risk_amount if SL is hit.

        Formula: loss_per_lot = (|entry-sl| / tick_size) * tick_value
                 lot = risk_amount / loss_per_lot
        Then clamp to [volume_min, volume_max] and round DOWN to volume_step.

        Args:
            broker_name: MT5 symbol name (e.g., "XAUUSD", "USTEC")
            entry: Entry price
            sl: Stop-loss price
            risk_amount: Maximum loss per trade in account currency

        Returns:
            Lot size (0.0 if below volume_min, clamped to volume_max).
        """
        if entry == sl:
            return 0.0

        info = self.client.symbol_info(broker_name)
        if info is None:
            return 0.0

        tick_size = info.trade_tick_size
        tick_value = info.trade_tick_value
        vol_min = info.volume_min
        vol_step = info.volume_step
        vol_max = info.volume_max

        if tick_size <= 0 or tick_value <= 0:
            return 0.0

        risk_in_ticks = abs(entry - sl) / tick_size
        loss_per_lot = risk_in_ticks * tick_value

        if loss_per_lot <= 0:
            return 0.0

        lot = risk_amount / loss_per_lot

        # Clamp to broker limits
        if lot < vol_min:
            return 0.0
        if lot > vol_max:
            lot = vol_max

        # Round down to volume_step (asla oversize etme — prop guvenligi)
        lot = floor(lot / vol_step) * vol_step

        # Final check after rounding
        return lot if lot >= vol_min else 0.0

    def can_trade(self) -> tuple[bool, str]:
        """Check if trading is allowed.

        Returns: (allowed, reason)
            allowed: True if both terminal.trade_allowed and account.trade_allowed
            reason: "OK" or description of block
        """
        terminal_info = self.client.terminal_info()
        account_info = self.client.account_info()

        if not terminal_info or not account_info:
            return False, "Terminal or account info unavailable"

        if not terminal_info.trade_allowed:
            return False, "Terminal: Algo trading disabled"

        if not account_info.trade_allowed:
            return False, "Account: Trading disabled"

        return True, "OK"

    def _get_day_start_equity(self) -> float:
        """Get (and cache) start-of-day equity for DD halt tracking.

        Stores in outputs/intraday/forward_ea/exec_day.json keyed by UTC date.
        Returns current equity if not yet cached for today.
        """
        account = self.client.account_info()
        if account is None:
            return 0.0

        today_utc = datetime.now(timezone.utc).date().isoformat()
        day_file = (
            Path(__file__).resolve().parent.parent.parent
            / "outputs"
            / "intraday"
            / "forward_ea"
            / "exec_day.json"
        )
        day_file.parent.mkdir(parents=True, exist_ok=True)

        # Load existing
        if day_file.exists():
            data = json.loads(day_file.read_text(encoding="utf-8"))
        else:
            data = {}

        if today_utc not in data:
            data[today_utc] = account.equity
            day_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
            return account.equity

        return data[today_utc]

    def _daily_dd_halt(self) -> tuple[bool, str]:
        """Check if daily drawdown halt should block new trades.

        Returns: (halt, reason)
            halt: True if daily loss exceeds daily_dd_halt_pct
            reason: description or empty string
        """
        account = self.client.account_info()
        if account is None:
            return False, ""

        start_equity = self._get_day_start_equity()
        if start_equity <= 0:
            return False, ""

        day_loss_pct = (start_equity - account.equity) / start_equity * 100.0
        limit = self.profile.daily_stop_pct * 100.0
        if day_loss_pct > limit:
            return True, f"Gunluk stop {day_loss_pct:.1f}% > {limit:.1f}% ({self.phase})"

        return False, ""

    def _weekly_dd_halt(self) -> tuple[bool, str]:
        """Haftalik stop -- risk.py profilinden.

        Gunluk stop tek gunu korur; ust uste uc kotu gun gunluk esigi hic
        asmadan haftalik butceyi bitirebilir. Profil bu esigi tasiyordu ama
        emir yolu hic okumuyordu.
        """
        account = self.client.account_info()
        if account is None:
            return False, ""

        start_equity = self._get_week_start_equity()
        if start_equity <= 0:
            return False, ""

        week_loss_pct = (start_equity - account.equity) / start_equity * 100.0
        limit = self.profile.weekly_stop_pct * 100.0
        if limit > 0 and week_loss_pct > limit:
            return True, f"Haftalik stop {week_loss_pct:.1f}% > {limit:.1f}% ({self.phase})"

        return False, ""

    def _get_week_start_equity(self) -> float:
        """ISO haftasinin ilk gorulen equity'si (gunluk mekanizmanin aynisi)."""
        account = self.client.account_info()
        if account is None:
            return 0.0
        year, week, _ = datetime.now(timezone.utc).isocalendar()
        key = f"{year}-W{week:02d}"
        if key not in self._week_start_equity:
            self._week_start_equity[key] = account.equity
        return self._week_start_equity[key]

    def _open_risk_halt(self, plan) -> tuple[bool, str]:
        """Toplam acik risk tavani -- risk.py profilinden.

        Acik her pozisyon politika geregi `normal_pct` ile boyutlandirildi, o
        yuzden toplam risk = acik pozisyon sayisi x normal_pct olarak sayilir.
        Broker'dan lot/SL geri hesaplamak yerine politikaya guvenmek, yanlis
        yonde hata yapmaz: gercek risk bundan buyuk olamaz.
        """
        cap = plan.max_open_risk_pct * 100.0
        if cap <= 0:
            return False, ""
        ours = [p for p in (self.client.positions_get() or [])
                if getattr(p, "magic", None) == self.config.magic]
        planned = (len(ours) + 1) * plan.normal_pct * 100.0
        if planned > cap:
            return True, (f"Toplam acik risk {planned:.1f}% > {cap:.1f}% "
                          f"({len(ours)} acik pozisyon)")
        return False, ""

    def _position_exists(self, symbol: str, comment_module: str) -> bool:
        """Check if a position already exists with same magic+symbol+comment."""
        positions = self.client.positions_get(symbol=symbol)
        if not positions:
            return False

        for pos in positions:
            if pos.magic != self.config.magic:
                continue
            # Match comment (may be truncated by broker to ~31 chars)
            comment_short = comment_module[: self._comment_max_len()]
            if pos.comment.startswith(comment_short):
                return True

        return False

    @staticmethod
    def _comment_max_len() -> int:
        """MT5 broker comment limit (typically ~31 chars)."""
        return 31

    def open_for_signal(self, pos: PaperPosition, balance: float) -> dict:
        """Place a real market order matching a paper signal.

        Args:
            pos: PaperPosition freshly created from a signal
            balance: Current account balance (for risk calculation)

        Returns: dict with keys:
            'action': 'open'|'skip'|'error'
            'module': pos.module
            'symbol': pos.symbol
            'lot': float (if action='open')
            'retcode': int (if action='open' or 'error')
            'ticket': int (if action='open')
            'reason': str (if action != 'open')
        """
        # Guard: non-live module
        if pos.module not in self.live_modules:
            return {
                "action": "skip",
                "module": pos.module,
                "symbol": pos.symbol,
                "reason": f"Not in LIVE_MODULES: {pos.module}",
            }

        # Guard: trade_allowed
        ok, reason = self.can_trade()
        if not ok:
            return {
                "action": "skip",
                "module": pos.module,
                "symbol": pos.symbol,
                "reason": f"trade_allowed: {reason}",
            }

        # Guard: gunluk ve haftalik stop (ikisi de risk.py profilinden)
        halt, reason = self._daily_dd_halt()
        if not halt:
            halt, reason = self._weekly_dd_halt()
        if halt:
            return {
                "action": "skip",
                "module": pos.module,
                "symbol": pos.symbol,
                "reason": reason,
            }

        # Guard: symbol available
        try:
            broker_symbol = mt5_io.resolve(pos.symbol)
        except mt5_io.MT5Error as e:
            return {
                "action": "skip",
                "module": pos.module,
                "symbol": pos.symbol,
                "reason": f"UNAVAILABLE: {str(e)}",
            }

        # Guard: no duplicate open position
        if self._position_exists(broker_symbol, pos.module):
            return {
                "action": "skip",
                "module": pos.module,
                "symbol": pos.symbol,
                "reason": f"Position already open for {pos.module}",
            }

        # Risk buyuklugu risk.py'den -- burada ikinci bir politika YOK.
        # Eski hali modul adinda "SWEEP" arayip %2.25 veriyordu; o carpan
        # 2026-08-06'da politikadan kaldirilmisti ama burada yasamaya devam
        # etmisti.
        plan = risk_plan(
            phase=self.phase, balance=balance, module_name=pos.module,
            module_weight=pos.weight, symbol_key=pos.symbol,
            entry=pos.entry, sl=pos.sl,
        )
        if not plan.real_money_allowed:
            return {
                "action": "skip",
                "module": pos.module,
                "symbol": pos.symbol,
                "reason": f"PAPER tier: gercek risk sifir ({plan.profile_name})",
            }

        # Toplam acik risk tavani
        halt, reason = self._open_risk_halt(plan)
        if halt:
            return {"action": "skip", "module": pos.module,
                    "symbol": pos.symbol, "reason": reason}

        # DAIMA normal risk. Kazanc sonrasi %3'e cikan boost gercek emir
        # yolunda BILEREK kullanilmaz: kartta insan gorup onaylar, otomatik
        # emir kendi kendine kaldirac artiramaz.
        risk_amount = plan.normal_usd

        # Calculate lot
        lot = self.lot_for(broker_symbol, pos.entry, pos.sl, risk_amount)
        if lot == 0.0:
            return {
                "action": "skip",
                "module": pos.module,
                "symbol": pos.symbol,
                "lot": 0.0,
                "reason": f"lot < volume_min (risk_amount={risk_amount:.2f})",
            }

        # Get tick to determine entry price (ask for long, bid for short)
        tick = self.client.symbol_info_tick(broker_symbol)
        if tick is None or tick.ask <= 0 or tick.bid <= 0:
            return {
                "action": "error",
                "module": pos.module,
                "symbol": pos.symbol,
                "reason": "Cannot get bid/ask quotes",
            }

        entry_price = tick.ask if pos.direction == 1 else tick.bid

        # Build order request
        request = {
            "action": self.client.TRADE_ACTION_DEAL,
            "symbol": broker_symbol,
            "volume": lot,
            "type": (
                self.client.ORDER_TYPE_BUY if pos.direction == 1 else self.client.ORDER_TYPE_SELL
            ),
            "price": entry_price,
            "sl": pos.sl,
            "tp": pos.tp,
            "deviation": self.config.deviation_points,
            "magic": self.config.magic,
            "comment": pos.module[: self._comment_max_len()],
            "type_time": self.client.ORDER_TIME_GTC,
            "type_filling": self.client.ORDER_FILLING_IOC,
        }

        # Send order
        result = self.client.order_send(request)
        if result is None:
            return {
                "action": "error",
                "module": pos.module,
                "symbol": pos.symbol,
                "reason": "order_send returned None",
            }

        if result.retcode != self.client.TRADE_RETCODE_DONE:
            return {
                "action": "error",
                "module": pos.module,
                "symbol": pos.symbol,
                "lot": lot,
                "retcode": result.retcode,
                "reason": f"Broker rejected: {result.comment}",
            }

        return {
            "action": "open",
            "module": pos.module,
            "symbol": pos.symbol,
            "lot": lot,
            "retcode": result.retcode,
            "ticket": result.order,
            "reason": "OK",
        }

    def close_position(self, position) -> dict:
        """Market-close a single broker position object (opposite side, by ticket).

        Args:
            position: broker position object (has ticket, type, symbol, volume, comment)

        Returns: dict with 'action' ('close'|'error'), ticket, and reason
        """
        # Opposite side
        order_type = (
            self.client.ORDER_TYPE_SELL if position.type == self.client.POSITION_TYPE_BUY else self.client.ORDER_TYPE_BUY
        )

        # Get current quote for close price
        tick = self.client.symbol_info_tick(position.symbol)
        if tick is None or tick.ask <= 0 or tick.bid <= 0:
            return {
                "action": "error",
                "ticket": position.ticket,
                "reason": "Cannot get quotes for close",
            }

        # Use opposite side's quote
        close_price = tick.bid if order_type == self.client.ORDER_TYPE_SELL else tick.ask

        request = {
            "action": self.client.TRADE_ACTION_DEAL,
            "position": position.ticket,
            "symbol": position.symbol,
            "volume": position.volume,
            "type": order_type,
            "price": close_price,
            "deviation": self.config.deviation_points,
            "magic": self.config.magic,
            "comment": f"Close {position.comment}"[: self._comment_max_len()],
            "type_time": self.client.ORDER_TIME_GTC,
            "type_filling": self.client.ORDER_FILLING_IOC,
        }

        result = self.client.order_send(request)
        if result is None or result.retcode != self.client.TRADE_RETCODE_DONE:
            return {
                "action": "error",
                "ticket": position.ticket,
                "reason": f"Close rejected: {result.comment if result else 'None'}",
            }

        return {
            "action": "close",
            "ticket": position.ticket,
            "reason": "OK",
        }

    def reconcile(self, book: Book) -> list[dict]:
        """Sync broker positions with paper book for LIVE modules only.

        1. For every OPEN paper position in a live module: if no matching broker
           position exists (magic+symbol+comment), open it.
        2. For every BROKER position with our magic: if the paper book no longer
           has a matching OPEN position, close it.

        Called each cycle by live_runner. Reads balance once from account_info.

        Args:
            book: Book with open_positions list

        Returns: List of action dicts (one per open/close attempted)
        """
        account = self.client.account_info()
        if account is None:
            return [{"action": "error", "reason": "Cannot read account info"}]

        balance = account.balance
        results = []

        # 1. Open missing live positions
        for paper_pos in book.open_positions:
            if paper_pos.module not in self.live_modules:
                continue
            try:
                broker_symbol = mt5_io.resolve(paper_pos.symbol)
            except mt5_io.MT5Error:
                # Symbol unavailable, skip
                continue
            if not self._position_exists(broker_symbol, paper_pos.module):
                result = self.open_for_signal(paper_pos, balance)
                results.append(result)

        # 2. Close orphan broker positions (our magic, but no paper match)
        positions = self.client.positions_get()
        if positions:
            for broker_pos in positions:
                if broker_pos.magic != self.config.magic:
                    continue
                # Eslesme: broker comment (kisaltilmis olabilir) ile paper modul
                # adinin AYNI kisaltmasi + sembol broker-adi uzerinden karsilastirilir.
                # Boylece open tarafindaki truncation ile birebir tutarli ve
                # reverse-map'in sessiz fallback'i devreye girmez.
                broker_comment = broker_pos.comment.strip()
                has_paper_match = any(
                    p.module[: self._comment_max_len()] == broker_comment
                    and mt5_io.SYMBOL_MAP.get(p.symbol, p.symbol) == broker_pos.symbol
                    and p.status == "open"
                    for p in book.open_positions
                )
                if not has_paper_match:
                    result = self.close_position(broker_pos)
                    results.append(result)

        return results
