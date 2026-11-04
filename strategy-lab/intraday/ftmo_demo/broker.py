"""FTMO Free Trial MT5 broker boundary.

This module is intentionally independent from the existing MavenTrade executor.
It only permits the explicitly configured FTMO Free Trial product and an MT5
account that reports DEMO mode. No signal generation or strategy policy lives
here.
"""

from __future__ import annotations

import argparse
import contextlib
import json
import math
import os
import subprocess
import sys
import threading
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_CEILING, ROUND_DOWN, ROUND_FLOOR, ROUND_HALF_UP
from pathlib import Path
from typing import Any, Callable, Literal
from zoneinfo import ZoneInfo


class BrokerError(RuntimeError):
    """A safety or broker validation failure."""


class UncertainExecution(BrokerError):
    """A send may have reached the server; it must never be blindly retried."""


@dataclass(frozen=True)
class FTMOConfig:
    terminal_path: Path
    login: int
    server: str
    product: Literal["free_trial"]
    magic: int = 26101601
    deviation_points: int = 20
    max_tick_age_seconds: int = 60
    daily_request_limit: int = 1500
    execution_enabled: bool = False
    approved_free_trial_login: int | None = None
    approved_free_trial_server: str | None = None

    def __post_init__(self) -> None:
        if self.product != "free_trial":
            raise ValueError("Yalnız product='free_trial' desteklenir.")
        if self.login <= 0 or not self.server.strip():
            raise ValueError("login ve server zorunludur.")
        if self.magic <= 0:
            raise ValueError("magic pozitif olmalı.")
        if self.daily_request_limit <= 0 or self.max_tick_age_seconds <= 0:
            raise ValueError("günlük request sınırı ve tick yaşı pozitif olmalı.")
        object.__setattr__(self, "terminal_path", Path(self.terminal_path))


@dataclass(frozen=True)
class OrderPlan:
    symbol: str
    side: Literal["buy", "sell"]
    volume: float
    entry: float
    stop: float
    risk_amount: float
    estimated_stop_loss: float
    comment: str
    cost_reserve: float = 0.0
    take_profit: float = 0.0


def _same_path(left: str | os.PathLike[str], right: str | os.PathLike[str]) -> bool:
    return os.path.normcase(os.path.abspath(os.fspath(left))) == os.path.normcase(
        os.path.abspath(os.fspath(right))
    )


def _running_terminal_path(path: Path) -> bool:
    """Return true only when a running terminal process has this exact image path."""
    if os.name != "nt":
        return False
    # Query process executable paths before initialize(): MT5 initialize can
    # launch a terminal, so calling it before this check would violate policy.
    escaped = str(path.resolve()).replace("'", "''")
    command = (
        "$p=Get-CimInstance Win32_Process -Filter \"name='terminal64.exe' OR name='terminal.exe'\";"
        f"$p | Where-Object {{$_.ExecutablePath -ieq '{escaped}'}} | Select-Object -First 1 -ExpandProperty ExecutablePath"
    )
    try:
        result = subprocess.run(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", command],
            capture_output=True,
            text=True,
            timeout=8,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    return (
        result.returncode == 0
        and bool(result.stdout.strip())
        and _same_path(result.stdout.strip(), path)
    )


def _mt5_default():
    try:
        import MetaTrader5 as mt5
    except ImportError as exc:  # pragma: no cover - machine-specific dependency
        raise BrokerError("MetaTrader5 Python paketi kurulu değil.") from exc
    return mt5


class FTMOBroker:
    """Guarded MT5 client for a pinned FTMO Free Trial demo terminal."""

    def __init__(
        self,
        config: FTMOConfig,
        *,
        client: Any | None = None,
        state_path: Path | None = None,
        process_checker: Callable[[Path], bool] | None = None,
    ) -> None:
        self.config = config
        self.client = client if client is not None else _mt5_default()
        self.state_path = (
            Path(state_path)
            if state_path
            else Path.home() / ".ftmo_demo_broker_state.json"
        )
        self.process_checker = process_checker or _running_terminal_path
        self._connected = False
        self._halt_reason: str | None = None
        self._lock = threading.RLock()

    def connect(self) -> dict[str, Any]:
        """Connect only to an already-running pinned terminal and verify demo identity."""
        path = self.config.terminal_path
        if not path.is_file():
            raise BrokerError(f"Terminal dosyası bulunamadı: {path}")
        if not self.process_checker(path):
            raise BrokerError(
                "Pinned MT5 terminali açık değil; otomatik başlatma yapılmadı."
            )
        if not self.client.initialize(
            path=str(path),
            login=self.config.login,
            server=self.config.server,
            timeout=10_000,
            portable=False,
        ):
            raise BrokerError(f"MT5 bağlantısı kurulamadı: {self.client.last_error()}")
        terminal = self.client.terminal_info()
        account = self.client.account_info()
        if terminal is None or account is None:
            self.client.shutdown()
            raise BrokerError("Terminal/account bilgisi okunamadı.")
        actual_path = getattr(terminal, "path", None)
        actual_login = getattr(account, "login", None)
        actual_server = getattr(account, "server", None)
        demo_mode = getattr(self.client, "ACCOUNT_TRADE_MODE_DEMO", 0)
        if not actual_path or not self._terminal_path_matches(actual_path, path):
            self.client.shutdown()
            raise BrokerError("Bağlı terminal yolu pinned terminal ile eşleşmiyor.")
        if actual_login != self.config.login or actual_server != self.config.server:
            self.client.shutdown()
            raise BrokerError("Bağlı MT5 login/server yapılandırmayla eşleşmiyor.")
        if getattr(account, "trade_mode", None) != demo_mode:
            self.client.shutdown()
            raise BrokerError(
                "Hesap demo trade_mode bildirmiyor; işlem yolu kilitlendi."
            )
        try:
            self._validate_ftmo_account(account)
        except BrokerError:
            self.client.shutdown()
            raise
        self._connected = True
        return {
            "terminal_path": actual_path,
            "login": actual_login,
            "server": actual_server,
            "trade_mode": getattr(account, "trade_mode"),
        }

    def _require_ready(self) -> None:
        if not self._connected:
            raise BrokerError("Önce connect() ile terminal kimliğini doğrulayın.")
        if self._halt_reason:
            raise BrokerError(f"İşlem kilidi etkin: {self._halt_reason}")
        terminal = self.client.terminal_info()
        account = self.client.account_info()
        if (
            terminal is None
            or account is None
            or not getattr(terminal, "connected", False)
        ):
            raise BrokerError("MT5 bağlantısı hazır değil.")
        if not getattr(terminal, "trade_allowed", False) or not getattr(
            account, "trade_allowed", False
        ):
            raise BrokerError("Terminal veya hesap işlem izni vermiyor.")
        if getattr(terminal, "tradeapi_disabled", False):
            raise BrokerError("Terminal trade API devre dışı.")
        if getattr(account, "trade_expert", True) is False:
            raise BrokerError("Hesap uzman danisman islemlerine izin vermiyor.")
        if getattr(account, "trade_mode", None) != getattr(
            self.client, "ACCOUNT_TRADE_MODE_DEMO", 0
        ):
            raise BrokerError("Demo hesap modu değişti; işlem yolu kilitlendi.")
        self._validate_ftmo_account(account)
        terminal_path = getattr(terminal, "path", None)
        if not terminal_path or not self._terminal_path_matches(
            terminal_path, self.config.terminal_path
        ):
            raise BrokerError("Bağlı terminal pinned path ile eşleşmiyor.")
        if (
            getattr(account, "login", None) != self.config.login
            or getattr(account, "server", None) != self.config.server
        ):
            raise BrokerError("Aktif login/server yapılandırmayla eşleşmiyor.")
        unresolved = [
            key
            for key, value in self._load_state().items()
            if isinstance(value, dict)
            and (
                value.get("status") in ("uncertain", "sending", "sent")
                or str(value.get("status", "")).startswith("halted")
            )
        ]
        if unresolved:
            raise BrokerError(
                f"Önce belirsiz emir/işlem reconcile edilmeli: {unresolved[0]}"
            )

    def _require_execution(self) -> None:
        if self.config.product != "free_trial" or not self.config.execution_enabled:
            raise BrokerError(
                "Emir yürütme kapalı. FTMO Free Trial için gözetimli mikro testte açıkça etkinleştirin."
            )
        if (
            self.config.approved_free_trial_login != self.config.login
            or self.config.approved_free_trial_server != self.config.server
        ):
            raise BrokerError(
                "Bu login/server için kullanıcı onaylı Free Trial kanıtı yok; emir kilitli."
            )

    @staticmethod
    def _terminal_path_matches(actual: str, expected: Path) -> bool:
        # terminal_info.path is the terminal data/install directory on MT5 builds.
        return _same_path(actual, expected) or _same_path(actual, expected.parent)

    def _validate_ftmo_account(self, account: Any) -> None:
        if str(getattr(account, "currency", "")).upper() != "USD":
            raise BrokerError(
                "Bu uygulama yalnız USD FTMO Free Trial hesabı için etkin."
            )
        identity = " ".join(
            (str(getattr(account, "company", "")), str(getattr(account, "server", "")))
        ).casefold()
        if "ftmo" not in identity:
            raise BrokerError("Broker/server FTMO olarak doğrulanamadı.")
        if (
            getattr(account, "login", None) != self.config.login
            or getattr(account, "server", None) != self.config.server
        ):
            raise BrokerError("Aktif login/server yapılandırmayla eşleşmiyor.")

    def _require_manage_ready(self) -> None:
        """Validate the exact demo identity while allowing position-risk cleanup during a halt."""
        if not self._connected:
            raise BrokerError("Önce connect() ile terminal kimliğini doğrulayın.")
        terminal, account = self.client.terminal_info(), self.client.account_info()
        if (
            terminal is None
            or account is None
            or not getattr(terminal, "connected", False)
        ):
            raise BrokerError("MT5 bağlantısı hazır değil.")
        if not getattr(terminal, "trade_allowed", False) or getattr(
            terminal, "tradeapi_disabled", False
        ):
            raise BrokerError("Terminal işlem izni vermiyor.")
        if not getattr(account, "trade_allowed", False):
            raise BrokerError("Hesap işlem izni vermiyor.")
        if getattr(account, "trade_mode", None) != getattr(
            self.client, "ACCOUNT_TRADE_MODE_DEMO", 0
        ):
            raise BrokerError("Demo hesap modu değişti.")
        self._validate_ftmo_account(account)
        if not self._terminal_path_matches(
            getattr(terminal, "path", ""), self.config.terminal_path
        ):
            raise BrokerError("Bağlı terminal pinned path ile eşleşmiyor.")

    def inspect(self, symbols: tuple[str, ...] = ()) -> dict[str, Any]:
        """Read-only account and symbol inspection; does not call trade methods."""
        if not self._connected:
            raise BrokerError("Önce connect() ile terminal kimliğini doğrulayın.")
        terminal = self.client.terminal_info()
        account = self.client.account_info()
        if terminal is None or account is None:
            raise BrokerError("Terminal/account bilgisi okunamadı.")
        symbol_data: dict[str, Any] = {}
        for symbol in symbols:
            info = self.client.symbol_info(symbol)
            tick = self.client.symbol_info_tick(symbol)
            symbol_data[symbol] = {
                "available": info is not None,
                "visible": getattr(info, "visible", None),
                "digits": getattr(info, "digits", None),
                "point": getattr(info, "point", None),
                "trade_tick_size": getattr(info, "trade_tick_size", None),
                "volume_min": getattr(info, "volume_min", None),
                "volume_max": getattr(info, "volume_max", None),
                "volume_step": getattr(info, "volume_step", None),
                "trade_contract_size": getattr(info, "trade_contract_size", None),
                "bid": getattr(tick, "bid", None),
                "ask": getattr(tick, "ask", None),
                "tick_time": getattr(tick, "time", None),
            }
        return {
            "product": self.config.product,
            "terminal_path": getattr(terminal, "path", None),
            "login": getattr(account, "login", None),
            "server": getattr(account, "server", None),
            "account_name": getattr(account, "name", None),
            "trade_mode": getattr(account, "trade_mode", None),
            "currency": getattr(account, "currency", None),
            "balance": getattr(account, "balance", None),
            "equity": getattr(account, "equity", None),
            "terminal_connected": getattr(terminal, "connected", None),
            "terminal_trade_allowed": getattr(terminal, "trade_allowed", None),
            "account_trade_allowed": getattr(account, "trade_allowed", None),
            "symbols": symbol_data,
        }

    def size_order(
        self,
        symbol: str,
        side: Literal["buy", "sell"],
        entry: float,
        stop: float,
        risk_amount: float,
        *,
        cost_reserve: float = 0.0,
        signal_id: str = "preview",
        take_profit: float | None = None,
    ) -> OrderPlan:
        """Size with MT5's account-currency profit calculation and round down."""
        self._require_ready()
        if side not in ("buy", "sell") or not all(
            map(math.isfinite, (entry, stop, risk_amount, cost_reserve))
        ):
            raise BrokerError("side/fiyat/risk girdisi geçersiz.")
        if take_profit is not None and (
            not math.isfinite(take_profit) or take_profit <= 0
        ):
            raise BrokerError("Take profit pozitif ve sonlu olmalı.")
        if (
            entry <= 0
            or stop <= 0
            or entry == stop
            or risk_amount <= 0
            or cost_reserve < 0
        ):
            raise BrokerError(
                "Fiyat ve risk girdileri pozitif, stop entry'den farklı olmalı."
            )
        if (side == "buy" and stop >= entry) or (side == "sell" and stop <= entry):
            raise BrokerError("Stop yönü pozisyon tarafıyla uyumsuz.")
        if take_profit is not None and (
            (side == "buy" and take_profit <= entry)
            or (side == "sell" and take_profit >= entry)
        ):
            raise BrokerError("Take profit yönü pozisyon tarafıyla uyumsuz.")
        budget = risk_amount - cost_reserve
        if budget <= 0:
            raise BrokerError("Maliyet rezervi risk bütçesini tüketiyor.")
        info = self.client.symbol_info(symbol)
        if info is None:
            raise BrokerError(f"Sembol bulunamadı: {symbol}")
        price_step = float(
            getattr(info, "trade_tick_size", 0) or getattr(info, "point", 0) or 0
        )
        if price_step <= 0:
            raise BrokerError("Sembol tick size geçersiz.")
        entry = self._snap_price(entry, price_step, ROUND_HALF_UP)
        stop = self._snap_price(
            stop, price_step, ROUND_FLOOR if side == "buy" else ROUND_CEILING
        )
        if take_profit is not None:
            take_profit = self._snap_price(
                take_profit, price_step, ROUND_CEILING if side == "buy" else ROUND_FLOOR
            )
        if entry == stop or (take_profit is not None and take_profit == entry):
            raise BrokerError(
                "Tick boyutuna yuvarlama giriş/stop/TP seviyelerini çakıştırdı."
            )
        if (side == "buy" and stop >= entry) or (side == "sell" and stop <= entry):
            raise BrokerError("Tick boyutuna yuvarlama sonrası stop yönü geçersiz.")
        if not getattr(info, "visible", True) and not self.client.symbol_select(
            symbol, True
        ):
            raise BrokerError(f"Sembol Market Watch'a eklenemedi: {symbol}")
        volume_min = float(getattr(info, "volume_min", 0) or 0)
        volume_step = float(getattr(info, "volume_step", 0) or 0)
        volume_max = float(getattr(info, "volume_max", 0) or 0)
        if min(volume_min, volume_step, volume_max) <= 0:
            raise BrokerError("Broker hacim limitleri geçersiz.")
        order_type = (
            self.client.ORDER_TYPE_BUY if side == "buy" else self.client.ORDER_TYPE_SELL
        )
        one_lot_pnl = self.client.order_calc_profit(
            order_type, symbol, 1.0, entry, stop
        )
        if (
            one_lot_pnl is None
            or not math.isfinite(float(one_lot_pnl))
            or float(one_lot_pnl) >= 0
        ):
            raise BrokerError("1 lot stop zararı hesaplanamadı veya zarar üretmiyor.")
        loss_per_lot = abs(float(one_lot_pnl))
        raw = budget / loss_per_lot
        bounded = min(raw, volume_max)
        step = Decimal(str(volume_step))
        volume = (Decimal(str(bounded)) / step).to_integral_value(
            rounding=ROUND_DOWN
        ) * step
        if volume < Decimal(str(volume_min)):
            raise BrokerError("Risk bütçesine uygun hacim broker minimumunun altında.")
        comment = self._comment(signal_id)
        return OrderPlan(
            symbol,
            side,
            float(volume),
            float(entry),
            float(stop),
            float(risk_amount),
            float(volume) * loss_per_lot,
            comment,
            float(cost_reserve),
            float(take_profit or 0.0),
        )

    def submit(self, plan: OrderPlan, signal_id: str) -> dict[str, Any]:
        """Check then submit once; ambiguous outcomes persist as uncertain and halt."""
        with self._lock, self._process_lock():
            return self._submit_locked(plan, signal_id)

    @contextlib.contextmanager
    def _process_lock(self):
        """Serialize submit across threads and processes; crash releases OS lock."""
        lock_path = self.state_path.with_suffix(self.state_path.suffix + ".lock")
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        with lock_path.open("a+b") as stream:
            stream.seek(0)
            if os.name == "nt":
                import msvcrt

                if stream.read(1) == b"":
                    stream.seek(0)
                    stream.write(b"0")
                    stream.flush()
                stream.seek(0)
                msvcrt.locking(stream.fileno(), msvcrt.LK_LOCK, 1)
                try:
                    yield
                finally:
                    stream.seek(0)
                    msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:  # pragma: no cover - Windows is the target runtime
                import fcntl

                fcntl.flock(stream.fileno(), fcntl.LOCK_EX)
                try:
                    yield
                finally:
                    fcntl.flock(stream.fileno(), fcntl.LOCK_UN)

    def _submit_locked(self, plan: OrderPlan, signal_id: str) -> dict[str, Any]:
        self._require_ready()
        self._require_execution()
        if plan.comment != self._comment(signal_id):
            raise BrokerError(
                "Plan signal_id ile aynı deterministic comment değerini taşımıyor."
            )
        state = self._load_state()
        key = self._key(signal_id)
        existing = state.get(key)
        if existing:
            if existing.get("status") == "uncertain":
                raise UncertainExecution(
                    "Önce reconcile() gerekir; otomatik tekrar gönderim yasak."
                )
            raise BrokerError(
                "Bu signal_id daha önce işlendi; duplicate emir engellendi."
            )
        all_positions = self.client.positions_get()
        all_orders = self.client.orders_get()
        if all_positions is None or all_orders is None:
            raise BrokerError("Pozisyon/emir listesi okunamadi; yeni emir engellendi.")
        foreign = [
            p for p in all_positions if getattr(p, "magic", None) != self.config.magic
        ]
        if foreign:
            raise BrokerError(
                "Yönetilmeyen/foreign pozisyon var; yeni emirler engellendi."
            )
        same_symbol = [p for p in all_positions if p.symbol == plan.symbol]
        if same_symbol:
            raise BrokerError(
                "Aynı sembolde açık pozisyon var; netting/hedging çakışması engellendi."
            )
        foreign_orders = [
            o for o in all_orders if getattr(o, "magic", None) != self.config.magic
        ]
        if foreign_orders:
            raise BrokerError(
                "Yönetilmeyen/foreign bekleyen emir var; yeni emirler engellendi."
            )
        tick = self.client.symbol_info_tick(plan.symbol)
        if tick is None:
            raise BrokerError("Güncel tick yok.")
        tick_time = int(getattr(tick, "time", 0) or 0)
        if (
            tick_time <= 0
            or abs(datetime.now(timezone.utc).timestamp() - tick_time)
            > self.config.max_tick_age_seconds
        ):
            raise BrokerError("Tick eski veya zaman damgası yok.")
        info = self.client.symbol_info(plan.symbol)
        if info is None:
            raise BrokerError("Sembol bilgisi yok.")
        price = float(tick.ask if plan.side == "buy" else tick.bid)
        if not math.isfinite(price) or price <= 0:
            raise BrokerError("Guncel fiyat sonlu ve pozitif olmali.")
        price_step = float(
            getattr(info, "trade_tick_size", 0) or getattr(info, "point", 0) or 0
        )
        if price_step <= 0:
            raise BrokerError("Sembol tick size geçersiz.")
        normalized_stop = self._snap_price(
            plan.stop, price_step, ROUND_FLOOR if plan.side == "buy" else ROUND_CEILING
        )
        normalized_tp = (
            self._snap_price(
                plan.take_profit,
                price_step,
                ROUND_CEILING if plan.side == "buy" else ROUND_FLOOR,
            )
            if plan.take_profit
            else 0.0
        )
        if normalized_stop != plan.stop or normalized_tp != plan.take_profit:
            plan = OrderPlan(
                plan.symbol,
                plan.side,
                plan.volume,
                plan.entry,
                normalized_stop,
                plan.risk_amount,
                plan.estimated_stop_loss,
                plan.comment,
                plan.cost_reserve,
                normalized_tp,
            )
        point = float(getattr(info, "point", 0) or 0)
        minimum_stop_distance = (
            float(getattr(info, "trade_stops_level", 0) or 0) * point
        )
        if point <= 0 or abs(price - plan.stop) < minimum_stop_distance:
            raise BrokerError("SL broker minimum stop mesafesini karşılamıyor.")
        if plan.take_profit:
            if (plan.side == "buy" and plan.take_profit <= price) or (
                plan.side == "sell" and plan.take_profit >= price
            ):
                raise BrokerError("Güncel fiyat TP seviyesini geçti.")
            if abs(price - plan.take_profit) < minimum_stop_distance:
                raise BrokerError("TP broker minimum stop mesafesini karşılamıyor.")
        live_type = (
            self.client.ORDER_TYPE_BUY
            if plan.side == "buy"
            else self.client.ORDER_TYPE_SELL
        )
        one_lot_loss = self.client.order_calc_profit(
            live_type, plan.symbol, 1.0, price, plan.stop
        )
        budget = plan.risk_amount - plan.cost_reserve
        step = Decimal(str(getattr(info, "volume_step", 0)))
        minimum = Decimal(str(getattr(info, "volume_min", 0)))
        maximum = Decimal(str(getattr(info, "volume_max", 0)))
        if one_lot_loss is None or float(one_lot_loss) >= 0 or budget <= 0 or step <= 0:
            raise BrokerError("Güncel fiyatla stop riski hesaplanamadı.")
        sized = (
            Decimal(str(budget / abs(float(one_lot_loss)))) / step
        ).to_integral_value(rounding=ROUND_DOWN) * step
        volume = min(Decimal(str(plan.volume)), maximum, sized)
        if volume < minimum:
            raise BrokerError(
                "Güncel quote sonrası risk bütçesi minimum hacmin altında."
            )
        plan = OrderPlan(
            plan.symbol,
            plan.side,
            float(volume),
            price,
            plan.stop,
            plan.risk_amount,
            float(volume) * abs(float(one_lot_loss)),
            plan.comment,
            plan.cost_reserve,
            plan.take_profit,
        )
        request = {
            "action": self.client.TRADE_ACTION_DEAL,
            "symbol": plan.symbol,
            "volume": plan.volume,
            "type": (
                self.client.ORDER_TYPE_BUY
                if plan.side == "buy"
                else self.client.ORDER_TYPE_SELL
            ),
            "price": price,
            "sl": plan.stop,
            "tp": plan.take_profit,
            "deviation": self.config.deviation_points,
            "magic": self.config.magic,
            "comment": plan.comment,
            "type_time": self.client.ORDER_TIME_GTC,
            "type_filling": self._filling(info),
        }
        self._consume_server_request(state, 2)
        check = self.client.order_check(request)
        if check is None or getattr(check, "retcode", None) not in (
            0,
            getattr(self.client, "TRADE_RETCODE_DONE", 10009),
        ):
            raise BrokerError(f"order_check reddetti: {check!r}")
        state[key] = {
            "signal_id": signal_id,
            "comment": plan.comment,
            "status": "sending",
            "symbol": plan.symbol,
            "stop": plan.stop,
            "take_profit": plan.take_profit,
            "volume": plan.volume,
        }
        self._save_state(state)
        try:
            result = self.client.order_send(request)
        except Exception as exc:
            state[key]["status"] = "uncertain"
            state[key]["error"] = str(exc)
            self._save_state(state)
            self._halt_reason = f"emir yanıtı belirsiz: {signal_id}"
            raise UncertainExecution(self._halt_reason) from exc
        if result is None:
            state[key]["status"] = "uncertain"
            self._save_state(state)
            self._halt_reason = f"emir yanıtı belirsiz: {signal_id}"
            raise UncertainExecution(self._halt_reason)
        retcode = getattr(result, "retcode", None)
        done = getattr(self.client, "TRADE_RETCODE_DONE", 10009)
        partial = getattr(self.client, "TRADE_RETCODE_DONE_PARTIAL", 10010)
        if retcode not in (done, partial):
            # A concrete server rejection is terminal for this signal ID.
            state[key].update(status="rejected", retcode=retcode)
            self._save_state(state)
            raise BrokerError(f"order_send reddetti: retcode={retcode}")
        ticket = getattr(result, "order", None) or getattr(result, "deal", None)
        state[key].update(status="sent", ticket=ticket, retcode=retcode)
        self._save_state(state)
        position = self._find_position(plan.symbol, plan.comment)
        tolerance = float(getattr(info, "point", 0) or 0) / 2
        sl_ok = position is not None and self._sl_matches(
            getattr(position, "sl", 0), plan.stop, tolerance
        )
        tp_ok = position is not None and (
            not plan.take_profit
            or self._sl_matches(getattr(position, "tp", 0), plan.take_profit, tolerance)
        )
        if not sl_ok or not tp_ok:
            self._emergency_close(plan, position)
            state[key]["status"] = "halted_no_broker_sl"
            self._save_state(state)
            self._halt_reason = f"broker SL/TP doğrulanamadı: {signal_id}"
            raise BrokerError(self._halt_reason)
        actual_volume = float(
            getattr(position, "volume", getattr(result, "volume", plan.volume))
        )
        actual_entry = float(getattr(position, "price_open", price))
        actual_loss = self.client.order_calc_profit(
            (
                self.client.ORDER_TYPE_BUY
                if plan.side == "buy"
                else self.client.ORDER_TYPE_SELL
            ),
            plan.symbol,
            actual_volume,
            actual_entry,
            plan.stop,
        )
        if (
            actual_loss is None
            or not math.isfinite(float(actual_loss))
            or float(actual_loss) >= 0
            or abs(float(actual_loss)) > plan.risk_amount - plan.cost_reserve + 1e-7
        ):
            self._emergency_close(plan, position)
            state[key]["status"] = "halted_risk_exceeded"
            self._save_state(state)
            self._halt_reason = f"gerçekleşen hacim stop riskini aşıyor: {signal_id}"
            raise BrokerError(self._halt_reason)
        state[key].update(
            status="confirmed", position_ticket=getattr(position, "ticket", ticket)
        )
        self._save_state(state)
        return {
            "status": "confirmed",
            "ticket": state[key]["position_ticket"],
            "retcode": retcode,
            "volume": actual_volume,
            "sl": getattr(position, "sl"),
            "fill_status": "partial" if retcode == partial else "filled",
        }

    def reconcile(self, signal_id: str) -> dict[str, Any]:
        """Inspect broker state for a previous signal; never resubmits it."""
        self._require_connected()
        state = self._load_state()
        key = self._key(signal_id)
        record = state.get(key)
        if not record:
            return {"status": "not_found"}
        if record.get("status") not in ("uncertain", "sending", "sent"):
            return {"status": record.get("status"), "record": record}
        comment = record["comment"]
        orders = self.client.orders_get() or ()
        positions = self.client.positions_get() or ()
        now = datetime.now(timezone.utc)
        deals = self.client.history_deals_get(now - timedelta(days=7), now) or ()
        matched = [
            x
            for x in (*orders, *positions, *deals)
            if getattr(x, "magic", None) == self.config.magic
            and getattr(x, "comment", "") == comment
        ]
        if matched:
            found_position = next(
                (
                    p
                    for p in positions
                    if getattr(p, "comment", "") == comment
                    and getattr(p, "magic", None) == self.config.magic
                ),
                None,
            )
            if found_position is not None:
                tolerance = (
                    float(
                        getattr(
                            self.client.symbol_info(found_position.symbol), "point", 0
                        )
                        or 0
                    )
                    / 2
                )
                sl_ok = self._sl_matches(
                    getattr(found_position, "sl", 0),
                    float(record.get("stop", 0)),
                    tolerance,
                )
                target = float(record.get("take_profit", 0) or 0)
                tp_ok = not target or self._sl_matches(
                    getattr(found_position, "tp", 0), target, tolerance
                )
                if not sl_ok or not tp_ok:
                    self._halt_reason = f"broker SL/TP doğrulanamadı: {signal_id}"
                    return {"status": "halted_no_broker_sl", "requires_operator": True}
            record["status"] = (
                "confirmed"
                if found_position is not None
                else "broker_match_no_open_position"
            )
            record["ticket"] = getattr(found_position or matched[0], "ticket", None)
            if found_position is not None:
                record["position_ticket"] = getattr(found_position, "ticket", None)
            self._save_state(state)
            if record["status"] == "confirmed":
                self._halt_reason = None
            return {
                "status": record["status"],
                "ticket": record["ticket"],
                "position_ticket": record.get("position_ticket"),
            }
        record["status"] = "uncertain"
        self._save_state(state)
        self._halt_reason = (
            f"emir broker geçmişinde kesinleşmedi: {signal_id}; tekrar gönderim yasak"
        )
        return {
            "status": "uncertain",
            "requires_operator": True,
            "reason": self._halt_reason,
        }

    def close_position(self, position_ticket: int) -> dict[str, Any]:
        """Close one bot-owned position by exact ticket; refuse foreign positions."""
        with self._lock, self._process_lock():
            return self._close_position_locked(position_ticket)

    def _close_position_locked(self, position_ticket: int) -> dict[str, Any]:
        self._require_manage_ready()
        self._require_execution()
        positions = [
            p
            for p in (self.client.positions_get() or ())
            if getattr(p, "ticket", None) == position_ticket
        ]
        if (
            len(positions) != 1
            or getattr(positions[0], "magic", None) != self.config.magic
        ):
            raise BrokerError("Pozisyon yok veya bu broker katmanına ait değil.")
        position = positions[0]
        tick, info = self.client.symbol_info_tick(
            position.symbol
        ), self.client.symbol_info(position.symbol)
        if tick is None or info is None:
            raise BrokerError("Kapatma için tick/sembol bilgisi yok.")
        is_buy = (
            getattr(position, "type", self.client.ORDER_TYPE_BUY)
            == self.client.ORDER_TYPE_BUY
        )
        request = {
            "action": self.client.TRADE_ACTION_DEAL,
            "symbol": position.symbol,
            "position": position_ticket,
            "volume": float(position.volume),
            "type": (
                self.client.ORDER_TYPE_SELL if is_buy else self.client.ORDER_TYPE_BUY
            ),
            "price": float(tick.bid if is_buy else tick.ask),
            "deviation": self.config.deviation_points,
            "magic": self.config.magic,
            "comment": f"FT-close-{position_ticket}",
            "type_time": self.client.ORDER_TIME_GTC,
            "type_filling": self._filling(info),
        }
        state = self._load_state()
        operation_key = f"_manage_close_{position_ticket}"
        if state.get(operation_key):
            raise BrokerError(
                "Bu kapatma için daha önce istek gönderildi; reconcile gerekli."
            )
        self._consume_server_request(state, 2)
        check = self.client.order_check(request)
        if check is None or getattr(check, "retcode", None) not in (
            0,
            getattr(self.client, "TRADE_RETCODE_DONE", 10009),
        ):
            raise BrokerError(f"Kapatma order_check reddetti: {check!r}")
        state[operation_key] = {"status": "sending", "ticket": position_ticket}
        self._save_state(state)
        try:
            result = self.client.order_send(request)
        except Exception as exc:
            state[operation_key]["status"] = "uncertain"
            self._save_state(state)
            self._halt_reason = f"kapatma yanıtı belirsiz: {position_ticket}"
            raise UncertainExecution(self._halt_reason) from exc
        if result is None or getattr(result, "retcode", None) != getattr(
            self.client, "TRADE_RETCODE_DONE", 10009
        ):
            state[operation_key]["status"] = "uncertain"
            self._save_state(state)
            self._halt_reason = f"kapatma sonucu belirsiz: {position_ticket}"
            raise UncertainExecution(self._halt_reason)
        state[operation_key]["status"] = "confirmed"
        self._save_state(state)
        return {
            "status": "close_sent",
            "ticket": position_ticket,
            "retcode": getattr(result, "retcode", None),
        }

    def cancel_order(self, order_ticket: int) -> dict[str, Any]:
        """Cancel one bot-owned pending order by exact ticket."""
        with self._lock, self._process_lock():
            return self._cancel_order_locked(order_ticket)

    def _cancel_order_locked(self, order_ticket: int) -> dict[str, Any]:
        self._require_manage_ready()
        self._require_execution()
        orders = [
            o
            for o in (self.client.orders_get() or ())
            if getattr(o, "ticket", None) == order_ticket
        ]
        if len(orders) != 1 or getattr(orders[0], "magic", None) != self.config.magic:
            raise BrokerError("Bekleyen emir yok veya bu broker katmanına ait değil.")
        request = {
            "action": self.client.TRADE_ACTION_REMOVE,
            "order": order_ticket,
            "magic": self.config.magic,
        }
        state = self._load_state()
        operation_key = f"_manage_cancel_{order_ticket}"
        if state.get(operation_key):
            raise BrokerError(
                "Bu iptal için daha önce istek gönderildi; reconcile gerekli."
            )
        self._consume_server_request(state, 2)
        check = self.client.order_check(request)
        if check is None or getattr(check, "retcode", None) not in (
            0,
            getattr(self.client, "TRADE_RETCODE_DONE", 10009),
        ):
            raise BrokerError(f"İptal order_check reddetti: {check!r}")
        state[operation_key] = {"status": "sending", "ticket": order_ticket}
        self._save_state(state)
        try:
            result = self.client.order_send(request)
        except Exception as exc:
            state[operation_key]["status"] = "uncertain"
            self._save_state(state)
            self._halt_reason = f"iptal yanıtı belirsiz: {order_ticket}"
            raise UncertainExecution(self._halt_reason) from exc
        if result is None or getattr(result, "retcode", None) != getattr(
            self.client, "TRADE_RETCODE_DONE", 10009
        ):
            state[operation_key]["status"] = "uncertain"
            self._save_state(state)
            self._halt_reason = f"iptal sonucu belirsiz: {order_ticket}"
            raise UncertainExecution(self._halt_reason)
        state[operation_key]["status"] = "confirmed"
        self._save_state(state)
        return {
            "status": "cancel_sent",
            "ticket": order_ticket,
            "retcode": getattr(result, "retcode", None),
        }

    def _require_connected(self) -> None:
        if not self._connected:
            raise BrokerError("Önce connect() ile terminal kimliğini doğrulayın.")

    @staticmethod
    def _sl_matches(actual: Any, requested: float, tolerance: float = 1e-7) -> bool:
        try:
            return float(actual or 0) > 0 and math.isclose(
                float(actual), requested, rel_tol=0, abs_tol=max(1e-7, tolerance)
            )
        except (TypeError, ValueError):
            return False

    @staticmethod
    def _snap_price(value: float, step: float, rounding: str) -> float:
        quantum = Decimal(str(step))
        return float(
            (Decimal(str(value)) / quantum).to_integral_value(rounding=rounding)
            * quantum
        )

    def _consume_server_request(self, state: dict[str, Any], amount: int = 1) -> None:
        day_key = (
            "_daily_requests_"
            + datetime.now(ZoneInfo("Europe/Prague")).date().isoformat()
        )
        count = int(state.get(day_key, 0))
        if count + amount > min(1500, self.config.daily_request_limit):
            self._halt_reason = "günlük server request güvenlik sınırı doldu"
            raise BrokerError(self._halt_reason)
        state[day_key] = count + amount
        self._save_state(state)

    def _find_position(self, symbol: str, comment: str):
        return next(
            (
                p
                for p in (self.client.positions_get(symbol=symbol) or ())
                if getattr(p, "magic", None) == self.config.magic
                and getattr(p, "comment", "") == comment
            ),
            None,
        )

    def _emergency_close(self, plan: OrderPlan, position: Any | None) -> None:
        if position is None:
            self._halt_reason = (
                "pozisyon/SL doğrulanamadı; otomatik close hedefi bulunamadı"
            )
            return
        tick = self.client.symbol_info_tick(plan.symbol)
        if tick is None:
            self._halt_reason = "SL eksik ve tick yok; acil close gönderilemedi"
            return
        is_buy = (
            getattr(position, "type", self.client.ORDER_TYPE_BUY)
            == self.client.ORDER_TYPE_BUY
        )
        request = {
            "action": self.client.TRADE_ACTION_DEAL,
            "symbol": plan.symbol,
            "position": getattr(position, "ticket"),
            "volume": float(getattr(position, "volume")),
            "type": (
                self.client.ORDER_TYPE_SELL if is_buy else self.client.ORDER_TYPE_BUY
            ),
            "price": float(tick.bid if is_buy else tick.ask),
            "deviation": self.config.deviation_points,
            "magic": self.config.magic,
            "comment": f"{plan.comment}-close",
            "type_time": self.client.ORDER_TIME_GTC,
            "type_filling": self._filling(self.client.symbol_info(plan.symbol)),
        }
        try:
            state = self._load_state()
            self._consume_server_request(state, 2)
            checked = self.client.order_check(request)
            if checked is not None and getattr(checked, "retcode", None) in (
                0,
                getattr(self.client, "TRADE_RETCODE_DONE", 10009),
            ):
                self.client.order_send(request)
        except Exception as exc:
            self._halt_reason = f"acil close başarısız: {exc}"

    def _filling(self, info: Any) -> int:
        mode = int(getattr(info, "filling_mode", 0) or 0)
        ioc_flag = int(getattr(self.client, "SYMBOL_FILLING_IOC", 2))
        fok_flag = int(getattr(self.client, "SYMBOL_FILLING_FOK", 1))
        if mode & ioc_flag:
            return int(getattr(self.client, "ORDER_FILLING_IOC", 1))
        if mode & fok_flag:
            return int(getattr(self.client, "ORDER_FILLING_FOK", 0))
        execution = int(getattr(info, "trade_exemode", -1))
        if execution != int(getattr(self.client, "SYMBOL_TRADE_EXECUTION_MARKET", 2)):
            return int(getattr(self.client, "ORDER_FILLING_RETURN", 2))
        raise BrokerError("Sembol için uyumlu order filling mode bulunamadı.")

    @staticmethod
    def _key(signal_id: str) -> str:
        if not signal_id or len(signal_id) > 120:
            raise BrokerError("signal_id boş veya çok uzun.")
        return signal_id

    def _comment(self, signal_id: str) -> str:
        import hashlib

        digest = hashlib.sha256(signal_id.encode("utf-8")).hexdigest()[:16]
        return f"FT{self.config.magic % 100000:05d}{digest}"[:31]

    def _load_state(self) -> dict[str, Any]:
        try:
            return json.loads(self.state_path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return {}
        except (OSError, json.JSONDecodeError) as exc:
            self._halt_reason = f"kalıcı execution state okunamadı: {exc}"
            raise BrokerError(self._halt_reason) from exc

    def _save_state(self, state: dict[str, Any]) -> None:
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.state_path.with_suffix(self.state_path.suffix + ".tmp")
        tmp.write_text(json.dumps(state, indent=2, sort_keys=True), encoding="utf-8")
        tmp.replace(self.state_path)


def _cli() -> int:
    parser = argparse.ArgumentParser(
        description="MT5 read-only inspect / FTMO Free Trial adapter"
    )
    sub = parser.add_subparsers(dest="command", required=True)
    discover = sub.add_parser(
        "discover", help="Açık terminali credential olmadan oku; emir göndermez"
    )
    discover.add_argument("--terminal-path", required=True, type=Path)
    discover.add_argument("--symbol", action="append", default=[])
    inspect = sub.add_parser(
        "inspect", help="Hesap ve sembol bilgilerini oku; emir göndermez"
    )
    inspect.add_argument("--terminal-path", required=True, type=Path)
    inspect.add_argument("--login", required=True, type=int)
    inspect.add_argument("--server", required=True)
    inspect.add_argument("--product", required=True, choices=("free_trial",))
    inspect.add_argument("--symbol", action="append", default=[])
    args = parser.parse_args()
    if args.command == "discover":
        try:
            result = read_only_inspect(args.terminal_path, tuple(args.symbol))
            print(json.dumps(result, indent=2, default=str))
            return 0 if result.get("connected") else 1
        except BrokerError as exc:
            print(f"HATA: {exc}", file=sys.stderr)
            return 2
    broker = FTMOBroker(
        FTMOConfig(args.terminal_path, args.login, args.server, args.product)
    )
    try:
        broker.connect()
        print(json.dumps(broker.inspect(tuple(args.symbol)), indent=2, default=str))
        return 0
    except BrokerError as exc:
        print(f"HATA: {exc}", file=sys.stderr)
        return 2
    finally:
        if broker._connected:
            broker.client.shutdown()


def read_only_inspect(
    terminal_path: Path,
    symbols: tuple[str, ...] = (),
    *,
    client: Any | None = None,
    process_checker: Callable[[Path], bool] | None = None,
) -> dict[str, Any]:
    """Read an already-running terminal without known login/server credentials."""
    mt5 = client if client is not None else _mt5_default()
    path = Path(terminal_path)
    checker = process_checker or _running_terminal_path
    if not path.is_file():
        return {"connected": False, "error": f"Terminal dosyası bulunamadı: {path}"}
    if not checker(path):
        return {
            "connected": False,
            "error": "Pinned terminal açık değil; otomatik başlatma yapılmadı.",
        }
    if not mt5.initialize(path=str(path), timeout=10_000, portable=False):
        return {
            "connected": False,
            "terminal_path": str(path),
            "error": str(mt5.last_error()),
        }
    try:
        terminal, account = mt5.terminal_info(), mt5.account_info()
        if terminal is None:
            return {
                "connected": False,
                "terminal_path": str(path),
                "error": str(mt5.last_error()),
            }
        result: dict[str, Any] = {
            "connected": bool(getattr(terminal, "connected", False)),
            "terminal_path": getattr(terminal, "path", None),
            "terminal_trade_allowed": getattr(terminal, "trade_allowed", None),
        }
        if not terminal.path or not FTMOBroker._terminal_path_matches(
            terminal.path, path
        ):
            result.update(
                connected=False,
                error="Bağlı terminal path verilen terminal ile eşleşmiyor.",
            )
            return result
        if account is None:
            result["account_error"] = str(mt5.last_error())
            return result
        result.update(
            {
                "login": getattr(account, "login", None),
                "server": getattr(account, "server", None),
                "account_name": getattr(account, "name", None),
                "trade_mode": getattr(account, "trade_mode", None),
                "currency": getattr(account, "currency", None),
                "balance": getattr(account, "balance", None),
                "equity": getattr(account, "equity", None),
            }
        )
        result["symbols"] = {}
        for symbol in symbols:
            info, tick = mt5.symbol_info(symbol), mt5.symbol_info_tick(symbol)
            result["symbols"][symbol] = {
                "available": info is not None,
                "digits": getattr(info, "digits", None),
                "point": getattr(info, "point", None),
                "volume_min": getattr(info, "volume_min", None),
                "volume_step": getattr(info, "volume_step", None),
                "volume_max": getattr(info, "volume_max", None),
                "bid": getattr(tick, "bid", None),
                "ask": getattr(tick, "ask", None),
                "tick_time": getattr(tick, "time", None),
            }
        return result
    finally:
        mt5.shutdown()


if __name__ == "__main__":  # pragma: no cover - CLI integration
    raise SystemExit(_cli())
