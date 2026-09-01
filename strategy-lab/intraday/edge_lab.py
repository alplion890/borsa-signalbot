"""Edge Lab v2 — 5-katman profesyonel kenar dogrulamasi.

1) [TASK-1] Monte Carlo: takvim-gunlu blok bootstrap (IID degil) -> vol
   clustering'i korur -> gercekci ardisik kayip -> gercek prop gecis orani.
2) [TASK-2] DSR/MinTRL: Opdyke SE + cok-test duzeltmeli Deflated Sharpe ->
   n_trials konfigurasyona karsi SR* benchmark -> GERCEK_KENAR mi GURULTU mu.
3) [TASK-3] Embargo: trade sayisi degil label-horizon bar * 15m (5 gun) bazli
   zaman damgasi purge -> meta-label sizintisini kapatir.
4) [TASK-4] Ic-CV rejim + holdout threshold: cluster ve threshold secimi OOS'u
   kirletmez; ayri holdout'ta raporlama.
5) [TASK-5] Genislik: tum enstirumanlarda edge_lab -> portfolyo DSR (sqrt-N).

Kullanim:
    python -m intraday.edge_lab
    python -m intraday.edge_lab --symbol EURUSD --k 4 --n_trials 50
    python -m intraday.edge_lab --breadth
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
from .indicators import adx as _adx
from .indicators import atr, swing_high, swing_low, rolling_high, rolling_low
from .honest_engine import simulate_trades, metrics
try:
    from .walkforward import _folds
except ModuleNotFoundError:
    _folds = None

# [TASK-3] Label horizon embargo: 480 bar * 15m = 7200 dk = ~5 is gunu
_EMBARGO_TD = pd.Timedelta(minutes=480 * 15)


# ---------------------------------------------------------------------------
# 0) Trade ledger uretimi
# ---------------------------------------------------------------------------

def _vwap_trend(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    c = df["close"]
    hlc3 = (df["high"] + df["low"] + c) / 3
    vol = (
        df["volume"].clip(lower=1e-9)
        if "volume" in df.columns and df["volume"].sum() > 0
        else pd.Series(1.0, index=df.index)
    )
    day = pd.Index(df.index.date)
    vwap = (hlc3 * vol).groupby(day).cumsum() / vol.groupby(day).cumsum()
    vwap_prev = vwap.shift(1)
    t = pd.Series(0, index=df.index, dtype=int)
    t[c > vwap_prev] = 1
    t[c < vwap_prev] = -1
    return t, vwap_prev


def build_ledger(symbol: str = "NASDAQ100", min_rr: float = 2.5) -> pd.DataFrame:
    print(f"  Veri yukleniyor: {symbol} 15m...")
    df = data.load_ohlcv(symbol, "15m", 1080)
    _required = {"open", "high", "low", "close"}
    missing = _required - set(df.columns)
    if missing:
        raise ValueError(f"build_ledger [{symbol}]: eksik kolonlar: {missing}")
    if len(df) < 100:
        raise ValueError(f"build_ledger [{symbol}]: yetersiz bar: {len(df)}")
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

    adx14 = _adx(df, 14)
    a_pct = (a / df["close"].replace(0, np.nan)) * 100
    vwap_dist = (df["close"] - vwap_prev) / a.replace(0, np.nan)
    range_pos = (df["close"] - rlo) / (rhi - rlo).replace(0, np.nan)
    hour = df.index.hour
    dow = df.index.dayofweek

    ledger = pd.DataFrame(index=r.index)
    ledger["r"]         = r
    ledger["dir"]       = np.where(le.reindex(r.index).fillna(False), 1, -1)
    ledger["atr_pct"]   = a_pct.reindex(r.index)
    ledger["adx"]       = adx14.reindex(r.index)
    ledger["vwap_dist"] = vwap_dist.reindex(r.index).abs()
    ledger["range_pos"] = range_pos.reindex(r.index)
    ledger["hour"]      = pd.Series(hour, index=df.index).reindex(r.index)
    ledger["dow"]       = pd.Series(dow, index=df.index).reindex(r.index)
    before = len(ledger)
    ledger = ledger.dropna()
    dropped = before - len(ledger)
    if dropped > 0:
        warnings.warn(f"build_ledger [{symbol}]: {dropped}/{before} satir NaN nedeniyle kaldirildi")
    return ledger


# ---------------------------------------------------------------------------
# [TASK-1] Monte Carlo — takvim-gunlu blok bootstrap
# ---------------------------------------------------------------------------

def _day_blocks(r: pd.Series) -> list[np.ndarray]:
    """R serisini takvim gunune gore bloklara ayir (block bootstrap icin).

    IID bootstrap yerine: ayni gune ait trade'ler ayni blokta tutuluyor.
    Vol clustering (ardisik kayiplar) dogal olarak korunur.
    """
    if not isinstance(r.index, pd.DatetimeIndex):
        return [r.to_numpy()]
    groups: dict = {}
    for ts, val in r.items():
        key = ts.date()
        groups.setdefault(key, []).append(float(val))
    return [np.array(v) for v in groups.values() if v]


def monte_carlo(
    r: pd.Series,
    runs: int = 5000,
    risk_pct: float = 0.01,
    target: float = 0.10,
    daily_dd: float = 0.05,
    total_dd: float = 0.10,
    days: int = 30,
    trades_per_day: float = 0.12,
) -> dict:
    """Takvim-gunlu blok bootstrap MC.

    Her run'da `days` adet rastgele gun-bloku resample edilir; DD takvim
    gunu basinda sifirlanir. IID'ye gore ardisik kayip senaryolari daha
    gercekci -> prop firm gecis orani daha muhafazakar.
    """
    blocks = _day_blocks(r)
    if not blocks:
        return {}
    n_blocks = len(blocks)
    rng = np.random.default_rng(42)

    results = {"pass": 0, "target_hit": 0, "daily_dd_hit": 0,
               "total_dd_hit": 0, "time_out": 0}
    final_eqs: list[float] = []
    max_dds: list[float] = []

    for _ in range(runs):
        block_idx = rng.integers(0, n_blocks, size=days)
        eq = 1.0
        peak = 1.0
        max_dd = 0.0
        outcome: str | None = None

        for bi in block_idx:
            day_open = eq
            for ri in blocks[bi]:
                eq *= 1.0 + ri * risk_pct
                peak = max(peak, eq)
                dd = (peak - eq) / peak
                max_dd = max(max_dd, dd)
                if daily_dd > 0 and day_open > 0:
                    if (day_open - eq) / day_open >= daily_dd:
                        outcome = "daily_dd_hit"
                        break
                if dd >= total_dd:
                    outcome = "total_dd_hit"
                    break
                if eq >= 1.0 + target:
                    outcome = "target_hit"
                    break
            if outcome:
                break

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
# [TASK-2] DSR harness — Deflated Sharpe + MinTRL + cok-test duzeltme
# ---------------------------------------------------------------------------

def dsr_harness(r: pd.Series, n_trials: int = 1) -> dict:
    """Deflated Sharpe Ratio + Bonferroni + MinTRL.

    Bailey & Lopez de Prado (2014):
    - sigma_SR: Opdyke (2007) carpiklik/basiklik duzeltmeli standart hata
    - SR*: N bagimsiz konfigurasyondan beklenen max SR (Euler-Mascheroni)
    - DSR = PSR(SR*) = Phi[(SR_hat - SR*) * sqrt(T-1) / sigma_SR]
    - MinTRL: kenar kanitlamak icin gereken minimum trade sayisi

    n_trials: test edilen toplam konfigurasyonu sayisi.
    """
    try:
        from scipy import stats as sp
    except ImportError:
        return {"hata": "scipy gerekli: pip install scipy"}

    n_nan = int(r.isna().sum())
    if n_nan > 0:
        warnings.warn(f"dsr_harness: {n_nan} NaN kaldirildi")
    arr = r.dropna().to_numpy(dtype=float)
    T = len(arr)
    if T < 20:
        return {"hata": f"yetersiz trade: {T}", "T": T}

    mu = arr.mean()
    sigma = arr.std(ddof=1)
    if sigma == 0:
        return {"hata": "sifir varyans", "T": T}

    sr_hat = mu / sigma

    # Opdyke (2007) SE — scipy kurtosis excess kurtosis dondurur (Fisher)
    g3 = float(sp.skew(arr))
    g4 = float(sp.kurtosis(arr))
    var_sr = max(
        0.0,
        (1.0 + 0.5 * sr_hat**2 - g3 * sr_hat + (g4 / 4.0) * sr_hat**2)
        / max(T - 1, 1),
    )
    sigma_sr = np.sqrt(var_sr)

    # SR* benchmark: N bagimsiz stratejiden beklenen max SR
    if n_trials <= 1:
        sr_star = 0.0
    else:
        gEM = 0.5772156649
        q1 = max(1e-12, 1.0 - 1.0 / n_trials)
        q2 = max(1e-12, 1.0 - 1.0 / (n_trials * np.e))
        sr_star = (1.0 - gEM) * float(sp.norm.ppf(q1)) + gEM * float(sp.norm.ppf(q2))

    dsr: float = float("nan")
    if sigma_sr > 0:
        z_psr = (sr_hat - sr_star) * np.sqrt(max(T - 1, 1)) / sigma_sr
        dsr = round(float(sp.norm.cdf(z_psr)), 4)

    t_stat = sr_hat * np.sqrt(T)
    p_raw = 1.0 - float(sp.norm.cdf(t_stat))
    p_bonf = round(min(1.0, p_raw * max(n_trials, 1)), 5)

    if sr_hat != 0 and sigma_sr > 0:
        min_trl: int = int(np.ceil(1.0 + (1.645 * sigma_sr / sr_hat) ** 2))
    else:
        min_trl = -1  # hesaplanamadi

    if not np.isnan(dsr):
        karar = "GERCEK_KENAR" if dsr >= 0.95 and p_bonf < 0.05 else (
            "MUHTEMEL_KENAR" if dsr >= 0.90 else "GURULTU"
        )
    else:
        karar = "HESAPLANAMADI"

    return {
        "T": T,
        "exp_r_per_trade": round(float(mu), 4),
        "sr_per_trade": round(float(sr_hat), 4),
        "sigma_sr_opdyke": round(float(sigma_sr), 4),
        "sr_star_benchmark": round(float(sr_star), 4),
        "dsr": dsr,
        "t_stat": round(float(t_stat), 3),
        "p_bonferroni": p_bonf,
        "min_trl_trades": min_trl,
        "n_trials_kullanildi": n_trials,
        "karar": karar,
    }


# ---------------------------------------------------------------------------
# 3) Regime clustering (in-sample) + [TASK-4] OOS ic-CV versiyonu
# ---------------------------------------------------------------------------

def cluster_regimes(
    ledger: pd.DataFrame, k: int = 4
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """In-sample K-means clustering. Sadece gorsellestirme icin; overfit riski var."""
    from sklearn.cluster import KMeans
    from sklearn.preprocessing import StandardScaler

    feat_cols = ["atr_pct", "adx", "vwap_dist", "range_pos", "hour"]
    feats = ledger[feat_cols].copy().replace([np.inf, -np.inf], np.nan).dropna()

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


def cluster_regimes_cv(
    ledger: pd.DataFrame, k: int = 4, n_folds: int = 5
) -> dict:
    """[TASK-4] Ic-CV rejim secimi: train'de cluster sec, test'te OOS degerlendirme.

    In-sample pozitif cluster secimi overfitting yaratir.
    OOS exp_r baz exp_r'dan yuksekse filtre gercekten calisiyordur.
    """
    from sklearn.cluster import KMeans
    from sklearn.preprocessing import StandardScaler

    feat_cols = ["atr_pct", "adx", "vwap_dist", "range_pos", "hour"]
    df = ledger[feat_cols + ["r"]].copy().replace([np.inf, -np.inf], np.nan).dropna()
    n = len(df)
    fold_size = n // n_folds

    oos_filtered: list[pd.Series] = []
    oos_all: list[pd.Series] = []

    for f in range(n_folds):
        te_start = f * fold_size
        te_end = (f + 1) * fold_size if f < n_folds - 1 else n
        train_df = pd.concat([df.iloc[:te_start], df.iloc[te_end:]])
        test_df = df.iloc[te_start:te_end]

        if len(train_df) < k * 10 or len(test_df) < 5:
            warnings.warn(
                f"cluster_regimes_cv: fold {f} atlandi "
                f"(train={len(train_df)}, test={len(test_df)}, k={k})"
            )
            continue

        scaler = StandardScaler()
        X_tr = scaler.fit_transform(train_df[feat_cols])
        km = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels_tr = km.fit_predict(X_tr)

        tr_copy = train_df.copy()
        tr_copy["cluster"] = labels_tr
        pos_cl = (
            tr_copy.groupby("cluster")["r"].mean()
            .pipe(lambda s: s[s > 0].index.tolist())
        )

        X_te = scaler.transform(test_df[feat_cols])
        labels_te = km.predict(X_te)
        filtered_r = test_df.loc[np.isin(labels_te, pos_cl), "r"]

        oos_filtered.append(filtered_r)
        oos_all.append(test_df["r"])

    if not oos_all:
        return {"hata": "yeterli fold yok"}

    all_r = pd.concat(oos_all)
    filt_r = pd.concat(oos_filtered) if oos_filtered else pd.Series(dtype=float)

    return {
        "oos_trades_toplam": len(all_r),
        "oos_exp_r_ham": round(float(all_r.mean()), 3) if len(all_r) else float("nan"),
        "oos_trades_filtreli": len(filt_r),
        "oos_exp_r_filtreli": round(float(filt_r.mean()), 3) if len(filt_r) else float("nan"),
        "oos_filtre_yuzde": round(100 * len(filt_r) / max(len(all_r), 1), 1),
        "oos_gelisim_R": round(
            float(filt_r.mean() - all_r.mean()), 3
        ) if len(filt_r) else float("nan"),
    }


# ---------------------------------------------------------------------------
# [TASK-3 & TASK-4] Meta-labeling: zaman-embargo + holdout threshold
# ---------------------------------------------------------------------------

def meta_label_wf(
    ledger: pd.DataFrame,
    n_folds: int = 5,
    embargo: int = 5,
    threshold: float = 0.55,
) -> dict:
    """Purged walk-forward CV + zaman-bazli embargo + holdout threshold.

    [TASK-3] Embargo: eski=trade sayisi; yeni=_EMBARGO_TD (480bar*15m=5gun)
    [TASK-4] Threshold: eski=tum OOS'ta sec (leak); yeni=%80 sec, %20 holdout raporu
    """
    from sklearn.ensemble import RandomForestClassifier

    feat_cols = ["dir", "atr_pct", "adx", "vwap_dist", "range_pos", "hour", "dow"]
    df = ledger[feat_cols + ["r"]].dropna().copy()
    df["y"] = (df["r"] > 0).astype(int)

    n = len(df)
    fold_size = n // n_folds
    oos_preds = pd.Series(index=df.index, dtype=float)
    use_time_emb = isinstance(df.index, pd.DatetimeIndex)

    for f in range(n_folds):
        te_start = f * fold_size
        te_end = (f + 1) * fold_size if f < n_folds - 1 else n
        test_idx = df.index[te_start:te_end]

        if use_time_emb:
            ts0 = df.index[te_start]
            ts1 = df.index[te_end - 1]
            train_mask = (df.index < ts0 - _EMBARGO_TD) | (df.index > ts1 + _EMBARGO_TD)
            train_idx = df.index[train_mask]
        else:
            tr_lo = df.index[:max(0, te_start - embargo)]
            tr_hi = df.index[min(n, te_end + embargo):]
            train_idx = tr_lo.union(tr_hi)

        if len(train_idx) < 30 or len(test_idx) < 5:
            continue

        Xtr = df.loc[train_idx, feat_cols]
        ytr = df.loc[train_idx, "y"]
        Xte = df.loc[test_idx, feat_cols]

        if ytr.nunique() < 2:
            continue

        clf = RandomForestClassifier(
            n_estimators=200, max_depth=4,
            min_samples_leaf=10, random_state=42, n_jobs=-1,
        )
        clf.fit(Xtr, ytr)
        probs = clf.predict_proba(Xte)[:, 1]
        out_of_range = (~np.isfinite(probs)) | (probs < 0) | (probs > 1)
        if out_of_range.any():
            warnings.warn(f"meta_label_wf fold {f}: {out_of_range.sum()} tahmin [0,1] disinda, clip edildi")
        oos_preds.loc[test_idx] = np.clip(probs, 0.0, 1.0)

    valid = oos_preds.dropna()
    df_v = df.loc[valid.index].copy()
    df_v["p_win"] = valid

    thresholds = [0.40, 0.45, 0.50, 0.52, 0.55, 0.58, 0.60, 0.65]
    sweep = []
    for th in thresholds:
        sel = df_v[df_v["p_win"] >= th]
        if len(sel) == 0:
            sweep.append({"th": th, "trades": 0, "exp_r": float("nan"),
                          "win_rate": float("nan"), "total_R": 0})
            continue
        sweep.append({
            "th": th,
            "trades": len(sel),
            "exp_r": round(float(sel["r"].mean()), 3),
            "win_rate": round(float((sel["r"] > 0).mean() * 100), 1),
            "total_R": round(float(sel["r"].sum()), 1),
        })

    # [TASK-4] %80 sel / %20 holdout threshold secimi
    split = int(len(df_v) * 0.80)
    sel_df = df_v.iloc[:split]
    holdout_df = df_v.iloc[split:]

    best_th = threshold
    holdout: dict = {"threshold": threshold, "trades": 0,
                     "exp_r": float("nan"), "win_rate": float("nan")}

    if len(sel_df) >= 20 and len(holdout_df) >= 5:
        sel_scores = [
            (th, float(sub["r"].mean()))
            for th in thresholds
            if len(sub := sel_df[sel_df["p_win"] >= th]) >= 10
        ]
        if sel_scores:
            best_th = max(sel_scores, key=lambda x: x[1])[0]

        ho = holdout_df[holdout_df["p_win"] >= best_th]
        holdout = {
            "threshold": best_th,
            "trades": len(ho),
            "exp_r": round(float(ho["r"].mean()), 3) if len(ho) else float("nan"),
            "win_rate": round(float((ho["r"] > 0).mean() * 100), 1) if len(ho) else float("nan"),
        }

    return {"sweep": pd.DataFrame(sweep), "predictions": df_v, "holdout": holdout}


# ---------------------------------------------------------------------------
# [TASK-5] Genislik tarama: cok-enstiruman portfolyo
# ---------------------------------------------------------------------------

def breadth_scan(
    symbols: list[str] | None = None,
    min_rr: float = 2.5,
    n_trials: int | None = None,
) -> pd.DataFrame:
    """Tum enstirumanlarda baz strateji tara, portfolyo duzeyinde DSR raporla.

    Portfolyo DSR n_trials=len(symbols)*10 ile hesaplanir.
    sqrt(N) Sharpe efekti: korelasyonsuz N enstiruman -> Sharpe * sqrt(N).
    """
    if symbols is None:
        symbols = list(INSTRUMENTS.keys())

    rows = []
    all_r_parts: list[pd.Series] = []

    for sym in symbols:
        try:
            led = build_ledger(sym, min_rr)
            r_sym = led["r"]
            m = metrics(r_sym)
            weeks = (led.index[-1] - led.index[0]).days / 7 if len(led) > 1 else 1.0
            rows.append({
                "symbol": sym,
                "trades": m["trades"],
                "exp_r": m["exp_r"],
                "win_rate": m["win_rate"],
                "pf": m["pf"],
                "trades_per_week": round(m["trades"] / max(weeks, 1e-6), 2),
                "total_R": round(float(r_sym.sum()), 1),
            })
            all_r_parts.append(r_sym)
        except Exception as exc:
            rows.append({"symbol": sym, "hata": str(exc)})

    report = pd.DataFrame(rows)

    if len(all_r_parts) >= 2:
        combined = pd.concat(all_r_parts).sort_index()
        nt = n_trials or (len(symbols) * 10)
        dsr = dsr_harness(combined, n_trials=nt)
        print(f"\n  PORTFOLYO DSR ({len(all_r_parts)} enstiruman, n_trials={nt}):")
        for kk, vv in dsr.items():
            print(f"    {kk}: {vv}")

    return report


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol", default="NASDAQ100")
    parser.add_argument("--min_rr", type=float, default=2.5)
    parser.add_argument("--mc_runs", type=int, default=5000)
    parser.add_argument("--k", type=int, default=4)
    parser.add_argument("--n_trials", type=int, default=50,
                        help="DSR icin test edilen toplam konfig sayisi")
    parser.add_argument("--breadth", action="store_true",
                        help="Tum enstirumanlarda genislik tarama calistir")
    args = parser.parse_args()

    print(f"\n{'='*68}")
    print(f"  EDGE LAB v2 | {args.symbol} 15m | min_rr={args.min_rr}")
    print(f"{'='*68}")

    ledger = build_ledger(args.symbol, args.min_rr)
    r = ledger["r"]
    m = metrics(r)
    weeks = (ledger.index[-1] - ledger.index[0]).days / 7
    print(f"\n  Baz: {m['trades']} trade, exp={m['exp_r']:+.3f}R, "
          f"WR={m['win_rate']}%, PF={m['pf']}, {m['trades']/weeks:.2f}/hafta")

    print(f"\n{'-'*68}")
    print(f"  [TASK-1] MC BLOK BOOTSTRAP ({args.mc_runs} run, 30g, takvim-gun DD)")
    print(f"{'-'*68}")
    for risk in [0.01, 0.015, 0.02]:
        mc = monte_carlo(r, runs=args.mc_runs, risk_pct=risk)
        print(f"\n  risk={risk*100:.1f}%  pas={mc['pass_rate']*100:5.1f}%  "
              f"target={mc['target_hit']*100:5.1f}%  "
              f"gun_dd={mc['daily_dd_hit']*100:5.1f}%  "
              f"tot_dd={mc['total_dd_hit']*100:5.1f}%  "
              f"sure={mc['time_out']*100:5.1f}%")
        print(f"           med_eq={mc['median_final_eq']:.3f}  "
              f"p10={mc['p10_final_eq']:.3f}  p90={mc['p90_final_eq']:.3f}  "
              f"med_dd={mc['median_max_dd']*100:.2f}%  "
              f"p90_dd={mc['p90_max_dd']*100:.2f}%")

    print(f"\n{'-'*68}")
    print(f"  [TASK-2] DSR / MULTI-TEST DUZELTME (n_trials={args.n_trials})")
    print(f"{'-'*68}")
    dsr = dsr_harness(r, n_trials=args.n_trials)
    for kk, vv in dsr.items():
        print(f"  {kk}: {vv}")

    print(f"\n{'-'*68}")
    print(f"  [3] REGIME K={args.k} — in-sample [UYARI: overfit riski]")
    print(f"{'-'*68}")
    summary, df_cl = cluster_regimes(ledger, k=args.k)
    print(summary.to_string())
    best = summary.iloc[0]
    worst = summary.iloc[-1]
    print(f"\n  En iyi (cluster {summary.index[0]}): exp={best['exp_r']:+.3f}R, "
          f"{int(best['trades'])} trade  <- IN-SAMPLE SECIM")
    print(f"  En kotu (cluster {summary.index[-1]}): exp={worst['exp_r']:+.3f}R")

    print(f"\n{'-'*68}")
    print(f"  [TASK-4a] REGIME OOS-CV — ic-CV ile overfit olcumu")
    print(f"{'-'*68}")
    rcv = cluster_regimes_cv(ledger, k=args.k)
    for kk, vv in rcv.items():
        print(f"  {kk}: {vv}")
    if "oos_gelisim_R" in rcv and isinstance(rcv["oos_gelisim_R"], float):
        gain = rcv["oos_gelisim_R"]
        print(f"  -> OOS gelisim: {gain:+.3f}R  "
              f"[{'GERCEK FILTRE' if gain > 0 else 'EZBERLEME (overfit)'}]")

    print(f"\n{'-'*68}")
    print("  [TASK-3/4b] META-LABELING (zaman-embargo + holdout threshold)")
    print(f"{'-'*68}")
    meta = meta_label_wf(ledger, n_folds=5, embargo=5)
    print(meta["sweep"].to_string(index=False))

    ho = meta["holdout"]
    print(f"\n  Holdout (%20): th={ho['threshold']:.2f}  "
          f"{ho['trades']} trade  exp={ho['exp_r']}R  WR={ho['win_rate']}%")
    ho_exp = ho["exp_r"]
    if isinstance(ho_exp, float) and not np.isnan(ho_exp):
        delta = ho_exp - m["exp_r"]
        print(f"  Meta-label kenar: {delta:+.3f}R  "
              f"[{'GERCEK' if delta > 0 else 'YOK/NOISE'}]")

    if args.breadth:
        print(f"\n{'-'*68}")
        print("  [TASK-5] GENISLIK TARAMA — tum enstirümanlar")
        print(f"{'-'*68}")
        bdf = breadth_scan(n_trials=args.n_trials)
        print(bdf.to_string(index=False))

    print(f"\n{'='*68}\n  TAMAM\n{'='*68}\n")


if __name__ == "__main__":
    main()
