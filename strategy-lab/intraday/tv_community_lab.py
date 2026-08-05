"""TradingView topluluk stratejileri -> honest engine -> Maven 5K geçiş testi.

TradingView'in en popüler halka açık intraday strateji ailelerini (kurallari
kamuya belli) bizim muhafazakâr fill modeliyle ayni veri + ayni maliyetle
yeniden test eder. TV strategy tester'in iyimser doldurmasina güvenilmez;
tek hakem honest_engine.

Aileler:
  1. ST_EMA200   : Supertrend(10,3) yön dönüşü + EMA200 filtresi (trend-follow)
  2. VWAP_FADE   : Günlük VWAP ±2σ bandina sapma + RSI(2) aşırılık, VWAP'a dönüş
  3. RSI2_TREND  : Connors RSI(2) aşırılık + EMA200 yönünde mean-reversion
  4. BB_SQUEEZE  : BB(20,2) Keltner(20,1.5) içinde sıkışma -> kırılım
  5. EMA921_PB   : EMA9/21 kesişimi sonrası EMA21'e pullback + VWAP tarafı
  6. KC_BREAK    : Keltner(20,2) kanal kırılımı + EMA200 filtresi

Her aday için: honest engine metrikleri + Maven 5K (%4 hedef, %10 statik DD,
süre limiti yok) rolling-start Monte Carlo geçiş simülasyonu.

Çalıştır (strategy-lab içinden):
    python -m intraday.tv_community_lab
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from .config import INSTRUMENTS
from .data import load_ohlcv
from .honest_engine import metrics, simulate_trades
from .indicators import atr, daily_vwap, ema

OUT = Path(__file__).resolve().parent.parent / "outputs" / "intraday"
OUT.mkdir(parents=True, exist_ok=True)

DAYS = 1080
MIN_RR_FLOOR = 1.2          # topluluk stratejileri çoğunlukla 1.5-2R hedefler


# --- indikatörler ---------------------------------------------------------

def supertrend(df: pd.DataFrame, period: int = 10, mult: float = 3.0) -> pd.Series:
    """Supertrend yönü: +1 boğa, -1 ayı. Klasik TV formülü, look-ahead'sız."""
    a = atr(df, period)
    hl2 = (df["high"] + df["low"]) / 2
    upper = (hl2 + mult * a).to_numpy()
    lower = (hl2 - mult * a).to_numpy()
    close = df["close"].to_numpy()
    n = len(df)
    fub = upper.copy()
    flb = lower.copy()
    trend = np.ones(n, dtype=int)
    for i in range(1, n):
        fub[i] = upper[i] if (upper[i] < fub[i - 1] or close[i - 1] > fub[i - 1]) else fub[i - 1]
        flb[i] = lower[i] if (lower[i] > flb[i - 1] or close[i - 1] < flb[i - 1]) else flb[i - 1]
        if trend[i - 1] == 1:
            trend[i] = -1 if close[i] < flb[i] else 1
        else:
            trend[i] = 1 if close[i] > fub[i] else -1
    return pd.Series(trend, index=df.index)


def rsi(s: pd.Series, n: int = 2) -> pd.Series:
    d = s.diff()
    up = d.clip(lower=0).ewm(alpha=1 / n, adjust=False).mean()
    dn = (-d.clip(upper=0)).ewm(alpha=1 / n, adjust=False).mean()
    rs = up / dn.replace(0, np.nan)
    return 100 - 100 / (1 + rs)


def in_session(df: pd.DataFrame, symbol: str) -> pd.Series:
    lo, hi = INSTRUMENTS[symbol].session_utc
    h = df.index.hour
    return pd.Series((h >= lo) & (h < hi), index=df.index)


# --- strateji sinyal üreticileri ------------------------------------------
# Her üretici: (long_entry, short_entry, long_sl, long_tp, short_sl, short_tp)

def sig_st_ema200(df: pd.DataFrame):
    st = supertrend(df)
    e200 = ema(df["close"], 200)
    a = atr(df)
    flip_up = (st == 1) & (st.shift(1) == -1)
    flip_dn = (st == -1) & (st.shift(1) == 1)
    le = flip_up & (df["close"] > e200)
    se = flip_dn & (df["close"] < e200)
    lsl = df["close"] - 1.5 * a
    ssl = df["close"] + 1.5 * a
    ltp = df["close"] + 3.0 * a
    stp = df["close"] - 3.0 * a
    return le, se, lsl, ltp, ssl, stp


def sig_vwap_fade(df: pd.DataFrame):
    vw = daily_vwap(df)
    dev = df["close"] - vw
    sd = dev.rolling(48).std()
    r2 = rsi(df["close"], 2)
    a = atr(df)
    le = (dev < -2.0 * sd) & (r2 < 10)
    se = (dev > 2.0 * sd) & (r2 > 90)
    lsl = df["close"] - 1.0 * a
    ssl = df["close"] + 1.0 * a
    ltp = vw
    stp = vw
    return le, se, lsl, ltp, ssl, stp


def sig_rsi2_trend(df: pd.DataFrame):
    e200 = ema(df["close"], 200)
    r2 = rsi(df["close"], 2)
    a = atr(df)
    le = (df["close"] > e200) & (r2 < 5)
    se = (df["close"] < e200) & (r2 > 95)
    lsl = df["close"] - 1.5 * a
    ssl = df["close"] + 1.5 * a
    ltp = df["close"] + 2.5 * a
    stp = df["close"] - 2.5 * a
    return le, se, lsl, ltp, ssl, stp


def sig_bb_squeeze(df: pd.DataFrame):
    c = df["close"]
    mid = c.rolling(20).mean()
    sd = c.rolling(20).std()
    bb_u, bb_l = mid + 2 * sd, mid - 2 * sd
    a20 = atr(df, 20)
    kc_u, kc_l = mid + 1.5 * a20, mid - 1.5 * a20
    squeeze = (bb_u < kc_u) & (bb_l > kc_l)
    sq_prev = squeeze.shift(1).fillna(False)
    e200 = ema(c, 200)
    le = sq_prev & ~squeeze & (c > bb_u) & (c > e200)
    se = sq_prev & ~squeeze & (c < bb_l) & (c < e200)
    lsl = mid
    ssl = mid
    ltp = c + 2.0 * (c - mid).abs()
    stp = c - 2.0 * (c - mid).abs()
    return le, se, lsl, ltp, ssl, stp


def sig_ema921_pb(df: pd.DataFrame):
    c = df["close"]
    e9, e21 = ema(c, 9), ema(c, 21)
    vw = daily_vwap(df)
    a = atr(df)
    bull = (e9 > e21) & (c > vw)
    bear = (e9 < e21) & (c < vw)
    touch_lo = df["low"] <= e21
    touch_hi = df["high"] >= e21
    le = bull & touch_lo & (c > e21)
    se = bear & touch_hi & (c < e21)
    lsl = df["low"].rolling(5).min() - 0.25 * a
    ssl = df["high"].rolling(5).max() + 0.25 * a
    ltp = c + 2.0 * (c - lsl)
    stp = c - 2.0 * (ssl - c)
    return le, se, lsl, ltp, ssl, stp


def sig_kc_break(df: pd.DataFrame):
    c = df["close"]
    mid = ema(c, 20)
    a20 = atr(df, 20)
    up, lo = mid + 2.0 * a20, mid - 2.0 * a20
    e200 = ema(c, 200)
    le = (c > up) & (c.shift(1) <= up.shift(1)) & (c > e200)
    se = (c < lo) & (c.shift(1) >= lo.shift(1)) & (c < e200)
    lsl = mid
    ssl = mid
    ltp = c + 2.0 * (c - mid)
    stp = c - 2.0 * (mid - c)
    return le, se, lsl, ltp, ssl, stp


STRATEGIES = {
    "ST_EMA200": sig_st_ema200,
    "VWAP_FADE": sig_vwap_fade,
    "RSI2_TREND": sig_rsi2_trend,
    "BB_SQUEEZE": sig_bb_squeeze,
    "EMA921_PB": sig_ema921_pb,
    "KC_BREAK": sig_kc_break,
}

GRID = [
    ("XAUUSD", "5m", 96), ("XAUUSD", "15m", 64),
    ("NASDAQ100", "5m", 96), ("NASDAQ100", "15m", 64),
    ("EURUSD", "15m", 64), ("GBPUSD", "15m", 64),
]


# --- Maven Monte Carlo -----------------------------------------------------

def maven_mc(r: pd.Series, risk_pct: float, horizon_days: int = 90,
             account: float = 5_000.0) -> dict:
    """Rolling günlük start'larla Maven eval: +%4 hedef, %10 statik DD."""
    if len(r) < 30:
        return {"starts": 0}
    target, breach = account * 1.04, account * 0.90
    days = pd.date_range(r.index[0].normalize(),
                         r.index[-1].normalize() - pd.Timedelta(days=horizon_days),
                         freq="D")
    idx = r.index
    vals = r.to_numpy()
    res = []
    for d0 in days:
        mask = idx >= d0
        if not mask.any():
            continue
        eq = account
        outcome, days_used = "open", horizon_days
        for t, rv in zip(idx[mask], vals[mask]):
            dd_elapsed = (t - d0).days
            if dd_elapsed > horizon_days:
                break
            eq += account * (risk_pct / 100.0) * rv
            if eq >= target:
                outcome, days_used = "pass", dd_elapsed
                break
            if eq <= breach:
                outcome, days_used = "bust", dd_elapsed
                break
        res.append((outcome, days_used))
    if not res:
        return {"starts": 0}
    df = pd.DataFrame(res, columns=["outcome", "days"])
    n = len(df)
    passed = df[df["outcome"] == "pass"]
    return {
        "starts": n,
        "pass_pct": round(100 * len(passed) / n, 1),
        "bust_pct": round(100 * (df["outcome"] == "bust").mean(), 1),
        "median_pass_days": float(passed["days"].median()) if len(passed) else np.nan,
    }


def main() -> None:
    rows = []
    ledgers = {}
    for name, fn in STRATEGIES.items():
        for symbol, tf, max_hold in GRID:
            try:
                df = load_ohlcv(symbol, tf, DAYS)
            except Exception as exc:
                print(f"veri yok: {symbol} {tf}: {exc}")
                continue
            le, se, lsl, ltp, ssl, stp = fn(df)
            sess = in_session(df, symbol)
            le, se = le & sess, se & sess
            r = simulate_trades(df, le, se, lsl, ltp, ssl, stp,
                                INSTRUMENTS[symbol], min_rr=MIN_RR_FLOOR,
                                max_rr=6.0, max_hold=max_hold)
            m = metrics(r)
            if m["trades"] < 60:
                continue
            key = f"{name}|{symbol}|{tf}"
            ledgers[key] = r
            row = {"strategy": name, "symbol": symbol, "tf": tf, **m}
            for risk in (1.0, 1.5, 2.0):
                mc = maven_mc(r, risk)
                row[f"pass90_r{risk}"] = mc.get("pass_pct", np.nan)
                row[f"bust90_r{risk}"] = mc.get("bust_pct", np.nan)
                row[f"days_r{risk}"] = mc.get("median_pass_days", np.nan)
            rows.append(row)
            print(f"{key}: trades={m['trades']} exp_r={m['exp_r']} pf={m['pf']} "
                  f"| r1.5 pass={row['pass90_r1.5']}% bust={row['bust90_r1.5']}%")

    out = pd.DataFrame(rows).sort_values("exp_r", ascending=False)
    out.to_csv(OUT / "tv_community_lab_results.csv", index=False)
    if ledgers:
        led = pd.concat(
            {k: v for k, v in ledgers.items()}, names=["candidate", "timestamp"]
        ).rename("r").reset_index()
        led.to_csv(OUT / "tv_community_lab_ledgers.csv", index=False)
    print(f"\nkaydedildi: {OUT / 'tv_community_lab_results.csv'} ({len(out)} aday)")


if __name__ == "__main__":
    main()
