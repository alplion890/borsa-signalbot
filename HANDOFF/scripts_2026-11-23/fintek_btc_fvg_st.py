"""Preregistered test: Fintek Mustafa YouTube BTC strategy (15m doji+bull + 5m FVG + 1m Supertrend 10,3).

Prereg: HANDOFF/fintek_btc_fvg_st_onkayit_2026-11-22.md (commit 20f58b2).
Downloads Binance Spot BTCUSDT 1m monthly archives (2024-11..2026-10) into git-ignored cache,
then runs the single preregistered rule with Maven measured BTCUSD cost.

Run from strategy-lab with vectorbt-lab venv:
  python ../HANDOFF/scripts_2026-11-23/fintek_btc_fvg_st.py
"""
from __future__ import annotations

import io
import json
import urllib.request
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

CACHE = Path("outputs/intraday/cache/binance_1m")
OUT = Path("outputs/intraday/fintek_btc_fvg_st")
PROFILE = Path("outputs/intraday/mt5_bridge/reality_profile.csv")
MONTHS = [
    f"{y}-{m:02d}"
    for y, m in (
        [(2024, 11), (2024, 12)]
        + [(2025, m) for m in range(1, 13)]
        + [(2026, m) for m in range(1, 11)]
    )
]
SPLIT_TS = pd.Timestamp("2025-11-01", tz="UTC")
SEED, REPS = 20261122, 10_000


def fetch_binance_1m() -> pd.DataFrame:
    CACHE.mkdir(parents=True, exist_ok=True)
    frames = []
    for ym in MONTHS:
        pq = CACHE / f"BTCUSDT_1m_{ym}.parquet"
        if not pq.exists():
            url = f"https://data.binance.vision/data/spot/monthly/klines/BTCUSDT/1m/BTCUSDT-1m-{ym}.zip"
            print(f"Downloading {ym}...", flush=True)
            try:
                with urllib.request.urlopen(url, timeout=60) as resp:
                    zbytes = resp.read()
            except Exception as exc:
                print(f"  WARN {ym} failed: {exc}", flush=True)
                continue
            with zipfile.ZipFile(io.BytesIO(zbytes)) as zf:
                name = zf.namelist()[0]
                with zf.open(name) as f:
                    raw = pd.read_csv(f, header=None, usecols=[0, 1, 2, 3, 4, 5])
            raw.columns = ["open_time", "open", "high", "low", "close", "volume"]
            # Handle both ms (13 digits) and us (16 digits, Binance 2025+)
            ot = raw["open_time"].astype(np.int64)
            unit = "us" if ot.iloc[0] > 10**14 else "ms"
            raw["ts"] = pd.to_datetime(ot, unit=unit, utc=True)
            df_m = raw.set_index("ts")[["open", "high", "low", "close", "volume"]].astype(float)
            df_m.to_parquet(pq)
        frames.append(pd.read_parquet(pq))
    df = pd.concat(frames).sort_index()
    df = df[~df.index.duplicated()]
    return df


def supertrend_dir(high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int = 10, mult: float = 3.0) -> np.ndarray:
    """Standard Wilder-ATR Supertrend direction (+1 up/green, -1 down/red)."""
    n = len(close)
    tr = np.empty(n, dtype=float)
    tr[0] = high[0] - low[0]
    prev_c = close[:-1]
    tr[1:] = np.maximum(high[1:] - low[1:], np.maximum(np.abs(high[1:] - prev_c), np.abs(low[1:] - prev_c)))
    # Wilder RMA
    atr = np.full(n, np.nan)
    atr[period - 1] = tr[:period].mean()
    alpha = 1.0 / period
    for i in range(period, n):
        atr[i] = atr[i - 1] * (1.0 - alpha) + tr[i] * alpha

    hl2 = (high + low) * 0.5
    ub = hl2 + mult * atr
    lb = hl2 - mult * atr

    final_ub = np.copy(ub)
    final_lb = np.copy(lb)
    st_dir = np.zeros(n, dtype=np.int8)
    st_dir[period - 1] = 1
    for i in range(period, n):
        final_ub[i] = ub[i] if (ub[i] < final_ub[i - 1] or close[i - 1] > final_ub[i - 1]) else final_ub[i - 1]
        final_lb[i] = lb[i] if (lb[i] > final_lb[i - 1] or close[i - 1] < final_lb[i - 1]) else final_lb[i - 1]
        if st_dir[i - 1] == 1:
            st_dir[i] = -1 if close[i] < final_lb[i] else 1
        else:
            st_dir[i] = 1 if close[i] > final_ub[i] else -1
    return st_dir


def simulate_strategy(df1m: pd.DataFrame, side: str = "long") -> pd.DataFrame:
    df5m = df1m.resample("5min", label="left", closed="left").agg(
        {"open": "first", "high": "max", "low": "min", "close": "last"}
    ).dropna()
    df15m = df1m.resample("15min", label="left", closed="left").agg(
        {"open": "first", "high": "max", "low": "min", "close": "last"}
    ).dropna()

    # 1. 15m setups
    o15, h15, l15, c15 = (df15m[k].to_numpy() for k in ("open", "high", "low", "close"))
    r15 = h15 - l15
    body15 = np.abs(c15 - o15)
    doji = (r15 > 0) & (body15 / np.where(r15 > 0, r15, 1.0) <= 0.25)

    setup_times: list[pd.Timestamp] = []
    idx15 = df15m.index
    for i in range(4, len(df15m)):
        if r15[i] <= 0 or not doji[i - 1]:
            continue
        if side == "long":
            prior_dn = c15[i - 1] < o15[i - 4]
            strong_bull = (c15[i] > o15[i]) and ((c15[i] - o15[i]) / r15[i] >= 0.60) and (c15[i] > h15[i - 1])
            if prior_dn and strong_bull:
                setup_times.append(idx15[i] + pd.Timedelta(minutes=15))  # close timestamp
        else:
            prior_up = c15[i - 1] > o15[i - 4]
            strong_bear = (c15[i] < o15[i]) and ((o15[i] - c15[i]) / r15[i] >= 0.60) and (c15[i] < l15[i - 1])
            if prior_up and strong_bear:
                setup_times.append(idx15[i] + pd.Timedelta(minutes=15))

    # 2. 5m FVGs
    h5, l5 = df5m["high"].to_numpy(), df5m["low"].to_numpy()
    idx5 = df5m.index
    fvgs: list[tuple[pd.Timestamp, float, float]] = []  # (close_ts, fvg_top, fvg_bot)
    for k in range(2, len(df5m)):
        if side == "long":
            if l5[k] > h5[k - 2]:
                top, bot = float(l5[k]), float(h5[k - 2])
                if (top - bot) / top >= 0.0015:
                    fvgs.append((idx5[k] + pd.Timedelta(minutes=5), top, bot))
        else:
            if h5[k] < l5[k - 2]:
                top, bot = float(l5[k - 2]), float(h5[k])
                if (top - bot) / bot >= 0.0015:
                    fvgs.append((idx5[k] + pd.Timedelta(minutes=5), top, bot))

    # Filter FVGs that occur within [t_setup - 15m, t_setup + 60m] of any 15m setup
    setup_ns = np.array([t.value for t in setup_times], dtype=np.int64)
    active_fvgs: list[tuple[int, float, float]] = []
    for f_ts, top, bot in fvgs:
        fn = f_ts.value
        # Find latest setup_ts <= fn + 15m (Wait: no look-ahead! Setup must be closed BEFORE or AT entry)
        # Wait: FVG formed during the 15m bull candle is known at t_setup, entry only after max(f_ts, t_setup)
        # Find any setup_ns such that setup_ns - 15m <= fn <= setup_ns + 60m
        pos = int(np.searchsorted(setup_ns, fn + 15 * 60 * 10**9, side="right")) - 1
        if pos >= 0:
            s_ns = int(setup_ns[pos])
            if s_ns - 15 * 60 * 10**9 <= fn <= s_ns + 60 * 60 * 10**9:
                ready_ns = max(fn, s_ns)  # no look-ahead: both 15m setup and 5m FVG must be closed
                active_fvgs.append((ready_ns, top, bot))

    # 3. 1m Supertrend(10, 3) and trade simulation
    o1, h1, l1, c1 = (df1m[k].to_numpy() for k in ("open", "high", "low", "close"))
    ts1 = df1m.index.asi8
    st1 = supertrend_dir(h1, l1, c1, 10, 3.0)
    d_sign = 1 if side == "long" else -1

    trades = []
    busy_until_idx = -1
    for ready_ns, fvg_top, fvg_bot in active_fvgs:
        start_i = int(np.searchsorted(ts1, ready_ns, side="left"))
        if start_i <= busy_until_idx or start_i >= len(ts1) - 2:
            continue
        end_search = min(start_i + 60, len(ts1) - 1)
        entry_i = -1
        for i in range(start_i, end_search):
            if side == "long":
                touched = (l1[i] <= fvg_top) and (l1[i] > fvg_bot)
                st_ok = st1[i] == 1
                if touched and st_ok and c1[i] > fvg_bot:
                    entry_i = i
                    break
                if l1[i] <= fvg_bot:
                    break  # FVG invalidated
            else:
                touched = (h1[i] >= fvg_bot) and (h1[i] < fvg_top)
                st_ok = st1[i] == -1
                if touched and st_ok and c1[i] < fvg_top:
                    entry_i = i
                    break
                if h1[i] >= fvg_top:
                    break
        if entry_i < 0:
            continue

        entry = float(c1[entry_i])
        stop = fvg_bot if side == "long" else fvg_top
        risk = (entry - stop) if side == "long" else (stop - entry)
        if risk <= 0:
            continue
        target = entry + d_sign * 2.0 * risk

        max_exit = min(entry_i + 1440, len(ts1) - 1)
        exit_px = float(c1[max_exit])
        exit_i = max_exit
        reason = "time_24h"
        for j in range(entry_i + 1, max_exit + 1):
            if side == "long":
                if l1[j] <= stop:
                    exit_px, exit_i, reason = min(float(o1[j]), stop), j, "stop"
                    break
                if h1[j] >= target:
                    exit_px, exit_i, reason = max(float(o1[j]), target), j, "target"
                    break
            else:
                if h1[j] >= stop:
                    exit_px, exit_i, reason = max(float(o1[j]), stop), j, "stop"
                    break
                if l1[j] <= target:
                    exit_px, exit_i, reason = min(float(o1[j]), target), j, "target"
                    break
        busy_until_idx = exit_i
        trades.append({
            "entry_time": df1m.index[entry_i],
            "exit_time": df1m.index[exit_i],
            "dir": d_sign,
            "entry": entry,
            "exit": exit_px,
            "stop": stop,
            "risk": risk,
            "reason": reason,
        })
    return pd.DataFrame(trades)


def boot_ci(x: np.ndarray) -> list[float]:
    if len(x) < 10:
        return [float("nan"), float("nan")]
    rng = np.random.default_rng(SEED)
    m = x[rng.integers(0, len(x), size=(REPS, len(x)))].mean(axis=1)
    return np.quantile(m, [0.025, 0.975]).tolist()


def evaluate(tr: pd.DataFrame, cost_frac: float) -> dict:
    if tr.empty:
        return {"n": 0, "PASS": False}
    res = {
        "n": int(len(tr)),
        "median_risk_pct": float((tr["risk"] / tr["entry"]).median() * 100.0),
        "reasons": tr["reason"].value_counts().to_dict(),
    }
    for lab, k in (("zero", 0.0), ("central", 1.0), ("pessimistic", 2.0)):
        cost_pts = k * cost_frac * (tr["entry"] + tr["exit"])
        net_pts = tr["dir"] * (tr["exit"] - tr["entry"]) - cost_pts
        r_ser = net_pts / tr["risk"]
        y1 = r_ser[tr["entry_time"] < SPLIT_TS]
        y2 = r_ser[tr["entry_time"] >= SPLIT_TS]
        res[lab] = {
            "mean_R": float(r_ser.mean()),
            "ci95_R": boot_ci(r_ser.to_numpy()),
            "year1_R": float(y1.mean()) if len(y1) else float("nan"),
            "year2_R": float(y2.mean()) if len(y2) else float("nan"),
            "year1_n": int(len(y1)),
            "year2_n": int(len(y2)),
            "win_pct": float((r_ser > 0).mean() * 100.0),
        }
    c, p = res["central"], res["pessimistic"]
    res["PASS"] = bool(
        not np.isnan(c["ci95_R"][0])
        and c["ci95_R"][0] > 0
        and c["year1_R"] > 0
        and c["year2_R"] > 0
        and p["mean_R"] > 0
    )
    return res


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    prof = pd.read_csv(PROFILE).set_index("symbol")["real_cost_per_side_central"]
    btc_cost = float(prof["BTCUSD"]) if "BTCUSD" in prof.index else float(prof["BTCUSDT"])

    df1m = fetch_binance_1m()
    print(f"Loaded BTCUSDT 1m: {len(df1m):,} bars ({df1m.index[0]} -> {df1m.index[-1]})", flush=True)

    tr_long = simulate_strategy(df1m, "long")
    tr_short = simulate_strategy(df1m, "short")
    tr_long.to_csv(OUT / "long_trades.csv", index=False)
    tr_short.to_csv(OUT / "short_trades.csv", index=False)

    res = {
        "bars_1m": int(len(df1m)),
        "from": str(df1m.index[0]),
        "to": str(df1m.index[-1]),
        "cost_per_side_frac": btc_cost,
        "LONG_PRIMARY": evaluate(tr_long, btc_cost),
        "SHORT_INFO_ONLY": evaluate(tr_short, btc_cost),
    }
    (OUT / "result.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
    for k in ("LONG_PRIMARY", "SHORT_INFO_ONLY"):
        v = res[k]
        if v["n"] == 0:
            print(f"{k}: n=0 PASS=False")
            continue
        c, p, z = v["central"], v["pessimistic"], v["zero"]
        print(
            f"{k:16s} n={v['n']:4d} zero={z['mean_R']:+.3f}R cen={c['mean_R']:+.3f}R "
            f"CI=[{c['ci95_R'][0]:+.3f},{c['ci95_R'][1]:+.3f}] "
            f"y1={c['year1_R']:+.3f}(n{c['year1_n']}) y2={c['year2_R']:+.3f}(n{c['year2_n']}) "
            f"2x={p['mean_R']:+.3f}R WR={c['win_pct']:.1f}% PASS={v['PASS']}"
        )


if __name__ == "__main__":
    main()
