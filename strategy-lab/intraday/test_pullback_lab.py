from __future__ import annotations
import sys, warnings
warnings.filterwarnings("ignore")
import pandas as pd
import numpy as np

from . import data
from .config import INSTRUMENTS
from .indicators import atr, swing_high, swing_low
from .honest_engine import simulate_trades, metrics
from .edge_lab import _adx

def ema(s: pd.Series, period: int) -> pd.Series:
    return s.ewm(span=period, adjust=False).mean()

def _make_pullback_signals(df, adx_thresh=25.0):
    adx = _adx(df, 14)
    a = atr(df, 14)
    buf = a * 0.25  # Stop Loss Buffer
    
    ema20 = ema(df["close"], 20)
    ema50 = ema(df["close"], 50)
    
    sh = swing_high(df)
    sl_ = swing_low(df)
    
    # Uptrend and Downtrend definitions
    uptrend = (ema20 > ema50) & (adx > adx_thresh)
    downtrend = (ema20 < ema50) & (adx > adx_thresh)
    
    # Pullback logic: Fiyat EMA20'nin altina sarsin ama uzerinde kapatsin
    long_raw = uptrend & (df["low"] < ema20) & (df["close"] > ema20)
    short_raw = downtrend & (df["high"] > ema20) & (df["close"] < ema20)
    
    le = long_raw & ~long_raw.shift(1).fillna(False)
    se = short_raw & ~short_raw.shift(1).fillna(False)
    
    # Risk calculation: low/high of the signal bar with ATR buffer
    lsl = df["low"].where(le) - buf.where(le)
    ssl = df["high"].where(se) + buf.where(se)
    
    # Use generic fixed RR in engine or swing points
    ltp = sh.where(le)
    stp = sl_.where(se)
    
    return le, se, lsl, ltp, ssl, stp

def run():
    symbol = "NASDAQ100"
    df = data.load_ohlcv(symbol, "5m", 1080) # 3 yillik data
    inst = INSTRUMENTS[symbol]
    
    # Filtresiz (ADX=0)
    le0, se0, lsl0, ltp0, ssl0, stp0 = _make_pullback_signals(df, adx_thresh=0.0)
    r_unfiltered = simulate_trades(df, le0, se0, lsl0, ltp0, ssl0, stp0, inst, min_rr=1.5, max_rr=3.0)
    m0 = metrics(r_unfiltered)
    
    # Filtreli (ADX>25)
    le, se, lsl, ltp, ssl, stp = _make_pullback_signals(df, adx_thresh=25.0)
    r_filtered = simulate_trades(df, le, se, lsl, ltp, ssl, stp, inst, min_rr=1.5, max_rr=3.0)
    m = metrics(r_filtered)
    
    print("=== MA PULLBACK TEST SONUCLARI (NASDAQ100 - 5m) ===")
    print("1. FILTRESIZ (Yatay piyasa ve dusuk volatilite DAHIL):")
    print(f"Trade sayisi: {m0['trades']}")
    print(f"Win Rate: {m0['win_rate']}%")
    print(f"Expected R: {m0['exp_r']:.3f} R")
    
    print("\n2. FILTRELI (Sadece ADX > 25, dusuk volatilite ve yatay HARIC):")
    print(f"Trade sayisi: {m['trades']}")
    print(f"Win Rate: {m['win_rate']}%")
    print(f"Expected R: {m['exp_r']:.3f} R")

if __name__ == "__main__":
    run()
