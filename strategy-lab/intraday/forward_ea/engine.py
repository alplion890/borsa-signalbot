"""Forward test cekirdegi — feed'den BAGIMSIZ.

`live_runner` (MT5) ve `cloud_runner` (bedava veri) ayni dongueyi kullanir.
Boyle olmasinin sebebi: iki taraf kendi kopyasini tutsaydi zamanla ayrisir,
bulut defteri MT5 defterinin olctugu seyi olcmez -- karsilastirma anlamsizlasir.
Ayni ders dedektorlerde de alinmisti (bkz live_runner `_fetch_ohlcv` notu).

Bu modul MT5 import ETMEZ: `MetaTrader5` paketi yalnizca Windows'ta kurulur,
bulut kosucusu Linux'ta calisir.
"""
from __future__ import annotations

from typing import Callable

import numpy as np
import pandas as pd

from .modules import LiveModule
from .positions import Book, PaperPosition

Fetch = Callable[[str, str, int], pd.DataFrame]


def naive(ts) -> pd.Timestamp:
    """Timestamp'i tz-naive UTC'ye indir (feed ne dondururse dondursun).

    Tum defter/state tz-naive UTC varsayar (mt5_io sozlesmesi). Tek bir
    tz-aware deger karisirsa `Invalid comparison between dtype=datetime64[ns]
    and Timestamp` ile TUM dongu patlar -- yani yeni bir feed eklemek mevcut
    modullerin verisini de goturur. Burasi son savunma hatti.
    """
    t = pd.Timestamp(ts)
    return t.tz_convert("UTC").tz_localize(None) if t.tz is not None else t


def bars_per_day(tf: str) -> int:
    return {"5m": 288, "15m": 96, "1H": 24}.get(tf, 96)


def pos_to_json(p: PaperPosition) -> dict:
    return {
        "module": p.module, "symbol": p.symbol, "direction": p.direction,
        "entry_time": str(p.entry_time), "entry": p.entry, "sl": p.sl, "tp": p.tp,
        "weight": p.weight, "max_hold_bars": p.max_hold_bars,
        "cost_per_side": p.cost_per_side, "bars_held": p.bars_held,
    }


def book_from_state(state: dict) -> Book:
    book = Book(closed=list(state.get("closed", [])))
    for d in state.get("open_positions", []):
        book.add(PaperPosition(
            module=d["module"], symbol=d["symbol"], direction=d["direction"],
            entry_time=naive(d["entry_time"]), entry=d["entry"], sl=d["sl"],
            tp=d["tp"], weight=d["weight"], max_hold_bars=d["max_hold_bars"],
            cost_per_side=d["cost_per_side"], bars_held=d.get("bars_held", 0),
        ))
    return book


def cycle(modules: list[LiveModule], book: Book, last_bar: dict, fetch: Fetch,
          warmup_days: int = 0, on_skip: Callable[[str, Exception], None] | None = None,
          ) -> list[PaperPosition]:
    """Dongu; bu turda YENI acilan pozisyonlari dondurur (Telegram icin).

    `fetch` bir modulun barlarini getirir. Feed hatasi TUM turu kirmamali:
    bir sembol dususe gecerse digerlerinin olcumu devam eder.
    """
    opened: list[PaperPosition] = []
    fetch_days = max(40, warmup_days + 5)  # indikator lookback + warmup
    for mod in modules:
        try:
            df = fetch(mod.symbol_key, mod.tf, fetch_days)
        except Exception as e:
            if on_skip is not None:
                on_skip(mod.name, e)
            continue
        if len(df) < 200:
            continue
        # son bar henuz kapanmamis olabilir -> sonuncuyu disla
        df = df.iloc[:-1]
        key = f"{mod.name}:{mod.symbol_key}"
        last = naive(last_bar[key]) if key in last_bar else None

        if last is None:
            # ilk calistirma: warmup yoksa sadece son bardan ileri git
            if warmup_days > 0:
                start_pos = max(200, len(df) - warmup_days * bars_per_day(mod.tf))
            else:
                start_pos = len(df) - 1
        else:
            newer = np.asarray(df.index > last)
            start_pos = int(np.argmax(newer)) if newer.any() else len(df)

        for k in range(start_pos, len(df)):
            sub = df.iloc[:k + 1]
            bar = sub.iloc[-1]
            bt = sub.index[-1]
            book.update_symbol(mod.symbol_key, bt, float(bar["high"]),
                               float(bar["low"]), float(bar["close"]))
            if not book.has_open(mod.name, mod.symbol_key):
                sig = mod.detect(sub)
                if sig is not None and sig.direction != 0 and abs(sig.entry - sig.sl) > 0:
                    pos = PaperPosition(
                        module=mod.name, symbol=mod.symbol_key, direction=sig.direction,
                        entry_time=bt, entry=sig.entry, sl=sig.sl, tp=sig.tp,
                        weight=mod.weight, max_hold_bars=mod.max_hold_bars,
                        cost_per_side=mod.cost_per_side,
                    )
                    book.add(pos)
                    opened.append(pos)
            last_bar[key] = str(bt)
    return opened
