"""Preregistered deep-scan candidates C1-C8 (2026-11-20).

Preregistration: HANDOFF/edge5k_adaylari_onkayit_2026-11-20.md
Total independent tests: 16 (Bonferroni alpha = 0.05 / 16 / 2).

    python -m intraday.edge5k_adaylari            # all C1-C8
    python -m intraday.edge5k_adaylari C1 C3 C6   # subset
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from .history_fetch import load_history
from .kaynak_adaylari import (
    NY,
    SPLIT,
    boot_bounds,
    cost_of,
    judge,
    nyse_days,
    stats,
    third_friday,
)
from .seffaf_adaylari import wilder_atr
from .stop_testi import apply_stop, atr_before, base_nb, nq_context

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "outputs" / "intraday" / "edge5k_adaylari"
YF_CACHE = ROOT / "outputs" / "intraday" / "cache" / "yf"

N_TESTS = 16
ALPHA = 0.05 / N_TESTS / 2.0
SWAP_PER_NIGHT = 0.000118
YF_START = "2011-12-01"
TRADE_COLS = ["key", "entry_ts", "exit_ts", "direction", "entry", "exit", "gross", "nights", "atr"]


# ---------- Calendar & Bar Helpers ----------

def is_early_close(d: pd.Timestamp) -> bool:
    """True for NYSE 13:00 ET early-close weekdays: Jul 3, day after Thanksgiving, Dec 24."""
    if d.dayofweek >= 5:
        return False
    if d.month == 7 and d.day == 3:
        return True
    if d.month == 12 and d.day == 24:
        return True
    return d.month == 11 and d.dayofweek == 4 and 23 <= d.day <= 29


def rth_close_hm(d: pd.Timestamp) -> str:
    """Bar-start HH:MM of the last RTH 5m bar on NYSE day d."""
    return "12:55" if is_early_close(d) else "15:55"


def _to_ny_bars(df_5m: pd.DataFrame) -> pd.DataFrame:
    """Return copy with NY-localized index plus naive NY date and HH:MM columns."""
    idx = df_5m.index
    utc = idx.tz_localize("UTC") if idx.tz is None else idx.tz_convert("UTC")
    ny_idx = utc.tz_convert(NY)
    out = df_5m.copy()
    out.index = ny_idx
    out["_date"] = ny_idx.normalize().tz_localize(None)
    out["_hm"] = ny_idx.strftime("%H:%M")
    return out


def _bar_utc_ts(ny_df_row_idx: pd.Timestamp, close_offset: bool = False) -> pd.Timestamp:
    """Convert NY-localized bar-open timestamp to naive UTC (add 5m if bar close)."""
    ts = ny_df_row_idx.tz_convert("UTC").tz_localize(None)
    return ts + pd.Timedelta(minutes=5) if close_offset else ts


def build_rth_daily(df_5m: pd.DataFrame) -> pd.DataFrame:
    """Build RTH (09:30-16:00 ET) daily OHLC on NYSE trading days from 5m bars."""
    ny = _to_ny_bars(df_5m)
    mins = ny.index.hour * 60 + ny.index.minute
    rth = ny.loc[(mins >= 570) & (mins < 960)]
    daily = rth.groupby("_date").agg({"open": "first", "high": "max", "low": "min", "close": "last"})
    daily.index = pd.DatetimeIndex(daily.index, name="date")
    if daily.empty:
        raise ValueError("No RTH bars found to build daily OHLC.")
    valid = nyse_days(str(daily.index[0].date()), str(daily.index[-1].date()))
    return daily.loc[daily.index.isin(valid)].dropna()


def build_xau_daily(df_5m: pd.DataFrame) -> pd.DataFrame:
    """Build Mon-Fri UTC daily OHLC for XAUUSD from 5m bars."""
    idx = df_5m.index
    utc = idx.tz_localize(None) if idx.tz is None else idx.tz_convert("UTC").tz_localize(None)
    df = df_5m.copy()
    df.index = utc
    df = df.loc[df.index.dayofweek < 5]
    daily = df.groupby(df.index.normalize()).agg(
        {"open": "first", "high": "max", "low": "min", "close": "last"}
    )
    daily.index = pd.DatetimeIndex(daily.index, name="date")
    return daily.dropna()


def _day_bar_lookup(ny: pd.DataFrame) -> dict[tuple[pd.Timestamp, str], tuple[float, float, float, float, pd.Timestamp]]:
    """Map (ny_date, hm) -> (open, high, low, close, ny_bar_open_ts)."""
    lookup: dict[tuple[pd.Timestamp, str], tuple[float, float, float, float, pd.Timestamp]] = {}
    dates = list(ny["_date"])
    hms = list(ny["_hm"])
    o = ny["open"].to_numpy(float)
    h = ny["high"].to_numpy(float)
    l = ny["low"].to_numpy(float)
    c = ny["close"].to_numpy(float)
    ts_list = ny.index
    for i in range(len(ny)):
        key = (dates[i], hms[i])
        if key not in lookup:
            lookup[key] = (o[i], h[i], l[i], c[i], ts_list[i])
    return lookup


def _empty_trades() -> pd.DataFrame:
    return pd.DataFrame(columns=TRADE_COLS)


def _finalize_trades(rows: list[dict], daily: pd.DataFrame, atr_through: np.ndarray) -> pd.DataFrame:
    if not rows:
        return _empty_trades()
    tr = pd.DataFrame(rows)
    tr["atr"] = atr_before(pd.DatetimeIndex(tr["key"]), daily, atr_through)
    return tr[TRADE_COLS].reset_index(drop=True)


# ---------- yfinance Cache ----------

def load_yf_series(
    ticker: str, col: str, cache_name: str,
    start: str = YF_START, cache_dir: Path = YF_CACHE,
) -> pd.Series:
    """Load daily series from CSV cache, or download once from yfinance and cache."""
    path = cache_dir / f"{cache_name}.csv"
    if path.exists():
        df = pd.read_csv(path, index_col=0, parse_dates=True)
        s = df.iloc[:, 0].astype(float).dropna()
        s.index = pd.DatetimeIndex(s.index).tz_localize(None).normalize()
        return s.sort_index()

    import yfinance as yf

    raw = yf.download(ticker, start=start, auto_adjust=False, progress=False)
    if raw is None or raw.empty:
        raise RuntimeError(f"yfinance returned empty data for {ticker}")
    if isinstance(raw.columns, pd.MultiIndex):
        if col not in raw.columns.get_level_values(0):
            raise KeyError(f"Column {col!r} missing in yfinance download for {ticker}")
        sub = raw[col]
        s = sub.iloc[:, 0] if isinstance(sub, pd.DataFrame) else sub
    else:
        if col not in raw.columns:
            raise KeyError(f"Column {col!r} missing in yfinance download for {ticker}")
        s = raw[col]
    s = s.astype(float).dropna()
    s.index = pd.DatetimeIndex(s.index).tz_localize(None).normalize()
    s = s.sort_index()
    cache_dir.mkdir(parents=True, exist_ok=True)
    s.to_frame(name=cache_name).to_csv(path)
    return s


def _asof_before(series: pd.Series, target_date: pd.Timestamp, max_lag_days: int = 5) -> float:
    """Return latest value on or before target_date within max_lag_days, else NaN."""
    sub = series.loc[series.index <= target_date]
    if sub.empty:
        return float("nan")
    lag = (target_date - sub.index[-1]).days
    return float(sub.iloc[-1]) if lag <= max_lag_days else float("nan")


# ---------- C1: End-of-Month Rebalance ----------

def c1_month_endpoints(days: pd.DatetimeIndex) -> list[tuple[pd.Timestamp, pd.Timestamp, pd.Timestamp, pd.Timestamp]]:
    """Return (prev_month_last, prev_day_before_entry, entry_5th_last, exit_last) per month."""
    grouped = list(pd.Series(days).groupby(days.to_period("M")))
    out = []
    for i in range(1, len(grouped)):
        prev_days = pd.DatetimeIndex(grouped[i - 1][1])
        cur_days = pd.DatetimeIndex(grouped[i][1])
        if len(cur_days) < 5:
            continue
        entry_d = cur_days[-5]
        prev_entry_d = cur_days[-6] if len(cur_days) >= 6 else prev_days[-1]
        out.append((prev_days[-1], prev_entry_d, entry_d, cur_days[-1]))
    return out


def trades_c1(df_5m: pd.DataFrame, tlt: pd.Series) -> pd.DataFrame:
    """C1: Enter 5th-to-last NYSE day close, exit last NYSE day close; sign from MTD(idx) - MTD(TLT)."""
    ny = _to_ny_bars(df_5m)
    bars = _day_bar_lookup(ny)
    daily = build_rth_daily(df_5m)
    atr_through = wilder_atr(daily, 14).to_numpy(float)
    last = daily.index[-1]
    # use the full calendar of the last month so an incomplete month is not cut short at the data end
    days = nyse_days(str(daily.index[0].date()), str((last + pd.offsets.MonthEnd(0)).date()))
    rows = []
    for prev_m_last, prev_entry_d, entry_d, exit_d in c1_month_endpoints(days):
        if exit_d > last:
            continue
        b_pm = bars.get((prev_m_last, rth_close_hm(prev_m_last)))
        b_en = bars.get((entry_d, rth_close_hm(entry_d)))
        b_ex = bars.get((exit_d, rth_close_hm(exit_d)))
        if not (b_pm and b_en and b_ex):
            continue
        tlt_0 = _asof_before(tlt, prev_m_last)
        tlt_1 = _asof_before(tlt, prev_entry_d)
        if np.isnan(tlt_0) or np.isnan(tlt_1) or tlt_0 <= 0:
            continue
        diff = (b_en[3] / b_pm[3] - 1.0) - (tlt_1 / tlt_0 - 1.0)
        if diff == 0:
            continue
        direction = -1 if diff > 0 else 1
        entry_px, exit_px = b_en[3], b_ex[3]
        rows.append({
            "key": entry_d,
            "entry_ts": _bar_utc_ts(b_en[4], close_offset=True),
            "exit_ts": _bar_utc_ts(b_ex[4], close_offset=True),
            "direction": direction,
            "entry": entry_px,
            "exit": exit_px,
            "gross": direction * (exit_px / entry_px - 1.0),
            "nights": int((exit_d - entry_d).days),
        })
    return _finalize_trades(rows, daily, atr_through)


# ---------- C2: Pre-Holiday Long ----------

def pre_holiday_days(start: str, end: str) -> pd.DatetimeIndex:
    """NYSE trading days whose next weekday (Mon-Fri) is a full NYSE closure holiday."""
    days = nyse_days(start, end)
    # calendar is known in advance: look past `end` so the last data day is not mistaken for a pre-holiday
    day_set = set(nyse_days(start, str((pd.Timestamp(end) + pd.Timedelta(days=10)).date())))
    bdays = pd.bdate_range(start, pd.Timestamp(end) + pd.Timedelta(days=7))
    bday_set = set(bdays)
    pre = []
    for d in days:
        nxt_wd = d + pd.Timedelta(days=3 if d.dayofweek == 4 else 1)
        if nxt_wd in bday_set and nxt_wd not in day_set:
            pre.append(d)
    return pd.DatetimeIndex(pre)


def trades_c2(df_5m: pd.DataFrame) -> pd.DataFrame:
    """C2: Long from previous NYSE day close to pre-holiday day close (early-close aware)."""
    ny = _to_ny_bars(df_5m)
    bars = _day_bar_lookup(ny)
    daily = build_rth_daily(df_5m)
    atr_through = wilder_atr(daily, 14).to_numpy(float)
    days = nyse_days(str(daily.index[0].date()), str(daily.index[-1].date()))
    pre_set = set(pre_holiday_days(str(days[0].date()), str(days[-1].date())))
    rows = []
    for prev_d, cur_d in zip(days[:-1], days[1:]):
        if cur_d not in pre_set:
            continue
        b_prev = bars.get((prev_d, rth_close_hm(prev_d)))
        b_cur = bars.get((cur_d, rth_close_hm(cur_d)))
        if not (b_prev and b_cur):
            continue
        entry_px, exit_px = b_prev[3], b_cur[3]
        rows.append({
            "key": cur_d,
            "entry_ts": _bar_utc_ts(b_prev[4], close_offset=True),
            "exit_ts": _bar_utc_ts(b_cur[4], close_offset=True),
            "direction": 1,
            "entry": entry_px,
            "exit": exit_px,
            "gross": exit_px / entry_px - 1.0,
            "nights": int((cur_d - prev_d).days),
        })
    return _finalize_trades(rows, daily, atr_through)


# ---------- C3: Third Friday Morning Settlement ----------

def trades_c3(df_5m: pd.DataFrame, direction: int) -> pd.DataFrame:
    """C3: Thursday close -> 3rd Friday 09:35 ET close (close of 09:30 ET 5m bar)."""
    if direction not in (1, -1):
        raise ValueError(f"direction must be +1 or -1, got {direction}")
    ny = _to_ny_bars(df_5m)
    bars = _day_bar_lookup(ny)
    daily = build_rth_daily(df_5m)
    atr_through = wilder_atr(daily, 14).to_numpy(float)
    days = nyse_days(str(daily.index[0].date()), str(daily.index[-1].date()))
    day_set = set(days)
    months = pd.period_range(days[0].to_period("M"), days[-1].to_period("M"), freq="M")
    rows = []
    for m in months:
        fri = third_friday(m.to_timestamp())
        thu = fri - pd.Timedelta(days=1)
        if fri not in day_set or thu not in day_set:
            continue
        b_thu = bars.get((thu, rth_close_hm(thu)))
        # Spec says "09:35 ET bar close": the 5m bar starting at 09:30 ET closes at 09:35 ET.
        b_fri = bars.get((fri, "09:30"))
        if not (b_thu and b_fri):
            continue
        entry_px, exit_px = b_thu[3], b_fri[3]
        rows.append({
            "key": fri,
            "entry_ts": _bar_utc_ts(b_thu[4], close_offset=True),
            "exit_ts": _bar_utc_ts(b_fri[4], close_offset=True),
            "direction": direction,
            "entry": entry_px,
            "exit": exit_px,
            "gross": direction * (exit_px / entry_px - 1.0),
            "nights": int((fri - thu).days),
        })
    return _finalize_trades(rows, daily, atr_through)


# ---------- C4: VIX Contango Day Long ----------

def trades_c4(df_5m: pd.DataFrame, vix: pd.Series, vix3m: pd.Series) -> tuple[pd.DataFrame, pd.Series]:
    """C4: Long 09:30 open -> close when prev NYSE day VIX < VIX3M; also return non-signal returns."""
    ny = _to_ny_bars(df_5m)
    bars = _day_bar_lookup(ny)
    daily = build_rth_daily(df_5m)
    atr_through = wilder_atr(daily, 14).to_numpy(float)
    days = nyse_days(str(daily.index[0].date()), str(daily.index[-1].date()))
    sig_rows, nonsig = [], {}
    for prev_d, d in zip(days[:-1], days[1:]):
        v0 = _asof_before(vix, prev_d, max_lag_days=0)
        v3 = _asof_before(vix3m, prev_d, max_lag_days=0)
        if np.isnan(v0) or np.isnan(v3):
            continue
        b_op = bars.get((d, "09:30"))
        b_cl = bars.get((d, rth_close_hm(d)))
        if not (b_op and b_cl):
            continue
        ret = b_cl[3] / b_op[0] - 1.0
        if v0 < v3:
            sig_rows.append({
                "key": d,
                "entry_ts": _bar_utc_ts(b_op[4], close_offset=False),
                "exit_ts": _bar_utc_ts(b_cl[4], close_offset=True),
                "direction": 1,
                "entry": b_op[0],
                "exit": b_cl[3],
                "gross": ret,
                "nights": 0,
            })
        else:
            nonsig[d] = ret
    return _finalize_trades(sig_rows, daily, atr_through), pd.Series(nonsig, dtype=float)


# ---------- C5: VIX Backwardation Filter on NB (NQ) ----------

def eval_c5(
    vix: pd.Series, vix3m: pd.Series, cost: float,
    nb_trades: pd.DataFrame | None = None,
) -> tuple[dict, pd.DataFrame]:
    """C5: Skip NB (k=1) trades where prev NYSE day VIX > VIX3M; evaluate filter value -(gross - 2c)."""
    if nb_trades is None:
        path, daily, atr_through = nq_context()
        nb_trades = apply_stop(path, base_nb(daily, atr_through), 1.0)
    if nb_trades.empty:
        raise ValueError("NB trades DataFrame is empty.")
    keys = pd.to_datetime(nb_trades["key"]).dt.normalize()
    all_days = nyse_days(str((keys.min() - pd.Timedelta(days=10)).date()), str(keys.max().date()))
    prev_map = {cur: prev for prev, cur in zip(all_days[:-1], all_days[1:])}

    skip_mask = []
    for k in keys:
        pd_prev = prev_map.get(k)
        if pd_prev is None:
            skip_mask.append(False)
            continue
        v0 = _asof_before(vix, pd_prev, max_lag_days=0)
        v3 = _asof_before(vix3m, pd_prev, max_lag_days=0)
        skip_mask.append(bool(not np.isnan(v0) and not np.isnan(v3) and v0 > v3))

    skipped = nb_trades.loc[skip_mask].copy().reset_index(drop=True)
    if skipped.empty:
        raise ValueError("C5 produced zero skipped trades.")

    s_idx = pd.to_datetime(skipped["key"])
    g = skipped["gross"].to_numpy(float)
    out: dict = {"n_all": int(len(nb_trades)), "n_skipped": int(len(skipped)),
                 "cost_per_side": cost, "n_tests": N_TESTS}
    for lab, c in (("zero", 0.0), ("central", cost), ("pessimistic", 2.0 * cost)):
        fval = pd.Series(-(g - 2.0 * c), index=s_idx).sort_index()
        early, late = fval[fval.index < SPLIT], fval[fval.index >= SPLIT]
        out[lab] = {
            "all": stats(fval),
            "ci_bp": boot_bounds(fval.to_numpy(), ALPHA, block=1),
            "pre2022": stats(early) if len(early) > 2 else None,
            "2022+": stats(late) if len(late) > 2 else None,
        }
    c_res = out["central"]
    out["PASS"] = bool(
        c_res["all"]["mean_bp"] > 0
        and c_res["ci_bp"][0] > 0
        and c_res["pre2022"] and c_res["pre2022"]["mean_bp"] > 0
        and c_res["2022+"] and c_res["2022+"]["mean_bp"] > 0
        and out["pessimistic"]["all"]["mean_bp"] > 0
    )
    return out, skipped


# ---------- C6: Small Gap + First 15m Candle Fill ----------

def _c6_walk_session(
    session: pd.DataFrame, direction: int, target: float, stop: float,
) -> tuple[float, pd.Timestamp]:
    """Walk 09:45..close bars; if bar touches both stop and target, stop fills first."""
    o = session["open"].to_numpy(float)
    h = session["high"].to_numpy(float)
    l = session["low"].to_numpy(float)
    c = session["close"].to_numpy(float)
    idx = session.index
    for i in range(len(session)):
        if direction == -1:
            if h[i] >= stop:
                return float(max(o[i], stop)), _bar_utc_ts(idx[i], close_offset=True)
            if l[i] <= target:  # buy-limit at target: fills at open if price already beyond it
                return float(min(o[i], target)), _bar_utc_ts(idx[i], close_offset=True)
        else:
            if l[i] <= stop:
                return float(min(o[i], stop)), _bar_utc_ts(idx[i], close_offset=True)
            if h[i] >= target:  # sell-limit at target
                return float(max(o[i], target)), _bar_utc_ts(idx[i], close_offset=True)
    return float(c[-1]), _bar_utc_ts(idx[-1], close_offset=True)


def trades_c6(df_5m: pd.DataFrame) -> pd.DataFrame:
    """C6: |gap| < 0.25*ATR14(prev), first 15m candle in fill dir -> enter 09:45 open, target/stop."""
    ny = _to_ny_bars(df_5m)
    bars = _day_bar_lookup(ny)
    daily = build_rth_daily(df_5m)
    atr_through = wilder_atr(daily, 14).to_numpy(float)
    atr_map = dict(zip(daily.index, atr_through))
    days = nyse_days(str(daily.index[0].date()), str(daily.index[-1].date()))
    by_date = {d: grp for d, grp in ny.groupby("_date")}
    rows = []
    for prev_d, d in zip(days[:-1], days[1:]):
        atr_prev = atr_map.get(prev_d, float("nan"))
        b_prev = bars.get((prev_d, rth_close_hm(prev_d)))
        b30, b35, b40, b45 = (bars.get((d, hm)) for hm in ("09:30", "09:35", "09:40", "09:45"))
        if np.isnan(atr_prev) or not (b_prev and b30 and b35 and b40 and b45):
            continue
        prev_close = b_prev[3]
        gap = b30[0] - prev_close
        if gap == 0 or abs(gap) >= 0.25 * atr_prev:
            continue
        candle = b40[3] - b30[0]
        if gap > 0 and candle < 0:
            direction, stop = -1, max(b30[1], b35[1], b40[1])
        elif gap < 0 and candle > 0:
            direction, stop = 1, min(b30[2], b35[2], b40[2])
        else:
            continue
        day_df = by_date[d]
        close_hm = rth_close_hm(d)
        walk_df = day_df.loc[(day_df["_hm"] >= "09:45") & (day_df["_hm"] <= close_hm)]
        if walk_df.empty:
            continue
        exit_px, exit_ts = _c6_walk_session(walk_df, direction, prev_close, stop)
        entry_px = b45[0]
        rows.append({
            "key": d,
            "entry_ts": _bar_utc_ts(b45[4], close_offset=False),
            "exit_ts": exit_ts,
            "direction": direction,
            "entry": entry_px,
            "exit": exit_px,
            "gross": direction * (exit_px / entry_px - 1.0),
            "nights": 0,
        })
    return _finalize_trades(rows, daily, atr_through)


# ---------- C7: Gap Fade Every Day ----------

def trades_c7(df_5m: pd.DataFrame) -> pd.DataFrame:
    """C7: Every NYSE day with gap != 0, fade gap from 09:30 open to session close."""
    ny = _to_ny_bars(df_5m)
    bars = _day_bar_lookup(ny)
    daily = build_rth_daily(df_5m)
    atr_through = wilder_atr(daily, 14).to_numpy(float)
    days = nyse_days(str(daily.index[0].date()), str(daily.index[-1].date()))
    rows = []
    for prev_d, d in zip(days[:-1], days[1:]):
        b_prev = bars.get((prev_d, rth_close_hm(prev_d)))
        b_op = bars.get((d, "09:30"))
        b_cl = bars.get((d, rth_close_hm(d)))
        if not (b_prev and b_op and b_cl):
            continue
        gap = b_op[0] - b_prev[3]
        if gap == 0:
            continue
        direction = -1 if gap > 0 else 1
        entry_px, exit_px = b_op[0], b_cl[3]
        rows.append({
            "key": d,
            "entry_ts": _bar_utc_ts(b_op[4], close_offset=False),
            "exit_ts": _bar_utc_ts(b_cl[4], close_offset=True),
            "direction": direction,
            "entry": entry_px,
            "exit": exit_px,
            "gross": direction * (exit_px / entry_px - 1.0),
            "nights": 0,
        })
    return _finalize_trades(rows, daily, atr_through)


# ---------- C8: Gold Asia Session Long ----------

def trades_c8(df_5m: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    """C8: XAUUSD Mon-Fri 00:00 UTC open -> 07:55 UTC close long; return 24h returns too."""
    idx = df_5m.index
    utc = idx.tz_localize(None) if idx.tz is None else idx.tz_convert("UTC").tz_localize(None)
    df = df_5m.copy()
    df.index = utc
    daily = build_xau_daily(df)
    atr_through = wilder_atr(daily, 14).to_numpy(float)

    o_00 = df.loc[df.index.strftime("%H:%M") == "00:00", "open"]
    o_00.index = o_00.index.normalize()
    o_00 = o_00[~o_00.index.duplicated()]

    c_755 = df.loc[df.index.strftime("%H:%M") == "07:55", "close"]
    c_755.index = c_755.index.normalize()
    c_755 = c_755[~c_755.index.duplicated()]

    rows, full_24h = [], {}
    for d in o_00.index:
        if d.dayofweek >= 5 or d not in c_755.index:
            continue
        entry_px = float(o_00[d])
        exit_px = float(c_755[d])
        rows.append({
            "key": d,
            "entry_ts": d,
            "exit_ts": d + pd.Timedelta(hours=8),
            "direction": 1,
            "entry": entry_px,
            "exit": exit_px,
            "gross": exit_px / entry_px - 1.0,
            "nights": 0,
        })
        nxt = d + pd.Timedelta(days=1)
        if nxt in o_00.index:
            full_24h[d] = float(o_00[nxt]) / entry_px - 1.0
    return _finalize_trades(rows, daily, atr_through), pd.Series(full_24h, dtype=float)


# ---------- Evaluation & CLI ----------

def _eval_overnight(tr: pd.DataFrame, cost: float) -> dict:
    if tr.empty:
        raise ValueError("Empty trades DataFrame for overnight candidate.")
    s_gross = pd.Series(tr["gross"].to_numpy(float), index=pd.to_datetime(tr["key"]))
    s_swap = pd.Series(
        (tr["gross"] - tr["nights"] * SWAP_PER_NIGHT).to_numpy(float),
        index=pd.to_datetime(tr["key"]),
    )
    res_0 = judge(s_gross, cost, n_tests=N_TESTS, block=1)
    res_s = judge(s_swap, cost, n_tests=N_TESTS, block=1)
    return {"swap0": res_0, "swap": res_s, "PASS": res_s["PASS"], "mean_nights": float(tr["nights"].mean())}


def _eval_intraday(tr: pd.DataFrame, cost: float, extra: dict | None = None) -> dict:
    if tr.empty:
        raise ValueError("Empty trades DataFrame for intraday candidate.")
    s = pd.Series(tr["gross"].to_numpy(float), index=pd.to_datetime(tr["key"]))
    return judge(s, cost, n_tests=N_TESTS, block=1, extra=extra)


def _summary_line(tid: str, res: dict, trades_df: pd.DataFrame) -> str:
    ev = res["swap"] if "swap" in res else res
    c = ev["central"]
    n = c["all"]["n"]
    keys = pd.to_datetime(trades_df["key"])
    yrs = max((keys.max() - keys.min()).days / 365.25, 1e-9)
    tpy = n / yrs
    ci = [round(x, 2) for x in c["ci_bp"]]
    pre = round(c["pre2022"]["mean_bp"], 2) if c.get("pre2022") else None
    post = round(c["2022+"]["mean_bp"], 2) if c.get("2022+") else None
    p2x = round(ev["pessimistic"]["all"]["mean_bp"], 2)
    return (
        f"{tid}: n={n} ({tpy:.1f}/yr) mean_bp={c['all']['mean_bp']:+.2f} "
        f"ci={ci} pre/post={pre}/{post} 2x={p2x:+.2f} PASS={res['PASS']}"
    )


def _run_group(group: str, cache: dict) -> list[tuple[str, dict, pd.DataFrame]]:
    if group in ("C1", "C2", "C3", "C4", "C6", "C7"):
        for s in ("SP500", "NASDAQ100"):
            if s not in cache:
                cache[s] = load_history(s, "5m", start_year=2012)
    if group in ("C1",) and "TLT" not in cache:
        cache["TLT"] = load_yf_series("TLT", "Adj Close", "TLT")
    if group in ("C4", "C5") and "VIX" not in cache:
        cache["VIX"] = load_yf_series("^VIX", "Close", "VIX")
        cache["VIX3M"] = load_yf_series("^VIX3M", "Close", "VIX3M")

    if group == "C1":
        return [(f"C1_{s}", _eval_overnight(tr := trades_c1(cache[s], cache["TLT"]), cost_of(s)), tr)
                for s in ("SP500", "NASDAQ100")]
    if group == "C2":
        return [(f"C2_{s}", _eval_overnight(tr := trades_c2(cache[s]), cost_of(s)), tr)
                for s in ("SP500", "NASDAQ100")]
    if group == "C3":
        out = []
        for s in ("SP500", "NASDAQ100"):
            for d_val, d_lab in ((1, "long"), (-1, "short")):
                tr = trades_c3(cache[s], d_val)
                out.append((f"C3_{s}_{d_lab}", _eval_overnight(tr, cost_of(s)), tr))
        return out
    if group == "C4":
        out = []
        for s in ("SP500", "NASDAQ100"):
            tr, nonsig = trades_c4(cache[s], cache["VIX"], cache["VIX3M"])
            s_m, ns_m = float(tr["gross"].mean()), float(nonsig.mean())
            extra = {"signal_mean_bp": s_m * 1e4, "nonsignal_mean_bp": ns_m * 1e4,
                     "nonsignal_n": int(len(nonsig)), "condition": s_m > ns_m}
            out.append((f"C4_{s}", _eval_intraday(tr, cost_of(s), extra=extra), tr))
        return out
    if group == "C5":
        res, skipped = eval_c5(cache["VIX"], cache["VIX3M"], cost_of("NASDAQ100"))
        return [("C5_NB_NQ", res, skipped)]
    if group == "C6":
        return [(f"C6_{s}", _eval_intraday(tr := trades_c6(cache[s]), cost_of(s)), tr)
                for s in ("NASDAQ100", "SP500")]
    if group == "C7":
        return [(f"C7_{s}", _eval_intraday(tr := trades_c7(cache[s]), cost_of(s)), tr)
                for s in ("NASDAQ100", "SP500")]
    if group == "C8":
        xau = load_history("XAUUSD", "5m", start_year=2012)
        tr, full24 = trades_c8(xau)
        same = pd.to_datetime(tr["key"]).isin(full24.index).to_numpy()  # prereg: same days on both sides
        a_m, f_m = float(tr.loc[same, "gross"].mean()), float(full24.mean())
        extra = {"asia_mean_bp": a_m * 1e4, "full_24h_mean_bp": f_m * 1e4,
                 "full_24h_n": int(len(full24)), "condition": a_m > (8.0 / 24.0) * f_m}
        return [("C8_XAUUSD", _eval_intraday(tr, cost_of("XAUUSD"), extra=extra), tr)]
    raise KeyError(f"Unknown candidate group: {group!r}")


ALL_GROUPS = ["C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8"]


def run(which: list[str] | None = None) -> dict:
    """Run requested candidate groups, write results.json + per-test CSVs, print summaries."""
    groups = which or list(ALL_GROUPS)
    OUT.mkdir(parents=True, exist_ok=True)
    cache: dict = {}
    results: dict = {}
    for g in groups:
        for tid, res, df in _run_group(g, cache):
            results[tid] = res
            df.to_csv(OUT / f"{tid}_trades.csv", index=False)
            print(_summary_line(tid, res, df))
    (OUT / "results.json").write_text(json.dumps(results, indent=2, default=str), encoding="utf-8")
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Run preregistered candidates C1-C8.")
    parser.add_argument("candidates", nargs="*", default=None, help="Candidate groups (e.g. C1 C3 C6)")
    args = parser.parse_args()
    run(args.candidates or None)


if __name__ == "__main__":
    main()
