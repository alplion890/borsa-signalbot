"""Edge Lab: 15m VWAP+sweep stratejisi icin 3 katmanli analiz.

1) Monte Carlo: trade siralamasini bootstrap'la rastgele dizi -> prop firm pas
   dagilimi, max DD dagilimi, 5%/gun risk olcumu.
2) Regime Clustering: K-means ile piyasa rejimleri (vol, trend, vwap uzakligi,
   saat) -> her rejimde beklenti -> en iyi rejim filtresi.
3) Meta-labeling: RandomForest + purged walk-forward CV -> trade-bazli "kazanma
   olasiligi" -> esik filtresiyle expectancy artisi.

Kullanim:
    python -m intraday.edge_lab
    python -m intraday.edge_lab --mc_runs 5000 --k 4
"""
from __future__ import annotations

import argparse
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
from .indicators import atr, swing_high, swing_low, rolling_high, rolling_low
from .honest_engine import simulate_trades, metrics
try:
    from .walkforward import _folds
except ModuleNotFoundError:
    _folds = None


# ---------------------------------------------------------------------------
# 0) Trade ledger uretimi (15m NASDAQ100 VWAP+sweep)
# ---------------------------------------------------------------------------

def _vwap_trend(df: pd.DataFrame) -> pd.Series:
    c = df["close"]
    hlc3 = (df["high"] + df["low"] + c) / 3
    vol = df["volume"].clip(lower=1e-9) if "volume" in df.columns and df["volume"].sum() > 0 \
        else pd.Series(1.0, index=df.index)
    day = pd.Index(df.index.date)
    vwap = (hlc3 * vol).groupby(day).cumsum() / vol.groupby(day).cumsum()
    vwap_prev = vwap.shift(1)
    t = pd.Series(0, index=df.index, dtype=int)
    t[c > vwap_prev] = 1
    t[c < vwap_prev] = -1
    return t, vwap_prev


def _adx(df: pd.DataFrame, n: int = 14) -> pd.Series:
    h, l, c = df["high"], df["low"], df["close"]
    pc = c.shift(1)
    tr = pd.concat([h - l, (h - pc).abs(), (l - pc).abs()], axis=1).max(axis=1)
    dm_p = (h - h.shift(1)).clip(lower=0).where((h - h.shift(1)) > (l.shift(1) - l), 0)
    dm_m = (l.shift(1) - l).clip(lower=0).where((l.shift(1) - l) > (h - h.shift(1)), 0)
    atr_n = tr.ewm(alpha=1/n, adjust=False).mean()
    di_p = 100 * dm_p.ewm(alpha=1/n, adjust=False).mean() / atr_n.replace(0, np.nan)
    di_m = 100 * dm_m.ewm(alpha=1/n, adjust=False).mean() / atr_n.replace(0, np.nan)
    dx = 100 * (di_p - di_m).abs() / (di_p + di_m).replace(0, np.nan)
    return dx.ewm(alpha=1/n, adjust=False).mean().shift(1)


def build_ledger(symbol: str = "NASDAQ100", min_rr: float = 2.5) -> pd.DataFrame:
    print(f"  Veri yukleniyor: {symbol} 15m...")
    df = data.load_ohlcv(symbol, "15m", 1080)
    print(f"  {len(df)} bar | {df.index[0].date()} - {df.index[-1].date()}")

    trend, vwap_prev = _vwap_trend(df)
    a = atr(df, ATR_LEN)
    buf = a * SL_ATR_BUFFER
    rlo = rolling_low(df, 20)
    rhi = rolling_high(df, 20)
    sh = swing_high(df)
    sl_ = swing_low(df)

    long_raw  = (df["low"] < rlo) & (df["close"] > rlo) & (trend > 0)
    short_raw = (df["high"] > rhi) & (df["close"] < rhi) & (trend < 0)
    le = long_raw  & ~long_raw.shift(1).fillna(False)
    se = short_raw & ~short_raw.shift(1).fillna(False)

    inst = INSTRUMENTS[symbol]
    r = simulate_trades(
        df, le, se,
        df["low"].where(le) - buf.where(le),
        sh.where(le),
        df["high"].where(se) + buf.where(se),
        sl_.where(se),
        inst, min_rr=min_rr,
    )

    # Trade-bazli ozellikler (entry barinda hesaplananlar -> look-ahead yok)
    adx14 = _adx(df, 14)
    atr_pct = (a / df["close"]) * 100
    vwap_dist = (df["close"] - vwap_prev) / a   # ATR-normalize
    range_pos = (df["close"] - rlo) / (rhi - rlo).replace(0, np.nan)
    hour = df.index.hour
    dow = df.index.dayofweek

    ledger = pd.DataFrame(index=r.index)
    ledger["r"] = r
    ledger["dir"] = np.where(le.reindex(r.index).fillna(False), 1, -1)
    ledger["atr_pct"]   = atr_pct.reindex(r.index)
    ledger["adx"]       = adx14.reindex(r.index)
    ledger["vwap_dist"] = vwap_dist.reindex(r.index).abs()
    ledger["range_pos"] = range_pos.reindex(r.index)
    ledger["hour"]      = hour[df.index.isin(r.index)]
    ledger["dow"]       = dow[df.index.isin(r.index)]
    return ledger.dropna()


# ---------------------------------------------------------------------------
# 1) Monte Carlo prop firm simulasyonu
# ---------------------------------------------------------------------------

def monte_carlo(r: pd.Series, runs: int = 5000, risk_pct: float = 0.01,
                target: float = 0.10, daily_dd: float = 0.05,
                total_dd: float = 0.10, days: int = 30,
                trades_per_day: float = 0.12) -> dict:
    """Bootstrap trade siralarini -> 30g prop firm pas/yanma istatistigi.

    trades_per_day: gunluk ortalama trade (0.62/hafta = 0.124/gun)
    """
    arr = r.to_numpy()
    n_trades = int(np.ceil(days * trades_per_day)) + 2
    rng = np.random.default_rng(42)

    results = {"pass": 0, "target_hit": 0, "daily_dd_hit": 0,
               "total_dd_hit": 0, "time_out": 0}
    final_eqs = []
    max_dds = []

    for _ in range(runs):
        # Bootstrap with replacement: ne sira sansi ne tekrar yanlilik
        sample = rng.choice(arr, size=n_trades, replace=True)
        # Trade'leri gunlere yay (Poisson varsayim: ortalama trades_per_day)
        eq = 1.0
        peak = 1.0
        max_dd = 0.0
        day_start_eq = 1.0
        t_count = 0
        outcome = None

        # Her trade'i tek tek isle, gunluk DD'yi her ~1/trades_per_day trade'de sifirla
        trades_per_day_int = max(1, int(round(1 / trades_per_day)))
        for k, ri in enumerate(sample):
            # Yeni gun mu?
            if k % trades_per_day_int == 0:
                day_start_eq = eq

            eq *= (1 + ri * risk_pct)
            peak = max(peak, eq)
            dd = (peak - eq) / peak
            max_dd = max(max_dd, dd)

            # Gun ici DD kontrolu
            day_dd = (day_start_eq - eq) / day_start_eq
            if day_dd >= daily_dd:
                outcome = "daily_dd_hit"; break
            if dd >= total_dd:
                outcome = "total_dd_hit"; break
            if eq >= 1 + target:
                outcome = "target_hit"; break

        if outcome is None:
            outcome = "time_out"

        results[outcome] = results.get(outcome, 0) + 1
        if outcome == "target_hit":
            results["pass"] += 1
        final_eqs.append(eq)
        max_dds.append(max_dd)

    n = runs
    return {
        "runs": runs,
        "pass_rate": results["pass"] / n,
        "target_hit": results["target_hit"] / n,
        "daily_dd_hit": results["daily_dd_hit"] / n,
        "total_dd_hit": results["total_dd_hit"] / n,
        "time_out": results["time_out"] / n,
        "median_final_eq": float(np.median(final_eqs)),
        "p10_final_eq": float(np.percentile(final_eqs, 10)),
        "p90_final_eq": float(np.percentile(final_eqs, 90)),
        "median_max_dd": float(np.median(max_dds)),
        "p90_max_dd": float(np.percentile(max_dds, 90)),
    }


# ---------------------------------------------------------------------------
# 2) Regime clustering
# ---------------------------------------------------------------------------

def cluster_regimes(ledger: pd.DataFrame, k: int = 4) -> pd.DataFrame:
    from sklearn.cluster import KMeans
    from sklearn.preprocessing import StandardScaler

    feats = ledger[["atr_pct", "adx", "vwap_dist", "range_pos", "hour"]].copy()
    feats = feats.replace([np.inf, -np.inf], np.nan).dropna()

    scaler = StandardScaler()
    X = scaler.fit_transform(feats)
    km = KMeans(n_clusters=k, random_state=42, n_init=10)
    labels = km.fit_predict(X)

    df = ledger.loc[feats.index].copy()
    df["cluster"] = labels

    summary = df.groupby("cluster").agg(
        trades=("r", "count"),
        exp_r=("r", "mean"),
        win_rate=("r", lambda s: (s > 0).mean() * 100),
        total_R=("r", "sum"),
        avg_atr=("atr_pct", "mean"),
        avg_adx=("adx", "mean"),
        avg_vwap=("vwap_dist", "mean"),
        avg_hour=("hour", "mean"),
    ).round(3).sort_values("exp_r", ascending=False)
    return summary, df


# ---------------------------------------------------------------------------
# 3) Meta-labeling: RandomForest + purged walk-forward
# ---------------------------------------------------------------------------

def meta_label_wf(ledger: pd.DataFrame, n_folds: int = 5, embargo: int = 5,
                  threshold: float = 0.55) -> dict:
    from sklearn.ensemble import RandomForestClassifier

    feat_cols = ["dir", "atr_pct", "adx", "vwap_dist", "range_pos", "hour", "dow"]
    df = ledger[feat_cols + ["r"]].dropna().copy()
    df["y"] = (df["r"] > 0).astype(int)

    n = len(df)
    fold_size = n // n_folds
    oos_preds = pd.Series(index=df.index, dtype=float)

    for f in range(n_folds):
        te_start = f * fold_size
        te_end = (f + 1) * fold_size if f < n_folds - 1 else n
        test_idx = df.index[te_start:te_end]

        # Embargo: test civarindaki egitim trade'lerini cikar
        tr_idx_lo = df.index[:max(0, te_start - embargo)]
        tr_idx_hi = df.index[min(n, te_end + embargo):]
        train_idx = tr_idx_lo.union(tr_idx_hi)

        if len(train_idx) < 30 or len(test_idx) < 5:
            continue

        Xtr = df.loc[train_idx, feat_cols]
        ytr = df.loc[train_idx, "y"]
        Xte = df.loc[test_idx, feat_cols]

        if ytr.nunique() < 2:
            continue

        clf = RandomForestClassifier(n_estimators=200, max_depth=4,
                                      min_samples_leaf=10, random_state=42,
                                      n_jobs=-1)
        clf.fit(Xtr, ytr)
        proba = clf.predict_proba(Xte)[:, 1]
        oos_preds.loc[test_idx] = proba

    valid = oos_preds.dropna()
    df_v = df.loc[valid.index].copy()
    df_v["p_win"] = valid

    # Threshold sweep
    thresholds = [0.40, 0.45, 0.50, 0.52, 0.55, 0.58, 0.60, 0.65]
    sweep = []
    for th in thresholds:
        sel = df_v[df_v["p_win"] >= th]
        if len(sel) == 0:
            sweep.append({"th": th, "trades": 0, "exp_r": np.nan,
                          "win_rate": np.nan, "total_R": 0})
            continue
        sweep.append({
            "th": th,
            "trades": len(sel),
            "exp_r": round(float(sel["r"].mean()), 3),
            "win_rate": round(float((sel["r"] > 0).mean() * 100), 1),
            "total_R": round(float(sel["r"].sum()), 1),
        })
    return {"sweep": pd.DataFrame(sweep), "predictions": df_v}


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol", default="NASDAQ100")
    parser.add_argument("--min_rr", type=float, default=2.5)
    parser.add_argument("--mc_runs", type=int, default=5000)
    parser.add_argument("--k", type=int, default=4)
    args = parser.parse_args()

    print(f"\n{'='*68}")
    print(f"  EDGE LAB | {args.symbol} 15m VWAP+sweep | min_rr={args.min_rr}")
    print(f"{'='*68}")

    # --- 0) Ledger ---
    ledger = build_ledger(args.symbol, args.min_rr)
    r = ledger["r"]
    m = metrics(r)
    weeks = (ledger.index[-1] - ledger.index[0]).days / 7
    print(f"\n  Baz strateji: {m['trades']} trade, exp={m['exp_r']:+.3f}R, "
          f"WR={m['win_rate']}%, PF={m['pf']}, {m['trades']/weeks:.2f} is/hafta")

    # --- 1) Monte Carlo ---
    print(f"\n{'-'*68}\n  [1] MONTE CARLO ({args.mc_runs} bootstrap, 30 gun, 1% risk)\n{'-'*68}")
    for risk in [0.01, 0.015, 0.02]:
        mc = monte_carlo(r, runs=args.mc_runs, risk_pct=risk,
                          trades_per_day=m["trades"] / (weeks * 5))
        print(f"\n  risk={risk*100:.1f}% -> pas={mc['pass_rate']*100:5.1f}%  "
              f"target_hit={mc['target_hit']*100:5.1f}%  "
              f"daily_dd_yan={mc['daily_dd_hit']*100:5.1f}%  "
              f"total_dd_yan={mc['total_dd_hit']*100:5.1f}%  "
              f"zaman_doldu={mc['time_out']*100:5.1f}%")
        print(f"           medyan_final_eq={mc['median_final_eq']:.3f}  "
              f"p10={mc['p10_final_eq']:.3f}  p90={mc['p90_final_eq']:.3f}  "
              f"medyan_max_dd={mc['median_max_dd']*100:.2f}%  "
              f"p90_max_dd={mc['p90_max_dd']*100:.2f}%")

    # --- 2) Clustering ---
    print(f"\n{'-'*68}\n  [2] REGIME CLUSTERING (K={args.k})\n{'-'*68}")
    summary, df_cl = cluster_regimes(ledger, k=args.k)
    print(summary.to_string())

    best = summary.iloc[0]
    worst = summary.iloc[-1]
    print(f"\n  En iyi rejim (cluster {summary.index[0]}): exp={best['exp_r']:+.3f}R, "
          f"{int(best['trades'])} trade")
    print(f"  En kotu rejim (cluster {summary.index[-1]}): exp={worst['exp_r']:+.3f}R, "
          f"{int(worst['trades'])} trade")
    # Pozitif rejimleri birlestirip filtreli expectancy
    pos_clusters = summary[summary["exp_r"] > 0].index.tolist()
    if pos_clusters:
        sel = df_cl[df_cl["cluster"].isin(pos_clusters)]
        print(f"\n  POZITIF rejim filtresi (cluster {pos_clusters}): "
              f"{len(sel)} trade, exp={sel['r'].mean():+.3f}R, "
              f"toplam={sel['r'].sum():.1f}R")

    # --- 3) Meta-labeling ---
    print(f"\n{'-'*68}\n  [3] META-LABELING (RandomForest + purged 5-fold)\n{'-'*68}")
    meta = meta_label_wf(ledger, n_folds=5, embargo=5)
    sw = meta["sweep"]
    print(sw.to_string(index=False))

    # En iyi threshold
    valid_sw = sw[sw["trades"] >= 20]
    if not valid_sw.empty:
        best_th = valid_sw.loc[valid_sw["exp_r"].idxmax()]
        print(f"\n  En iyi esik: {best_th['th']:.2f} -> "
              f"{int(best_th['trades'])} trade, exp={best_th['exp_r']:+.3f}R, "
              f"WR={best_th['win_rate']}%, toplam={best_th['total_R']}R")
        print(f"  Baz expectancy:      {m['exp_r']:+.3f}R")
        print(f"  Meta-label expectancy: {best_th['exp_r']:+.3f}R  "
              f"(degisim: {(best_th['exp_r'] - m['exp_r']):+.3f}R)")

    print(f"\n{'='*68}\n  TAMAM\n{'='*68}\n")


if __name__ == "__main__":
    main()
