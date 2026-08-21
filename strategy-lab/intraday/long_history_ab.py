"""Canli modulleri UZUN gecmiste yeniden kos -- yeni arama YOK.

SORU: bugunku kanit 3 yillik pencereden geliyor. Bu edge hep var miydi, yoksa
son uc yilin rejimine mi ozgu? Challenge parasi bu varsayima yatiriliyor.

NE YAPAR: modullerin AYNI konfigini 2012'den bugune kosar, yil yil doker.
NE YAPMAZ: parametre taramaz, konfig secmez, "daha iyisini" aramaz. Sifir
yeni hipotez -- yani `search_budget` anlaminda butce YEMEZ.

Dedektorler `forward_ea/modules.py`'deki canli tanimlarin vektorel aynasidir.
Ayna dogru mu? `test_long_history_ab.py` bunu ayni pencerede mevcut sonucu
yeniden uretterek dogrular; tutmazsa olculen sey canli modul degildir.

Calistir:
    python -m intraday.long_history_ab
    python -m intraday.long_history_ab --modules SWEEP_CORE NQ_ORB
"""
from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import pandas as pd

from .config import ATR_LEN, INSTRUMENTS
from .edge_lab import _adx
from .history_fetch import load_history
from .honest_engine import simulate_trades
from .indicators import atr
from .internet_seed_strategies import LondonCase, ORBCase, _build_london, _build_orb
from .overfit_stats import sharpe
from .search_budget import trial_budget

OUT = Path(__file__).resolve().parent.parent / "outputs" / "intraday"


@dataclass(frozen=True)
class ModuleSpec:
    name: str
    symbol: str
    tf: str
    build: Callable[[pd.DataFrame], tuple]
    min_rr: float
    max_rr: float
    max_hold: int
    adaptive_rr: bool = False


def _atr_rank(df: pd.DataFrame) -> pd.Series:
    return (atr(df, ATR_LEN) / df["close"]).rolling(500, min_periods=100).rank(pct=True)


def _sweep_build(df: pd.DataFrame) -> tuple:
    """SWEEP_CORE: ADX>25 likidite sweep, Carsamba haric (canli ile ayni)."""
    from .adx_lab import _make_signals

    le, se, lsl, ltp, ssl, stp, _ = _make_signals(df, 25.0)
    carsamba = pd.Series(df.index.dayofweek == 2, index=df.index)
    return le & ~carsamba, se & ~carsamba, lsl, ltp, ssl, stp


_NQ_ORB = ORBCase("NASDAQ100", 14.5, 15, 20.5, "retest", "none", 1.5, "other_side", 1.0, 48)
_GOLD_ORB = ORBCase("XAUUSD", 13.5, 60, 21.0, "retest", "vwap", 1.0, "other_side", 1.0, 48)
_EUR_LONDON = LondonCase("EURUSD", 2.0, 7.0, 11.0, "none", 1.5, "other_side", 1.0, 48)
_GBP_LONDON = LondonCase("GBPUSD", 0.0, 7.0, 11.0, "ema", 1.5, "other_side", 1.0, 48)


def _orb_build(case: ORBCase, adx_min: float = 0.0, atr_max_rank: float = 1.0):
    def build(df: pd.DataFrame) -> tuple:
        le, se, lsl, ltp, ssl, stp = _build_orb(df, case)
        ok = pd.Series(True, index=df.index)
        if adx_min > 0:
            ok &= _adx(df, 14) > adx_min
        if atr_max_rank < 1.0:
            ok &= _atr_rank(df) <= atr_max_rank
        return le & ok, se & ok, lsl, ltp, ssl, stp
    return build


def _london_build(case: LondonCase, adx_min: float = 0.0, adx_max: float = 0.0,
                  range_regime: str | None = None):
    def build(df: pd.DataFrame) -> tuple:
        le, se, lsl, ltp, ssl, stp = _build_london(df, case)
        ok = pd.Series(True, index=df.index)
        adx = _adx(df, 14)
        if adx_min > 0:
            ok &= adx > adx_min
        if adx_max > 0:
            ok &= adx < adx_max
        if range_regime is not None:
            h = df.index.hour + df.index.minute / 60.0
            in_range = (h >= case.range_start) & (h < case.range_end)
            hi = df["high"].where(in_range).groupby(df.index.date).transform("max")
            lo = df["low"].where(in_range).groupby(df.index.date).transform("min")
            gunluk = ((hi - lo) / df["close"]).groupby(df.index.date).last()
            rank = gunluk.rolling(20, min_periods=10).rank(pct=True)
            rejim = pd.cut(rank, [-0.01, 0.33, 0.67, 1.01],
                           labels=["tight_range", "normal_range", "wide_range"])
            gunluk_ok = (rejim == range_regime)
            gun = pd.Series(df.index.date, index=df.index)
            ok &= gun.map(gunluk_ok).fillna(False).astype(bool)
        return le & ok, se & ok, lsl, ltp, ssl, stp
    return build


SPECS: list[ModuleSpec] = [
    ModuleSpec("SWEEP_CORE", "NASDAQ100", "15m", _sweep_build, 2.0, 8.0, 480,
               adaptive_rr=True),
    ModuleSpec("NQ_ORB", "NASDAQ100", "5m", _orb_build(_NQ_ORB, adx_min=28.0),
               1.49, 1.5, 48),
    ModuleSpec("GOLD_ORB", "XAUUSD", "5m",
               _orb_build(_GOLD_ORB, adx_min=20.0, atr_max_rank=0.67), 0.99, 1.0, 48),
    ModuleSpec("EUR_LONDON", "EURUSD", "5m",
               _london_build(_EUR_LONDON, adx_max=18.0), 1.49, 1.5, 48),
    ModuleSpec("GBP_LONDON", "GBPUSD", "5m",
               _london_build(_GBP_LONDON, range_regime="normal_range"), 1.49, 1.5, 48),
]


def spec_by_name(name: str) -> ModuleSpec:
    for s in SPECS:
        if s.name == name:
            return s
    raise KeyError(name)


def run_spec(spec: ModuleSpec, df: pd.DataFrame) -> pd.Series:
    """Bir modulu verilen gecmiste kos, (zaman -> R) dondur."""
    le, se, lsl, ltp, ssl, stp = spec.build(df)
    inst = INSTRUMENTS[spec.symbol]
    if not spec.adaptive_rr:
        return simulate_trades(df, le, se, lsl, ltp, ssl, stp, inst,
                               min_rr=spec.min_rr, max_rr=spec.max_rr,
                               max_hold=spec.max_hold)
    # SWEEP: TP capi ATR rejimine gore degisir (canli dedektorle ayni)
    rank = _atr_rank(df)
    parcalar = []
    for mask, max_rr in ((rank < 0.33, 4.0),
                         ((rank >= 0.33) & (rank < 0.67), 6.0),
                         (rank >= 0.67, 8.0)):
        r = simulate_trades(df, le & mask, se & mask, lsl, ltp, ssl, stp, inst,
                            min_rr=spec.min_rr, max_rr=max_rr,
                            max_hold=spec.max_hold)
        if len(r):
            parcalar.append(r)
    return pd.concat(parcalar).sort_index() if parcalar else pd.Series(dtype=float)


def yearly(r: pd.Series) -> pd.DataFrame:
    if not len(r):
        return pd.DataFrame()
    d = pd.DataFrame({"r": r.values}, index=pd.to_datetime(r.index))
    g = d.groupby(d.index.year)["r"]
    return pd.DataFrame({"islem": g.size(), "toplam_R": g.sum(), "exp_R": g.mean()})


def summarize(r: pd.Series) -> dict:
    if not len(r):
        return {"islem": 0, "toplam_R": 0.0, "exp_R": float("nan"),
                "haftalik_SR": float("nan"), "aktif_hafta": 0, "butce": 0}
    wk = r.resample("W").sum()
    wk = wk[wk != 0]
    sr = sharpe(wk) if len(wk) > 1 else float("nan")
    return {"islem": len(r), "toplam_R": float(r.sum()), "exp_R": float(r.mean()),
            "haftalik_SR": sr, "aktif_hafta": len(wk),
            "butce": trial_budget(sr, len(wk)) if sr == sr and sr > 0 else 0}


def main() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    p = argparse.ArgumentParser()
    p.add_argument("--modules", nargs="+", default=None)
    p.add_argument("--from-year", type=int, default=2012)
    a = p.parse_args()

    secili = [s for s in SPECS if a.modules is None or s.name in a.modules]
    satirlar = []
    for spec in secili:
        try:
            df = load_history(spec.symbol, spec.tf, start_year=a.from_year)
        except FileNotFoundError as e:
            print("\n[{}] veri yok: {}".format(spec.name, e))
            continue
        print("\n" + "=" * 74)
        print("  {}  ({} {}, {:,} bar, {} -> {})".format(
            spec.name, spec.symbol, spec.tf, len(df),
            df.index[0].date(), df.index[-1].date()))
        print("=" * 74)
        r = run_spec(spec, df)
        yil = yearly(r)
        if yil.empty:
            print("  hic islem yok")
            continue
        print(yil.to_string(float_format=lambda x: "{:+.2f}".format(x)))
        ozet = summarize(r)
        pozitif = int((yil["toplam_R"] > 0).sum())
        print("\n  TOPLAM: {} islem  {:+.1f}R  exp_R={:+.3f}  haftalik SR={:+.3f}".format(
            ozet["islem"], ozet["toplam_R"], ozet["exp_R"], ozet["haftalik_SR"]))
        print("  Pozitif yil: {}/{}   deneme butcesi: {:,}".format(
            pozitif, len(yil), ozet["butce"]))
        satirlar.append(dict(modul=spec.name, **ozet, pozitif_yil=pozitif,
                             yil_sayisi=len(yil)))

    if satirlar:
        out = OUT / "long_history_ab.csv"
        pd.DataFrame(satirlar).to_csv(out, index=False)
        print("\nOzet: {}".format(out))


if __name__ == "__main__":
    main()
