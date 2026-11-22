"""Fetch extra Databento data for the third futures round (git-ignored output, CME license).

Run from strategy-lab with the vectorbt-lab venv:
  python ../HANDOFF/scripts_2026-11-21/fetch_extra.py gc1m|rty1m|c1daily|nqtrades|nqtrades2|x1h|bbox|nqmbo
Streams in yearly (1m) or weekly (trades) chunks because multi-year streaming returned 504.
Already completed chunks are skipped, so the script can be re-run after a failure.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import databento as db
import pandas as pd

OUT = Path("outputs/databento")
END = "2026-11-20"
ROOTS = ["ES", "NQ", "YM", "RTY", "CL", "BZ", "GC", "SI", "HG", "NG", "ZN", "ZB", "ZF", "ZT",
         "6E", "6B", "6J", "6A", "6C", "6S", "ZC", "ZS", "ZW"]
CAP_USD = {"gc1m": 1.5, "rty1m": 12.0, "c1daily": 1.5, "nqtrades": 34.0, "bbomicro": 2.0, "gc1h": 1.5, "vdaily": 3.0,
           "nqtrades2": 66.0, "x1h": 3.2, "bbox": 4.6, "nqmbo": 22.0}


def load_key() -> None:
    for line in Path(".env").read_text(encoding="utf-8").splitlines():
        if line.startswith("DATABENTO_API_KEY="):
            os.environ["DATABENTO_API_KEY"] = line.split("=", 1)[1].strip()
    if not os.environ.get("DATABENTO_API_KEY"):
        raise SystemExit("DATABENTO_API_KEY missing in .env")


def chunks(pkg: str) -> tuple[str, str, list[str], list[tuple[str, str]]]:
    if pkg in ("gc1m", "rty1m"):
        sym = "GC.c.0" if pkg == "gc1m" else "RTY.c.0"
        yrs = [(f"{y}-01-01" if y > 2010 else "2010-06-06", f"{y + 1}-01-01" if y < 2026 else END)
               for y in range(2010, 2027)]
        return "ohlcv-1m", pkg, [sym], yrs
    if pkg == "c1daily":
        return "ohlcv-1d", pkg, [f"{r}.c.1" for r in ROOTS], [("2010-06-06", END)]
    if pkg == "gc1h":
        return "ohlcv-1h", pkg, ["GC.v.0"], [("2010-06-06", END)]
    if pkg == "vdaily":
        return "ohlcv-1d", pkg, [f"{r}.v.{k}" for r in ROOTS for k in (0, 1)], [("2010-06-06", END)]
    if pkg == "bbomicro":
        return "bbo-1m", pkg, ["MGC.c.0", "M2K.c.0"], [("2025-01-01", "2026-01-01"), ("2026-01-01", END)]
    if pkg == "nqtrades2":
        days = pd.date_range("2026-03-01", "2026-09-01", freq="7D").strftime("%Y-%m-%d").tolist() + ["2026-09-01"]
        return "trades", pkg, ["NQ.v.0"], list(zip(days[:-1], days[1:]))
    if pkg == "x1h":
        return "ohlcv-1h", pkg, ["CL.v.0", "ZN.v.0", "6E.v.0"], [("2010-06-06", END)]
    if pkg == "bbox":
        return "bbo-1m", pkg, ["MCL.c.0", "6E.c.0", "ZN.c.0", "CL.c.0", "M6E.c.0"], [("2025-01-01", END)]
    if pkg == "nqmbo":
        return "mbo", pkg, ["NQ.v.0"], [(d, (pd.Timestamp(d) + pd.Timedelta(days=1)).strftime("%Y-%m-%d"))
                                        for d in pd.bdate_range("2026-10-05", "2026-10-16").strftime("%Y-%m-%d")]
    if pkg == "nqtrades":
        days = pd.date_range("2026-09-01", END, freq="7D").strftime("%Y-%m-%d").tolist() + [END]
        return "trades", pkg, ["NQ.c.0"], list(zip(days[:-1], days[1:]))
    raise SystemExit(f"unknown package {pkg}")


def main(pkg: str) -> None:
    load_key()
    schema, name, syms, spans = chunks(pkg)
    c = db.Historical()
    kw = dict(dataset="GLBX.MDP3", schema=schema, symbols=syms, stype_in="continuous")
    total = c.metadata.get_cost(start=spans[0][0], end=spans[-1][1], **kw)
    print(f"{pkg}: estimated ${total:.2f} (cap ${CAP_USD[pkg]})", flush=True)
    if total > CAP_USD[pkg]:
        raise SystemExit("estimate above cap, aborting")
    dest = OUT / name
    dest.mkdir(parents=True, exist_ok=True)
    for a, b in spans:
        f = dest / f"{name}_{a}_{b}.dbn.zst"
        if f.exists():
            continue
        part = f.with_suffix(".part")
        c.timeseries.get_range(start=a, end=b, path=str(part), **kw)
        part.rename(f)
        print("done", f.name, flush=True)


if __name__ == "__main__":
    main(sys.argv[1])
