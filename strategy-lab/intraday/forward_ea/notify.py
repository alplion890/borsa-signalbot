"""Forward EA -> Telegram koprusu.

Yeni acilan paper pozisyonu, signalbot'un mesaj formatiyla (Maven emir karti
dahil) Telegram'a gonderir. Boylece MT5 verisiyle uretilen sinyal ANINDA
telefona duser; emri Maven kuralina uygun olarak SEN elle girersin.

Guvenlik/kurallar:
- Token/chat_id yalnizca env'den (telegram_notify ile ayni sozlesme).
- Env eksikse dongu KIRILMAZ: mesaj stdout'a yazilir, runner devam eder.
- Bayat sinyal filtresi: warmup/backfill sirasinda acilan eski pozisyonlar
  gonderilmez (MAX_AGE_MIN'den eski entry_time atlanir).
"""
from __future__ import annotations

import datetime as dt
import os

import pandas as pd

from ..signalbot import sessions, telegram_notify
from ..signalbot.message import format_signal
from ..signalbot.risk import risk_plan, tier_of
from .positions import PaperPosition

# Backfill spam korumasi: bundan eski entry_time'li pozisyon bildirilmez.
MAX_AGE_MIN = 30.0


def _age_minutes(entry_time: pd.Timestamp, now: dt.datetime) -> float:
    ts = pd.Timestamp(entry_time)
    if ts.tzinfo is None:
        ts = ts.tz_localize("UTC")
    return (now - ts.to_pydatetime()).total_seconds() / 60.0


def build_message(pos: PaperPosition, now: dt.datetime) -> str:
    """Tek pozisyondan signalbot formatinda Telegram mesaji uret."""
    phase = os.environ.get("PHASE", "bnpl_challenge")
    balance = float(os.environ.get("ACCOUNT_BALANCE", "5000"))
    plan = risk_plan(
        phase=phase, balance=balance, module_name=pos.module,
        module_weight=pos.weight, symbol_key=pos.symbol,
        entry=pos.entry, sl=pos.sl,
    )
    return format_signal(
        tier=tier_of(pos.module), module=pos.module, symbol_key=pos.symbol,
        direction=pos.direction, entry=pos.entry, sl=pos.sl, tp=pos.tp,
        lot=plan.normal_lot, risk_usd=plan.normal_usd, risk_plan=plan,
        trt_time=sessions.to_trt(now),
        signal_age_minutes=_age_minutes(pos.entry_time, now),
        data_source="mt5",
    )


def notify_new_positions(new_positions: list[PaperPosition],
                         now: dt.datetime | None = None,
                         send_fn=None) -> list[str]:
    """Taze pozisyonlari Telegram'a gonder; gonderilen mesajlari dondur.

    send_fn test enjeksiyonu icindir; None ise telegram_notify.send kullanilir.
    Gonderim hatasi donguyu kirmaz (stdout'a yazilir).
    """
    now = now or dt.datetime.now(dt.timezone.utc)
    sender = send_fn or telegram_notify.send
    sent: list[str] = []
    for pos in new_positions:
        age = _age_minutes(pos.entry_time, now)
        if age > MAX_AGE_MIN:
            continue  # backfill kalintisi, bildirme
        msg = build_message(pos, now)
        try:
            sender(msg)
        except Exception as e:  # env eksik / ag hatasi: dongu devam etsin
            print(f"  [TELEGRAM ATLA] {pos.module}: {e}")
            print(msg)
        sent.append(msg)
    return sent
