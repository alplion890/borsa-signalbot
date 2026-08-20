"""Bulut forward kosucusu — bedava veriyle, 7/24, PC kapaliyken de.

NEDEN VAR: yerel forward EA olcumu MetaTrader terminaline bagli. Terminal
kapaliyken dongu hic kosmuyor; 2026-08 basinda bu yuzden gunlerce delik olustu
(runner.log'da 1000+ "terminal kapali" kaydi). Defterdeki delik = kanit kaybi.
Bu kosucu ayni modulleri ayni dongueyle (`engine.cycle`) bedava feed'lerden
besler ve GitHub Actions'ta calisir.

NE DEGIL: bu bir emir motoru degil. Telegram'a cikmaz (bildirim isini bulut
signalbot zaten yapiyor; iki taraf da gonderirse ayni sinyal iki kere duser),
gercek emir atmaz, broker'a hic baglanmaz.

DEFTERLER AYRI TUTULUR -- KARISTIRMA:
    forward_ledger.csv  broker feed'i, yerel olcum       (referans)
    cloud_ledger.csv    bedava feed, bulut olcumu        (bu dosya)
Iki feed arasinda baz farki var (olculdu: NASDAQ'ta gurultu p95 0.074R, FX'te
getiri korelasyonu 0.86). Satirlari tek deftere karistirmak, farkli dolum
varsayimlarini ayni havuzda toplamak olurdu -- olcum bozulur. Karsilastirma
`source` kolonu uzerinden yapilir.

Calistir:
    python -m intraday.forward_ea.cloud_runner --once
    python -m intraday.forward_ea.cloud_runner --once --warmup 14
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from . import cloud_feed
from .engine import book_from_state, cycle, pos_to_json
from .modules import LiveModule, forward_test_modules
from .positions import Book

DEFAULT_STATE_DIR = (Path(__file__).resolve().parent.parent.parent
                     / "outputs" / "intraday" / "forward_ea")
STATE_NAME = "cloud_state.json"
LEDGER_NAME = "cloud_ledger.csv"

_LEDGER_COLUMNS = ["entry_time", "exit_time", "module", "symbol", "dir", "entry",
                   "sl", "tp", "exit", "bars_held", "status", "r", "weight",
                   "weighted_r", "source", "backfill"]


def _load_state(path: Path) -> dict:
    if not path.exists():
        return {"last_bar": {}, "open_positions": []}
    state = json.loads(path.read_text(encoding="utf-8"))
    # `closed` bilerek state'te TUTULMAZ: defterin tek kaynagi CSV. Ikisi de
    # tutulursa her kosumda 100+ KB'lik JSON yeniden yazilir ve iki kopya
    # zamanla ayrisir.
    state.pop("closed", None)
    return state


def _save_state(path: Path, book: Book, last_bar: dict) -> None:
    path.write_text(json.dumps({
        "schema": 1,
        "updated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "last_bar": {k: str(v) for k, v in last_bar.items()},
        "open_positions": [pos_to_json(p) for p in book.open_positions],
    }, indent=2, default=str), encoding="utf-8")


def _existing_keys(ledger_path: Path) -> set[tuple[str, str, str]]:
    """Deftere zaten dusmus islemler (modul, sembol, giris zamani).

    State kaybolursa (cache silinir, dosya bozulur) ayni islem ikinci kez
    yazilabilir. Cift kayit, olculen exp_R'yi sessizce sisirir -- defterin
    tek isi dogru saymak oldugu icin burada acikca engelleniyor.
    """
    if not ledger_path.exists():
        return set()
    old = pd.read_csv(ledger_path)
    if old.empty:
        return set()
    return {(str(m), str(s), str(t)) for m, s, t
            in zip(old["module"], old["symbol"], old["entry_time"])}


def _append_ledger(ledger_path: Path, rows: list[dict], backfill: bool = False) -> int:
    if not rows:
        return 0
    known = _existing_keys(ledger_path)
    fresh = [r for r in rows
             if (str(r["module"]), str(r["symbol"]), str(r["entry_time"])) not in known]
    if not fresh:
        return 0
    frame = pd.DataFrame(fresh)
    frame["source"] = [cloud_feed.source_of(s) if cloud_feed.supports(s) else "unknown"
                       for s in frame["symbol"]]
    # Warmup kosumu gecmis barlari isler: bu satirlar BACKTEST'tir, forward
    # kaniti degil. Isaretlenmezse aylar sonra "bulutta canli olculdu" diye
    # okunur ve defteri kirletir.
    frame["backfill"] = 1 if backfill else 0
    frame = frame[_LEDGER_COLUMNS]
    header = not ledger_path.exists()
    frame.to_csv(ledger_path, mode="a", header=header, index=False)
    return len(fresh)


def run_once(warmup_days: int = 0, modules: list[LiveModule] | None = None,
             fetch=None, state_dir: Path | None = None) -> dict:
    state_dir = Path(state_dir) if state_dir is not None else DEFAULT_STATE_DIR
    state_dir.mkdir(parents=True, exist_ok=True)
    state_path = state_dir / STATE_NAME
    ledger_path = state_dir / LEDGER_NAME

    modules = modules if modules is not None else forward_test_modules()
    fetch = fetch if fetch is not None else cloud_feed.ohlcv

    state = _load_state(state_path)
    book = book_from_state(state)
    last_bar = dict(state.get("last_bar", {}))
    open_before = len(book.open_positions)

    skipped: list[str] = []

    def _skip(name: str, exc: Exception) -> None:
        print(f"  [ATLA] {name}: {exc}")
        skipped.append(name)

    opened = cycle(modules, book, last_bar, fetch,
                   warmup_days=warmup_days, on_skip=_skip)
    written = _append_ledger(ledger_path, book.closed, backfill=warmup_days > 0)
    _save_state(state_path, book, last_bar)

    summary = {
        "opened": len(opened),
        "closed": len(book.closed),
        "written": written,
        "open_now": len(book.open_positions),
        "open_before": open_before,
        "skipped": skipped,
        "ledger": str(ledger_path),
    }
    _print_summary(summary, book, ledger_path)
    return summary


def _print_summary(summary: dict, book: Book, ledger_path: Path) -> None:
    print("\n" + "=" * 78)
    print("  BULUT FORWARD DEFTERI (bedava feed — broker baglantisi yok)")
    print("=" * 78)
    print(f"  Yeni acilan: {summary['opened']}   bu turda kapanan: "
          f"{summary['closed']}   deftere yazilan: {summary['written']}")
    print(f"  Acik pozisyon: {summary['open_now']}")
    for p in book.open_positions:
        yon = "LONG" if p.direction == 1 else "SHORT"
        print(f"    {p.module:26} {p.symbol:9} {yon:5} entry={p.entry:.2f} "
              f"bar={p.bars_held}/{p.max_hold_bars}")
    if summary["skipped"]:
        print(f"  Feed'i alinamayan: {', '.join(summary['skipped'])}")
    if ledger_path.exists():
        led = pd.read_csv(ledger_path)
        if len(led):
            wr = (led["r"] > 0).mean() * 100
            print(f"  Toplam kayit: {len(led)}  win%={wr:.1f}  "
                  f"toplam R={led['r'].sum():+.2f}")
    print("=" * 78 + "\n")


def main() -> None:
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--once", action="store_true", help="tek dongu (varsayilan)")
    p.add_argument("--warmup", type=int, default=0,
                   help="ilk calistirmada N gun geriye doldur")
    args = p.parse_args()
    run_once(warmup_days=args.warmup)


if __name__ == "__main__":
    main()
