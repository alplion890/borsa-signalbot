"""Round 5 — Part 2: Order Flow rules OF1 (Absorption), OF2 (Stacked Imbalance), OF3 (Delta Divergence).

Prereg: HANDOFF/futures_tur5_onkayit_2026-11-23.md (commit 1df1cd7).
Data: nqtrades2 (NQ.v.0, 2026-03-01..09-01) + nqtrades (NQ.c.0, 2026-09-01..11-19), RTH 09:30-16:00 NY.
Thin-day rule: skip days with RTH trade count < 50% of median.
Execution: signal at bar close t_close; entry at first trade >= t_close + 150ms;
tick-by-tick exit (target limit, stop + 150ms first trade, time stop + 150ms, or 15:55 NY).
Cost: MNQ 0.555 pts/side (central), 2x = 1.110 pts/side.

Run from strategy-lab with vectorbt-lab venv:
  python ../HANDOFF/scripts_2026-11-23/run_orderflow.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import databento as db
import numpy as np
import pandas as pd

SRC = Path("outputs/databento")
OUT = Path("outputs/intraday/futures_round5")
TICK = 0.25
DELAY_NS = 150_000_000  # 150 ms
MNQ_COST_PTS = 0.555
SPLIT_DATE = "2026-07-10"
SEED, REPS = 20261123, 10_000
N_TESTS = 11
Q_LO = 0.05 / N_TESTS / 2.0


def boot_ci(x: np.ndarray) -> list[float]:
    if len(x) < 10:
        return [float("nan"), float("nan")]
    rng = np.random.default_rng(SEED)
    m = x[rng.integers(0, len(x), size=(REPS, len(x)))].mean(axis=1)
    return np.quantile(m, [Q_LO, 1.0 - Q_LO]).tolist()


def iter_day_files() -> list[tuple[Path, str]]:
    files: list[tuple[Path, str]] = []
    for f in sorted((SRC / "nqtrades2").glob("*.dbn.zst")):
        files.append((f, "NQ.v.0"))
    for f in sorted((SRC / "nqtrades").glob("*.dbn.zst")):
        files.append((f, "NQ.c.0"))
    return files


def extract_rth_days() -> tuple[dict[str, list[pd.DataFrame]], dict[str, int]]:
    """Stream weekly files into per-day RTH DataFrames (ts_ns, price, size, side)."""
    day_chunks: dict[str, list[pd.DataFrame]] = {}
    for f, sym in iter_day_files():
        df = db.DBNStore.from_file(f).to_df()
        df = df[df["symbol"] == sym][["price", "size", "side"]]
        if df.empty:
            continue
        ny = df.index.tz_convert("America/New_York")
        mins = ny.hour * 60 + ny.minute
        mask = (mins >= 570) & (mins < 960) & (ny.dayofweek < 5)
        df = df.loc[mask]
        if df.empty:
            continue
        ny_m = ny[mask]
        day_str = ny_m.strftime("%Y-%m-%d")
        sub = pd.DataFrame({
            "ts_ns": df.index.asi8,
            "price": df["price"].to_numpy(dtype=np.float64),
            "size": df["size"].to_numpy(dtype=np.int64),
            "is_buy": (df["side"].to_numpy() == "B"),
            "is_sell": (df["side"].to_numpy() == "A"),
            "min_of_day": (ny_m.hour * 60 + ny_m.minute).to_numpy(dtype=np.int32),
        })
        for d, idx in sub.groupby(day_str).groups.items():
            day_chunks.setdefault(d, []).append(sub.loc[idx])
    counts = {d: sum(len(c) for c in v) for d, v in day_chunks.items()}
    return day_chunks, counts


def tick_exit(
    ts: np.ndarray,
    px: np.ndarray,
    entry_idx: int,
    direction: int,
    stop: float,
    target: float,
    deadline_ns: int,
) -> tuple[float, int, str]:
    """Simulate tick-by-tick exit from entry_idx+1 up to deadline_ns."""
    end_idx = int(np.searchsorted(ts, deadline_ns, side="right"))
    if end_idx <= entry_idx + 1:
        return float(px[entry_idx]), int(ts[entry_idx]), "time"
    w_px = px[entry_idx + 1 : end_idx]
    if direction == 1:
        hit_stop = np.flatnonzero(w_px <= stop)
        hit_tp = np.flatnonzero(w_px >= target)
    else:
        hit_stop = np.flatnonzero(w_px >= stop)
        hit_tp = np.flatnonzero(w_px <= target)

    s_i = int(hit_stop[0]) if len(hit_stop) else 10**12
    t_i = int(hit_tp[0]) if len(hit_tp) else 10**12

    if s_i == 10**12 and t_i == 10**12:
        # Time stop: first trade >= deadline_ns (or last trade before end)
        t_pos = int(np.searchsorted(ts, deadline_ns, side="left"))
        if t_pos >= len(ts):
            t_pos = len(ts) - 1
        return float(px[t_pos]), int(ts[t_pos]), "time"

    if s_i <= t_i:
        # Stop triggered at entry_idx + 1 + s_i -> exit at +150ms first trade
        trig_ts = int(ts[entry_idx + 1 + s_i])
        ex_pos = int(np.searchsorted(ts, trig_ts + DELAY_NS, side="left"))
        if ex_pos >= len(ts):
            ex_pos = len(ts) - 1
        return float(px[ex_pos]), int(ts[ex_pos]), "stop"
    else:
        # Target limit filled at target price
        ex_ts = int(ts[entry_idx + 1 + t_i])
        return float(target), ex_ts, "target"


def build_1m_footprint(day: pd.DataFrame) -> list[dict]:
    """Build 1m RTH bars (min_of_day 570..959) with footprint stats."""
    ts = day["ts_ns"].to_numpy()
    px = day["price"].to_numpy()
    sz = day["size"].to_numpy()
    is_b = day["is_buy"].to_numpy()
    is_s = day["is_sell"].to_numpy()
    mod = day["min_of_day"].to_numpy()

    bars = []
    # Find boundaries where mod changes
    unique_mins, start_idx = np.unique(mod, return_index=True)
    end_idx = np.append(start_idx[1:], len(mod))
    for m, a, b in zip(unique_mins, start_idx, end_idx):
        p_sl = px[a:b]
        s_sl = sz[a:b]
        b_sl = is_b[a:b]
        a_sl = is_s[a:b]
        o, h, l, c = float(p_sl[0]), float(p_sl.max()), float(p_sl.min()), float(p_sl[-1])
        ask_v = s_sl[b_sl].sum()
        bid_v = s_sl[a_sl].sum()
        vol = int(ask_v + bid_v)
        delta = int(ask_v - bid_v)
        top_ask = int(s_sl[b_sl & (p_sl >= h - 0.75 - 1e-9)].sum())
        bot_bid = int(s_sl[a_sl & (p_sl <= l + 0.75 + 1e-9)].sum())

        # Compute price-level ask/bid for stacked imbalance
        ticks = np.round((p_sl - l) / TICK).astype(np.int64)
        n_lvl = int(ticks.max()) + 1
        if n_lvl <= 2000:
            ask_lvl = np.bincount(ticks[b_sl], weights=s_sl[b_sl], minlength=n_lvl)
            bid_lvl = np.bincount(ticks[a_sl], weights=s_sl[a_sl], minlength=n_lvl)
        else:
            ask_lvl = np.zeros(0)
            bid_lvl = np.zeros(0)

        bars.append({
            "min": int(m),
            "o": o, "h": h, "l": l, "c": c,
            "vol": vol, "delta": delta,
            "top_ask": top_ask, "bot_bid": bot_bid,
            "ask_lvl": ask_lvl, "bid_lvl": bid_lvl,
            "last_ts": int(ts[b - 1]),
        })
    return bars


def check_stack(bar: dict) -> tuple[bool, bool, float, float]:
    """Return (has_buy_stack, has_sell_stack, buy_top_px, sell_bot_px)."""
    ask = bar["ask_lvl"]
    bid = bar["bid_lvl"]
    n = len(ask)
    if n < 3:
        return False, False, 0.0, 0.0
    l = bar["l"]

    # Buy imbalance at level k (k >= 1): ask[k] >= 3 * max(bid[k-1], 1) and ask[k] >= 30
    buy_imb = np.zeros(n, dtype=bool)
    buy_imb[1:] = (ask[1:] >= 3.0 * np.maximum(bid[:-1], 1.0)) & (ask[1:] >= 30.0)
    # Sell imbalance at level k (k <= n-2): bid[k] >= 3 * max(ask[k+1], 1) and bid[k] >= 30
    sell_imb = np.zeros(n, dtype=bool)
    sell_imb[:-1] = (bid[:-1] >= 3.0 * np.maximum(ask[1:], 1.0)) & (bid[:-1] >= 30.0)

    def _longest_run(arr: np.ndarray) -> tuple[int, int, int]:
        best_len, best_s, best_e = 0, -1, -1
        cur_len, cur_s = 0, 0
        for i, v in enumerate(arr):
            if v:
                if cur_len == 0:
                    cur_s = i
                cur_len += 1
                if cur_len > best_len:
                    best_len, best_s, best_e = cur_len, cur_s, i
            else:
                cur_len = 0
        return best_len, best_s, best_e

    bl, bs, be = _longest_run(buy_imb)
    sl, ss, se = _longest_run(sell_imb)
    has_b = bl >= 3
    has_s = sl >= 3
    return has_b, has_s, l + be * TICK, l + ss * TICK


def run_day_strategies(date: str, day: pd.DataFrame) -> tuple[list[dict], list[dict], list[dict], list[dict]]:
    ts = day["ts_ns"].to_numpy()
    px = day["price"].to_numpy()
    bars = build_1m_footprint(day)
    if len(bars) < 30:
        return [], [], [], []

    # NY timestamp helper for bar close (m + 1 minute)
    day_midnight_ny = pd.Timestamp(date + " 00:00:00", tz="America/New_York")
    flat_1555_ns = int((day_midnight_ny + pd.Timedelta(minutes=955)).tz_convert("UTC").value)

    of1_trades, of2_trades, of3_trades, of1_events = [], [], [], []

    # ---- OF1: Footprint Absorption (1m) ----
    vols = np.array([b["vol"] for b in bars], dtype=float)
    adeltas = np.array([abs(b["delta"]) for b in bars], dtype=float)
    busy_until = 0
    for i in range(20, len(bars)):
        b = bars[i]
        m_close = b["min"] + 1  # 09:50 = 590, 15:45 = 945
        if m_close < 590 or m_close > 945:
            continue
        t_close_ns = int((day_midnight_ny + pd.Timedelta(minutes=m_close)).tz_convert("UTC").value)
        if t_close_ns < busy_until:
            continue
        rng = b["h"] - b["l"]
        if rng < 3.0 - 1e-9 or b["vol"] <= 0:
            continue
        mu_v, sd_v = vols[i - 20 : i].mean(), vols[i - 20 : i].std(ddof=1)
        mu_d, sd_d = adeltas[i - 20 : i].mean(), adeltas[i - 20 : i].std(ddof=1)
        if not (b["vol"] >= mu_v + 1.5 * sd_v and abs(b["delta"]) >= mu_d + 1.5 * sd_d):
            continue

        direction = 0
        stop = 0.0
        if b["delta"] > 0 and (b["top_ask"] / b["vol"]) >= 0.35 and b["c"] <= b["h"] - 0.50 * rng:
            direction, stop = -1, b["h"] + 1.00
        elif b["delta"] < 0 and (b["bot_bid"] / b["vol"]) >= 0.35 and b["c"] >= b["l"] + 0.50 * rng:
            direction, stop = 1, b["l"] - 1.00
        if direction == 0:
            continue

        of1_events.append({"date": date, "t_close_ns": t_close_ns, "dir": direction, "h": b["h"], "l": b["l"]})
        if len(of1_trades) >= 3:
            continue

        ent_pos = int(np.searchsorted(ts, t_close_ns + DELAY_NS, side="left"))
        if ent_pos >= len(ts):
            continue
        entry = float(px[ent_pos])
        risk = (entry - stop) if direction == 1 else (stop - entry)
        if risk <= 0:
            continue
        target = entry + direction * 2.0 * risk
        deadline = min(t_close_ns + 10 * 60 * 10**9, flat_1555_ns)
        ex_px, ex_ts, reason = tick_exit(ts, px, ent_pos, direction, stop, target, deadline)
        busy_until = ex_ts
        of1_trades.append({
            "date": date, "dir": direction, "entry": entry, "exit": ex_px, "risk": risk,
            "pnl_pts": direction * (ex_px - entry), "reason": reason,
        })

    # ---- OF2: Stacked Imbalance (1m) ----
    busy_until = 0
    for i, b in enumerate(bars):
        m_close = b["min"] + 1  # 09:35 = 575, 15:45 = 945
        if m_close < 575 or m_close > 945:
            continue
        if len(of2_trades) >= 3:
            break
        t_close_ns = int((day_midnight_ny + pd.Timedelta(minutes=m_close)).tz_convert("UTC").value)
        if t_close_ns < busy_until:
            continue
        has_b, has_s, b_top, s_bot = check_stack(b)
        if has_b and has_s:
            continue
        direction, stop = 0, 0.0
        if has_b and b["c"] > b["o"] and b["c"] >= b_top - 1e-9:
            direction, stop = 1, b["l"] - 0.50
        elif has_s and b["c"] < b["o"] and b["c"] <= s_bot + 1e-9:
            direction, stop = -1, b["h"] + 0.50
        if direction == 0:
            continue

        ent_pos = int(np.searchsorted(ts, t_close_ns + DELAY_NS, side="left"))
        if ent_pos >= len(ts):
            continue
        entry = float(px[ent_pos])
        risk = (entry - stop) if direction == 1 else (stop - entry)
        if risk <= 0 or risk > 15.0:
            continue
        target = entry + direction * 1.5 * risk
        deadline = min(t_close_ns + 5 * 60 * 10**9, flat_1555_ns)
        ex_px, ex_ts, reason = tick_exit(ts, px, ent_pos, direction, stop, target, deadline)
        busy_until = ex_ts
        of2_trades.append({
            "date": date, "dir": direction, "entry": entry, "exit": ex_px, "risk": risk,
            "pnl_pts": direction * (ex_px - entry), "reason": reason,
        })

    # ---- OF3: Delta Divergence (5m) ----
    b5_map: dict[int, list[dict]] = {}
    for b in bars:
        slot = ((b["min"] - 570) // 5) * 5 + 570
        b5_map.setdefault(slot, []).append(b)
    b5 = []
    for slot in sorted(b5_map.keys()):
        g = b5_map[slot]
        b5.append({
            "slot": slot,
            "o": g[0]["o"],
            "h": max(x["h"] for x in g),
            "l": min(x["l"] for x in g),
            "c": g[-1]["c"],
            "delta": sum(x["delta"] for x in g),
        })
    busy_until = 0
    for i in range(20, len(b5)):
        x = b5[i]
        m_close = x["slot"] + 5  # 11:15 = 675, 15:30 = 930
        if m_close < 675 or m_close > 930:
            continue
        if len(of3_trades) >= 2:
            break
        t_close_ns = int((day_midnight_ny + pd.Timedelta(minutes=m_close)).tz_convert("UTC").value)
        if t_close_ns < busy_until:
            continue
        h_prev = max(b5[k]["h"] for k in range(i - 20, i))
        l_prev = min(b5[k]["l"] for k in range(i - 20, i))
        rng = x["h"] - x["l"]
        if rng <= 0:
            continue
        direction, stop = 0, 0.0
        if x["h"] > h_prev and x["delta"] < 0 and x["c"] < x["h"] - 0.50 * rng:
            direction, stop = -1, x["h"] + 1.00
        elif x["l"] < l_prev and x["delta"] > 0 and x["c"] > x["l"] + 0.50 * rng:
            direction, stop = 1, x["l"] - 1.00
        if direction == 0:
            continue

        ent_pos = int(np.searchsorted(ts, t_close_ns + DELAY_NS, side="left"))
        if ent_pos >= len(ts):
            continue
        entry = float(px[ent_pos])
        risk = (entry - stop) if direction == 1 else (stop - entry)
        if risk <= 0:
            continue
        target = entry + direction * 2.0 * risk
        deadline = min(t_close_ns + 15 * 60 * 10**9, flat_1555_ns)
        ex_px, ex_ts, reason = tick_exit(ts, px, ent_pos, direction, stop, target, deadline)
        busy_until = ex_ts
        of3_trades.append({
            "date": date, "dir": direction, "entry": entry, "exit": ex_px, "risk": risk,
            "pnl_pts": direction * (ex_px - entry), "reason": reason,
        })

    return of1_trades, of2_trades, of3_trades, of1_events


def summarize_of(trades: list[dict]) -> dict:
    if not trades:
        return {"n": 0, "PASS": False}
    df = pd.DataFrame(trades)
    res = {
        "n": int(len(df)),
        "median_risk_pts": float(df["risk"].median()),
        "reasons": df["reason"].value_counts().to_dict(),
    }
    for lab, k in (("zero", 0.0), ("central", 1.0), ("pessimistic", 2.0)):
        net_pts = df["pnl_pts"] - 2.0 * k * MNQ_COST_PTS
        r_ser = net_pts / df["risk"]
        bp_ser = (net_pts / df["entry"]) * 1e4
        h1 = r_ser[df["date"] < SPLIT_DATE]
        h2 = r_ser[df["date"] >= SPLIT_DATE]
        res[lab] = {
            "mean_R": float(r_ser.mean()),
            "ci_bonf_R": boot_ci(r_ser.to_numpy()),
            "half1_R": float(h1.mean()) if len(h1) else float("nan"),
            "half2_R": float(h2.mean()) if len(h2) else float("nan"),
            "half1_n": int(len(h1)),
            "half2_n": int(len(h2)),
            "mean_bp": float(bp_ser.mean()),
            "win_pct": float((r_ser > 0).mean() * 100.0),
        }
    c = res["central"]
    p = res["pessimistic"]
    res["PASS"] = bool(
        not np.isnan(c["ci_bonf_R"][0])
        and c["ci_bonf_R"][0] > 0
        and c["half1_R"] > 0
        and c["half2_R"] > 0
        and p["mean_R"] > 0
    )
    return res


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    day_chunks, counts = extract_rth_days()
    cnt_s = pd.Series(counts)
    med = float(cnt_s.median())
    thin = sorted(cnt_s.index[cnt_s < 0.5 * med].tolist())
    valid_days = sorted(d for d in day_chunks if d not in thin)
    print(f"Total RTH days: {len(day_chunks)}, median trades/day: {med:.0f}, skipped thin: {len(thin)} ({thin})", flush=True)

    of1_all, of2_all, of3_all, of1_ev = [], [], [], []
    for idx, d in enumerate(valid_days):
        day_df = pd.concat(day_chunks[d], ignore_index=True).sort_values("ts_ns", kind="mergesort")
        t1, t2, t3, ev1 = run_day_strategies(d, day_df)
        of1_all.extend(t1)
        of2_all.extend(t2)
        of3_all.extend(t3)
        of1_ev.extend(ev1)
        if (idx + 1) % 30 == 0:
            print(f"Processed {idx+1}/{len(valid_days)} days... (OF1={len(of1_all)}, OF2={len(of2_all)}, OF3={len(of3_all)})", flush=True)

    pd.DataFrame(of1_ev).to_csv(OUT / "of1_events.csv", index=False)
    res = {
        "days_valid": len(valid_days),
        "days_skipped_thin": len(thin),
        "skipped_thin_list": thin,
        "median_trades_per_day": med,
        "split_date": SPLIT_DATE,
        "cost_pts_per_side": MNQ_COST_PTS,
        "bonferroni_n": N_TESTS,
        "OF1_ABS": summarize_of(of1_all),
        "OF2_STACK": summarize_of(of2_all),
        "OF3_DDIV": summarize_of(of3_all),
    }
    (OUT / "orderflow_result.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
    for k in ("OF1_ABS", "OF2_STACK", "OF3_DDIV"):
        v = res[k]
        if v["n"] == 0:
            print(f"{k}: n=0 PASS=False")
            continue
        c, p, z = v["central"], v["pessimistic"], v["zero"]
        print(
            f"{k:10s} n={v['n']:4d} zero={z['mean_R']:+.3f}R cen={c['mean_R']:+.3f}R "
            f"CI=[{c['ci_bonf_R'][0]:+.3f},{c['ci_bonf_R'][1]:+.3f}] "
            f"h1={c['half1_R']:+.3f} h2={c['half2_R']:+.3f} 2x={p['mean_R']:+.3f}R PASS={v['PASS']}"
        )


if __name__ == "__main__":
    main()
