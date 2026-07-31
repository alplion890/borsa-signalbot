"""NQ_ORB mantigi baska sembollerde de tutuyor mu? (genellenebilirlik testi)

Amac
----
Yeni edge ARAMAK DEGIL. Kanitli NQ_ORB config'ini HIC DEGISTIRMEDEN baska
sembollere uygulamak. Mantik gercekse endekslerde genel olarak calismali;
sadece US100'de calisiyorsa o bir tesaduf isareti.

Disiplin (p-hacking'i onleyen kural)
------------------------------------
1. Config SABIT: NASDAQ100 ORB open=14.5 range=15 retest none rr=1.5
   sl=other_side hold=48, ADX>30. Sembol basina HICBIR parametre ayarlanmaz.
2. TUM semboller onceden taahhut edilir ve HEPSI raporlanir.
3. Karar HAVUZLANMIS sonuca gore verilir, en iyi sembole gore DEGIL.
4. En iyiyi secme istegine karsi DSR basilir.

Sinif ayrimi
------------
BIRINCIL  : SP500  -- US100 ile ayni seans, ayni varlik sinifi. Asil test bu.
KESIFSEL  : XAUUSD/XAGUSD/EURUSD/GBPUSD -- 14.5 NY acilisi bunlar icin de
            gercek bir olay ama modul endeks icin tasarlandi. Sonuclari
            "kanit" degil "baglam" olarak oku.
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

from pathlib import Path

from . import data
from .config import INSTRUMENTS
from .edge_lab import _adx
from .honest_engine import metrics, oos_metrics, simulate_trades
from .internet_seed_strategies import ORBCase, _build_orb
from .overfit_stats import deflated_from_trials, probabilistic_sharpe_ratio, sharpe

DAYS = 1080
ADX_MIN = 30.0
PRIMARY = ["NASDAQ100", "SP500"]
EXPLORATORY = ["XAUUSD", "XAGUSD", "EURUSD", "GBPUSD"]

# NQ_ORB kanitli config -- sembol basina DEGISTIRILMEZ
BASE = dict(open_hour=14.5, range_minutes=15, trade_end_hour=20.5,
            entry_mode="retest", trend_filter="none", rr=1.5,
            sl_mode="other_side", atr_mult=1.0, max_hold=48)


def make_folds(idx: pd.DatetimeIndex, n: int = 6):
    edges = pd.date_range(idx.min(), idx.max(), periods=n + 1)
    return [(edges[i], edges[i], edges[i], edges[i + 1]) for i in range(n)]


def run_symbol(symbol: str) -> tuple[dict, pd.Series]:
    df = data.load_ohlcv(symbol, "5m", DAYS)
    case = ORBCase(symbol, **BASE)
    le, se, lsl, ltp, ssl, stp = _build_orb(df, case)
    ok = _adx(df, 14) > ADX_MIN
    le, se = le & ok, se & ok
    r = simulate_trades(df, le, se, lsl, ltp, ssl, stp, INSTRUMENTS[symbol],
                        min_rr=0.5, max_rr=10.0, max_hold=BASE["max_hold"])
    m = metrics(r)
    if len(r):
        m.update(oos_metrics(r, make_folds(df.index)))
        years = r.groupby(r.index.year).mean()
        m["pos_years"] = f"{int((years > 0).sum())}/{len(years)}"
        m["min_year"] = round(float(years.min()), 3)
    m["sharpe"] = round(sharpe(r), 4) if len(r) > 2 else np.nan
    return {"symbol": symbol, **m}, r


def _print(rows: list[dict]) -> None:
    print(f"{'sembol':<12}{'islem':>7}{'exp_R':>8}{'win%':>7}{'PF':>7}"
          f"{'SR':>8}{'yil+':>7}{'minYil':>8}{'top_R':>8}")
    for m in rows:
        print(f"{m['symbol']:<12}{m['trades']:>7}{m['exp_r']:>8.3f}{m['win_rate']:>7.1f}"
              f"{m['pf']:>7.2f}{m.get('sharpe', np.nan):>8.3f}"
              f"{str(m.get('pos_years', '-')):>7}{m.get('min_year', np.nan):>8.3f}"
              f"{m.get('total_R', 0):>8.1f}")


def run() -> None:
    print(f"\n=== NQ_ORB config'i sabit, sembol degisiyor (ADX>{ADX_MIN}, 3 yil 5m)")
    print("    Config: ORB open=14.5 range=15 retest none rr=1.5 sl=other_side hold=48\n")

    prim_rows, prim_r = [], {}
    for s in PRIMARY:
        m, r = run_symbol(s)
        prim_rows.append(m)
        prim_r[s] = r

    print("BIRINCIL (endeks, ayni seans):")
    _print(prim_rows)

    exp_rows, exp_r = [], {}
    for s in EXPLORATORY:
        try:
            m, r = run_symbol(s)
            exp_rows.append(m)
            exp_r[s] = r
        except Exception as exc:
            print(f"  {s}: atlandi ({type(exc).__name__})")

    print("\nKESIFSEL (endeks disi -- kanit degil, baglam):")
    _print(exp_rows)

    # --- havuzlanmis karar (en iyiyi SECME) ---
    pooled = pd.concat(list(prim_r.values())).sort_index()
    pm = metrics(pooled)
    py = pooled.groupby(pooled.index.year).mean()
    print(f"\n--- HAVUZLANMIS BIRINCIL ({' + '.join(PRIMARY)}) ---")
    print(f"  islem={pm['trades']}  exp_R={pm['exp_r']:+.3f}  win={pm['win_rate']:.1f}%  "
          f"PF={pm['pf']:.2f}  SR={sharpe(pooled):+.4f}")
    print(f"  yil-yil pozitif: {int((py > 0).sum())}/{len(py)}   en kotu yil: {py.min():+.3f}")
    print(f"  PSR(SR>0): {probabilistic_sharpe_ratio(pooled):.3f}")

    all_tr = {**prim_r, **exp_r}
    out = deflated_from_trials(all_tr)
    print(f"\n--- en iyiyi secme durtusune karsi denetim ({out['n_trials']} sembol) ---")
    print(f"  en iyi sembol    : {out['best']}  (SR {out['sharpe']:+.4f})")
    print(f"  sans esigi E[max]: {out['sr_threshold']:.4f}")
    print(f"  DSR              : {out['dsr']:.4f}  "
          f"({'gecti' if out['dsr'] >= 0.95 else 'GECMEDI -- tek sembol secme'})")

    dest = Path(__file__).resolve().parents[1] / "outputs" / "intraday" / "orb_cross_symbol.csv"
    pd.DataFrame(prim_rows + exp_rows).to_csv(dest, index=False)
    print(f"\nCikti: {dest}")


if __name__ == "__main__":
    run()
