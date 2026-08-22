"""Yerel defterdeki warmup satirlarini GERIYE DONUK isaretle -- tek seferlik.

SORUN (2026-08-21): `forward_ledger.csv`'de `backfill` kolonu yoktu. Defterin
en eski kaydi 2026-05-20, oysa forward EA repoya 2026-06-19'da girdi. Yani
bastaki islemler bir `--warmup` kosumundan geliyor: gecmis barlar uzerinde
uretilmis BACKTEST sonuclari. Kolon olmadigi icin bunlar aylarca "canli
forward kaniti" diye sayildi -- 126 islemlik defterin tamami saf forward
sanildi.

YONTEM: EA'nin var olmadigi tarihten onceki satirlar backfill (=1). Sonrasi
forward (=0). Bu kesin bir ayrim DEGIL: sonradan yapilmis bir warmup kosumu
de eski barlari islemis olabilir, ama boyle bir kosumun kaydi yok.
Belirsizlik burada yaziyor ki rakam bir daha oldugundan emin sanilmasin.

State dosyasi da guncellenir: defter her dongude `forward_state.json`
icindeki `closed` listesinden yeniden yazilir, yalnizca CSV'yi duzeltmek
bir sonraki kosumda geri alinirdi.

Calistir:
    python -m intraday.forward_ea.label_backfill --uygula
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

STATE_DIR = Path(__file__).resolve().parent.parent.parent / "outputs" / "intraday" / "forward_ea"
STATE_JSON = STATE_DIR / "forward_state.json"
LEDGER_CSV = STATE_DIR / "forward_ledger.csv"

# forward_ea'nin repodaki ilk commit tarihi. Oncesinde EA yoktu, dolayisiyla
# o islemler canli olculmus olamaz.
EA_BASLANGIC = pd.Timestamp("2026-06-19")


def classify(entry_time) -> int:
    return 1 if pd.Timestamp(entry_time) < EA_BASLANGIC else 0


def apply(state_path: Path = STATE_JSON, ledger_path: Path = LEDGER_CSV,
          dry_run: bool = True) -> dict:
    ozet = {"state": 0, "ledger": 0, "backfill": 0, "forward": 0}

    if state_path.exists():
        state = json.loads(state_path.read_text(encoding="utf-8"))
        for row in state.get("closed", []):
            if "backfill" not in row:
                row["backfill"] = classify(row["entry_time"])
                ozet["state"] += 1
            ozet["backfill" if row["backfill"] else "forward"] += 1
        if not dry_run:
            state_path.write_text(json.dumps(state, indent=2, default=str),
                                  encoding="utf-8")

    if ledger_path.exists():
        led = pd.read_csv(ledger_path, parse_dates=["entry_time"])
        if "backfill" not in led.columns:
            led["backfill"] = led["entry_time"].map(classify)
            ozet["ledger"] = len(led)
            if not dry_run:
                led.to_csv(ledger_path, index=False)

    return ozet


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--uygula", action="store_true", help="yaz (yoksa sadece raporlar)")
    a = p.parse_args()
    ozet = apply(dry_run=not a.uygula)
    print(f"state satiri isaretlendi : {ozet['state']}")
    print(f"ledger satiri isaretlendi: {ozet['ledger']}")
    print(f"  backfill (EA yokken)   : {ozet['backfill']}")
    print(f"  forward  (EA varken)   : {ozet['forward']}")
    if not a.uygula:
        print("\n(kuru kosum -- yazmak icin --uygula)")


if __name__ == "__main__":
    main()
