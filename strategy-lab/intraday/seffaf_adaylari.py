"""Preregistered transparent-source candidates B1-B7 (2026-11-18).

Preregistration: HANDOFF/seffaf_kaynak_adaylari_onkayit_2026-11-18.md
Total independent tests: 9 (Bonferroni alpha = 0.05 / 9).

B6 intra-bar assumption: when today's open < yesterday's low and today's high >=
yesterday's low, buy stop fills at yesterday's low and exits at today's close
(mirror for shorts). Although today's low < yesterday's low on a long fill,
intra-bar ordering is unknown on daily bars, so stop is assumed NOT hit after fill.

    python -m intraday.seffaf_adaylari
    python -m intraday.seffaf_adaylari --only B1 B3 B7
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

from .history_fetch import load_history
from .kaynak_adaylari import SPLIT, boot_bounds, cost_of, judge, stats
from .noise_band_research import previous_session, sessions as nb_sessions, simulate as nb_simulate

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "outputs" / "intraday" / "seffaf_adaylari"
BTC_1H = ROOT / "outputs" / "intraday" / "cache" / "binance" / "BTCUSDT_1h.csv"
NY = ZoneInfo("America/New_York")

N_TESTS = 9
ALPHA = 0.05 / N_TESTS / 2.0
B2_LOOKBACKS = (5, 10, 20, 30, 60, 90, 150, 250, 360)
B7_SWAP_PER_NIGHT = 0.000118
B2_SWAP_ANNUAL = 0.30


# ---------- Resampling & Indicators ----------

def _ensure_utc(df: pd.DataFrame) -> pd.DataFrame:
    if df.index.tz is None:
        return df.tz_localize("UTC")
    return df.tz_convert("UTC")


def resample_ohlc(df_5m: pd.DataFrame, rule: str) -> pd.DataFrame:
    """Resample 5m bars with left-labeled, left-closed bins; drop empty bars."""
    agg = {"open": "first", "high": "max", "low": "min", "close": "last"}
    if "volume" in df_5m.columns:
        agg["volume"] = "sum"
    return df_5m.resample(rule, label="left", closed="left").agg(agg).dropna(
        subset=["open", "high", "low", "close"]
    )


def resample_nq_daily(df_5m: pd.DataFrame) -> pd.DataFrame:
    """Aggregate NY regular session (09:30-16:00 ET) into one bar per NY date."""
    utc = _ensure_utc(df_5m)
    ny = utc.tz_convert(NY)
    mins = ny.index.hour * 60 + ny.index.minute
    reg = ny.loc[(mins >= 570) & (mins < 960)].copy()
    reg["_date"] = reg.index.normalize().tz_localize(None)
    daily = reg.groupby("_date").agg(
        {"open": "first", "high": "max", "low": "min", "close": "last"}
    )
    daily.index = pd.DatetimeIndex(daily.index, name="date")
    return daily.dropna()


def resample_btc_daily(df_1h: pd.DataFrame) -> pd.DataFrame:
    """Aggregate UTC hourly BTC bars into UTC calendar daily OHLC."""
    return resample_ohlc(df_1h, "1D")


def load_btc_1h(path: Path = BTC_1H) -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=["ts"]).set_index("ts")
    return df.sort_index()


def wilder_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    prev_c = df["close"].shift(1)
    tr = pd.concat(
        [df["high"] - df["low"], (df["high"] - prev_c).abs(), (df["low"] - prev_c).abs()],
        axis=1,
    ).max(axis=1)
    return tr.ewm(alpha=1.0 / period, adjust=False).mean()


# ---------- Evaluation Helpers ----------

def _series_eval(s: pd.Series, block: int) -> dict:
    s = s.dropna().sort_index()
    early, late = s[s.index < SPLIT], s[s.index >= SPLIT]
    return {
        "all": stats(s) if len(s) > 0 else None,
        "ci_bp": boot_bounds(s.to_numpy(), ALPHA, block) if len(s) > 0 else [0.0, 0.0],
        "pre2022": stats(early) if len(early) > 2 else None,
        "2022+": stats(late) if len(late) > 2 else None,
    }


def _check_pass(res: dict) -> bool:
    c, p = res["central"], res["pessimistic"]
    if not c["all"] or not c["pre2022"] or not c["2022+"] or not p["all"]:
        return False
    return bool(
        c["all"]["mean_bp"] > 0
        and c["ci_bp"][0] > 0
        and c["pre2022"]["mean_bp"] > 0
        and c["2022+"]["mean_bp"] > 0
        and p["all"]["mean_bp"] > 0
    )


def _eval_daily_variants(
    zero: pd.Series, central: pd.Series, pess: pd.Series, block: int,
    cost: float, extra: dict | None = None,
) -> dict:
    out: dict = {
        "cost_per_side": cost,
        "n_tests": N_TESTS,
        "zero": _series_eval(zero, block),
        "central": _series_eval(central, block),
        "pessimistic": _series_eval(pess, block),
    }
    if extra:
        out["extra"] = extra
    out["PASS"] = _check_pass(out)
    return out


# ---------- B1: Noise Band + 5m Pullback Overlay ----------

def _nb_overlay_day(day: pd.DataFrame, upper: np.ndarray, lower: np.ndarray,
                    vwap: np.ndarray, date: str) -> list[dict]:
    """Simulate one NB session with 5m pullback delay on entries and non-EOD exits."""
    o = day["open"].to_numpy(float)
    c = day["close"].to_numpy(float)
    decision_bars = set(range(5, 72, 6))
    trades: list[dict] = []
    pos: dict | None = None
    pending_dir = 0
    pending_exit = False

    for k in range(5, len(c) - 1):
        ret5 = c[k] / c[k - 1] - 1.0
        if pos is None:
            if pending_dir == 0 and k in decision_bars:
                pending_dir = 1 if c[k] > upper[k] else (-1 if c[k] < lower[k] else 0)
            if pending_dir != 0 and ((pending_dir == 1 and ret5 < 0) or (pending_dir == -1 and ret5 > 0)):
                pos = {"date": date, "direction": pending_dir, "entry": float(o[k + 1]),
                       "entry_time": str(day.index[k + 1])}
                pending_dir = 0
        else:
            d = int(pos["direction"])
            if not pending_exit and k in decision_bars:
                pending_exit = (c[k] <= max(upper[k], vwap[k])) if d == 1 else (c[k] >= min(lower[k], vwap[k]))
            if pending_exit and ((d == 1 and ret5 > 0) or (d == -1 and ret5 < 0)):
                pos.update(exit=float(o[k + 1]), exit_time=str(day.index[k + 1]), reason="band_vwap")
                trades.append(pos)
                pos = None
                pending_exit = False
    if pos is not None:
        pos.update(exit=float(c[-1]), exit_time=str(day.index[-1] + pd.Timedelta(minutes=5)),
                   reason="session_close")
        trades.append(pos)
    return trades


def simulate_nb_overlay(frame: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """Run NB signal logic with 5m pullback overlay across complete NY sessions."""
    days = nb_sessions(_ensure_utc(frame))
    history, trades, eligible = [], [], []
    for date, day in days.items():
        vals = day[["open", "high", "low", "close", "volume"]].to_numpy(float)
        o, h, l, c, v = vals.T
        moves = np.abs(c / o[0] - 1.0)
        if len(history) < 14 or previous_session(date) not in days:
            history.append(moves)
            continue
        sigma = np.mean(history[-14:], axis=0)
        prev = float(days[previous_session(date)]["close"].iloc[-1])
        upper, lower = max(o[0], prev) * (1.0 + sigma), min(o[0], prev) * (1.0 - sigma)
        vwap = np.cumsum((h + l + c) / 3.0 * v) / np.cumsum(v)
        eligible.append(date)
        trades.extend(_nb_overlay_day(day, upper, lower, vwap, date))
        history.append(moves)
    return pd.DataFrame(trades), eligible


def _nb_daily_series(trades: pd.DataFrame, dates: list[str], cost: float, factor: float) -> pd.Series:
    daily = pd.Series(0.0, index=pd.to_datetime(dates))
    if not trades.empty:
        net = trades["direction"] * (trades["exit"] / trades["entry"] - 1.0) - factor * 2.0 * cost
        grp = net.groupby(pd.to_datetime(trades["date"])).sum()
        daily.update(grp)
    return daily


def run_b1(df_nq_5m: pd.DataFrame | None = None) -> tuple[dict, pd.DataFrame]:
    raw = _ensure_utc(df_nq_5m if df_nq_5m is not None else load_history("NASDAQ100", "5m", start_year=2012))
    cost = cost_of("NASDAQ100")
    base_tr, dates = nb_simulate(raw)
    ov_tr, _ = simulate_nb_overlay(raw)

    d_zero = _nb_daily_series(ov_tr, dates, cost, 0.0) - _nb_daily_series(base_tr, dates, cost, 0.0)
    d_cent = _nb_daily_series(ov_tr, dates, cost, 1.0) - _nb_daily_series(base_tr, dates, cost, 1.0)
    d_pess = _nb_daily_series(ov_tr, dates, cost, 2.0) - _nb_daily_series(base_tr, dates, cost, 2.0)

    extra = {
        "baseline_trades": int(len(base_tr)),
        "overlay_trades": int(len(ov_tr)),
        "baseline_central_mean_bp": float(_nb_daily_series(base_tr, dates, cost, 1.0).mean() * 1e4),
        "overlay_central_mean_bp": float(_nb_daily_series(ov_tr, dates, cost, 1.0).mean() * 1e4),
    }
    res = _eval_daily_variants(d_zero, d_cent, d_pess, block=5, cost=cost, extra=extra)
    daily_df = pd.DataFrame({
        "date": d_zero.index,
        "baseline_gross": _nb_daily_series(base_tr, dates, cost, 0.0).to_numpy(),
        "overlay_gross": _nb_daily_series(ov_tr, dates, cost, 0.0).to_numpy(),
        "diff_zero": d_zero.to_numpy(),
        "diff_central": d_cent.to_numpy(),
        "diff_pessimistic": d_pess.to_numpy(),
    })
    return res, daily_df


# ---------- B2: BTC Donchian Ensemble Long-Only ----------

def _donchian_model_pos(close: np.ndarray, n: int) -> np.ndarray:
    s = pd.Series(close)
    rmax = s.rolling(n).max().to_numpy()
    rmin = s.rolling(n).min().to_numpy()
    mid = (rmax + rmin) / 2.0
    pos = np.zeros(len(close), dtype=float)
    in_pos = False
    stop = np.nan
    for t in range(len(close)):
        if np.isnan(rmax[t]) or np.isnan(rmin[t]):
            continue
        if not in_pos:
            if close[t] >= rmax[t]:
                in_pos = True
                stop = mid[t]
                pos[t] = 1.0
        else:
            stop = max(stop, mid[t])
            if close[t] < stop:
                in_pos = False
                stop = np.nan
            else:
                pos[t] = 1.0
    return pos


def btc_donchian_weights(close: pd.Series, lookbacks: tuple[int, ...] = B2_LOOKBACKS) -> pd.DataFrame:
    """Compute per-lookback daily weights capped at 2.0x total leverage."""
    ret = close.pct_change()
    vol90 = ret.rolling(90).std() * np.sqrt(365.0)
    lev = np.minimum(2.0, 0.25 / vol90.replace(0.0, np.nan)).fillna(0.0).to_numpy()
    w_unit = lev / float(len(lookbacks))
    arr = close.to_numpy(float)
    cols = {f"w_{n}": _donchian_model_pos(arr, n) * w_unit for n in lookbacks}
    return pd.DataFrame(cols, index=close.index)


def run_b2(df_btc_daily: pd.DataFrame | None = None) -> tuple[dict, pd.DataFrame]:
    daily = df_btc_daily if df_btc_daily is not None else resample_btc_daily(load_btc_1h())
    cost = cost_of("BTCUSDT")
    close = daily["close"]
    ret = close.pct_change().fillna(0.0)
    weights = btc_donchian_weights(close)

    # Start evaluation once 90-day vol window is populated
    valid_mask = close.pct_change().rolling(90).std().notna()
    w_prev = weights.shift(1).fillna(0.0)
    gross = (w_prev.sum(axis=1) * ret).loc[valid_mask]
    turnover = (weights - w_prev).abs().sum(axis=1).loc[valid_mask]
    total_w_prev = w_prev.sum(axis=1).loc[valid_mask]

    net_cent = gross - cost * turnover
    net_pess = gross - 2.0 * cost * turnover
    swap = (B2_SWAP_ANNUAL / 365.0) * total_w_prev
    net_swap = net_cent - swap

    res = _eval_daily_variants(
        gross, net_cent, net_pess, block=5, cost=cost,
        extra={
            "mean_total_weight": float(total_w_prev.mean()),
            "mean_daily_turnover": float(turnover.mean()),
            "swap_central": _series_eval(net_swap, block=5),
        },
    )
    out_df = pd.DataFrame({
        "date": gross.index,
        "total_weight": total_w_prev.to_numpy(),
        "turnover": turnover.to_numpy(),
        "gross": gross.to_numpy(),
        "net_central": net_cent.to_numpy(),
        "net_pessimistic": net_pess.to_numpy(),
        "net_central_swap": net_swap.to_numpy(),
    })
    return res, out_df


# ---------- B3: XAU H1 Gold Trend Breakout Lite ----------

def _b3_daily_ema_flags(d1: pd.DataFrame, h1_index: pd.DatetimeIndex) -> tuple[np.ndarray, np.ndarray]:
    ema = d1["close"].ewm(span=100, adjust=False).mean()
    # Use only completed UTC days: shift by 1 day before mapping to H1 date
    rising = (ema > ema.shift(3)).shift(1).fillna(False)
    falling = (ema < ema.shift(3)).shift(1).fillna(False)
    h1_dates = h1_index.normalize()
    return (
        rising.reindex(h1_dates).fillna(False).to_numpy(bool),
        falling.reindex(h1_dates).fillna(False).to_numpy(bool),
    )


def simulate_b3(h1: pd.DataFrame, d1: pd.DataFrame) -> pd.DataFrame:
    """Simulate Gold Trend Breakout Lite on H1 + completed D1 EMA100."""
    atr = wilder_atr(h1, 14).to_numpy(float)
    prev_hi = h1["high"].shift(1).rolling(120).max().to_numpy(float)
    prev_lo = h1["low"].shift(1).rolling(120).min().to_numpy(float)
    ema_up, ema_dn = _b3_daily_ema_flags(d1, h1.index)

    o, h, l, c = (h1[col].to_numpy(float) for col in ("open", "high", "low", "close"))
    idx = h1.index
    trades: list[dict] = []
    pos: dict | None = None

    for i in range(len(h1)):
        long_sig = (not np.isnan(prev_hi[i])) and (c[i] > prev_hi[i]) and ema_up[i]
        short_sig = (not np.isnan(prev_lo[i])) and (c[i] < prev_lo[i]) and ema_dn[i]

        if pos is not None:
            d = int(pos["direction"])
            exit_px: float | None = None
            reason = ""
            if pos.get("exit_next_open"):
                exit_px, reason = o[i], "opposite_signal"
            elif d == 1 and l[i] <= pos["stop"]:
                exit_px, reason = min(o[i], pos["stop"]), "stop"
            elif d == -1 and h[i] >= pos["stop"]:
                exit_px, reason = max(o[i], pos["stop"]), "stop"

            if exit_px is not None:
                gross = d * (exit_px / pos["entry"] - 1.0)
                trades.append({
                    "entry_time": pos["entry_time"], "exit_time": idx[i],
                    "direction": d, "entry": pos["entry"], "exit": float(exit_px),
                    "gross": float(gross), "reason": reason,
                })
                pos = None
            else:
                if d == 1 and (h[i] - pos["entry"]) >= pos["r"]:
                    pos["stop"] = max(pos["stop"], pos["entry"] + 0.1 * pos["r"])
                elif d == -1 and (pos["entry"] - l[i]) >= pos["r"]:
                    pos["stop"] = min(pos["stop"], pos["entry"] - 0.1 * pos["r"])
                if (d == 1 and short_sig) or (d == -1 and long_sig):
                    pos["exit_next_open"] = True
                continue

        if pos is None and i + 1 < len(h1) and not np.isnan(atr[i]) and atr[i] > 0:
            if long_sig and not short_sig:
                r = 3.0 * atr[i]
                pos = {"entry_time": idx[i + 1], "direction": 1, "entry": o[i + 1],
                       "r": r, "stop": o[i + 1] - r}
            elif short_sig and not long_sig:
                r = 3.0 * atr[i]
                pos = {"entry_time": idx[i + 1], "direction": -1, "entry": o[i + 1],
                       "r": r, "stop": o[i + 1] + r}

    return pd.DataFrame(trades)


def run_b3(df_xau_5m: pd.DataFrame | None = None) -> tuple[dict, pd.DataFrame]:
    raw = df_xau_5m if df_xau_5m is not None else load_history("XAUUSD", "5m", start_year=2012)
    h1, d1 = resample_ohlc(raw, "1h"), resample_ohlc(raw, "1D")
    tr = simulate_b3(h1, d1)
    gross = pd.Series(tr["gross"].to_numpy(), index=pd.to_datetime(tr["entry_time"])) if not tr.empty else pd.Series(dtype=float)
    res = judge(gross, cost_of("XAUUSD"), n_tests=N_TESTS, block=1)
    return res, tr


# ---------- B4: XAU M30 EMA Cross ----------

def simulate_b4(m30: pd.DataFrame) -> pd.DataFrame:
    """Simulate XAU M30 EMA20/50/200 cross with 1% SL and 18:00 UTC flat rule."""
    c_s = m30["close"]
    e20 = c_s.ewm(span=20, adjust=False).mean().to_numpy(float)
    e50 = c_s.ewm(span=50, adjust=False).mean().to_numpy(float)
    e200 = c_s.ewm(span=200, adjust=False).mean().to_numpy(float)
    o, h, l, c = (m30[col].to_numpy(float) for col in ("open", "high", "low", "close"))
    idx = m30.index
    close_ts = idx + pd.Timedelta(minutes=30)
    close_mins = close_ts.hour * 60 + close_ts.minute

    trades: list[dict] = []
    pos: dict | None = None

    for i in range(1, len(m30)):
        if pos is not None:
            d = int(pos["direction"])
            exit_px: float | None = None
            reason = ""
            if idx[i] >= pos["flat_at"]:
                exit_px, reason = o[i], "flat_18utc"
            elif d == 1 and l[i] <= pos["stop"]:
                exit_px, reason = min(o[i], pos["stop"]), "stop"
            elif d == -1 and h[i] >= pos["stop"]:
                exit_px, reason = max(o[i], pos["stop"]), "stop"

            if exit_px is not None:
                trades.append({
                    "entry_time": pos["entry_time"], "exit_time": idx[i],
                    "direction": d, "entry": pos["entry"], "exit": float(exit_px),
                    "gross": float(d * (exit_px / pos["entry"] - 1.0)), "reason": reason,
                })
                pos = None
                continue

        if pos is None and i + 1 < len(m30) and 300 <= close_mins[i] <= 1020:
            cross_up = e20[i] > e50[i] and e20[i - 1] <= e50[i - 1]
            cross_dn = e20[i] < e50[i] and e20[i - 1] >= e50[i - 1]
            d = 0
            if cross_up and c[i] > e20[i] and c[i] > e200[i]:
                d = 1
            elif cross_dn and c[i] < e20[i] and c[i] < e200[i]:
                d = -1
            if d != 0 and idx[i + 1] < idx[i + 1].normalize() + pd.Timedelta(hours=18):
                ent = o[i + 1]
                pos = {
                    "entry_time": idx[i + 1],
                    "direction": d,
                    "entry": ent,
                    "stop": ent * (0.99 if d == 1 else 1.01),
                    "flat_at": idx[i + 1].normalize() + pd.Timedelta(hours=18),
                }

    return pd.DataFrame(trades)


def run_b4(df_xau_5m: pd.DataFrame | None = None) -> tuple[dict, pd.DataFrame]:
    raw = df_xau_5m if df_xau_5m is not None else load_history("XAUUSD", "5m", start_year=2012)
    m30 = resample_ohlc(raw, "30min")
    tr = simulate_b4(m30)
    gross = pd.Series(tr["gross"].to_numpy(), index=pd.to_datetime(tr["entry_time"])) if not tr.empty else pd.Series(dtype=float)
    res = judge(gross, cost_of("XAUUSD"), n_tests=N_TESTS, block=1)
    return res, tr


# ---------- B5: Turtle Soup Daily ----------

def simulate_b5(daily: pd.DataFrame) -> pd.DataFrame:
    """Simulate Raschke Turtle Soup on daily bars (NQ or XAU)."""
    atr = wilder_atr(daily, 14).shift(1).to_numpy(float)
    o, h, l, c = (daily[col].to_numpy(float) for col in ("open", "high", "low", "close"))
    idx = daily.index
    trades: list[dict] = []
    pos: dict | None = None

    for i in range(20, len(daily)):
        if pos is not None:
            d = int(pos["direction"])
            if d == -1 and h[i] >= pos["stop"]:
                exit_px, reason = max(o[i], pos["stop"]), "stop"
            elif d == 1 and l[i] <= pos["stop"]:
                exit_px, reason = min(o[i], pos["stop"]), "stop"
            else:
                exit_px, reason = c[i], "next_close"
            trades.append({
                "entry_time": pos["entry_time"], "exit_time": idx[i],
                "direction": d, "entry": pos["entry"], "exit": float(exit_px),
                "gross": float(d * (exit_px / pos["entry"] - 1.0)), "reason": reason,
            })
            pos = None
            continue

        if np.isnan(atr[i]) or (h[i] - l[i]) > 3.0 * atr[i]:
            continue
        win_h, win_l = h[i - 20 : i], l[i - 20 : i]
        max_h, min_l = win_h.max(), win_l.min()
        age_h = 20 - int(np.where(win_h == max_h)[0][-1])
        age_l = 20 - int(np.where(win_l == min_l)[0][-1])

        short_sig = h[i] > max_h and age_h >= 4 and c[i] < max_h
        long_sig = l[i] < min_l and age_l >= 4 and c[i] > min_l
        if short_sig and not long_sig and i + 1 < len(daily):
            pos = {"entry_time": idx[i], "direction": -1, "entry": c[i], "stop": h[i]}
        elif long_sig and not short_sig and i + 1 < len(daily):
            pos = {"entry_time": idx[i], "direction": 1, "entry": c[i], "stop": l[i]}

    return pd.DataFrame(trades)


def run_b5(sym: str, df_5m: pd.DataFrame | None = None) -> tuple[dict, pd.DataFrame]:
    raw = df_5m if df_5m is not None else load_history(sym, "5m", start_year=2012)
    daily = resample_nq_daily(raw) if sym == "NASDAQ100" else resample_ohlc(raw, "1D")
    tr = simulate_b5(daily)
    gross = pd.Series(tr["gross"].to_numpy(), index=pd.to_datetime(tr["entry_time"])) if not tr.empty else pd.Series(dtype=float)
    res = judge(gross, cost_of(sym), n_tests=N_TESTS, block=1)
    return res, tr


# ---------- B6: Williams Oops Daily ----------

def simulate_b6(daily: pd.DataFrame) -> pd.DataFrame:
    """Simulate Williams Oops (n=1 exit at today's close) on daily bars."""
    o, h, l, c = (daily[col].to_numpy(float) for col in ("open", "high", "low", "close"))
    idx = daily.index
    trades: list[dict] = []

    for i in range(1, len(daily)):
        if o[i] < l[i - 1] and h[i] >= l[i - 1]:
            fill = float(l[i - 1])
            trades.append({
                "entry_time": idx[i], "exit_time": idx[i], "direction": 1,
                "entry": fill, "exit": float(c[i]),
                "gross": float(c[i] / fill - 1.0), "reason": "close",
            })
        elif o[i] > h[i - 1] and l[i] <= h[i - 1]:
            fill = float(h[i - 1])
            trades.append({
                "entry_time": idx[i], "exit_time": idx[i], "direction": -1,
                "entry": fill, "exit": float(c[i]),
                "gross": float(1.0 - c[i] / fill), "reason": "close",
            })

    return pd.DataFrame(trades)


def run_b6(sym: str, df_5m: pd.DataFrame | None = None) -> tuple[dict, pd.DataFrame]:
    raw = df_5m if df_5m is not None else load_history(sym, "5m", start_year=2012)
    daily = resample_nq_daily(raw) if sym == "NASDAQ100" else resample_ohlc(raw, "1D")
    tr = simulate_b6(daily)
    gross = pd.Series(tr["gross"].to_numpy(), index=pd.to_datetime(tr["entry_time"])) if not tr.empty else pd.Series(dtype=float)
    res = judge(gross, cost_of(sym), n_tests=N_TESTS, block=1)
    return res, tr


# ---------- B7: IBS NQ Daily Long-Only ----------

def simulate_b7(daily: pd.DataFrame) -> pd.DataFrame:
    """Simulate IBS mean-reversion long-only on NY regular-session NQ daily bars."""
    h, l, c = daily["high"].to_numpy(float), daily["low"].to_numpy(float), daily["close"].to_numpy(float)
    idx = daily.index
    trades: list[dict] = []
    entry_px: float | None = None
    entry_ts: pd.Timestamp | None = None

    for i in range(len(daily)):
        rng = h[i] - l[i]
        if rng <= 0:
            continue
        ibs = (c[i] - l[i]) / rng
        if entry_px is None:
            if ibs < 0.2:
                entry_px, entry_ts = float(c[i]), idx[i]
        elif ibs > 0.8:
            nights = int((idx[i] - entry_ts).days)
            trades.append({
                "entry_time": entry_ts, "exit_time": idx[i], "direction": 1,
                "entry": entry_px, "exit": float(c[i]),
                "gross": float(c[i] / entry_px - 1.0), "nights": nights,
            })
            entry_px, entry_ts = None, None

    return pd.DataFrame(trades)


def run_b7(df_nq_5m: pd.DataFrame | None = None) -> tuple[dict, pd.DataFrame]:
    raw = df_nq_5m if df_nq_5m is not None else load_history("NASDAQ100", "5m", start_year=2012)
    daily = resample_nq_daily(raw)
    tr = simulate_b7(daily)
    cost = cost_of("NASDAQ100")
    gross = pd.Series(tr["gross"].to_numpy(), index=pd.to_datetime(tr["entry_time"]))
    swap_adj = gross - B7_SWAP_PER_NIGHT * tr["nights"].to_numpy(float)
    swap_res = judge(swap_adj, cost, n_tests=N_TESTS, block=1)
    res = judge(
        gross, cost, n_tests=N_TESTS, block=1,
        extra={
            "mean_nights_held": float(tr["nights"].mean()),
            "total_nights_held": int(tr["nights"].sum()),
            "swap_central": swap_res["central"],
        },
    )
    return res, tr


# ---------- Runner & CLI ----------

ALL_IDS = ["B1", "B2", "B3", "B4", "B5_NQ", "B5_XAU", "B6_NQ", "B6_XAU", "B7"]
ALIASES = {"B5": ["B5_NQ", "B5_XAU"], "B6": ["B6_NQ", "B6_XAU"]}


def _expand_which(which: list[str] | None) -> list[str]:
    if not which:
        return list(ALL_IDS)
    out: list[str] = []
    for item in which:
        out.extend(ALIASES.get(item, [item]))
    return list(dict.fromkeys(out))


def _summary_line(cid: str, res: dict) -> str:
    c = res["central"]
    n = c["all"]["n"] if c.get("all") else 0
    mbp = c["all"]["mean_bp"] if c.get("all") else float("nan")
    ci = [round(x, 2) for x in c["ci_bp"]]
    pre = round(c["pre2022"]["mean_bp"], 2) if c.get("pre2022") else None
    post = round(c["2022+"]["mean_bp"], 2) if c.get("2022+") else None
    return f"{cid}: n={n}, mean_bp={mbp:.2f}, ci_bp={ci}, pre/post={pre}/{post}, PASS={res['PASS']}"


def run(which: list[str] | None = None) -> dict:
    """Execute requested candidates, write JSON + CSV artifacts, and print summaries."""
    ids = _expand_which(which)
    OUT.mkdir(parents=True, exist_ok=True)
    nq_5m = load_history("NASDAQ100", "5m", start_year=2012) if any(
        x in ids for x in ("B1", "B5_NQ", "B6_NQ", "B7")
    ) else None
    xau_5m = load_history("XAUUSD", "5m", start_year=2012) if any(
        x in ids for x in ("B3", "B4", "B5_XAU", "B6_XAU")
    ) else None

    dispatch = {
        "B1": lambda: run_b1(nq_5m),
        "B2": lambda: run_b2(),
        "B3": lambda: run_b3(xau_5m),
        "B4": lambda: run_b4(xau_5m),
        "B5_NQ": lambda: run_b5("NASDAQ100", nq_5m),
        "B5_XAU": lambda: run_b5("XAUUSD", xau_5m),
        "B6_NQ": lambda: run_b6("NASDAQ100", nq_5m),
        "B6_XAU": lambda: run_b6("XAUUSD", xau_5m),
        "B7": lambda: run_b7(nq_5m),
    }

    results: dict = {}
    for cid in ids:
        res, df = dispatch[cid]()
        results[cid] = res
        (OUT / f"{cid}.json").write_text(json.dumps(res, indent=2, default=str), encoding="utf-8")
        df.to_csv(OUT / f"{cid}_trades.csv", index=False)
        print(_summary_line(cid, res))
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Run preregistered candidates B1-B7.")
    parser.add_argument("--only", nargs="*", default=None, help="Candidate IDs (e.g. B1 B3 B5_NQ)")
    args = parser.parse_args()
    run(args.only)


if __name__ == "__main__":
    main()
