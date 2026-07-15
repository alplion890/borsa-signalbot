"""Forward EA ana dongu — MT5 demo'da canli forward test.

Her dongu, her modul icin:
  1. MT5'ten guncel bar ceker.
  2. En son islenen bardan sonraki yeni barlari sirayla isler:
       - once acik paper-pozisyonlari gunceller (SL/TP/timeout, honest)
       - sonra o barda yeni sinyal var mi bakar; varsa pozisyon acar
  3. Durumu (acik pozisyon + kapanmis ledger + son bar) JSON'a yazar.

Restart'a dayanikli: state JSON'dan yuklenir, kaldigi yerden devam eder.
Boylece Windows Task Scheduler ile 5 dakikada bir cagirilabilir.

Calistir:
    python -m intraday.forward_ea.live_runner --once          # tek dongu
    python -m intraday.forward_ea.live_runner --loop 300       # 300sn'de bir
    python -m intraday.forward_ea.live_runner --once --warmup 14  # 14 gun backfill
    python -m intraday.forward_ea.live_runner --status         # sadece pano
"""
from __future__ import annotations

import json
import sys
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
import logging
logging.disable(logging.INFO)
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from ..mt5_bridge import mt5_io
from .modules import LiveModule, default_modules
from .order_executor import OrderExecutor
from .positions import Book, PaperPosition

STATE_DIR = Path(__file__).resolve().parent.parent.parent / "outputs" / "intraday" / "forward_ea"
STATE_DIR.mkdir(parents=True, exist_ok=True)
STATE_JSON = STATE_DIR / "forward_state.json"
LEDGER_CSV = STATE_DIR / "forward_ledger.csv"


def _load_state() -> dict:
    if STATE_JSON.exists():
        return json.loads(STATE_JSON.read_text(encoding="utf-8"))
    return {"last_bar": {}, "open_positions": [], "closed": []}


def _save_state(book: Book, last_bar: dict) -> None:
    state = {
        "last_bar": {k: str(v) for k, v in last_bar.items()},
        "open_positions": [_pos_to_json(p) for p in book.open_positions],
        "closed": book.closed,
    }
    STATE_JSON.write_text(json.dumps(state, indent=2, default=str), encoding="utf-8")
    led = book.ledger()
    if len(led):
        led.to_csv(LEDGER_CSV)


def _pos_to_json(p: PaperPosition) -> dict:
    return {
        "module": p.module, "symbol": p.symbol, "direction": p.direction,
        "entry_time": str(p.entry_time), "entry": p.entry, "sl": p.sl, "tp": p.tp,
        "weight": p.weight, "max_hold_bars": p.max_hold_bars,
        "cost_per_side": p.cost_per_side, "bars_held": p.bars_held,
    }


def _book_from_state(state: dict) -> Book:
    book = Book(closed=list(state.get("closed", [])))
    for d in state.get("open_positions", []):
        book.add(PaperPosition(
            module=d["module"], symbol=d["symbol"], direction=d["direction"],
            entry_time=pd.Timestamp(d["entry_time"]), entry=d["entry"], sl=d["sl"],
            tp=d["tp"], weight=d["weight"], max_hold_bars=d["max_hold_bars"],
            cost_per_side=d["cost_per_side"], bars_held=d.get("bars_held", 0),
        ))
    return book


def _cycle(modules: list[LiveModule], book: Book, last_bar: dict,
           warmup_days: int = 0) -> list[PaperPosition]:
    """Dongu; bu turda YENI acilan pozisyonlari dondurur (Telegram icin)."""
    opened: list[PaperPosition] = []
    fetch_days = max(40, warmup_days + 5)  # indikator lookback + warmup
    for mod in modules:
        try:
            df = mt5_io.ohlcv(mod.symbol_key, mod.tf, days=fetch_days)
        except mt5_io.MT5Error as e:
            print(f"  [ATLA] {mod.name}: {e}")
            continue
        if len(df) < 200:
            continue
        # son bar henuz kapanmamis olabilir -> sonuncuyu disla
        df = df.iloc[:-1]
        key = f"{mod.name}:{mod.symbol_key}"
        last = pd.Timestamp(last_bar[key]) if key in last_bar else None

        if last is None:
            # ilk calistirma: warmup yoksa sadece son bardan ileri git
            if warmup_days > 0:
                start_pos = max(200, len(df) - warmup_days * _bars_per_day(mod.tf))
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


def _bars_per_day(tf: str) -> int:
    return {"5m": 288, "15m": 96, "1H": 24}.get(tf, 96)


def _dashboard(book: Book, acc: dict) -> None:
    led = book.ledger()
    print("\n" + "=" * 92)
    print(f"  FORWARD EA — {acc['login']} @ {acc['server']} (demo forward test)")
    print("=" * 92)
    print(f"  Acik pozisyon: {len(book.open_positions)}")
    for p in book.open_positions:
        d = "LONG" if p.direction == 1 else "SHORT"
        print(f"    {p.module:22} {p.symbol:8} {d:5} entry={p.entry:.2f} "
              f"sl={p.sl:.2f} tp={p.tp:.2f} bar={p.bars_held}/{p.max_hold_bars}")
    if len(led):
        wr = (led["r"] > 0).mean() * 100
        print(f"\n  Kapanmis trade: {len(led)}  win%={wr:.1f}  "
              f"toplam R={led['r'].sum():+.2f}  weighted R={led['weighted_r'].sum():+.2f}")
        print(f"  Son 5 trade:")
        for t, row in led.tail(5).iterrows():
            print(f"    {str(t)[:16]} {row['module']:20} {row['status']:7} R={row['r']:+.3f}")
        print(f"\n  Ledger: {LEDGER_CSV}")
    else:
        print("\n  Henuz kapanmis trade yok (forward test yeni basladi).")
    print("=" * 92 + "\n")


def run_once(warmup_days: int = 0, status_only: bool = False, live: bool = False) -> None:
    # Safety banner: loud warning if live mode is active
    if live and not status_only:
        print("\n" + "!" * 92)
        print("  *** CANLI MOD: gercek emir atilacak (LIVE_MODULES) ***")
        print("!" * 92 + "\n")

    state = _load_state()
    book = _book_from_state(state)
    last_bar = state.get("last_bar", {})
    modules = default_modules()
    with mt5_io.session():
        acc = mt5_io.account()
        if not status_only:
            opened = _cycle(modules, book, last_bar, warmup_days)
            _save_state(book, last_bar)
            if opened:
                from .notify import notify_new_positions
                sent = notify_new_positions(opened)
                if sent:
                    print(f"  [TELEGRAM] {len(sent)} yeni sinyal bildirildi.")

            # Wire OrderExecutor: reconcile live positions after paper state is saved
            if live:
                try:
                    executor = OrderExecutor()
                    results = executor.reconcile(book)
                    if results:
                        print("\n--- CANLI EMIR (reconcile) ---")
                        for action in results:
                            if action.get("action") != "skip":
                                module = action.get("module", "?")
                                symbol = action.get("symbol", "?")
                                act = action.get("action", "?")
                                if act == "open":
                                    lot = action.get("lot", 0.0)
                                    retcode = action.get("retcode", "?")
                                    print(f"  [CANLI] open {module:22} {symbol:8} lot={lot:.2f} retcode={retcode}")
                                elif act == "close":
                                    ticket = action.get("ticket", "?")
                                    print(f"  [CANLI] close ticket={ticket}")
                                elif act == "error":
                                    reason = action.get("reason", "?")
                                    print(f"  [CANLI HATA] {module} {symbol}: {reason}")
                        print("--- (END reconcile) ---\n")
                except Exception as e:
                    print(f"\n  [CANLI HATA] reconcile: {e}\n")

        _dashboard(book, acc)


def run_loop(interval_s: int, warmup_days: int = 0, live: bool = False) -> None:
    print(f"  Forward EA loop basladi (her {interval_s}sn). Ctrl+C ile dur.\n")
    first = True
    while True:
        try:
            run_once(warmup_days if first else 0, live=live)
            first = False
        except Exception as e:
            print(f"  [HATA] dongu: {e}")
        time.sleep(interval_s)


def _load_env_file() -> None:
    """strategy-lab/.env varsa KEY=VALUE satirlarini env'e yukle (ezme yok).

    Telegram token'i gibi sirlar icin: dosya git'e girmez (.gitignore),
    Task Scheduler ortaminda da calisir.
    """
    env_path = Path(__file__).resolve().parent.parent.parent / ".env"
    if not env_path.exists():
        return
    import os
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key, val = key.strip(), val.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = val


def main() -> None:
    import argparse
    _load_env_file()
    p = argparse.ArgumentParser()
    p.add_argument("--once", action="store_true", help="tek dongu calistir")
    p.add_argument("--loop", type=int, metavar="SN", help="SN saniyede bir dongu")
    p.add_argument("--warmup", type=int, default=0, help="ilk calistirmada N gun backfill")
    p.add_argument("--status", action="store_true", help="sadece panoyu goster")
    p.add_argument("--live", action="store_true", help="gercek MT5 emri at (whitelist modulleri). Yoksa sadece paper.")
    args = p.parse_args()

    if args.status:
        run_once(status_only=True)
    elif args.loop:
        run_loop(args.loop, args.warmup, live=args.live)
    else:
        run_once(args.warmup, live=args.live)


if __name__ == "__main__":
    main()
