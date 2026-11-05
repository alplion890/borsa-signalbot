"""SWEEP_CORE prop-compliance (H1) and sweep-depth robustness (H2) test.

Preregistration: HANDOFF/sweep_prop_uyum_onkayit_2026-11-05.md (commit eb30887).

The simulator below is a line-by-line copy of honest_engine._simulate_bar_sl_first
plus two optional masks (no_entry, force_exit). With empty masks it must match
honest_engine.simulate_trades exactly; run() asserts this before reporting.

    python -m intraday.sweep_prop_lab
"""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

from .config import ATR_LEN, INSTRUMENTS
from .event_calendar import cpi_events, fomc_events, nfp_events
from .history_fetch import load_history
from .honest_engine import simulate_trades
from .indicators import atr, rolling_high, rolling_low
from .long_history_ab import _atr_rank, _sweep_build

NY = ZoneInfo("America/New_York")
BAR = pd.Timedelta(minutes=15)
NEWS_WINDOW = pd.Timedelta(minutes=5)
DEPTH_K = 0.10
OUT = Path(__file__).resolve().parent.parent / "outputs" / "intraday" / "sweep_prop_lab"


def simulate(df, le, se, lsl, ltp, ssl, stp, inst, min_rr, max_rr, max_hold,
             no_entry=None, force_exit=None) -> pd.Series:
    price = df["close"].to_numpy(); opn = df["open"].to_numpy(dtype=float)
    high = df["high"].to_numpy(); low = df["low"].to_numpy()
    idx = df.index; n = len(df); cost = inst.cost_per_side
    le = le.fillna(False).to_numpy(); se = se.fillna(False).to_numpy()
    lsl = lsl.to_numpy(dtype=float); ltp = ltp.to_numpy(dtype=float)
    ssl = ssl.to_numpy(dtype=float); stp = stp.to_numpy(dtype=float)
    blk = np.zeros(n, bool) if no_entry is None else no_entry.to_numpy(bool)
    fx = np.zeros(n, bool) if force_exit is None else force_exit.to_numpy(bool)
    out = {}; last_exit = -1
    for i in range(n):
        is_long, is_short = le[i], se[i]
        if not (is_long or is_short) or i <= last_exit or blk[i]:
            continue
        entry = price[i]
        sl_px, tp_px = (lsl[i], ltp[i]) if is_long else (ssl[i], stp[i])
        if not (np.isfinite(sl_px) and np.isfinite(tp_px)):
            continue
        risk = (entry - sl_px) if is_long else (sl_px - entry)
        reward = (tp_px - entry) if is_long else (entry - tp_px)
        if risk <= 0 or reward <= 0:
            continue
        rr = reward / risk
        if rr < min_rr:
            continue
        if rr > max_rr:
            tp_px = entry + max_rr * risk if is_long else entry - max_rr * risk
            rr = max_rr
        slf = risk / entry; outcome = None
        for j in range(i + 1, min(i + 1 + max_hold, n)):
            if (opn[j] <= sl_px if is_long else opn[j] >= sl_px):
                outcome = ((opn[j] - entry) if is_long else (entry - opn[j])) / risk; last_exit = j; break
            if (opn[j] >= tp_px if is_long else opn[j] <= tp_px):
                outcome = rr; last_exit = j; break
            if is_long:
                if low[j] <= sl_px: outcome = -1.0; last_exit = j; break
                if high[j] >= tp_px: outcome = rr; last_exit = j; break
            else:
                if high[j] >= sl_px: outcome = -1.0; last_exit = j; break
                if low[j] <= tp_px: outcome = rr; last_exit = j; break
            if fx[j]:
                move = (price[j] - entry) if is_long else (entry - price[j])
                outcome = move / risk; last_exit = j; break
        if outcome is None:
            jx = min(i + max_hold, n - 1)
            move = (price[jx] - entry) if is_long else (entry - price[jx])
            outcome = move / risk; last_exit = jx
        outcome -= 2 * cost / slf
        out[idx[i]] = outcome
    return pd.Series(out).sort_index() if out else pd.Series(dtype=float)


def base_signals(df: pd.DataFrame):
    le, se, lsl, ltp, ssl, stp = _sweep_build(df)
    rank = _atr_rank(df)
    cap = pd.Series(np.select([rank < .33, rank < .67], [4., 6.], default=8.), index=df.index)
    ltp = pd.Series(np.minimum(ltp, df.close + (df.close - lsl) * cap), index=df.index)
    stp = pd.Series(np.maximum(stp, df.close - (ssl - df.close) * cap), index=df.index)
    ok = rank.notna()
    return le & ok, se & ok, lsl, ltp, ssl, stp


def depth_mask(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    a = atr(df, ATR_LEN)
    long_ok = (rolling_low(df, 20) - df["low"]) >= DEPTH_K * a
    short_ok = (df["high"] - rolling_high(df, 20)) >= DEPTH_K * a
    return long_ok.fillna(False), short_ok.fillna(False)


def news_times_utc() -> pd.DatetimeIndex:
    stamps = [dt.datetime.combine(e.gun, e.aciklama_et, NY).astimezone(dt.timezone.utc)
              for e in fomc_events() + cpi_events() + nfp_events()]
    return pd.DatetimeIndex(sorted(stamps)).tz_convert(None)


def prop_masks(idx: pd.DatetimeIndex) -> tuple[pd.Series, pd.Series]:
    friday_late = pd.Series((idx.dayofweek == 4) & (idx.hour >= 20), index=idx)
    entry_at = idx + BAR
    news = news_times_utc().to_numpy()
    pos = np.searchsorted(news, entry_at.to_numpy())
    near = np.zeros(len(idx), bool)
    for k in (pos - 1, pos):
        k = np.clip(k, 0, len(news) - 1)
        near |= np.abs(entry_at.to_numpy() - news[k]) <= NEWS_WINDOW.to_timedelta64()
    no_entry = friday_late | pd.Series(near, index=idx)
    return no_entry, friday_late


def stats(r: pd.Series) -> dict:
    eq = r.cumsum()
    return {"n": int(len(r)), "mean_r": round(float(r.mean()), 4), "sum_r": round(float(r.sum()), 2),
            "worst": round(float(r.min()), 2), "max_dd_r": round(float((eq.cummax() - eq).max()), 2),
            "pre2022": round(float(r[r.index.year < 2022].mean()), 4),
            "post2022": round(float(r[r.index.year >= 2022].mean()), 4),
            "worst5": [round(float(x), 2) for x in r.nsmallest(5)]}


def jaccard(a: set, b: set) -> float:
    return len(a & b) / len(a | b) if (a | b) else float("nan")


def feed_agreement() -> dict:
    from .adx_lab import _make_signals
    from .signalbot import free_data
    snaps = sorted((OUT.parent / "research_panel" / "broker_history").glob("NASDAQ100_15m_*.csv"),
                   key=lambda p: p.stat().st_mtime)
    m = pd.read_csv(snaps[-1]); tcol = [c for c in m.columns if "time" in c.lower()][0]
    m.index = pd.to_datetime(m[tcol]); m = m[["open", "high", "low", "close", "volume"]].astype(float)
    y = free_data.ohlcv("NASDAQ100", "15m", days=59); y.index = y.index.tz_convert(None)
    common = m.index.intersection(y.index)
    res = {"common_bars": int(len(common)), "maven_snapshot": snaps[-1].name}
    sig = {}
    for name, frame in (("maven", m), ("nqf", y)):
        le, se, *_ = _make_signals(frame, 25.0)
        lok, sok = depth_mask(frame)
        sig[name] = {"base": set(frame.index[(le | se)]) & set(common),
                     "h2": set(frame.index[(le & lok) | (se & sok)]) & set(common)}
    for k in ("base", "h2"):
        res[k] = {"maven": len(sig["maven"][k]), "nqf": len(sig["nqf"][k]),
                  "common": len(sig["maven"][k] & sig["nqf"][k]),
                  "jaccard": round(jaccard(sig["maven"][k], sig["nqf"][k]), 3)}
    return res


def run() -> dict:
    spec_name = "SWEEP_CORE"
    df = load_history("NASDAQ100", "15m", start_year=2012)
    inst = INSTRUMENTS["NASDAQ100"]
    le, se, lsl, ltp, ssl, stp = base_signals(df)
    kw = dict(min_rr=2.0, max_rr=8.0, max_hold=480)
    ref = simulate_trades(df, le, se, lsl, ltp, ssl, stp, inst, **kw)
    base = simulate(df, le, se, lsl, ltp, ssl, stp, inst, **kw)
    assert ref.index.equals(base.index) and np.allclose(ref.to_numpy(), base.to_numpy()), \
        "lab simulator diverged from honest_engine"
    no_entry, force_exit = prop_masks(df.index)
    h1 = simulate(df, le, se, lsl, ltp, ssl, stp, inst, **kw, no_entry=no_entry, force_exit=force_exit)
    lok, sok = depth_mask(df)
    h2 = simulate(df, le & lok, se & sok, lsl, ltp, ssl, stp, inst, **kw)
    res = {"spec": spec_name, "bars": int(len(df)), "first": str(df.index.min()), "last": str(df.index.max()),
           "parity_with_engine": True, "base": stats(base), "h1": stats(h1), "h2": stats(h2)}
    try:
        res["feed_agreement"] = feed_agreement()
    except Exception as exc:  # reported, not hidden
        res["feed_agreement"] = {"error": f"{type(exc).__name__}: {exc}"}
    b, a1, a2 = res["base"], res["h1"], res["h2"]
    res["h1_accept"] = bool(a1["mean_r"] >= b["mean_r"] - 0.02 and
                            (a1["worst"] >= b["worst"] or a1["max_dd_r"] <= b["max_dd_r"]))
    fa = res["feed_agreement"]
    primary = ("h2" in fa and fa["h2"]["jaccard"] > fa["base"]["jaccard"])
    secondary = a2["mean_r"] >= b["mean_r"] - 0.02 and a2["n"] >= 0.6 * b["n"]
    res["h2_primary"], res["h2_secondary"] = bool(primary), bool(secondary)
    res["h2_accept"] = bool(primary and secondary)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "result_2026-11-05.json").write_text(json.dumps(res, indent=2), encoding="utf-8")
    return res


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
