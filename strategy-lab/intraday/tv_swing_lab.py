"""TradingView topluluğunun açık kaynaklı klasik swing/trend stratejileri.

Kaynak: TradingView masaüstü uygulaması "Popüler > Stratejiler" listesi
canlı incelendi (2026-07-03). Listenin çoğunluğu kapalı kaynak / davetiyeli
"Smart Money / ML / Order Block" hype scriptleri — kuralları görülemediği
için dürüstçe test edilemez, elenir.

Burada test edilenler kamuya açık, formülü herkesçe bilinen, TV
topluluğunda binlerce kez yeniden yayınlanmış klasikler (listede de
görüldü, formülleri endüstri standardı ve kaynak kodu kamuya açık):
  - UT_BOT     : ATR Trailing Stop (QuantNomad / orijinal Yo_adriiiiaan)
  - HALFTREND  : HalfTrend kanal dönüşü (everget formülü)
  - CHANDELIER : Chandelier Exit trend-takip
  - DONCHIAN   : Donchian/Turtle 20-55 kırılım (klasik trend-following)

Zaman dilimleri: 1H (intraday) + 4H (swing, 1H'den resample).
Swing pozisyon büyüklüğü daha büyük SL mesafesi = Maven %10 statik DD'ye
göre risk-yüzdesi ayarlanmalı; bu dosya sadece edge (exp_R/PF) ölçer,
risk boyutlandırma challenge_sim'de yapılır.

Çalıştır (strategy-lab içinden):
    python -m intraday.tv_swing_lab
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
from .indicators import atr, ema
from .tv_community_lab import in_session, maven_mc

OUT = Path(__file__).resolve().parent.parent / "outputs" / "intraday"
OUT.mkdir(parents=True, exist_ok=True)

DAYS = 1080
MIN_RR_FLOOR = 1.2


def resample_ohlcv(df: pd.DataFrame, rule: str) -> pd.DataFrame:
    o = df["open"].resample(rule).first()
    h = df["high"].resample(rule).max()
    l = df["low"].resample(rule).min()
    c = df["close"].resample(rule).last()
    v = df["volume"].resample(rule).sum()
    out = pd.concat({"open": o, "high": h, "low": l, "close": c, "volume": v}, axis=1)
    return out.dropna()


def load_1h_base(symbol: str) -> pd.DataFrame:
    """1H veri döner; cache yoksa (XAUUSD) 15m'den resample eder."""
    try:
        return load_ohlcv(symbol, "1H", DAYS)
    except ModuleNotFoundError:
        m15 = load_ohlcv(symbol, "15m", DAYS)
        return resample_ohlcv(m15, "1h")


# --- indikatörler -----------------------------------------------------

def ut_bot_trail(df: pd.DataFrame, key: float = 2.0, atr_period: int = 1) -> pd.Series:
    """UT Bot ATR Trailing Stop - orijinal kamuya açık formül."""
    a = atr(df, atr_period)
    nloss = key * a
    src = df["close"].to_numpy()
    n = len(src)
    stop = np.zeros(n)
    stop[0] = src[0] - nloss.iloc[0]
    for i in range(1, n):
        prev = stop[i - 1]
        if src[i] > prev and src[i - 1] > prev:
            stop[i] = max(prev, src[i] - nloss.iloc[i])
        elif src[i] < prev and src[i - 1] < prev:
            stop[i] = min(prev, src[i] + nloss.iloc[i])
        elif src[i] > prev:
            stop[i] = src[i] - nloss.iloc[i]
        else:
            stop[i] = src[i] + nloss.iloc[i]
    return pd.Series(stop, index=df.index)


def halftrend(df: pd.DataFrame, amplitude: int = 2, atr_period: int = 100) -> pd.Series:
    """HalfTrend yön serisi: +1 boğa, -1 ayı (everget formülünün basitleştirilmiş hali)."""
    high, low, close = df["high"], df["low"], df["close"]
    high_ma = high.rolling(amplitude).mean()
    low_ma = low.rolling(amplitude).mean()
    a = atr(df, atr_period) / 2.0
    n = len(df)
    trend = np.zeros(n, dtype=int)
    trend[0] = 1
    hi, lo = high_ma.to_numpy(), low_ma.to_numpy()
    c = close.to_numpy()
    for i in range(1, n):
        trend[i] = trend[i - 1]
        if trend[i - 1] == 1 and c[i] < lo[i] - a.iloc[i]:
            trend[i] = -1
        elif trend[i - 1] == -1 and c[i] > hi[i] + a.iloc[i]:
            trend[i] = 1
    return pd.Series(trend, index=df.index)


def chandelier_exit(df: pd.DataFrame, period: int = 22, mult: float = 3.0):
    a = atr(df, period)
    long_stop = df["high"].rolling(period).max() - mult * a
    short_stop = df["low"].rolling(period).min() + mult * a
    return long_stop, short_stop


# --- strateji sinyal üreticileri ------------------------------------------

def sig_ut_bot(df: pd.DataFrame):
    stop = ut_bot_trail(df)
    c = df["close"]
    le = (c > stop) & (c.shift(1) <= stop.shift(1))
    se = (c < stop) & (c.shift(1) >= stop.shift(1))
    lsl = stop
    ssl = stop
    ltp = c + 2.0 * (c - stop)
    stp = c - 2.0 * (stop - c)
    return le, se, lsl, ltp, ssl, stp


def sig_halftrend(df: pd.DataFrame):
    tr = halftrend(df)
    flip_up = (tr == 1) & (tr.shift(1) == -1)
    flip_dn = (tr == -1) & (tr.shift(1) == 1)
    a = atr(df)
    c = df["close"]
    le = flip_up
    se = flip_dn
    lsl = c - 1.5 * a
    ssl = c + 1.5 * a
    ltp = c + 3.0 * a
    stp = c - 3.0 * a
    return le, se, lsl, ltp, ssl, stp


def sig_chandelier(df: pd.DataFrame):
    long_stop, short_stop = chandelier_exit(df)
    c = df["close"]
    dir_up = c > long_stop.shift(1)
    dir_up_prev = c.shift(1) > long_stop.shift(2)
    le = dir_up & ~dir_up_prev.fillna(False)
    dir_dn = c < short_stop.shift(1)
    dir_dn_prev = c.shift(1) < short_stop.shift(2)
    se = dir_dn & ~dir_dn_prev.fillna(False)
    a = atr(df)
    lsl = long_stop
    ssl = short_stop
    ltp = c + 2.5 * a
    stp = c - 2.5 * a
    return le, se, lsl, ltp, ssl, stp


def sig_donchian(df: pd.DataFrame, entry_n: int = 20, exit_n: int = 10):
    hi_n = df["high"].rolling(entry_n).max()
    lo_n = df["low"].rolling(entry_n).min()
    c = df["close"]
    a = atr(df)
    le = (c > hi_n.shift(1))
    se = (c < lo_n.shift(1))
    lsl = df["low"].rolling(exit_n).min()
    ssl = df["high"].rolling(exit_n).max()
    ltp = c + 3.0 * a
    stp = c - 3.0 * a
    return le, se, lsl, ltp, ssl, stp


STRATEGIES = {
    "UT_BOT": sig_ut_bot,
    "HALFTREND": sig_halftrend,
    "CHANDELIER": sig_chandelier,
    "DONCHIAN": sig_donchian,
}

SYMBOLS = ["XAUUSD", "NASDAQ100", "EURUSD", "GBPUSD"]
TFS = [("1H", 200), ("4H", 60)]   # (timeframe, max_hold bar sayısı)


def main() -> None:
    rows = []
    ledgers = {}
    for symbol in SYMBOLS:
        base = load_1h_base(symbol)
        frames = {"1H": base, "4H": resample_ohlcv(base, "4h")}
        for tf, max_hold in TFS:
            df = frames[tf]
            for name, fn in STRATEGIES.items():
                le, se, lsl, ltp, ssl, stp = fn(df)
                sess = in_session(df, symbol) if tf == "1H" else pd.Series(True, index=df.index)
                le, se = le & sess, se & sess
                r = simulate_trades(df, le, se, lsl, ltp, ssl, stp,
                                    INSTRUMENTS[symbol], min_rr=MIN_RR_FLOOR,
                                    max_rr=8.0, max_hold=max_hold)
                m = metrics(r)
                if m["trades"] < 40:
                    continue
                key = f"{name}|{symbol}|{tf}"
                ledgers[key] = r
                row = {"strategy": name, "symbol": symbol, "tf": tf, **m}
                for risk in (1.0, 1.5, 2.0):
                    mc = maven_mc(r, risk, horizon_days=90)
                    row[f"pass90_r{risk}"] = mc.get("pass_pct", np.nan)
                    row[f"bust90_r{risk}"] = mc.get("bust_pct", np.nan)
                rows.append(row)
                print(f"{key}: trades={m['trades']} exp_r={m['exp_r']} pf={m['pf']} "
                      f"| r1.5 pass={row['pass90_r1.5']}% bust={row['bust90_r1.5']}%")

    out = pd.DataFrame(rows).sort_values("exp_r", ascending=False)
    out.to_csv(OUT / "tv_swing_lab_results.csv", index=False)
    if ledgers:
        led = pd.concat(
            {k: v for k, v in ledgers.items()}, names=["candidate", "timestamp"]
        ).rename("r").reset_index()
        led.to_csv(OUT / "tv_swing_lab_ledgers.csv", index=False)
    print(f"\nkaydedildi: {OUT / 'tv_swing_lab_results.csv'} ({len(out)} aday)")


if __name__ == "__main__":
    main()
