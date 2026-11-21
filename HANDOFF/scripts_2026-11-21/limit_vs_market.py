"""C: descriptive limit-vs-market entry measurement on NQ trades (aggressor side), 2026-09-01..2026-11-19.

Prereg: HANDOFF/futures_hacim_carry_onkayit_2026-11-21.md section C (commit 4348418). No pass/fail rule.
Bid proxy = last sell-aggressor trade price (side 'A'), ask proxy = last buy-aggressor price (side 'B').
A resting limit counts as filled only if price trades one tick THROUGH it within 60 s (no queue optimism).
Run from strategy-lab with the vectorbt-lab venv:
  python ../HANDOFF/scripts_2026-11-21/limit_vs_market.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import databento as db
import numpy as np
import pandas as pd

sys.path.insert(0, ".")
sys.path.insert(0, str(Path(__file__).resolve().parent))

SRC = Path("outputs/databento/nqtrades")
OUT = Path("outputs/intraday/limit_vs_market")
TICK = 0.25
WAIT_NS = 60 * 10**9
HORIZONS = {"1m": 60, "5m": 300, "15m": 900}


def load_day_frames() -> dict[str, pd.DataFrame]:
    days: dict[str, list[pd.DataFrame]] = {}
    for f in sorted(SRC.glob("*.dbn.zst")):
        t = db.DBNStore.from_file(f).to_df()
        t = t[t["symbol"] == "NQ.c.0"][["price", "size", "side"]]
        ny = t.index.tz_convert("America/New_York")
        mins = ny.hour * 60 + ny.minute
        t = t[(mins >= 570) & (mins < 960) & (ny.dayofweek < 5)]
        for d, g in t.groupby(ny[(mins >= 570) & (mins < 960) & (ny.dayofweek < 5)].strftime("%Y-%m-%d")):
            days.setdefault(d, []).append(g)
    return {d: pd.concat(v).sort_index() for d, v in days.items()}


def quotes(t: pd.DataFrame) -> pd.DataFrame:
    bid = t["price"].where(t["side"] == "A").ffill()
    ask = t["price"].where(t["side"] == "B").ffill()
    q = pd.DataFrame({"bid": bid, "ask": ask, "price": t["price"]}).dropna()
    q = q[q["ask"] > q["bid"]]
    q["mid"] = (q["bid"] + q["ask"]) / 2
    return q


def events_for_day(t: pd.DataFrame, event_times: list[pd.Timestamp], tag: str) -> list[dict]:
    q = quotes(t)
    if q.empty:
        return []
    ts = q.index.asi8
    px = t["price"].to_numpy()
    tts = t.index.asi8
    rows = []
    for et in event_times:
        e = et.value
        i = np.searchsorted(ts, e, side="right") - 1
        if i < 0:
            continue
        bid, ask, mid0 = q["bid"].iat[i], q["ask"].iat[i], q["mid"].iat[i]
        a, b = np.searchsorted(tts, e, side="right"), np.searchsorted(tts, e + WAIT_NS, side="right")
        win = px[a:b]
        fut = {h: q["mid"].iat[max(np.searchsorted(ts, e + s * 10**9, side="right") - 1, 0)]
               for h, s in HORIZONS.items()}
        for d in (1, -1):
            limit, market = (bid, ask) if d == 1 else (ask, bid)
            filled = bool(len(win) and ((win.min() <= limit - TICK) if d == 1 else (win.max() >= limit + TICK)))
            row = {"tag": tag, "time": str(et), "dir": d, "half_spread": (ask - bid) / 2, "filled": filled}
            for h, m in fut.items():
                row[f"dm_{h}"] = d * (m - mid0)
                row[f"mkt_{h}"] = d * (m - market)
                row[f"lim_{h}"] = d * (m - limit) if filled else 0.0
            rows.append(row)
    return rows


def nb_entry_times(start: str) -> list[pd.Timestamp]:
    from futures_cost_retest import load_1m, to_5m
    from intraday.noise_band_research import simulate
    f5 = to_5m(load_1m("NQ.c.0"))
    tr, _ = simulate(f5[["open", "high", "low", "close", "volume"]].loc[pd.Timestamp(start, tz="UTC") - pd.Timedelta(days=40):])
    times = pd.to_datetime(tr["entry_time"], utc=True)
    return list(times[times >= pd.Timestamp(start, tz="UTC")])


def summarize(df: pd.DataFrame) -> dict:
    out = {"n": int(len(df)), "fill_rate": float(df["filled"].mean()), "half_spread_med": float(df["half_spread"].median())}
    for h in HORIZONS:
        f = df[df["filled"]]
        out[h] = {"E_dm_all": float(df[f"dm_{h}"].mean()), "E_dm_filled": float(f[f"dm_{h}"].mean()) if len(f) else None,
                  "adverse_selection": float(df[f"dm_{h}"].mean() - f[f"dm_{h}"].mean()) if len(f) else None,
                  "market_pnl_pts": float(df[f"mkt_{h}"].mean()), "limit_pnl_pts": float(df[f"lim_{h}"].mean()),
                  "limit_pnl_if_filled": float(f[f"lim_{h}"].mean()) if len(f) else None}
    return out


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    days = load_day_frames()
    counts = pd.Series({d: len(t) for d, t in days.items()})
    thin = sorted(counts.index[counts < 0.5 * counts.median()])   # prereg EK 2: skip thin roll-week days
    days = {d: t for d, t in days.items() if d not in thin}
    nb = nb_entry_times(min(days))
    rows = []
    for d, t in days.items():
        base = pd.Timestamp(d + " 09:35", tz="America/New_York")
        grid = [base + pd.Timedelta(minutes=5 * k) for k in range(75)]
        rows += events_for_day(t, [g.tz_convert("UTC") for g in grid], "grid5m")
        rows += events_for_day(t, [x for x in nb if x.tz_convert("America/New_York").strftime("%Y-%m-%d") == d], "nb_nq")
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "events.csv", index=False)
    res = {"days": len(days), "first": min(days), "last": max(days), "skipped_thin_days": thin}
    for tag, g in df.groupby("tag"):
        res[tag] = summarize(g)
    (OUT / "result.json").write_text(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
