"""signalbot (yfinance ^NDX) ile forward EA (MT5 US100 CFD) fiyat farki.

NEDEN: Telegram sinyali yfinance endeks serisinden uretiliyor, ama emir MT5'te
US100 CFD'sinde aciliyor. Iki seri AYNI DEGIL:
  - endeks spot, CFD ise vadeli-benzeri bir taban farki (basis) tasir
  - CFD 23 saat islem gorur, endeks sadece ABD seansinda hesaplanir
  - yfinance gecikmeli olabilir (spec.expected_delay_minutes)

Sabit basis ZARARSIZDIR: dedektor seviyeleri de ayni seriden hesapliyor, hepsi
birlikte kayar. TEHLIKELI OLAN basis'in oynakligi -- cunku sinyal fiyati ile
girilen fiyat arasindaki farki O yaratir ve dogrudan R'den yer.

Bu yuzden olculen sey basis'in kendisi degil, basis'in ARTIK OYNAKLIGI:
sabit kismi cikarilir, kalan gurultu R cinsine cevrilir.

Kullanim (MT5 terminali acik + Maven hesabinda login olmali):
    python -m intraday.mt5_bridge.feed_parity
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from ..signalbot import free_data
from . import mt5_io

SIGNALBOT_KEY = "NASDAQ100"   # free_data -> ^NDX
TF = "5m"
DAYS = 30
LEDGER = "outputs/intraday/forward_ea/forward_ledger.csv"
NQ_MODULES = ("NQ_ORB_STRONG_TREND", "SWEEP_CORE_AVOID_MID_VWAP")


def _median_stop_distance(path: str = LEDGER) -> float | None:
    """Defterdeki NASDAQ modullerinin medyan stop mesafesi (fiyat puani).

    R'yi puana cevirmek icin gerekli: 1R = |entry - sl|.
    """
    try:
        df = pd.read_csv(path)
    except OSError:
        return None
    sub = df[df["module"].isin(NQ_MODULES)]
    if sub.empty:
        return None
    return float((sub["entry"] - sub["sl"]).abs().median())


def load_pair(days: int = DAYS, tf: str = TF) -> pd.DataFrame:
    """Iki feed'i ortak zaman damgalarinda hizala (UTC, tz-naive)."""
    yf_df = free_data.ohlcv(SIGNALBOT_KEY, tf, days=days)
    if yf_df.empty:
        raise RuntimeError("yfinance ^NDX verisi bos geldi.")
    yf_close = yf_df["close"]
    yf_close.index = pd.DatetimeIndex(yf_close.index).tz_convert("UTC").tz_localize(None)

    with mt5_io.session():
        mt5_df = mt5_io.ohlcv(SIGNALBOT_KEY, tf, days=days)
    mt5_close = mt5_df["close"]
    idx = pd.DatetimeIndex(mt5_close.index)
    if idx.tz is not None:
        idx = idx.tz_convert("UTC").tz_localize(None)
    mt5_close = mt5_close.set_axis(idx)

    pair = pd.concat({"yf": yf_close, "mt5": mt5_close}, axis=1).dropna()
    if pair.empty:
        raise RuntimeError("Iki feed'in ortak zaman damgasi yok "
                           "(saat dilimi veya seans uyusmazligi).")
    return pair


def report(days: int = DAYS, tf: str = TF) -> dict:
    pair = load_pair(days, tf)
    basis = pair["mt5"] - pair["yf"]
    # Sabit/yavas suruklenen kismi cikar: gunluk medyan basis.
    daily = basis.groupby(basis.index.normalize()).transform("median")
    residual = basis - daily

    yf_ret = pair["yf"].pct_change()
    mt5_ret = pair["mt5"].pct_change()
    both = pd.concat([yf_ret, mt5_ret], axis=1).dropna()

    stop = _median_stop_distance()
    out = {
        "ortak_bar": len(pair),
        "pencere": f"{pair.index.min()} -> {pair.index.max()}",
        "basis_ortalama": float(basis.mean()),
        "basis_std": float(basis.std(ddof=1)),
        "basis_gun_ici_surukleme": float(daily.groupby(daily.index.normalize())
                                         .first().diff().abs().mean()),
        "artik_std_puan": float(residual.std(ddof=1)),
        "artik_p95_puan": float(residual.abs().quantile(0.95)),
        "getiri_korelasyonu": float(both.iloc[:, 0].corr(both.iloc[:, 1])),
        "medyan_stop_puan": stop,
    }
    if stop:
        out["artik_std_R"] = out["artik_std_puan"] / stop
        out["artik_p95_R"] = out["artik_p95_puan"] / stop
    return out


def main() -> None:
    res = report()
    print(f"Ortak bar      : {res['ortak_bar']}")
    print(f"Pencere        : {res['pencere']}")
    print(f"Getiri koresp. : {res['getiri_korelasyonu']:.4f}")
    print(f"Basis ortalama : {res['basis_ortalama']:+.2f} puan "
          f"(std {res['basis_std']:.2f})")
    print(f"Gunler arasi basis kaymasi: {res['basis_gun_ici_surukleme']:.2f} puan")
    print(f"ARTIK gurultu  : std {res['artik_std_puan']:.2f} puan, "
          f"p95 {res['artik_p95_puan']:.2f} puan")
    if res.get("medyan_stop_puan"):
        print(f"Medyan stop    : {res['medyan_stop_puan']:.1f} puan (defterden)")
        print(f"=> ARTIK std   : {res['artik_std_R']:.3f} R")
        print(f"=> ARTIK p95   : {res['artik_p95_R']:.3f} R")


if __name__ == "__main__":
    main()
