"""Download Databento packages into a local, git-ignored folder (CME license: never commit raw data).

Usage (from repo root, vectorbt-lab venv):
  python HANDOFF/scripts_2026-11-21/databento_fetch.py daily
  python HANDOFF/scripts_2026-11-21/databento_fetch.py nq1m
Each package prints get_cost first and refuses to run above its cap.
"""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path

import databento as db

OUT = Path("strategy-lab/outputs/databento")
END = "2026-11-20"
ROOTS = ["ES", "NQ", "YM", "RTY", "CL", "BZ", "GC", "SI", "HG", "NG", "ZN", "ZB", "ZF", "ZT",
         "6E", "6B", "6J", "6A", "6C", "6S", "ZC", "ZS", "ZW"]
C0 = [f"{r}.c.0" for r in ROOTS]
CURVE = [f"{r}.c.{k}" for r in ("CL", "GC", "SI", "NG", "HG") for k in (1, 2, 3)]
GLBX_START = "2010-06-06"

PACKAGES = {
    "daily": (6.0, [
        ("glbx_ohlcv1d_c0", dict(dataset="GLBX.MDP3", schema="ohlcv-1d", symbols=C0, start=GLBX_START)),
        ("glbx_ohlcv1d_curve", dict(dataset="GLBX.MDP3", schema="ohlcv-1d", symbols=CURVE, start=GLBX_START)),
        ("glbx_statistics_c0", dict(dataset="GLBX.MDP3", schema="statistics", symbols=C0, start=GLBX_START)),
        ("ifeu_brn_ohlcv1d", dict(dataset="IFEU.IMPACT", schema="ohlcv-1d", symbols=["BRN.c.0"], start="2018-12-23")),
        ("glbx_definition_c0", dict(dataset="GLBX.MDP3", schema="definition", symbols=C0, start=GLBX_START)),
    ]),
    "nq1m": (45.0, [
        ("glbx_ohlcv1m_es_nq", dict(dataset="GLBX.MDP3", schema="ohlcv-1m", symbols=["ES.c.0", "NQ.c.0"],
                                    start=GLBX_START)),
    ]),
}


def load_key() -> None:
    for line in Path("strategy-lab/.env").read_text(encoding="utf-8").splitlines():
        if line.startswith("DATABENTO_API_KEY="):
            os.environ["DATABENTO_API_KEY"] = line.split("=", 1)[1].strip()
    if not os.environ.get("DATABENTO_API_KEY"):
        raise SystemExit("DATABENTO_API_KEY missing in strategy-lab/.env")


def main(pkg: str) -> None:
    load_key()
    cap, jobs = PACKAGES[pkg]
    c = db.Historical()
    OUT.mkdir(parents=True, exist_ok=True)
    total = sum(c.metadata.get_cost(stype_in="continuous", end=END, **kw) for _, kw in jobs)
    print(f"{pkg}: estimated ${total:.2f} (cap ${cap})", flush=True)
    if total > cap:
        raise SystemExit("estimate above cap, aborting")
    # Streaming get_range returned 504 gateway timeouts for multi-year requests -> batch jobs.
    pending = {}
    for name, kw in jobs:
        dest = OUT / name
        if dest.exists() and any(dest.rglob("*.dbn.zst")):
            print("skip", dest)
            continue
        job = c.batch.submit_job(stype_in="continuous", end=END, encoding="dbn", compression="zstd",
                                 split_duration="none", **kw)
        pending[job["id"]] = dest
        print("submitted", name, job["id"], flush=True)
    while pending:
        time.sleep(15)
        done = {j["id"] for j in c.batch.list_jobs(states="done") if j["id"] in pending}
        for jid in done:
            dest = pending.pop(jid)
            files = c.batch.download(job_id=jid, output_dir=dest)
            print("saved", dest, [f"{f.name} {f.stat().st_size / 1e6:.1f}MB" for f in files], flush=True)


if __name__ == "__main__":
    main(sys.argv[1])
