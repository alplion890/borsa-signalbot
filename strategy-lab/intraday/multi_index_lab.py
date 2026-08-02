"""Kanitli modulleri TUM ABD endekslerine yay -- veri hizini 4x'e cikar.

Amac
----
Yeni edge ARAMAK DEGIL. NQ_ORB ve SWEEP_CORE config'lerini HIC DEGISTIRMEDEN
4 ABD endeksinde kosturmak. Iki kazanc:
  1. Yapisal tez ("ORB/sweep endeks CFD'lerinde calisir") bagimsiz sinanir.
  2. Gecerse canli veri hizi ~4x olur -> "NQ oldu mu" sorusu 12 hafta yerine
     ~3 haftada cevaplanir.

Disiplin (p-hacking'i onleyen kurallar)
--------------------------------------
1. Config SABIT. Sembol basina hicbir parametre ayarlanmaz.
2. Semboller ONCEDEN taahhut edilir (US100/US500/US30/US2000), hepsi raporlanir.
3. Karar HAVUZLANMIS sonuca gore -- en iyi sembol SECILMEZ.
4. Maliyet MT5'ten OLCULUR, tahmin edilmez.
5. DSR basilir (en iyiyi secme durtusune karsi).

Veri
----
MT5'ten M5, ~6 ay (broker gecmisi bu kadar). Dukascopy 3 yillik setinden KISA --
tek basina kanit degil, forward testle birleserek anlam kazanir.

Calistirma:
    python -m intraday.multi_index_lab
"""
from __future__ import annotations

import sys
import time
import warnings
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from .config import Instrument
from .edge_lab import _adx
from .honest_engine import metrics, simulate_trades
from .internet_seed_strategies import ORBCase, _build_orb
from .overfit_stats import deflated_from_trials, probabilistic_sharpe_ratio, sharpe

# Onceden taahhut edilen sembol listesi -- sonradan eklenmeyecek/cikarilmayacak
SYMBOLS = ["US100", "US500", "US30", "US2000"]
DAYS = 180
ADX_MIN = 30.0

# NQ_ORB kanitli config -- sembol basina DEGISTIRILMEZ
ORB_KW = dict(open_hour=14.5, range_minutes=15, trade_end_hour=20.5,
              entry_mode="retest", trend_filter="none", rr=1.5,
              sl_mode="other_side", atr_mult=1.0, max_hold=48)
SWEEP_ADX = 25.0
SWEEP_MIN_RR = 2.0
OUT = Path(__file__).resolve().parents[1] / "outputs" / "intraday"


def fetch(symbols: list[str], days: int = DAYS) -> tuple[dict, dict]:
    """MT5'ten M5 bar + gercek spread. Maliyet olculur, tahmin edilmez."""
    import MetaTrader5 as mt5

    if not mt5.initialize():
        raise RuntimeError(f"MT5 baglanamadi: {mt5.last_error()} -- terminali ac.")
    frames, costs = {}, {}
    end = datetime.now()
    try:
        for s in symbols:
            if not mt5.symbol_select(s, True):
                print(f"  [ATLA] {s}: sembol secilemedi")
                continue
            time.sleep(0.4)
            rates = mt5.copy_rates_range(s, mt5.TIMEFRAME_M5, end - timedelta(days=days), end)
            if rates is None or len(rates) == 0:
                print(f"  [ATLA] {s}: bar verisi gelmedi")
                continue
            df = pd.DataFrame(rates)
            df["timestamp"] = pd.to_datetime(df["time"], unit="s")
            df = df.set_index("timestamp").rename(columns={"tick_volume": "volume"})
            frames[s] = df[["open", "high", "low", "close", "volume"]].astype(float).sort_index()

            info = mt5.symbol_info(s)
            px = float(df["close"].iloc[-1])
            # spread puan cinsinden -> fiyata orani; tek yon = yarisi
            spread_abs = info.spread * info.point
            costs[s] = float(spread_abs / px / 2.0) if px > 0 else 9e-05
            print(f"  {s:8} {len(df):>6} bar  {df.index.min().date()} -> {df.index.max().date()}"
                  f"  spread={spread_abs:.2f} ({spread_abs/px*1e4:.2f} bps)  cost/side={costs[s]:.2e}")
    finally:
        mt5.shutdown()
    return frames, costs


def _instrument(sym: str, cost: float, px: float) -> Instrument:
    return Instrument(key=sym, duka="", cost_per_side=cost,
                      session_utc=(13, 21), pip=max(px * 1e-5, 1e-6))


def run_orb(df: pd.DataFrame, inst: Instrument) -> pd.Series:
    case = ORBCase(inst.key, **ORB_KW)
    le, se, lsl, ltp, ssl, stp = _build_orb(df, case)
    ok = _adx(df, 14) > ADX_MIN
    return simulate_trades(df, le & ok, se & ok, lsl, ltp, ssl, stp, inst,
                           min_rr=0.5, max_rr=10.0, max_hold=ORB_KW["max_hold"])


def to_15m(df: pd.DataFrame) -> pd.DataFrame:
    """SWEEP_CORE canlida 15m calisir (LiveModule tf='15m'). 5m -> 15m resample."""
    o = df.resample("15min").agg({"open": "first", "high": "max", "low": "min",
                                  "close": "last", "volume": "sum"})
    return o.dropna()


def run_sweep(df5: pd.DataFrame, inst: Instrument) -> pd.Series:
    """SWEEP_CORE'un canli dedektoruyle ayni mantik, vektorize backtest hali.

    DIKKAT: canli modul 15m TF ve max_hold=480 bar kullanir. 5m'de kosturmak
    tamamen farkli (cok daha gurultulu) bir strateji olur -- bu hata bir kez
    yapildi ve sonuclari gecersiz kildi.
    """
    from .adx_lab import _make_signals

    df = to_15m(df5)
    le, se, lsl, ltp, ssl, stp, a = _make_signals(df, SWEEP_ADX)
    # Carsamba kapali (quality_11 kurali)
    not_wed = pd.Series(df.index.dayofweek != 2, index=df.index)
    le, se = le & not_wed, se & not_wed

    entry = df["close"]
    atr_rank = (a / df["close"]).rolling(500, min_periods=100).rank(pct=True)
    max_rr = pd.Series(np.where(atr_rank < 0.33, 4.0,
                       np.where(atr_rank < 0.67, 6.0, 8.0)), index=df.index)

    lr, sr = entry - lsl, ssl - entry
    lrr, srr = (ltp - entry) / lr.replace(0, np.nan), (entry - stp) / sr.replace(0, np.nan)
    le = le & (lr > 0) & (lrr >= SWEEP_MIN_RR) & atr_rank.notna()
    se = se & (sr > 0) & (srr >= SWEEP_MIN_RR) & atr_rank.notna()
    ltp2 = entry + np.minimum(lrr, max_rr) * lr
    stp2 = entry - np.minimum(srr, max_rr) * sr
    return simulate_trades(df, le, se, lsl, ltp2, ssl, stp2, inst,
                           min_rr=SWEEP_MIN_RR, max_rr=8.0, max_hold=480)


def _report(title: str, res: dict[str, pd.Series]) -> dict:
    print(f"\n--- {title}")
    print(f"{'sembol':<10}{'islem':>7}{'exp_R':>9}{'win%':>7}{'PF':>7}{'SR':>9}{'top_R':>9}")
    for s, r in res.items():
        m = metrics(r)
        print(f"{s:<10}{m['trades']:>7}{m['exp_r']:>9.3f}{m['win_rate']:>7.1f}"
              f"{m['pf']:>7.2f}{sharpe(r) if len(r) > 2 else np.nan:>9.3f}{r.sum():>9.1f}")
    pooled = pd.concat([r for r in res.values() if len(r)]).sort_index()
    pm = metrics(pooled)
    psr = probabilistic_sharpe_ratio(pooled)
    print(f"{'HAVUZ':<10}{pm['trades']:>7}{pm['exp_r']:>9.3f}{pm['win_rate']:>7.1f}"
          f"{pm['pf']:>7.2f}{sharpe(pooled):>9.3f}{pooled.sum():>9.1f}   PSR={psr:.3f}")
    out = deflated_from_trials(res)
    print(f"  en iyiyi secme denetimi: best={out['best']} sans_esigi={out['sr_threshold']:.4f} "
          f"DSR={out['dsr']:.4f}")
    return {"strateji": title, "islem": pm["trades"], "exp_r": pm["exp_r"],
            "win_rate": pm["win_rate"], "pf": pm["pf"], "psr": round(psr, 4)
            if psr == psr else None, "dsr_best": out["dsr"]}


def run() -> None:
    print("=== MT5'ten veri + gercek spread")
    frames, costs = fetch(SYMBOLS)
    if not frames:
        print("Hic veri gelmedi. MT5 terminali acik mi?")
        return

    orb, sweep, rows = {}, {}, []
    for s, df in frames.items():
        inst = _instrument(s, costs[s], float(df["close"].iloc[-1]))
        try:
            orb[s] = run_orb(df, inst)
        except Exception as exc:
            print(f"  [ORB atlandi] {s}: {type(exc).__name__}: {exc}")
        try:
            sweep[s] = run_sweep(df, inst)
        except Exception as exc:
            print(f"  [SWEEP atlandi] {s}: {type(exc).__name__}: {exc}")

    print(f"\n{'='*74}")
    print(f"SABIT CONFIG, 4 ABD ENDEKSI, ~{DAYS} gun M5  (ADX>{ADX_MIN})")
    print("="*74)
    if orb:
        rows.append(_report("ORB (NQ config'i birebir)", orb))
    if sweep:
        rows.append(_report("SWEEP_CORE (canli dedektorle ayni mantik)", sweep))

    print("\n--- KARAR KURALI (onceden yazildi)")
    print("  HAVUZ exp_R > 0 ve PSR >= 0.80  -> aday olarak canliya ekle")
    print("  aksi halde                       -> aile kapanir, eklenmez")
    for r in rows:
        ok = r["exp_r"] > 0 and (r["psr"] or 0) >= 0.80
        print(f"  {r['strateji'][:34]:<36} exp_R={r['exp_r']:+.3f} PSR={r['psr']} "
              f"-> {'EKLE' if ok else 'EKLEME'}")

    dest = OUT / "multi_index_lab.csv"
    pd.DataFrame(rows).to_csv(dest, index=False)
    print(f"\nCikti: {dest}")


if __name__ == "__main__":
    run()
