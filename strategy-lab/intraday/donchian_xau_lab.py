"""DONCHIAN_XAU_1H -- on-kayitli hipotez (bkz hypotheses.json, id=donchian_xau_1h).

NE: Turtle-tipi Donchian kanal kirilim. Kapanis N-barlik ust bandi (rolling
high, shift(1) ile look-ahead'siz) yukari kirarsa long, alt bandi asagi
kirarsa short. Stop = karsi kanal (turtle klasigi), hedef = risk * rr.

NEDEN: momentum-devam mekanizmasi, backtest'e bakip parametre secilmedi.
Iki N degeri (turtle klasigi 20/55) -- deneme_sayisi=2, hypotheses.json'da
on-kayitli. CAND_ modul: default_modules()'e girmez, sadece bu script ile
kosulur.

Calistir:
    python -m intraday.donchian_xau_lab
"""
from __future__ import annotations

import sys
from dataclasses import dataclass

import pandas as pd

from .config import ATR_LEN, INSTRUMENTS
from .history_fetch import load_history
from .honest_engine import simulate_trades
from .indicators import atr, rolling_high, rolling_low
from .overfit_stats import sharpe

RR = 2.0
MAX_HOLD_BARS = 200  # ~8 gun @ 1h


@dataclass(frozen=True)
class DonchianCase:
    n: int


def _resample_1h(df5m: pd.DataFrame) -> pd.DataFrame:
    agg = {"open": "first", "high": "max", "low": "min", "close": "last",
           "volume": "sum"}
    out = df5m.resample("1h").agg(agg).dropna(subset=["open", "high", "low", "close"])
    return out


def build_signals(df: pd.DataFrame, case: DonchianCase) -> tuple:
    upper = rolling_high(df, case.n)
    lower = rolling_low(df, case.n)
    close = df["close"]

    le = (close > upper) & (close.shift(1) <= upper.shift(1))
    se = (close < lower) & (close.shift(1) >= lower.shift(1))

    long_sl = lower.where(le)
    short_sl = upper.where(se)
    long_risk = (close - long_sl)
    short_risk = (short_sl - close)
    long_tp = (close + RR * long_risk).where(le)
    short_tp = (close - RR * short_risk).where(se)
    return le, se, long_sl, long_tp, short_sl, short_tp


def summarize(r: pd.Series) -> dict:
    if not len(r):
        return {"islem": 0, "toplam_R": 0.0, "exp_R": float("nan"),
                "haftalik_SR": float("nan"), "aktif_hafta": 0}
    wk = r.resample("W").sum()
    wk = wk[wk != 0]
    sr = sharpe(wk) if len(wk) > 1 else float("nan")
    return {"islem": len(r), "toplam_R": float(r.sum()), "exp_R": float(r.mean()),
            "haftalik_SR": sr, "aktif_hafta": len(wk)}


def main() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    df5m = load_history("XAUUSD", "5m", start_year=2012)
    df = _resample_1h(df5m)
    inst = INSTRUMENTS["XAUUSD"]
    print(f"XAUUSD 1h (5m'den resample): {len(df):,} bar, {df.index[0].date()} -> {df.index[-1].date()}")

    for n in (20, 55):
        case = DonchianCase(n)
        le, se, lsl, ltp, ssl, stp = build_signals(df, case)
        r = simulate_trades(df, le, se, lsl, ltp, ssl, stp, inst,
                            min_rr=RR - 0.01, max_rr=RR, max_hold=MAX_HOLD_BARS)
        ozet = summarize(r)
        print(f"\n=== N={n} ===")
        print(f"  islem={ozet['islem']}  toplam_R={ozet['toplam_R']:+.2f}  "
              f"exp_R={ozet['exp_R']:+.3f}  haftalik_SR={ozet['haftalik_SR']:+.3f}  "
              f"aktif_hafta={ozet['aktif_hafta']}")
        if ozet["islem"] > 0:
            r.to_csv(f"donchian_xau_n{n}_trades.csv", header=["r"])


if __name__ == "__main__":
    main()
