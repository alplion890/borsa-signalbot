"""Round 5 — Part 3: Descriptive MBO Iceberg analysis (OF4, NO pass/fail decision rule).

Prereg: HANDOFF/futures_tur5_onkayit_2026-11-23.md (commit 1df1cd7).
Data: outputs/databento/nqmbo (NQ.v.0, 2026-10-05..2026-10-16, 10 trading days, RTH 09:30-16:00 NY).
Measures:
  - Native icebergs: same order_id sum(fill_qty) > initial_add_qty and sum(fill_qty) >= 20
  - Synthetic refills: same (price, passive_side), add within <=50ms after fill, >=3 refills & >=50 contracts in 5s
  - Toxicity (price drift between t_detect and t_detect + 150ms), +1m and +5m directional drift
  - Overlap with OF1 absorption events (outputs/intraday/futures_round5/of1_events.csv)

Run from strategy-lab with vectorbt-lab venv:
  python ../HANDOFF/scripts_2026-11-23/run_mbo_iceberg.py
"""
from __future__ import annotations

import json
from collections import deque
from pathlib import Path

import databento as db
import numpy as np
import pandas as pd

SRC = Path("outputs/databento/nqmbo")
OUT = Path("outputs/intraday/futures_round5")
DELAY_150MS = 150_000_000
WIN_50MS = 50_000_000
WIN_5S = 5_000_000_000
H1M = 60 * 10**9
H5M = 300 * 10**9


def analyze_day(path: Path, of1_df: pd.DataFrame) -> dict:
    df = db.DBNStore.from_file(path).to_df()
    df = df[df["symbol"] == "NQ.v.0"][["action", "side", "price", "size", "order_id"]]
    ny = df.index.tz_convert("America/New_York")
    mins = ny.hour * 60 + ny.minute
    mask = (mins >= 570) & (mins < 960) & (ny.dayofweek < 5)
    df = df.loc[mask]
    if df.empty:
        return {"file": path.name, "empty": True}

    date_str = ny[mask][0].strftime("%Y-%m-%d")
    ts = df.index.asi8
    act = df["action"].to_numpy()
    side = df["side"].to_numpy()
    px = df["price"].to_numpy(dtype=np.float64)
    sz = df["size"].to_numpy(dtype=np.int64)
    oid = df["order_id"].to_numpy(dtype=np.int64)

    # Trade stream for mid/last price lookup
    tr_mask = (act == "T") | (act == "F")
    tr_ts = ts[tr_mask]
    tr_px = px[tr_mask]

    def price_at(t_ns: int) -> float:
        i = int(np.searchsorted(tr_ts, t_ns, side="left"))
        if i >= len(tr_ts):
            i = len(tr_ts) - 1
        return float(tr_px[i]) if len(tr_px) else float("nan")

    # 1. Native iceberg detection via order_id
    # Initial add size per order_id
    add_mask = act == "A"
    add_oid = oid[add_mask]
    add_sz = sz[add_mask]
    add_side = side[add_mask]
    add_px = px[add_mask]
    # Keep first add per order_id
    init_qty: dict[int, int] = {}
    init_side: dict[int, str] = {}
    init_px: dict[int, float] = {}
    for o, s, sd, p in zip(add_oid, add_sz, add_side, add_px):
        oi = int(o)
        if oi not in init_qty:
            init_qty[oi] = int(s)
            init_side[oi] = str(sd)
            init_px[oi] = float(p)

    # Accumulate fills per order_id ('F' = passive fill in MDP3 MBO)
    fill_mask = act == "F"
    f_oid = oid[fill_mask]
    f_sz = sz[fill_mask]
    f_ts = ts[fill_mask]
    f_px = px[fill_mask]
    f_side = side[fill_mask]

    cum_fill: dict[int, int] = {}
    native_events: list[dict] = []
    detected_native: set[int] = set()
    for o, s, t, p, sd in zip(f_oid, f_sz, f_ts, f_px, f_side):
        oi = int(o)
        if oi not in init_qty:
            continue
        nv = cum_fill.get(oi, 0) + int(s)
        cum_fill[oi] = nv
        if oi not in detected_native and nv > init_qty[oi] and nv >= 20:
            detected_native.add(oi)
            # Passive side 'B' = Bid (support -> long), 'A' = Ask (resistance -> short)
            d = 1 if init_side[oi] == "B" else (-1 if init_side[oi] == "A" else 0)
            if d == 0:
                continue
            p0 = float(p)
            p150 = price_at(int(t) + DELAY_150MS)
            p1m = price_at(int(t) + H1M)
            p5m = price_at(int(t) + H5M)
            native_events.append({
                "date": date_str, "t_ns": int(t), "dir": d, "price": p0,
                "init_qty": init_qty[oi], "det_qty": nv,
                "slip_150ms": d * (p150 - p0),  # positive = price moved in passive favor (worse entry)
                "drift_1m_from_150ms": d * (p1m - p150),
                "drift_5m_from_150ms": d * (p5m - p150),
            })

    # 2. Synthetic refill detection: fill at (px, side) followed by add with new order_id within <=50ms
    last_fill: dict[tuple[float, str], tuple[int, int, int]] = {}  # (px, side) -> (ts, oid, qty)
    refill_win: dict[tuple[float, str], deque] = {}  # (px, side) -> deque of (ts, qty)
    synth_events: list[dict] = []
    last_synth_ts: dict[tuple[float, str], int] = {}

    for t, a, sd, p, s, o in zip(ts, act, side, px, sz, oid):
        if a == "F" and (sd == "B" or sd == "A"):
            key = (float(p), str(sd))
            last_fill[key] = (int(t), int(o), int(s))
        elif a == "A" and (sd == "B" or sd == "A"):
            key = (float(p), str(sd))
            lf = last_fill.get(key)
            if lf is not None and (int(t) - lf[0]) <= WIN_50MS and int(o) != lf[1]:
                dq = refill_win.setdefault(key, deque())
                dq.append((int(t), lf[2]))
                while dq and (int(t) - dq[0][0]) > WIN_5S:
                    dq.popleft()
                tot_q = sum(x[1] for x in dq)
                if len(dq) >= 3 and tot_q >= 50:
                    prev_s = last_synth_ts.get(key, 0)
                    if int(t) - prev_s > WIN_5S:
                        last_synth_ts[key] = int(t)
                        d = 1 if sd == "B" else -1
                        p0 = float(p)
                        p150 = price_at(int(t) + DELAY_150MS)
                        p1m = price_at(int(t) + H1M)
                        p5m = price_at(int(t) + H5M)
                        synth_events.append({
                            "date": date_str, "t_ns": int(t), "dir": d, "price": p0,
                            "refills": len(dq), "qty": tot_q,
                            "slip_150ms": d * (p150 - p0),
                            "drift_1m_from_150ms": d * (p1m - p150),
                            "drift_5m_from_150ms": d * (p5m - p150),
                        })

    # 3. Overlap with OF1 events on same date (any native/synth iceberg within [t_close - 60s, t_close] and same dir)
    of1_day = of1_df[of1_df["date"] == date_str] if not of1_df.empty else pd.DataFrame()
    all_ice = native_events + synth_events
    of1_matched = 0
    for _, ev in of1_day.iterrows():
        tc = int(ev["t_close_ns"])
        ed = int(ev["dir"])
        hit = any((tc - H1M) <= x["t_ns"] <= tc and x["dir"] == ed for x in all_ice)
        if hit:
            of1_matched += 1

    return {
        "date": date_str,
        "rows_rth": int(len(df)),
        "native_n": len(native_events),
        "synth_n": len(synth_events),
        "of1_n": int(len(of1_day)),
        "of1_matched": of1_matched,
        "native_events": native_events,
        "synth_events": synth_events,
    }


def agg_events(ev_list: list[dict]) -> dict:
    if not ev_list:
        return {"n": 0}
    df = pd.DataFrame(ev_list)
    return {
        "n": int(len(df)),
        "slip_150ms_mean_pts": float(df["slip_150ms"].mean()),
        "slip_150ms_median_pts": float(df["slip_150ms"].median()),
        "drift_1m_mean_pts": float(df["drift_1m_from_150ms"].mean()),
        "drift_5m_mean_pts": float(df["drift_5m_from_150ms"].mean()),
        "drift_1m_win_pct": float((df["drift_1m_from_150ms"] > 0).mean() * 100.0),
        "drift_5m_win_pct": float((df["drift_5m_from_150ms"] > 0).mean() * 100.0),
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    of1_path = OUT / "of1_events.csv"
    if of1_path.exists() and of1_path.stat().st_size > 10:
        of1_df = pd.read_csv(of1_path)
    else:
        of1_df = pd.DataFrame(columns=["date", "t_close_ns", "dir"])

    files = sorted(SRC.glob("*.dbn.zst"))
    per_day = []
    nat_all, syn_all = [], []
    tot_of1, tot_match = 0, 0
    for f in files:
        r = analyze_day(f, of1_df)
        if r.get("empty"):
            continue
        nat_all.extend(r["native_events"])
        syn_all.extend(r["synth_events"])
        tot_of1 += r["of1_n"]
        tot_match += r["of1_matched"]
        per_day.append({
            "date": r["date"], "rows_rth": r["rows_rth"],
            "native_n": r["native_n"], "synth_n": r["synth_n"],
            "of1_n": r["of1_n"], "of1_matched": r["of1_matched"],
        })
        print(f"{r['date']}: rows={r['rows_rth']:,} native={r['native_n']} synth={r['synth_n']} of1={r['of1_matched']}/{r['of1_n']}", flush=True)

    summary = {
        "descriptive_only": True,
        "days": len(per_day),
        "per_day": per_day,
        "native": agg_events(nat_all),
        "synthetic": agg_events(syn_all),
        "of1_overlap": {
            "of1_total": tot_of1,
            "of1_with_iceberg": tot_match,
            "overlap_pct": float(tot_match / tot_of1 * 100.0) if tot_of1 else None,
        },
    }
    (OUT / "mbo_iceberg_desc.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
    print(json.dumps({k: v for k, v in summary.items() if k != "per_day"}, indent=1))


if __name__ == "__main__":
    main()
