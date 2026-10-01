"""Phone watch alert for discretionary NQ review; never a trade signal."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import os
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd

from ..indicators import adx, atr, ema
from . import free_data, telegram_notify
from .mobile_chart import render_chart

UTC = dt.timezone.utc
NY = ZoneInfo("America/New_York")
TR = ZoneInfo("Europe/Istanbul")
STATE_PATH = Path(os.environ.get("MOBILE_WATCH_STATE_PATH", ".signalbot/mobile_watch.json"))
MAX_BAR_AGE_MINUTES = 35
NEAR_LEVEL_ATR = 0.5


def _closed(frame: pd.DataFrame, now: dt.datetime) -> pd.DataFrame:
    if frame.empty or frame.index.tz is None:
        return frame.iloc[:0]
    now_ts = pd.Timestamp(now).tz_convert(frame.index.tz)
    return frame.loc[frame.index + pd.Timedelta(minutes=15) <= now_ts]


def _ny_dates(index: pd.DatetimeIndex) -> pd.Index:
    return pd.Index(index.tz_convert(NY).date)


def _in_window(now: dt.datetime) -> bool:
    from .scan_schedule import is_open
    return is_open(now)


def _previous_day_levels(frame: pd.DataFrame) -> tuple[float, float] | None:
    dates = _ny_dates(frame.index)
    today = dates[-1]
    previous = dates[dates < today].unique()
    if len(previous) == 0:
        return None
    day = frame.loc[dates == previous[-1]]
    if len(day) < 8:
        return None
    return float(day["high"].max()), float(day["low"].min())


def _ny_cash_vwap(frame: pd.DataFrame) -> float | None:
    local = frame.index.tz_convert(NY)
    date = local[-1].date()
    minutes = local.hour * 60 + local.minute
    mask = (local.date == date) & (minutes >= 9 * 60 + 30) & (minutes < 16 * 60)
    part = frame.loc[mask]
    volume = pd.to_numeric(part.get("volume"), errors="coerce")
    if part.empty or volume is None or volume.isna().any() or volume.sum() <= 0:
        return None
    typical = (part["high"] + part["low"] + part["close"]) / 3
    return float((typical * volume).sum() / volume.sum())


def _same_slot_volume(frame: pd.DataFrame) -> float | None:
    local = frame.index.tz_convert(NY)
    last = local[-1]
    earlier = frame.loc[(local.date < last.date()) &
                        (local.hour == last.hour) &
                        (local.minute == last.minute)].tail(20)
    volumes = pd.to_numeric(earlier["volume"], errors="coerce")
    if len(volumes) < 10 or volumes.isna().any() or volumes.median() <= 0:
        return None
    current = float(frame["volume"].iloc[-1])
    return current / float(volumes.median()) if current > 0 else None


def _rsi14(close: pd.Series) -> float | None:
    delta = close.diff()
    gain = delta.clip(lower=0).ewm(alpha=1 / 14, adjust=False).mean()
    loss = (-delta.clip(upper=0)).ewm(alpha=1 / 14, adjust=False).mean()
    up, down = float(gain.iloc[-1]), float(loss.iloc[-1])
    if not math.isfinite(up) or not math.isfinite(down):
        return None
    if down == 0:
        return 100.0 if up > 0 else 50.0
    return 100 - 100 / (1 + up / down)


def candidate(frame: pd.DataFrame, now: dt.datetime) -> dict | None:
    """Return one observational level watch from the latest closed 15m bar."""
    if now.tzinfo is None:
        raise ValueError("now must be timezone aware")
    tr = now.astimezone(TR)
    if not _in_window(now):
        return None
    bars = _closed(frame, now)
    if len(bars) < 60:
        return None
    bar_close = bars.index[-1].to_pydatetime() + dt.timedelta(minutes=15)
    age = (now - bar_close).total_seconds() / 60
    if age < 0 or age > MAX_BAR_AGE_MINUTES:
        return None
    levels = _previous_day_levels(bars)
    if levels is None:
        return None
    last = bars.iloc[-1]
    current_atr = float(atr(bars).iloc[-1])
    if not math.isfinite(current_atr) or current_atr <= 0:
        return None
    close = float(last["close"])
    options = [("gun yuksegi", levels[0]), ("gun dusugu", levels[1])]
    name, level = min(options, key=lambda pair: abs(close - pair[1]))
    distance = abs(close - level)
    fast = float(ema(bars["close"], 20).iloc[-1])
    slow = float(ema(bars["close"], 50).iloc[-1])
    trend = "yukari" if close > fast > slow else "asagi" if close < fast < slow else "karisik"
    vwap = _ny_cash_vwap(bars)
    volume_ratio = _same_slot_volume(bars)
    level_watch = distance <= NEAR_LEVEL_ATR * current_atr
    previous_vwap = _ny_cash_vwap(bars.iloc[:-1])
    previous_close = float(bars["close"].iloc[-2])
    vwap_reclaim = (vwap is not None and previous_vwap is not None and
                    volume_ratio is not None and volume_ratio >= 1.3 and
                    ((previous_close <= previous_vwap and close > vwap and trend == "yukari") or
                     (previous_close >= previous_vwap and close < vwap and trend == "asagi")))
    # Notification thresholds only; never change mechanical entry/risk rules.
    move_1h = (close / float(bars['close'].iloc[-5]) - 1) * 100
    adx14 = float(adx(bars, 14, shift=0).iloc[-1])
    trend_watch = (trend != 'karisik' and math.isfinite(adx14) and adx14 >= 25
                   and abs(move_1h) >= 0.5 and volume_ratio is not None
                   and volume_ratio >= 1.3)
    move_watch = abs(move_1h) >= 1.0
    if not level_watch and not vwap_reclaim and not trend_watch and not move_watch:
        return None
    reason = (f"onceki NY {name} yakininda ({distance / current_atr:.2f} ATR)"
              if level_watch else
              f"NY nakit VWAP {'ustune' if trend == 'yukari' else 'altina'} geri gecis; hacim {volume_ratio:.1f}x"
              if vwap_reclaim else
              f"son 1 saat {move_1h:+.2f}%; ADX {adx14:.1f}; hacim {volume_ratio:.1f}x"
              if trend_watch else f"son 1 saat {move_1h:+.2f}%")
    event = (name if level_watch else 'vwap_' + trend if vwap_reclaim else
             'trend_' + trend if trend_watch else 'move_' + ('up' if move_1h > 0 else 'down'))
    rsi14 = _rsi14(bars["close"])
    return {
        "key": f"{tr.date()}:{event}",
        "bar_close": bar_close,
        "age": age,
        "level_name": name,
        "level": level,
        "close": close,
        "distance_atr": distance / current_atr,
        "reason": reason,
        "trend": trend,
        "ema20": fast,
        "ema50": slow,
        "vwap": vwap,
        "vwap_side": "ustunde" if vwap is not None and close >= vwap else "altinda" if vwap is not None else "bilinmiyor",
        "volume_ratio": volume_ratio,
        "adx": adx14 if math.isfinite(adx14) else None,
        "rsi": rsi14,
    }


def format_watch(item: dict, now: dt.datetime) -> str:
    bar_tr = item["bar_close"].astimezone(TR).strftime("%H:%M TR")
    volume = (f"{item['volume_ratio']:.1f}x" if item["volume_ratio"] is not None
              else "olculemedi")
    adx_text = f"{item['adx']:.0f}" if item["adx"] is not None else "yok"
    rsi_text = f"{item['rsi']:.0f}" if item["rsi"] is not None else "yok"
    vwap_text = f"{item['vwap']:.1f}" if item["vwap"] is not None else "yok"
    return "\n".join([
        f"DISKRESYONER IZLEME | NQ/US100 | {now.astimezone(TR):%H:%M} TR",
        f"Neden: NQ {item['reason']}.",
        f"15dk: EMA20 {item['ema20']:.1f}, EMA50 {item['ema50']:.1f}; NY VWAP {vwap_text} ({item['vwap_side']}); ADX {adx_text}, RSI {rsi_text}, hacim {volume}.",
        f"Capraz piyasa: {item.get('es_context', 'ES tepkisi olculemedi')}.",
        f"Veri: Yahoo NQ=F, kapanmis 15dk bar {bar_tr}, {item['age']:.0f} dk once. NQ seviyesi {item['level']:.1f}; Maven US100 emir fiyati DEGIL.",
        "MT5 US100'de mum/seviye teyidi gerekir. 2/4 + tez + curuten + on-kayit; karar ve emir sende. Mekanik LIVE sinyali degildir. Gercek yeni giris kapisi 18:15-20:00 TR; bu kart gun boyu izleme icindir.",
    ])


def run(*, now: dt.datetime | None = None, state_path: Path = STATE_PATH,
        fetch=None, send=None, dry_run: bool = False) -> str | None:
    now = now or dt.datetime.now(UTC)
    if not _in_window(now):
        print("Mobil izleme: karar penceresi disinda.")
        return None
    frame = (fetch or free_data.ohlcv)("NASDAQ100", "15m", days=30)
    closed = _closed(frame, now)
    if not closed.empty:
        age = (now - (closed.index[-1].to_pydatetime() +
                      dt.timedelta(minutes=15))).total_seconds() / 60
        print(f"Mobil izleme: son kapanmis NQ bar {closed.index[-1].isoformat()}, "
              f"kapanistan beri {age:.0f} dk.")
        health_path = os.environ.get('MOBILE_WATCH_HEALTH_PATH')
        if health_path and not dry_run and len(closed) >= 60 and 0 <= age <= MAX_BAR_AGE_MINUTES:
            path = Path(health_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open('a', encoding='utf-8') as stream:
                stream.write(json.dumps({'evaluated_at': now.isoformat(),
                                         'bar_time': closed.index[-1].isoformat(),
                                         'age_minutes': age}) + '\n')
    item = candidate(frame, now)
    if item is None:
        print("Mobil izleme: guncel seviye adayi yok.")
        return None
    try:
        state = json.loads(state_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        state = {}
    notified = state.get("notified", [])
    if not isinstance(notified, list):
        notified = []
    if item["key"] in notified:
        print("Mobil izleme: bu gun/seviye daha once bildirildi.")
        return None
    nq = closed
    try:
        es = _closed((fetch or free_data.ohlcv)("SP500", "15m", days=2), now)
        if len(es) >= 5 and abs((es.index[-1] - nq.index[-1]).total_seconds()) <= 900:
            nq_move = (float(nq["close"].iloc[-1]) /
                       float(nq["close"].iloc[-5]) - 1) * 100
            es_move = (float(es["close"].iloc[-1]) /
                       float(es["close"].iloc[-5]) - 1) * 100
            item["es_context"] = (f"NQ son 1s {nq_move:+.2f}%, "
                                  f"ES son 1s {es_move:+.2f}% (Yahoo vadeli)")
    except (OSError, ValueError, KeyError, TypeError, ZeroDivisionError) as exc:
        print(f"Mobil izleme: ES baglami alinamadi ({type(exc).__name__}).")
    message = format_watch(item, now)
    from .mt5_context import describe
    broker_context = describe('NASDAQ100', now=now)
    if broker_context:
        message += '\n' + broker_context
    if dry_run:
        print(message)
        return message
    if send is not None:
        send(message)
    else:
        try:
            png = render_chart(nq, level=item["level"])
            telegram_notify.send_photo(png, message[:1024])
            if len(message) > 1024:
                telegram_notify.send(message)
            print('Mobil izleme: PNG Telegram API tarafindan kabul edildi.')
        except Exception as exc:
            print(f"Mobil izleme: grafik gonderilemedi ({type(exc).__name__}); metin deneniyor.")
            telegram_notify.send(message)
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps({"notified": [
        key for key in notified if key.startswith(str(now.astimezone(TR).date()))
    ] + [item["key"]]}), encoding="utf-8")
    print(f"Mobil izleme: Telegram'a bildirildi ({item['key']}).")
    return message


def main() -> None:
    parser = argparse.ArgumentParser(description="Diskresyoner mobil izleme adayi")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    run(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
