"""A/B: NQ_ORB'un RANGE TANIMI degissin, gerisi sabit kalsin.

Soru
----
NQ_ORB kanitli motorunun tetik seviyesi "seansin ilk 15 dakikasinin high/low'u".
Dual Thrust (je-suis-tm/quant-trading, Apache-2.0) ayni aileden ama range'i
farkli tanimlar:

    range = max(HH - LC, HC - LL)   <- onceki N gunun gunluk ozetinden
    long  tetik = seans_acilis + K * range
    short tetik = seans_acilis - K * range

Yeni strateji DEGIL: ayni sembol, ayni seans, ayni SL mantigi (karsi tetik
cizgisi), ayni RR, ayni hold, ayni ADX filtresi. Sadece "tetik nerede" degisiyor.

Durustluk notu
--------------
K ve N icin kucuk bir grid deniyoruz -> bu COKLU KARSILASTIRMA. Bu yuzden
sonucta `overfit_stats.deflated_from_trials` ile DSR basiliyor: en iyi varyant,
denenen varyant sayisi hesaba katilinca hala anlamli mi? Baseline dahil TUM
varyantlar aday sayilir.
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
from .config import INSTRUMENTS
from .edge_lab import _adx
from .honest_engine import metrics, oos_metrics, simulate_trades
from .internet_seed_strategies import ORBCase, _build_orb, _one_signal_per_day

SYMBOL = "NASDAQ100"
DAYS = 1080
CASE = ORBCase(SYMBOL, 14.5, 15, 20.5, "retest", "none", 1.5, "other_side", 1.0, 48)
ADX_MIN = 30.0          # strong_trend rejimi (kanitli filtre)
SESSION_OPEN = 14.5     # NY acilis (CASE.open_hour ile ayni)
TRADE_END = 20.5
K_GRID = (0.3, 0.5, 0.7)
N_GRID = (2, 4)


def _hour_float(index: pd.DatetimeIndex) -> np.ndarray:
    return index.hour.to_numpy() + index.minute.to_numpy() / 60.0


def dual_thrust_range(df: pd.DataFrame, n_days: int) -> pd.Series:
    """Onceki N GUNUN ozetinden Dual Thrust range'i. Ileriye bakmaz (shift(1))."""
    day = pd.Index(df.index.date)
    daily = pd.DataFrame({
        "high": df["high"].groupby(day).max(),
        "low": df["low"].groupby(day).min(),
        "close": df["close"].groupby(day).last(),
    })
    hh = daily["high"].rolling(n_days).max()
    ll = daily["low"].rolling(n_days).min()
    hc = daily["close"].rolling(n_days).max()
    lc = daily["close"].rolling(n_days).min()
    rng = np.maximum(hh - lc, hc - ll).shift(1)  # shift: bugun ONCEKI gunlerden
    return pd.Series(day, index=df.index).map(rng)


def session_open_price(df: pd.DataFrame, open_hour: float) -> pd.Series:
    """Seans acilis barinin open'i, gun ici her bara yayilir."""
    h = _hour_float(df.index)
    day = pd.Index(df.index.date)
    at_open = df["open"].where(h >= open_hour)
    return at_open.groupby(day).transform("first")


def build_dual_thrust(df: pd.DataFrame, k: float, n_days: int, rr: float,
                      max_hold: int) -> tuple:
    """ORB ile ayni imza: (le, se, long_sl, long_tp, short_sl, short_tp)."""
    h = _hour_float(df.index)
    rng = dual_thrust_range(df, n_days)
    s_open = session_open_price(df, SESSION_OPEN)

    buy_line = s_open + k * rng
    sell_line = s_open - k * rng
    window = (h >= SESSION_OPEN) & (h < TRADE_END)

    long_raw = window & (df["close"] > buy_line) & (df["close"].shift(1) <= buy_line.shift(1))
    short_raw = window & (df["close"] < sell_line) & (df["close"].shift(1) >= sell_line.shift(1))

    le = _one_signal_per_day(long_raw.fillna(False))
    se = _one_signal_per_day((short_raw & ~le).fillna(False))

    entry = df["close"]
    # ORB "other_side" mantiginin karsiligi: karsi tetik cizgisi
    long_sl = sell_line.where(le)
    short_sl = buy_line.where(se)
    long_tp = (entry + rr * (entry - long_sl)).where(le)
    short_tp = (entry - rr * (short_sl - entry)).where(se)
    return le, se, long_sl, long_tp, short_sl, short_tp


def make_folds(idx: pd.DatetimeIndex, n: int = 6):
    edges = pd.date_range(idx.min(), idx.max(), periods=n + 1)
    return [(edges[i], edges[i], edges[i], edges[i + 1]) for i in range(n)]


def _row(label: str, r: pd.Series, folds) -> tuple[dict, pd.Series]:
    m = metrics(r)
    if len(r):
        m.update(oos_metrics(r, folds))
    print(f"{label:<26} {m['trades']:>6} {m['exp_r']:>8.3f} {m['win_rate']:>6.1f} "
          f"{m['pf']:>6.2f} {m.get('oos_exp_r', np.nan):>8.3f} "
          f"{str(m.get('pos_folds', '-')):>7} {m.get('total_R', 0):>8.1f}")
    return {"varyant": label, **m}, r


def run() -> None:
    inst = INSTRUMENTS[SYMBOL]
    df = data.load_ohlcv(SYMBOL, "5m", DAYS)
    adx_ok = _adx(df, 14) > ADX_MIN
    folds = make_folds(df.index)

    print(f"\n=== NQ_ORB A/B: RANGE TANIMI (giris saati/SL mantigi/RR/hold/ADX>{ADX_MIN} sabit)")
    print(f"{'varyant':<26} {'islem':>6} {'exp_R':>8} {'win%':>6} {'PF':>6} "
          f"{'OOS_R':>8} {'fold+':>7} {'top_R':>8}")

    trials: dict[str, pd.Series] = {}
    rows = []

    le, se, lsl, ltp, ssl, stp = _build_orb(df, CASE)
    le, se = le & adx_ok, se & adx_ok
    r = simulate_trades(df, le, se, lsl, ltp, ssl, stp, inst,
                        min_rr=0.5, max_rr=10.0, max_hold=CASE.max_hold)
    row, r = _row("BASELINE (ORB 15dk)", r, folds)
    rows.append(row)
    trials["BASELINE_ORB15"] = r

    for n_days in N_GRID:
        for k in K_GRID:
            le, se, lsl, ltp, ssl, stp = build_dual_thrust(df, k, n_days, CASE.rr, CASE.max_hold)
            le, se = le & adx_ok, se & adx_ok
            r = simulate_trades(df, le, se, lsl, ltp, ssl, stp, inst,
                                min_rr=0.5, max_rr=10.0, max_hold=CASE.max_hold)
            label = f"DUAL_THRUST N={n_days} K={k}"
            row, r = _row(label, r, folds)
            rows.append(row)
            trials[label] = r

    print("\n--- coklu-karsilastirma denetimi (baseline dahil tum varyantlar aday) ---")
    # Tembel import: bu modulun sinyal uretici kismi (`build_dual_thrust`)
    # forward EA'nin bulut kosucusundan cagriliyor ve orada scipy KURULU
    # DEGIL. Ust seviyede import edilirse bulut defteri her saat cokur --
    # 2026-08-21'de tam bu oldu, olcum 14 saat durdu.
    from .overfit_stats import deflated_from_trials

    out = deflated_from_trials(trials)
    print(f"  aday sayisi      : {out['n_trials']}")
    print(f"  en iyi           : {out['best']}")
    print(f"  SR               : {out['sharpe']:+.4f}")
    print(f"  sans esigi E[max]: {out['sr_threshold']:.4f}")
    print(f"  DSR              : {out['dsr']:.4f}  "
          f"({'GECTI' if out['dsr'] >= 0.95 else 'GECMEDI -- benimseme'})")

    dest = data.OUT_DIR / "dual_thrust_ab.csv" if hasattr(data, "OUT_DIR") else None
    summary = pd.DataFrame(rows)
    if dest is None:
        from pathlib import Path
        dest = Path(__file__).resolve().parents[1] / "outputs" / "intraday" / "dual_thrust_ab.csv"
    summary.to_csv(dest, index=False)
    print(f"\nCikti: {dest}")


if __name__ == "__main__":
    run()
