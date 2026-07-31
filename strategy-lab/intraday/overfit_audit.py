"""Gecmis taramalari coklu-karsilastirma altinda yeniden yargila.

Calistirma:
    python -m intraday.overfit_audit

Uc bolum:
  1. TV topluluk taramasi (65 aday)        -> DSR + PBO
  2. Internet seed rejim kovalari (setup x rejim) -> DSR + PBO
  3. Forward EA canli defteri               -> PSR (arama degil, tek teyit testi)

Kritik ayrim:
  DSR/PBO  = ARAMA sonucu icin. "Kac aday denedim" bilgisini ister.
  PSR      = TEYIT testi icin. Forward test tek denemedir; deflate edilmez.
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

import pandas as pd

warnings.filterwarnings("ignore")
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from .overfit_stats import (
    align_trials,
    deflated_from_trials,
    probabilistic_sharpe_ratio,
    probability_of_backtest_overfitting,
    sharpe,
)

OUT = Path(__file__).resolve().parents[1] / "outputs" / "intraday"
MIN_BUCKET_TRADES = 30


def _ledger_trials(path: Path, key: str = "candidate") -> dict[str, pd.Series]:
    df = pd.read_csv(path, parse_dates=["timestamp"])
    return {
        name: g.set_index("timestamp")["r"].sort_index()
        for name, g in df.groupby(key)
    }


def _regime_trials(path: Path) -> dict[str, pd.Series]:
    """Her (setup x rejim kovasi) ayri bir adaydir -- secim tam burada yapiliyor."""
    df = pd.read_csv(path, parse_dates=["timestamp"])
    trials: dict[str, pd.Series] = {}
    for setup, g in df.groupby("setup"):
        for col in ("adx_regime", "atr_regime", "range_regime"):
            for val in g[col].dropna().unique():
                sub = g[g[col] == val]
                if len(sub) >= MIN_BUCKET_TRADES:
                    trials[f"{setup}|{col}={val}"] = sub.set_index("timestamp")["r"].sort_index()
    return trials


def _audit(label: str, trials: dict[str, pd.Series], freq: str = "W") -> dict:
    out = deflated_from_trials(trials)
    try:
        pbo = probability_of_backtest_overfitting(align_trials(trials, freq), n_splits=8)
    except ValueError as exc:
        pbo = {"pbo": float("nan"), "n_combinations": 0, "median_logit": float("nan")}
        print(f"  [PBO atlandi: {exc}]")
    print(f"\n=== {label}")
    print(f"  aday sayisi      : {out['n_trials']}")
    print(f"  en iyi aday      : {out['best']}")
    print(f"  islem            : {out['trades']}")
    print(f"  SR (islem basi)  : {out['sharpe']:+.4f}")
    print(f"  sans esigi E[max]: {out['sr_threshold']:.4f}   <-- sifir-edge adaylarin en iyisinden beklenen")
    print(f"  DSR              : {out['dsr']:.4f}   ({'GECTI' if out['dsr'] >= 0.95 else 'GECMEDI (>=0.95 gerekir)'})")
    print(f"  PBO              : {pbo['pbo']}   ({'saglikli' if pbo['pbo'] <= 0.20 else 'secim proseduru gurultu seciyor'})")
    return {"kapsam": label, **out, "pbo": pbo["pbo"], "pbo_kombinasyon": pbo["n_combinations"]}


def _forward_psr(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=["entry_time"])
    rows = []
    print("\n=== 3. Forward EA canli defteri (PSR -- deflate YOK, tek teyit testi)")
    for name, g in df.groupby("module"):
        s = g.set_index("entry_time")["r"].sort_index()
        psr = probabilistic_sharpe_ratio(s)
        verdict = "yetersiz ornek" if len(s) < 10 else ("guclu" if psr >= 0.95 else "belirsiz" if psr >= 0.5 else "negatif kanit")
        print(f"  {name:28} n={len(s):3d} expR={s.mean():+.3f} SR={sharpe(s):+.4f} PSR={psr:.3f}  {verdict}")
        rows.append({"kapsam": "forward", "modul": name, "islem": len(s),
                     "exp_r": round(float(s.mean()), 3), "sharpe": round(sharpe(s), 4),
                     "psr": round(psr, 4) if psr == psr else None, "yorum": verdict})
    return pd.DataFrame(rows)


def main() -> None:
    rows = []

    scalp = OUT / "tv_community_lab_ledgers.csv"
    swing = OUT / "tv_swing_lab_ledgers.csv"
    if scalp.exists() and swing.exists():
        trials = {f"scalp:{k}": v for k, v in _ledger_trials(scalp).items()}
        trials |= {f"swing:{k}": v for k, v in _ledger_trials(swing).items()}
        rows.append(_audit("1. TV topluluk taramasi (scalp + swing birlikte)", trials))

    seed = OUT / "internet_seed_regime_ledgers.csv"
    if seed.exists():
        rows.append(_audit("2. Internet seed: setup x rejim kovasi", _regime_trials(seed)))

    summary = pd.DataFrame(rows)
    fwd = OUT / "forward_ea" / "forward_ledger.csv"
    fwd_df = _forward_psr(fwd) if fwd.exists() else pd.DataFrame()

    dest = OUT / "overfit_audit.csv"
    pd.concat([summary, fwd_df], ignore_index=True).to_csv(dest, index=False)
    print(f"\nCikti: {dest}")


if __name__ == "__main__":
    main()
