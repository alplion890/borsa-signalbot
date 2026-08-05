"""Inside-Day Break laboratuvari (Kathy Lien / BK Traders videosu).

Video iddiasi (EURUSD, 5pm NY -> 5pm NY gunluk mum):
  "Gun 5:01pm NY'de onceki gunun range'i ICINDE acilirsa, %84.92 ihtimalle
   seans bitmeden onceki gunun high VEYA low'u KIRILIR."

Bu modul iki sey yapar:
  1) HAM ISTATISTIK dogrulamasi -- iddia bizim veride de tutuyor mu?
  2) TRADE EDILEBILIR formulasyonlarin honest_engine ile backtest'i.

Kritik ayrim: "%85 bir taraf kirilir" bir YON sinyali degil, bir HEDEF
istatistigi. Video da bunu kabul ediyor ("yonu kendi indikatorunle bul").
Yani ham istatistik ne kadar yuksek olursa olsun, maliyet+SL sonrasi
beklenen R'yi ancak gercek bir giris/cikis kurali gosterir. Uc varyant:

  A) BREAKOUT      : range disina 15m kapanisla cikinca yonunde gir
  B) NEAREST       : gun acilisinda yakin sinira dogru gir (kirilim beklentisi)
  C) FARTHEST      : gun acilisinda uzak sinira dogru gir (range ici donus)

Kullanim:
    python -m intraday.inside_day_lab                # EURUSD 3y
    python -m intraday.inside_day_lab EURUSD GBPUSD NASDAQ100 XAUUSD
"""
from __future__ import annotations

import sys
import warnings

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from . import data
from .config import INSTRUMENTS, ATR_LEN, SL_ATR_BUFFER
from .honest_engine import simulate_trades, metrics, oos_metrics
from .indicators import atr

# 5pm New York = FX gunluk kapanis. DST'yi dogru yakalamak icin UTC degil
# America/New_York uzerinden hesaplanir.
NY_TZ = "America/New_York"
DAY_BOUNDARY_HOUR = 17

BARS_PER_DAY_15M = 96
MIN_BARS_FOR_VALID_DAY = 60   # yarim/tatil gunlerini ele
MAX_HOLD_BARS = BARS_PER_DAY_15M   # islem gun icinde kapanir

DEFAULT_SYMBOLS = ["EURUSD"]
DAYS = 1080


# ---------------------------------------------------------------------------
# Gunluk cerceve (5pm NY -> 5pm NY)
# ---------------------------------------------------------------------------

def add_trading_day(df: pd.DataFrame) -> pd.DataFrame:
    """15m bar'lara 5pm-NY bazli 'trading_day' etiketi ekler."""
    ny = df.index.tz_localize("UTC").tz_convert(NY_TZ)
    tday = (ny - pd.Timedelta(hours=DAY_BOUNDARY_HOUR)).normalize()
    out = df.copy()
    out["trading_day"] = pd.to_datetime(tday.tz_localize(None))
    return out


def daily_frame(df: pd.DataFrame) -> pd.DataFrame:
    """5pm-NY gunluk OHLC + onceki gun seviyeleri + inside-open bayragi."""
    g = df.groupby("trading_day")
    d = pd.DataFrame({
        "open": g["open"].first(),
        "high": g["high"].max(),
        "low": g["low"].min(),
        "close": g["close"].last(),
        "bars": g["close"].size(),
    })
    d = d[d["bars"] >= MIN_BARS_FOR_VALID_DAY]

    d["prev_high"] = d["high"].shift(1)
    d["prev_low"] = d["low"].shift(1)
    d["prev_bars"] = d["bars"].shift(1)
    d = d.dropna(subset=["prev_high", "prev_low"])

    d["inside_open"] = (d["open"] > d["prev_low"]) & (d["open"] < d["prev_high"])
    d["broke_high"] = d["high"] > d["prev_high"]
    d["broke_low"] = d["low"] < d["prev_low"]
    d["broke_any"] = d["broke_high"] | d["broke_low"]
    d["broke_both"] = d["broke_high"] & d["broke_low"]
    d["prev_range"] = d["prev_high"] - d["prev_low"]
    # acilisin onceki range icindeki konumu (0 = low, 1 = high)
    d["open_pos"] = (d["open"] - d["prev_low"]) / d["prev_range"]
    return d


# ---------------------------------------------------------------------------
# 1) Ham istatistik dogrulamasi
# ---------------------------------------------------------------------------

def stat_report(d: pd.DataFrame, label: str) -> None:
    """Videonun ham iddiasini farkli pencerelerde test et."""
    print(f"\n=== HAM ISTATISTIK: {label} (5pm NY gunluk) ===")
    print(f"{'pencere':<10} {'inside-gun':>11} {'kirildi':>9} {'oran %':>8} "
          f"{'ikisi de':>9} {'tum gun %':>10}")
    for name, days in (("son 6ay", 182), ("son 1y", 365), ("son 2y", 730), ("tumu", 99999)):
        cut = d.index.max() - pd.Timedelta(days=days)
        sub = d[d.index >= cut]
        ins = sub[sub["inside_open"]]
        if len(ins) < 10:
            continue
        rate = ins["broke_any"].mean() * 100
        both = ins["broke_both"].mean() * 100
        base = sub["broke_any"].mean() * 100   # inside filtresi OLMADAN
        print(f"{name:<10} {len(ins):>11} {int(ins['broke_any'].sum()):>9} "
              f"{rate:>8.2f} {both:>8.1f}% {base:>9.2f}")
    print("  NOT: 'tum gun %' = inside filtresi uygulanmadan ayni oran."
          "\n  Ikisi yakinsa filtrenin BILGI KATKISI yoktur (baz oran yanilgisi).")


# ---------------------------------------------------------------------------
# 2) Trade edilebilir varyantlar -> honest_engine sinyalleri
# ---------------------------------------------------------------------------

def _blank(idx):
    return pd.Series(False, index=idx), pd.Series(np.nan, index=idx)


def build_signals(
    df: pd.DataFrame,
    d: pd.DataFrame,
    variant: str,
    sl_atr: float = 1.0,
    rr: float = 2.0,
) -> tuple:
    """Secilen varyant icin (long_entry, short_entry, l_sl, l_tp, s_sl, s_tp)."""
    idx = df.index
    a = atr(df, ATR_LEN)
    buf = a * SL_ATR_BUFFER

    le = pd.Series(False, index=idx)
    se = pd.Series(False, index=idx)
    l_sl = pd.Series(np.nan, index=idx)
    l_tp = pd.Series(np.nan, index=idx)
    s_sl = pd.Series(np.nan, index=idx)
    s_tp = pd.Series(np.nan, index=idx)

    qualifying = d[d["inside_open"]]
    day_groups = df.groupby("trading_day")

    for day, row in qualifying.iterrows():
        if day not in day_groups.groups:
            continue
        bars = df.loc[day_groups.groups[day]]
        if bars.empty:
            continue
        ph, pl = row["prev_high"], row["prev_low"]

        if variant == "A":
            # Range disina 15m KAPANISLA cikan ilk bar -> o yonde gir.
            up = bars.index[bars["close"] > ph]
            dn = bars.index[bars["close"] < pl]
            t_up = up[0] if len(up) else None
            t_dn = dn[0] if len(dn) else None
            if t_up is None and t_dn is None:
                continue
            if t_dn is None or (t_up is not None and t_up <= t_dn):
                t, side = t_up, "long"
            else:
                t, side = t_dn, "short"
            entry = df["close"].loc[t]
            risk = sl_atr * a.loc[t] + buf.loc[t]
            if not np.isfinite(risk) or risk <= 0:
                continue
            if side == "long":
                le.loc[t] = True
                l_sl.loc[t] = entry - risk
                l_tp.loc[t] = entry + rr * risk
            else:
                se.loc[t] = True
                s_sl.loc[t] = entry + risk
                s_tp.loc[t] = entry - rr * risk

        elif variant in ("B", "C"):
            # Gunun ILK bar'inin kapanisinda gir. Hedef bir range siniri.
            t = bars.index[0]
            entry = df["close"].loc[t]
            risk = sl_atr * a.loc[t] + buf.loc[t]
            if not np.isfinite(risk) or risk <= 0:
                continue
            near_low = row["open_pos"] < 0.5
            # B: yakin sinira dogru (kirilim beklentisi)
            # C: uzak sinira dogru (range ici donus)
            go_short = near_low if variant == "B" else (not near_low)
            if go_short:
                target = pl if variant == "B" else pl
                target = pl - 0.1 * risk if variant == "B" else pl
                se.loc[t] = True
                s_sl.loc[t] = entry + risk
                s_tp.loc[t] = target
            else:
                target = ph + 0.1 * risk if variant == "B" else ph
                le.loc[t] = True
                l_sl.loc[t] = entry - risk
                l_tp.loc[t] = target
        else:
            raise ValueError(f"bilinmeyen varyant: {variant}")

    return le, se, l_sl, l_tp, s_sl, s_tp


def make_folds(idx: pd.DatetimeIndex, n: int = 6):
    """oos_metrics icin basit zaman-dilimi fold'lari."""
    edges = pd.date_range(idx.min(), idx.max(), periods=n + 1)
    return [(edges[i], edges[i], edges[i], edges[i + 1]) for i in range(n)]


def run_variant(df, d, instrument, variant, sl_atr, rr, folds):
    le, se, l_sl, l_tp, s_sl, s_tp = build_signals(df, d, variant, sl_atr, rr)
    r = simulate_trades(
        df, le, se, l_sl, l_tp, s_sl, s_tp, instrument,
        min_rr=0.5, max_rr=10.0, max_hold=MAX_HOLD_BARS,
    )
    m = metrics(r)
    o = oos_metrics(r, folds) if len(r) else {"oos_exp_r": np.nan, "pos_folds": "0/0"}
    m.update(o)
    return m


VARIANT_NAMES = {
    "A": "BREAKOUT  (range disi 15m kapanis)",
    "B": "NEAREST   (acilista yakin sinira)",
    "C": "FARTHEST  (acilista uzak sinira)",
}


def run_symbol(symbol: str) -> None:
    instrument = INSTRUMENTS[symbol]
    df = data.load_ohlcv(symbol, "15m", DAYS)
    df = add_trading_day(df)
    d = daily_frame(df)

    print("\n" + "=" * 78)
    print(f"  {symbol}  |  {df.index.min():%Y-%m-%d} -> {df.index.max():%Y-%m-%d}  "
          f"|  {len(d)} gun")
    print("=" * 78)

    stat_report(d, symbol)

    folds = make_folds(df.index)
    print(f"\n=== HONEST ENGINE BACKTEST: {symbol} (maliyet sonrasi, R cinsi) ===")
    print(f"{'varyant':<38} {'SLxATR':>7} {'RR':>5} {'islem':>6} {'exp_R':>7} "
          f"{'win%':>6} {'PF':>6} {'OOS_R':>7} {'fold+':>6} {'top_R':>7}")

    for variant in ("A", "B", "C"):
        grid = [(k, rr) for k in (0.75, 1.0, 1.5) for rr in (1.5, 2.0, 3.0)]
        if variant in ("B", "C"):
            grid = [(k, 0.0) for k in (0.75, 1.0, 1.5)]   # TP sabit: range siniri
        for sl_atr, rr in grid:
            m = run_variant(df, d, instrument, variant, sl_atr, rr, folds)
            if m["trades"] == 0:
                continue
            rr_txt = f"{rr:.1f}" if rr else "sinir"
            print(f"{VARIANT_NAMES[variant]:<38} {sl_atr:>7.2f} {rr_txt:>5} "
                  f"{m['trades']:>6} {m['exp_r']:>7.3f} {m['win_rate']:>6.1f} "
                  f"{m['pf']:>6.2f} {m.get('oos_exp_r', np.nan):>7.3f} "
                  f"{str(m.get('pos_folds', '-')):>6} {m.get('total_R', 0):>7.1f}")


def main() -> None:
    symbols = sys.argv[1:] or DEFAULT_SYMBOLS
    for s in symbols:
        if s not in INSTRUMENTS:
            print(f"[atlandi] tanimsiz enstruman: {s}")
            continue
        try:
            run_symbol(s)
        except Exception as exc:
            print(f"[hata] {s}: {exc}")


if __name__ == "__main__":
    main()
