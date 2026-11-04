"""Independent FTMO demo runner. Default commands never transmit orders."""

from __future__ import annotations

import argparse
import hashlib
from dataclasses import asdict, replace
from datetime import datetime, timedelta, timezone
import json
import math
from pathlib import Path
import time

from . import policy
from .signals import MODULES, VERSION, closed_bars, latest_signal, strategy_hash
from .storage import Store, atomic_json, single_process, utc_now

DEFAULT_DIR = Path(__file__).resolve().parents[2] / "outputs/intraday/ftmo_demo"


def timestamp(value):
    result = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if result.tzinfo is None:
        raise ValueError("UTC ofseti zorunlu")
    return result.astimezone(timezone.utc)


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_calendar(path):
    data = read_json(path)
    events = []
    for event in data["events"]:
        identity = event["event_id"]
        if identity not in policy.KNOWN_RESTRICTED_EVENT_IDS:
            raise ValueError("Bilinmeyen resmi olay kimligi: " + str(identity))
        affected = set(event["affected_symbols"])
        if identity.startswith("USD_"):
            affected.update(("NASDAQ100", "SP500"))
        events.append(
            policy.RestrictedEvent(
                identity, timestamp(event["timestamp_utc"]), frozenset(affected)
            )
        )
    return policy.NewsCalendar(
        events,
        timestamp(data["generated_at_utc"]),
        timestamp(data["coverage_from_utc"]),
        timestamp(data["coverage_to_utc"]),
        data["source"],
        data["validated"] is True,
    )


def session_gate(data, symbol, now):
    """No guessed weekly sessions; explicit sourced UTC windows are mandatory."""
    if data.get("validated") is not True or not data.get("source", "").startswith(
        "https://ftmo.com/"
    ):
        return "unknown", None
    generated = timestamp(data["generated_at_utc"])
    if not timedelta(0) <= now - generated <= timedelta(hours=24):
        return "unknown", None
    windows = sorted(data.get("symbols", {}).get(symbol, []), key=lambda x: x["open"])
    for window in windows:
        opened, closes = timestamp(window["open"]), timestamp(window["close"])
        if opened <= now < closes:
            if closes - now <= timedelta(minutes=5):
                return "close", closes
            # Conservative v1: no entries during final two hours of ANY session.
            return ("blocked" if closes - now <= timedelta(hours=2) else "open"), closes
    return "closed", None


def verified_cost(info, client, symbol, side, price, config):
    costs = config["costs"][symbol]
    commission = float(costs["commission_roundtrip_per_lot"])
    slippage = float(costs["slippage_points"])
    max_spread = float(costs["max_spread_points"])
    if (
        not all(math.isfinite(v) and v >= 0 for v in (commission, slippage, max_spread))
        or max_spread <= 0
    ):
        raise ValueError("Dogrulanmis maliyet/spread esigi gerekli")
    adverse = (
        price - info.point * slippage
        if side == "buy"
        else price + info.point * slippage
    )
    loss = client.order_calc_profit(
        client.ORDER_TYPE_BUY if side == "buy" else client.ORDER_TYPE_SELL,
        symbol,
        1.0,
        price,
        adverse,
    )
    if loss is None or not math.isfinite(float(loss)):
        raise ValueError("Kayma maliyeti hesaplanamadi")
    return commission + abs(loss), max_spread


class DemoRunner:
    def __init__(self, config, directory, broker):
        self.config, self.directory, self.broker = config, Path(directory), broker
        self.client = broker.client
        self.store = Store(self.directory)

    def context(self, now):
        account = self.client.account_info()
        if account is None:
            raise ValueError("Hesap okunamadi")
        inception = timestamp(self.config["inception"])
        deals = self.client.history_deals_get(inception - timedelta(days=1), now)
        if deals is None:
            raise ValueError("Islem gecmisi okunamadi")
        raw = [dict(d._asdict()) for d in deals]
        rows = policy.history_records_from_mt5(
            raw, inception=inception, complete_through=now
        )
        history = policy.reconstruct_history(
            rows,
            complete_from=inception,
            complete_through=now,
            inception=inception,
            current_balance=account.balance,
        )
        snapshot = policy.AccountSnapshot(
            account.balance,
            account.equity,
            now,
            history.day_start_balance,
            history.closed_balance_high,
        )
        return account, raw, history, snapshot

    def positions(self):
        positions, orders = self.client.positions_get(), self.client.orders_get()
        if positions is None or orders is None:
            raise ValueError("Pozisyon/emir sorgusu basarisiz")
        return list(positions), list(orders)

    def exposures(self, positions):
        total, group = 0.0, 0.0
        details = []
        tracked = self.store.get("positions", {})
        for p in positions:
            if p.magic != self.broker.config.magic or str(p.ticket) not in tracked:
                raise ValueError("Yonetilmeyen pozisyon: yeni girisler kilitli")
            if not p.sl:
                raise ValueError("Stopsuz pozisyon: yeni girisler kilitli")
            tick, info = self.client.symbol_info_tick(
                p.symbol
            ), self.client.symbol_info(p.symbol)
            if tick is None or info is None:
                raise ValueError("Pozisyon fiyati okunamadi")
            side = "buy" if p.type == self.client.ORDER_TYPE_BUY else "sell"
            current = tick.bid if side == "buy" else tick.ask
            values = [
                self.client.order_calc_profit(p.type, p.symbol, p.volume, price, p.sl)
                for price in (p.price_open, current)
            ]
            if any(v is None or not math.isfinite(v) for v in values):
                raise ValueError("Acik stop riski hesaplanamadi")
            per_lot, _ = verified_cost(
                info, self.client, p.symbol, side, current, self.config
            )
            risk = max(0.0, *(-v for v in values)) + per_lot * p.volume
            total += risk
            key = tracked[str(p.ticket)]["symbol_key"]
            if key in ("NASDAQ100", "SP500"):
                group += risk
            details.append(
                {
                    "symbol": p.symbol,
                    "side": side,
                    "size": p.volume,
                    "risk": risk,
                    "value": risk,
                    "ticket": p.ticket,
                }
            )
        return total, group, details

    def close_owned(self, positions, orders, calendar, now, reason, execute):
        tracked = self.store.get("positions", {})
        for item, operation in [(p, "close") for p in positions] + [
            (o, "cancel") for o in orders
        ]:
            if item.magic != self.broker.config.magic:
                continue
            if operation == "close" and str(item.ticket) not in tracked:
                raise ValueError(
                    "Sahipsiz bot pozisyonu; operator uzlastirmasi gerekli"
                )
            key = next(
                (k for k, v in self.config["symbols"].items() if v == item.symbol),
                item.symbol,
            )
            news = policy.check_news(calendar, now=now, symbol=key, action="exit")
            known_restricted = any(
                key in e.affected_symbols
                and abs((e.timestamp_utc - now).total_seconds()) <= 120
                for e in calendar.events
            )
            if known_restricted or news.action in (
                policy.NewsAction.FORBID_EXECUTION,
                policy.NewsAction.BLOCK_UNKNOWN,
            ):
                self.store.event(
                    "critical_restricted_exit",
                    {"ticket": item.ticket, "reason": reason},
                )
                continue
            self.store.event(
                "protective_exit" if execute else "exit_preview",
                {"ticket": item.ticket, "reason": reason, "operation": operation},
            )
            if execute:
                result = (
                    self.broker.close_position(item.ticket)
                    if operation == "close"
                    else self.broker.cancel_order(item.ticket)
                )
                self.store.event("exit_result", result)

    def recover_intents(self, positions, deals=()):
        """Adopt only journaled own fills after a crash, never retry an intent."""
        tracked = self.store.get("positions", {})
        for identity, record in self.store.get("intents", {}).items():
            result = self.broker.reconcile(identity)
            if result["status"] in ("uncertain", "sending", "sent") or result[
                "status"
            ].startswith("halted"):
                raise ValueError(
                    "Belirsiz emir; operator uzlastirmasi gerekli: " + identity
                )
            ticket = result.get("ticket") or result.get("record", {}).get(
                "position_ticket"
            )
            found = next((p for p in positions if p.ticket == ticket), None)
            if found is not None and str(found.ticket) not in tracked:
                tracked[str(found.ticket)] = {
                    **record,
                    "identifier": getattr(found, "identifier", found.ticket),
                }
                self.store.event("recovered_fill", {"ticket": found.ticket}, identity)
            elif (
                found is None
                and ticket
                and result["status"] in ("confirmed", "broker_match_no_open_position")
            ):
                if any(r["id"] == identity for r in self.store.get("completed", [])):
                    continue
                comment = result.get("record", {}).get("comment")
                matches = [
                    d
                    for d in deals
                    if d.get("position_id") == ticket
                    or (
                        comment
                        and d.get("comment") == comment
                        and d.get("magic") == self.broker.config.magic
                    )
                ]
                if not matches:
                    raise ValueError(
                        "Tamamlanmis emir gecmisi uzlastirilamadi: " + identity
                    )
                identifier = matches[0]["position_id"]
                tracked[str(ticket)] = {**record, "identifier": identifier}
        self.store.set("positions", tracked)

    def cycle(self, *, execute=False, micro=False, now=None):
        live_clock = now is None
        now = now or utc_now()
        if (
            self.config["product"] != "free_trial"
            or self.config["strategy_hash"] != strategy_hash()
        ):
            raise ValueError("Hesap urunu veya sabit strateji hash degisti")
        # Revalidate identity on each cycle, including readonly cycles.
        identity = self.broker.inspect(tuple(self.config["symbols"].values()))
        if (
            identity["login"] != self.config["login"]
            or identity["server"] != self.config["server"]
        ):
            raise ValueError("Hesap kimligi degisti")
        if execute and self.store.get("halt"):
            raise ValueError("Kalici olay kilidi: " + str(self.store.get("halt")))
        if execute and not micro and not self.store.get("smoke_verified"):
            raise ValueError(
                "Once gozetimli micro komutuyla demo emir/stop/cikis dogrulanmali"
            )
        account, deals, history, snapshot = self.context(now)
        positions, orders = self.positions()
        self.recover_intents(positions, deals)
        input_blockers = []
        try:
            calendar = load_calendar(self.directory / "calendar.json")
        except (OSError, ValueError, KeyError, TypeError) as exc:
            input_blockers.append("Takvim: " + str(exc))
            calendar = policy.NewsCalendar((), now, now, now, "", False)
        try:
            sessions = read_json(self.directory / "sessions.json")
        except (OSError, ValueError, KeyError, TypeError) as exc:
            input_blockers.append("Seans: " + str(exc))
            sessions = {}
        for key, symbol in self.config["symbols"].items():
            if symbol not in self.config.get("costs", {}):
                input_blockers.append(symbol + ": dogrulanmis maliyetler eksik")
            if session_gate(sessions, key, now)[0] == "unknown":
                input_blockers.append(key + ": seans bilgisi eski/eksik")
            if (
                policy.check_news(
                    calendar, now=now, symbol=key, action="manage_open"
                ).action
                == policy.NewsAction.BLOCK_UNKNOWN
            ):
                input_blockers.append(key + ": takvim eski/eksik")
        tracked = self.store.get("positions", {})
        active_tickets = {str(p.ticket) for p in positions}
        # Broker history is authoritative; never infer fills from OHLC bars.
        for ticket, record in list(tracked.items()):
            if ticket not in active_tickets:
                related = [
                    d
                    for d in deals
                    if str(d.get("position_id")) == str(record["identifier"])
                ]
                exits = [d for d in related if d.get("entry") in (1, 2, 3)]
                if not exits:
                    raise ValueError("Kayip pozisyon gecmiste dogrulanamadi")
                net = sum(
                    float(d.get(k, 0) or 0)
                    for d in related
                    for k in ("profit", "commission", "swap", "fee")
                )
                completed = self.store.get("completed", [])
                completed.append(
                    {
                        **record,
                        "ticket": ticket,
                        "net": net,
                        "exit_time": max(d["time"] for d in exits),
                        "r": net / record["risk"],
                    }
                )
                self.store.set("completed", completed)
                self.store.event("position_closed", completed[-1], record["id"])
                del tracked[ticket]
        self.store.set("positions", tracked)
        daily_loss = snapshot.day_start_balance - account.equity
        daily_floor = snapshot.day_start_balance - 150.0
        max_floor = snapshot.closed_balance_high - 500.0
        day_key = now.astimezone(policy.PRAGUE).date().isoformat()
        if account.equity <= max_floor:
            self.store.set("firm_breach", {"at": now.isoformat(), "reason": "max_loss"})
        if account.equity <= daily_floor:
            self.store.set(
                "firm_breach", {"at": now.isoformat(), "reason": "daily_loss"}
            )
        if daily_loss >= 75.0:
            self.store.set("daily_stop", day_key)
        halt = bool(
            self.store.get("firm_breach")
            or self.store.get("daily_stop") == day_key
            or account.equity <= max(daily_floor, max_floor) + 50.0
        )
        if halt:
            self.close_owned(positions, orders, calendar, now, "risk_guard", execute)
        # Flatten before restricted news and before session closes; never remove SLs.
        exit_symbols = set()
        for key, symbol in self.config["symbols"].items():
            session, _ = session_gate(sessions, key, now)
            pre_news = any(
                key in e.affected_symbols
                and timedelta(minutes=2) < e.timestamp_utc - now <= timedelta(minutes=5)
                for e in calendar.events
            )
            if pre_news or session == "close":
                exit_symbols.add(symbol)
        if exit_symbols and not halt:
            self.close_owned(
                [p for p in positions if p.symbol in exit_symbols],
                [o for o in orders if o.symbol in exit_symbols],
                calendar,
                now,
                "news_or_session_exit",
                execute,
            )
        positions, orders = self.positions()
        exposure_error = None
        try:
            open_risk, group_risk, risk_rows = self.exposures(positions)
        except ValueError as exc:
            open_risk, group_risk, risk_rows = 0.0, 0.0, []
            exposure_error = str(exc)
        if orders:
            exposure_error = "Bekleyen emir var; yeni giris kilitli"
        missing_sl = [
            p for p in positions if p.magic == self.broker.config.magic and not p.sl
        ]
        if missing_sl:
            self.store.set("halt", "Broker stopu eksik; operator incelemesi gerekli")
            self.close_owned(
                missing_sl, [], calendar, now, "missing_broker_stop", execute
            )
            halt = True
        signals = []
        frames = {}
        for module, key in MODULES.items():
            try:
                frame = closed_bars(self.client, self.config["symbols"][key], now)
                frames[key] = frame
                bar_stamp = str(frame.index[-1])
                if self.store.get("exported:" + key) != bar_stamp:
                    export = self.directory / "bars"
                    export.mkdir(exist_ok=True)
                    csv = frame.to_csv(index_label="time")
                    (export / (key + ".csv")).write_text(csv, encoding="utf-8")
                    atomic_json(
                        export / (key + ".json"),
                        {
                            "source": "ftmo_mt5",
                            "server": self.config["server"],
                            "login": self.config["login"],
                            "symbol": self.config["symbols"][key],
                            "symbol_key": key,
                            "tf": "15m",
                            "time_basis": "UTC",
                            "observed_at": now.isoformat(),
                            "sha256": hashlib.sha256(csv.encode()).hexdigest(),
                            "strategy_hash": strategy_hash(),
                        },
                    )
                    self.store.set("exported:" + key, bar_stamp)
                signal = latest_signal(module, frame, now)
                if signal:
                    signals.append(signal)
            except Exception as exc:
                self.store.event("data_block", {"module": module, "reason": str(exc)})
        # Time exit only; broker SL/TP control price exits.
        if not halt:
            for p in positions:
                record = tracked.get(str(p.ticket))
                if record and record["symbol_key"] in frames:
                    import pandas as pd

                    frame = frames[record["symbol_key"]]
                    age_bars = int(
                        (
                            frame.index
                            > pd.Timestamp(record["bar_time"])
                            .tz_convert("UTC")
                            .tz_localize(None)
                        ).sum()
                    )
                    if age_bars >= 480:
                        self.close_owned(
                            [p], [], calendar, now, "480_bar_timeout", execute
                        )
        for signal in sorted(signals, key=lambda s: (s["bar_time"], s["module"])):
            seen_key = ("seen:" if execute else "preview:") + signal["id"]
            if self.store.get(seen_key):
                continue
            self.store.set(seen_key, True)
            signal.update(
                account={
                    "login": self.config["login"],
                    "server": self.config["server"],
                },
                source="ftmo_mt5",
                data_time=now.isoformat(),
                observations=self.observations(now),
                micro=micro,
            )
            try:
                if halt or exposure_error or input_blockers:
                    raise ValueError(
                        exposure_error
                        or "; ".join(input_blockers)
                        or "Ic risk durma kapisi"
                    )
                if any(
                    p.symbol == self.config["symbols"][signal["symbol_key"]]
                    for p in positions
                ):
                    raise ValueError("Sembolde mevcut pozisyon var")
                key = signal["symbol_key"]
                session, close_time = session_gate(sessions, key, now)
                news = policy.check_news(
                    calendar, now=now, symbol=key, market_close_at=close_time
                )
                if news.action != policy.NewsAction.ALLOW:
                    raise ValueError(news.reason)
                if session != "open":
                    raise ValueError("Dogrulanmis acik seans/gap kapisi uygun degil")
                symbol = self.config["symbols"][key]
                tick, info = self.client.symbol_info_tick(
                    symbol
                ), self.client.symbol_info(symbol)
                if tick is None or info is None or now.timestamp() - tick.time > 30:
                    raise ValueError("Guncel tick yok")
                side = "buy" if signal["direction"] == 1 else "sell"
                entry = tick.ask if side == "buy" else tick.bid
                per_lot, max_spread = verified_cost(
                    info, self.client, symbol, side, entry, self.config
                )
                if (tick.ask - tick.bid) / info.point > max_spread:
                    raise ValueError("Spread esigi asildi")
                one = self.client.order_calc_profit(
                    (
                        self.client.ORDER_TYPE_BUY
                        if side == "buy"
                        else self.client.ORDER_TYPE_SELL
                    ),
                    symbol,
                    1.0,
                    entry,
                    signal["sl"],
                )
                if one is None or not math.isfinite(one) or one >= 0:
                    raise ValueError("Stop riski gecersiz")
                budget = min(min(account.balance, account.equity) * 0.005, 25.0)
                reserve = budget * per_lot / (abs(one) + per_lot)
                plan = self.broker.size_order(
                    symbol,
                    side,
                    entry,
                    signal["sl"],
                    budget,
                    cost_reserve=reserve,
                    signal_id=signal["id"],
                    take_profit=signal["tp"],
                )
                if micro:
                    plan = replace(
                        plan,
                        volume=info.volume_min,
                        estimated_stop_loss=abs(one) * info.volume_min,
                        cost_reserve=per_lot * info.volume_min,
                    )
                    reserve = plan.cost_reserve
                decision = policy.evaluate_entry(
                    snapshot,
                    policy.RiskRequest(
                        plan.estimated_stop_loss,
                        reserve,
                        open_risk,
                        symbol=key,
                        group="NQ_SP" if key in ("NASDAQ100", "SP500") else "",
                    ),
                    daily_net_pnl=history.daily_net.get(
                        now.astimezone(policy.PRAGUE).date(), 0
                    ),
                    group_risk=group_risk,
                )
                if not decision.allowed:
                    raise ValueError(", ".join(decision.reasons))
                self.store.event(
                    "intent" if execute else "preview",
                    {**signal, "plan": asdict(plan), "risk": asdict(decision)},
                    signal["id"],
                )
                if execute:
                    send_now = utc_now() if live_clock else now
                    if (
                        policy.check_news(
                            calendar,
                            now=send_now,
                            symbol=key,
                            market_close_at=close_time,
                        ).action
                        != policy.NewsAction.ALLOW
                    ):
                        raise ValueError("Gonderim oncesi haber kapisi kapandi")
                    intents = self.store.get("intents", {})
                    intents[signal["id"]] = {
                        **signal,
                        "risk": plan.estimated_stop_loss + reserve,
                    }
                    self.store.set("intents", intents)
                    result = self.broker.submit(plan, signal["id"])
                    self.store.event("execution", result, signal["id"])
                    fresh, _ = self.positions()
                    matched = next(
                        (p for p in fresh if p.ticket == result["ticket"]), None
                    )
                    if matched is None:
                        raise ValueError("Yeni pozisyon kimligi uzlastirilamadi")
                    tracked[str(matched.ticket)] = {
                        **signal,
                        "identifier": getattr(matched, "identifier", matched.ticket),
                        "risk": plan.estimated_stop_loss + reserve,
                    }
                    self.store.set("positions", tracked)
                    if micro:
                        exit_news = policy.check_news(
                            calendar, now=utc_now(), symbol=key, action="exit"
                        )
                        if exit_news.action in (
                            policy.NewsAction.FORBID_EXECUTION,
                            policy.NewsAction.BLOCK_UNKNOWN,
                        ):
                            raise ValueError(
                                "Micro cikisi haber penceresine girdi; operator gerekli"
                            )
                        closed = self.broker.close_position(matched.ticket)
                        self.store.event("micro_close", closed, signal["id"])
                        remaining, _ = self.positions()
                        if any(p.ticket == matched.ticket for p in remaining):
                            raise ValueError("Micro pozisyon kapanisi dogrulanamadi")
                        self.store.set(
                            "smoke_verified",
                            {"at": utc_now().isoformat(), "signal_id": signal["id"]},
                        )
                        break
                    positions = fresh
                    open_risk, group_risk, risk_rows = self.exposures(positions)
            except Exception as exc:
                self.store.event(
                    "signal_block", {**signal, "reason": str(exc)}, signal["id"]
                )
                # Any send may have reached the broker: do not continue trading.
                from .broker import BrokerError

                if execute and (
                    isinstance(exc, BrokerError)
                    or signal["id"] in self.store.get("intents", {})
                ):
                    self.store.set("halt", str(exc))
                    raise
        completed = [
            row for row in self.store.get("completed", []) if not row.get("micro")
        ]
        cons = policy.consistency_status(
            history, cycle_start=timestamp(self.config["inception"])
        )
        first = min(
            (
                datetime.fromtimestamp(d["time"], timezone.utc)
                for d in deals
                if d["type"] in (0, 1)
            ),
            default=None,
        )
        days = (now - first).total_seconds() / 86400 if first else 0
        clean = (
            not self.store.get("firm_breach")
            and not self.store.get("halt")
            and not exposure_error
        )
        accepted = len(completed) >= 20 and days >= 14 and bool(clean)
        curve = self.store.get("equity_history", [])
        curve.append({"time": now.isoformat(), "value": account.equity})
        self.store.set("equity_history", curve[-5000:])
        module_rows = [
            {
                "name": name,
                "trades": sum(r["module"] == name for r in completed),
                "net": sum(r["net"] for r in completed if r["module"] == name),
                "r": sum(r["r"] for r in completed if r["module"] == name),
            }
            for name in MODULES
        ]
        status = {
            "updated_at": now.isoformat(),
            "source": "FTMO MT5 / " + VERSION,
            "status": (
                "RISK DURDU"
                if halt
                else (
                    exposure_error
                    or (
                        "GIRIS KILITLI"
                        if input_blockers
                        else ("DEMO EMIR ACIK" if execute else "EMIRSIZ KONTROL")
                    )
                )
            ),
            "account": {
                "label": f"{self.config['server']} / {self.config['login']}",
                "currency": "USD",
                "mode": "Free Trial",
            },
            "metrics": {
                "balance": account.balance,
                "equity": account.equity,
                "profit": history.net_trading_result,
                "consistency_pct": cons.ratio * 100 if cons.ratio is not None else None,
                "payout_ready": False,
                "accepted_trades": len(completed),
                "required_trades": 20,
                "technical_accepted": accepted,
                "paid_review_candidate": accepted
                and sum(r["net"] for r in completed) > 0,
                "eligible_days": int(days),
                "required_days": 14,
                "open_risk_usd": open_risk,
            },
            "modules": module_rows,
            "floors": [
                {"name": "Gunluk firma tabani", "value": daily_floor},
                {"name": "Hareketli firma tabani", "value": max_floor},
                {
                    "name": "Firma tabanina tampon",
                    "value": account.equity - max(daily_floor, max_floor),
                },
                {
                    "name": "Karin tamami cekilirse kalan tampon (tahmini)",
                    "value": account.equity
                    - max(0, history.net_trading_result)
                    - max_floor,
                },
            ],
            "equity_history": curve[-5000:],
            "open_risk": risk_rows,
            "notes": input_blockers
            + [
                "Free Trial gercek odeme yapmaz. Ucretli hesap otomatik acilmaz.",
                "20 islem / 14 gun teknik esiktir; karlilik kaniti degildir.",
                "Makro/trend/AI yalniz gozlem; emir kararini etkilemez.",
            ],
        }
        atomic_json(self.directory / "status.json", status)
        return status

    def observations(self, now):
        path = self.directory / "observations.json"
        if not path.exists():
            return {"available": False, "reason": "Makro/trend/AI gozlemi saglanmadi"}
        data = read_json(path)
        return {"available": True, "observed_at": now.isoformat(), "provided": data}


def build_broker(config, directory, *, execute=False):
    from .broker import FTMOConfig, FTMOBroker

    authorization = read_json(directory / "authorization.json") if execute else {}
    if execute:
        verify_authorization(authorization, config)
    broker = FTMOBroker(
        config=FTMOConfig(
            Path(config["terminal_path"]),
            config["login"],
            config["server"],
            config["product"],
            execution_enabled=execute,
            approved_free_trial_login=authorization.get("login"),
            approved_free_trial_server=authorization.get("server"),
        ),
        state_path=directory / "broker_state.json",
    )
    broker.connect()
    return broker


def verify_authorization(evidence, config):
    if (
        evidence.get("product") != "free_trial"
        or evidence.get("reviewed_by_user") is not True
        or evidence.get("login") != config["login"]
        or evidence.get("server") != config["server"]
        or not str(evidence.get("source", "")).startswith(
            ("https://trader.ftmo.com/", "https://ftmo.com/")
        )
        or not evidence.get("reference")
    ):
        raise ValueError(
            "Client Area Free Trial urunu ve hesap kimligi elle dogrulanmis yetki kaydi gerekli"
        )


def cli(argv=None):
    parser = argparse.ArgumentParser(
        description="FTMO Free Trial; varsayilan emirsizdir"
    )
    parser.add_argument("--directory", type=Path, default=DEFAULT_DIR)
    sub = parser.add_subparsers(dest="command", required=True)
    inspect = sub.add_parser("inspect")
    inspect.add_argument("--terminal-path", type=Path, required=True)
    enroll = sub.add_parser("enroll")
    enroll.add_argument("--terminal-path", type=Path, required=True)
    enroll.add_argument("--confirm-free-trial", action="store_true", required=True)
    enroll.add_argument(
        "--symbols",
        type=Path,
        required=True,
        help="Ic anahtar -> dogrulanmis broker sembolu JSON",
    )
    enroll.add_argument(
        "--inception", required=True, help="Ilk 5000 USD baslangic kaydinin UTC zamani"
    )
    enroll.add_argument(
        "--free-trial-evidence",
        type=Path,
        required=True,
        help="Client Area urunu ve hesap kimligi kullanici tarafindan kontrol edilmis JSON",
    )
    sub.add_parser(
        "micro",
        help="Gozetimli ilk gercek Sweep sinyalinde min lot demo giris ve hemen cikis; tek tur",
    )
    sub.add_parser("check")
    run = sub.add_parser("run")
    run.add_argument("--execute-demo", action="store_true")
    run.add_argument("--once", action="store_true")
    sub.add_parser("dashboard")
    args = parser.parse_args(argv)
    directory = args.directory.resolve()
    if args.command == "dashboard":
        from .dashboard import serve

        serve(directory / "status.json")
        return 0
    if args.command in ("inspect", "enroll"):
        from .broker import read_only_inspect

        data = read_only_inspect(args.terminal_path)
        print(json.dumps(data, ensure_ascii=False, indent=2, default=str))
        if args.command == "inspect":
            atomic_json(
                directory / "inspection.json",
                {**data, "observed_at": utc_now().isoformat()},
            )
            if not data.get("connected"):
                atomic_json(
                    directory / "status.json",
                    {
                        "updated_at": utc_now().isoformat(),
                        "source": "FTMO MT5",
                        "status": "BAGLANTI DOGRULANAMADI",
                        "notes": [
                            data.get("error", "Hesap okunamadi"),
                            "Hesap kaydi ve demo emir testi yapilmadi. Ucretli hesap etkin degil.",
                        ],
                    },
                )
            return 0 if data.get("connected") else 2
        if not data.get("connected") or not data.get("login"):
            raise ValueError("FTMO baglantisi dogrulanamadi; profil olusturulmadi")
        mapping = read_json(args.symbols)
        if set(mapping) != set(MODULES.values()) or len(set(mapping.values())) != 4:
            raise ValueError("Dort tekil Sweep sembolu gerekli")
        config = {
            "terminal_path": str(args.terminal_path.resolve()),
            "login": data["login"],
            "server": data["server"],
            "product": "free_trial",
            "inception": timestamp(args.inception).isoformat(),
            "symbols": mapping,
            "costs": {},
            "strategy_hash": strategy_hash(),
            "version": VERSION,
        }
        evidence = read_json(args.free_trial_evidence)
        verify_authorization(evidence, config)
        with single_process(directory):
            if (directory / "config.json").exists():
                raise ValueError("Mevcut hesap profili otomatik uzerine yazilmaz")
            broker = build_broker(config, directory)
            try:
                inspection = broker.inspect(tuple(mapping.values()))
                if any(
                    not item.get("available")
                    or not item.get("volume_step")
                    or not item.get("point")
                    for item in inspection["symbols"].values()
                ):
                    raise ValueError("FTMO sembol/kontrat bilgileri dogrulanamadi")
                atomic_json(directory / "inspection.json", inspection)
                atomic_json(directory / "config.json", config)
                atomic_json(directory / "authorization.json", evidence)
            finally:
                broker.client.shutdown()
        return 0
    config = read_json(directory / "config.json")
    execute = args.command == "micro" or (args.command == "run" and args.execute_demo)
    with single_process(directory):
        broker = build_broker(config, directory, execute=execute)
        runner = DemoRunner(config, directory, broker)
        try:
            while True:
                try:
                    status = runner.cycle(
                        execute=execute, micro=args.command == "micro"
                    )
                    print(json.dumps(status["metrics"], ensure_ascii=False))
                except Exception as exc:
                    runner.store.event("halt", {"reason": str(exc)})
                    atomic_json(
                        directory / "status.json",
                        {
                            "updated_at": utc_now().isoformat(),
                            "source": "FTMO MT5",
                            "status": "KILITLI",
                            "notes": [
                                str(exc),
                                "Yeni emirler engellendi; ucretli hesap etkin degil.",
                            ],
                        },
                    )
                    raise
                if args.command in ("check", "micro") or args.once:
                    break
                time.sleep(10)
        finally:
            runner.store.close()
            broker.client.shutdown()
    return 0


if __name__ == "__main__":
    raise SystemExit(cli())
