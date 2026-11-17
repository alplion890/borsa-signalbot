"""Source-scan candidates A1-A4 (ITSM non-US, option-expiration week, turn-of-month, BTC overnight).

Preregistered (rules fixed before results): HANDOFF/kaynak_adaylari_onkayit_2026-11-18.md

    python -m intraday.kaynak_adaylari            # all
    python -m intraday.kaynak_adaylari A2 A3      # subset
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
from pandas.tseries.holiday import (AbstractHolidayCalendar, GoodFriday, Holiday, USLaborDay,
                                    USMartinLutherKingJr, USMemorialDay, USPresidentsDay,
                                    USThanksgivingDay, nearest_workday)

from .history_fetch import load_history

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "outputs" / "intraday" / "kaynak_adaylari"
PROFILE = ROOT / "outputs" / "intraday" / "mt5_bridge" / "reality_profile.csv"
BTC = ROOT / "outputs" / "intraday" / "cache" / "binance" / "BTCUSDT_1h.csv"
SEED = 20261118
REPS = 10_000
SPLIT = pd.Timestamp("2022-01-01")
NY = ZoneInfo("America/New_York")


class NYSECalendar(AbstractHolidayCalendar):
    rules = [
        Holiday("NewYear", month=1, day=1, observance=nearest_workday),
        USMartinLutherKingJr, USPresidentsDay, GoodFriday, USMemorialDay,
        Holiday("Juneteenth", month=6, day=19, start_date="2022-01-01", observance=nearest_workday),
        Holiday("July4", month=7, day=4, observance=nearest_workday),
        USLaborDay, USThanksgivingDay,
        Holiday("Christmas", month=12, day=25, observance=nearest_workday),
    ]


SPECIAL_CLOSED = pd.to_datetime(["2012-10-29", "2012-10-30", "2018-12-05", "2025-01-09"])


def nyse_days(start: str, end: str) -> pd.DatetimeIndex:
    days = pd.bdate_range(start, end)
    hol = NYSECalendar().holidays(start, end)
    hol = hol[~((hol.month == 12) & (hol.day == 31))]  # NYSE stays open Fri Dec 31 when Jan 1 is Saturday
    return days[~days.isin(hol) & ~days.isin(SPECIAL_CLOSED)]


def cost_of(sym: str) -> float:
    return float(pd.read_csv(PROFILE).set_index("symbol").loc[sym, "real_cost_per_side_central"])


def boot_bounds(x: np.ndarray, alpha: float, block: int) -> list[float]:
    rng = np.random.default_rng(SEED)
    n = len(x)
    if block <= 1:
        idx = rng.integers(0, n, size=(REPS, n))
    else:
        starts = rng.integers(0, n, size=(REPS, (n + block - 1) // block))
        idx = ((starts[:, :, None] + np.arange(block)) % n).reshape(REPS, -1)[:, :n]
    m = x[idx].mean(axis=1)
    return (np.quantile(m, [alpha, 1 - alpha]) * 1e4).tolist()


def stats(net: pd.Series) -> dict:
    yrs = max((net.index[-1] - net.index[0]).days / 365.25, 1e-9)
    return {"n": int(len(net)), "mean_bp": float(net.mean() * 1e4), "win_pct": float((net > 0).mean() * 100),
            "sum_pct_per_year": float(net.sum() / yrs * 100), "sharpe_per_trade": float(net.mean() / net.std())}


def judge(gross: pd.Series, cost: float | None, n_tests: int, block: int,
          extra: dict | None = None) -> dict:
    """gross: per-trade gross return (fraction), DatetimeIndex. cost: per side; None = not measured."""
    gross = gross.dropna().sort_index()
    alpha = 0.05 / n_tests / 2
    out: dict = {"cost_per_side": cost, "n_tests": n_tests}
    costs = {"zero": 0.0} if cost is None else {"zero": 0.0, "central": cost, "pessimistic": 2 * cost}
    for lab, c in costs.items():
        net = gross - 2 * c
        early, late = net[net.index < SPLIT], net[net.index >= SPLIT]
        out[lab] = {"all": stats(net), "ci_bp": boot_bounds(net.to_numpy(), alpha, block),
                    "pre2022": stats(early) if len(early) > 2 else None,
                    "2022+": stats(late) if len(late) > 2 else None}
    if extra:
        out["extra"] = extra
    if cost is None:
        out["PASS"] = None
        out["note"] = "maliyet olculmedi"
        return out
    c = out["central"]
    ok = (c["all"]["mean_bp"] > 0 and c["ci_bp"][0] > 0 and c["pre2022"]["mean_bp"] > 0
          and c["2022+"]["mean_bp"] > 0 and out["pessimistic"]["all"]["mean_bp"] > 0)
    if extra and "condition" in extra:
        ok = ok and bool(extra["condition"])
    out["PASS"] = bool(ok)
    return out


# ---------- A1: intraday time-series momentum, non-US indices ----------
A1_SESSIONS = {
    "UK100": ("Europe/London", "08:00", "16:30"),
    "GER40": ("Europe/Berlin", "09:00", "17:30"),
    "FRA40": ("Europe/Paris", "09:00", "17:30"),
    "JAP225": ("Asia/Tokyo", "09:00", "15:00"),
}
JPX_CLOSE_CHANGE = pd.Timestamp("2024-11-05")


def a1_trades(sym: str) -> pd.Series:
    tz, o, c = A1_SESSIONS[sym]
    f = load_history(sym, "5m", start_year=2012)
    f.index = f.index.tz_localize("UTC").tz_convert(tz)
    f = f[f.index.dayofweek < 5]
    day = f.index.normalize().tz_localize(None)
    hm = f.index.strftime("%H:%M")
    g = pd.DataFrame({"day": day, "hm": hm, "open": f["open"].to_numpy(), "close": f["close"].to_numpy()})
    piv_o = g.pivot_table(index="day", columns="hm", values="open", aggfunc="first")
    piv_c = g.pivot_table(index="day", columns="hm", values="close", aggfunc="first")
    rows = {}
    prev_close = np.nan
    for d in piv_c.index:
        close_t = "15:30" if (sym == "JAP225" and d >= JPX_CLOSE_CHANGE) else c
        ct = pd.Timestamp(f"2000-01-01 {close_t}")
        ot = pd.Timestamp(f"2000-01-01 {o}")
        k = lambda t: t.strftime("%H:%M")
        first_end, last_bar, entry_bar = k(ot + pd.Timedelta(minutes=25)), k(ct - pd.Timedelta(minutes=5)), k(ct - pd.Timedelta(minutes=30))
        try:
            fe, eo, xc = piv_c.at[d, first_end], piv_o.at[d, entry_bar], piv_c.at[d, last_bar]
        except KeyError:
            fe = eo = xc = np.nan
        if not np.isnan(prev_close) and not np.isnan(fe) and not np.isnan(eo) and not np.isnan(xc):
            r1 = fe / prev_close - 1
            if r1 != 0:
                rows[d] = np.sign(r1) * (xc / eo - 1)
        if not np.isnan(xc):
            prev_close = xc
    return pd.Series(rows, dtype=float)


def run_a1() -> dict:
    out = {}
    for sym in A1_SESSIONS:
        try:
            tr = a1_trades(sym)
        except FileNotFoundError as exc:
            out[sym] = {"error": str(exc)}
            continue
        cost = None if sym == "GER40" else cost_of(sym)
        out[sym] = judge(tr, cost, n_tests=4, block=5)
        out[sym]["first"], out[sym]["last"] = str(tr.index[0].date()), str(tr.index[-1].date())
    return out


# ---------- US daily closes (A2, A3) ----------
def us_closes(sym: str) -> pd.Series:
    f = load_history(sym, "5m", start_year=2012)
    loc = f.index.tz_localize("UTC").tz_convert(NY)
    m = loc.strftime("%H:%M") == "15:55"
    s = pd.Series(f["close"].to_numpy()[m], index=loc[m].normalize().tz_localize(None))
    s = s[~s.index.duplicated()]
    return s[s.index.isin(nyse_days(str(s.index[0].date()), str(s.index[-1].date())))]


def third_friday(d: pd.Timestamp) -> pd.Timestamp:
    first = d.replace(day=1)
    return first + pd.Timedelta(days=(4 - first.dayofweek) % 7 + 14)


def run_a2() -> dict:
    out = {}
    for sym in ("SP500", "NASDAQ100"):
        cl = us_closes(sym)
        wk = cl.groupby(cl.index.to_period("W-FRI")).last()
        ret = wk / wk.shift(1) - 1
        ret.index = ret.index.end_time.normalize()  # Friday of each week
        oe = pd.Series([third_friday(d) == d for d in ret.index], index=ret.index)
        ret = ret.dropna()
        oe = oe.reindex(ret.index)
        diff = float(ret[oe].mean() - ret[~oe].mean())
        res = judge(ret[oe], cost_of(sym), n_tests=2, block=1,
                    extra={"oe_minus_other_bp": diff * 1e4, "other_weeks_mean_bp": float(ret[~oe].mean() * 1e4),
                           "other_weeks_n": int((~oe).sum()), "condition": diff > 0})
        out[sym] = res
    return out


def run_a3() -> dict:
    out = {}
    for sym in ("SP500", "NASDAQ100"):
        cl = us_closes(sym)
        r = (cl / cl.shift(1) - 1).dropna()
        prev = cl.index.to_series().shift(1).reindex(r.index)
        tom = pd.Series(prev.dt.month.to_numpy() != r.index.month, index=r.index)  # first day of new month
        diff = float(r[tom].mean() - r[~tom].mean())
        res = judge(r[tom], cost_of(sym), n_tests=2, block=1,
                    extra={"tom_minus_other_bp": diff * 1e4, "other_days_mean_bp": float(r[~tom].mean() * 1e4),
                           "condition": diff > 0})
        out[sym] = res
    return out


# ---------- A4: BTC overnight (NYSE closed) ----------
def btc_overnight() -> pd.DataFrame:
    df = pd.read_csv(BTC, parse_dates=["ts"]).set_index("ts")
    loc = df.index.tz_localize("UTC").tz_convert(NY)
    days = nyse_days(str(loc[0].date()), str(loc[-1].date()))
    o = pd.Series(df["open"].to_numpy(), index=loc)
    lo = pd.Series(df["low"].to_numpy(), index=loc)
    hi = pd.Series(df["high"].to_numpy(), index=loc)
    rows = []
    for d, nxt in zip(days[:-1], days[1:]):
        t0 = pd.Timestamp(d.date()).tz_localize(NY) + pd.Timedelta(hours=16)
        t1 = pd.Timestamp(nxt.date()).tz_localize(NY) + pd.Timedelta(hours=10)
        if t0 not in o.index or t1 not in o.index:
            continue
        e, x = o[t0], o[t1]
        seg = slice(t0, t1 - pd.Timedelta(hours=1))
        rows.append((d, x / e - 1, lo[seg].min() / e - 1, hi[seg].max() / e - 1))
    return pd.DataFrame(rows, columns=["date", "ret", "low", "high"]).set_index("date")


def run_a4() -> dict:
    from .fx_fix_btc_hours import btc_daily
    cost = cost_of("BTCUSDT")
    ov = btc_overnight()
    h6 = btc_daily(0.0)["H6_btc_21_23"]
    h6.index = pd.to_datetime(h6.index)
    res = judge(ov["ret"], cost, n_tests=1, block=5)
    late_ov = (ov["ret"] - 2 * cost)[ov.index >= SPLIT]
    late_h6 = (h6 - 2 * cost)[h6.index >= SPLIT]
    j = pd.concat([ov["ret"], h6], axis=1, keys=["ov", "h6"]).dropna()
    res["compare_h6"] = {
        "sharpe_2022+_overnight": float(late_ov.mean() / late_ov.std()),
        "sharpe_2022+_h6_per_day": float(late_h6.mean() / late_h6.std()),
        "std_2022+_overnight": float(late_ov.std()), "std_2022+_h6": float(late_h6.std()),
        "corr_same_day": float(j.corr().iloc[0, 1]),
        "worst_intraday_pct_overnight": float(ov["low"].min() * 100),
        "median_hold_nights_note": "weekday ~18h, Fri->Mon ~66h",
    }
    return res


RUNNERS = {"A1": run_a1, "A2": run_a2, "A3": run_a3, "A4": run_a4}


def main(which: list[str]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for k in which:
        res = RUNNERS[k]()
        (OUT / f"{k}.json").write_text(json.dumps(res, indent=2, default=str), encoding="utf-8")
        print(f"== {k}")
        print(json.dumps(res, indent=1, default=str)[:6000])


if __name__ == "__main__":
    main(sys.argv[1:] or list(RUNNERS))
