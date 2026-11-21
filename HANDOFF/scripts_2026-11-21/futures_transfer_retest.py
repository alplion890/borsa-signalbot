"""Second futures transfer retest: Baltussen last-30 (F1/F2), Williams Oops (F3/F4), refs B7/B5.

Prereg: HANDOFF/futures_tasima_onkayit_2026-11-21.md (commit 4f78b05). Run from strategy-lab:
  python ../HANDOFF/scripts_2026-11-21/futures_transfer_retest.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, ".")
sys.path.insert(0, str(Path(__file__).resolve().parent))
from futures_cost_retest import load_1m, roll_dates, to_5m  # noqa: E402
from intraday.last30_momentum import trades_for  # noqa: E402
from intraday.seffaf_adaylari import resample_nq_daily, simulate_b5, simulate_b6, simulate_b7  # noqa: E402

OUT = Path("outputs/intraday/futures_transfer_retest")
PROFILE = Path("outputs/intraday/mt5_bridge/reality_profile.csv")
COST_PTS = {"NQ.c.0": 0.555, "ES.c.0": 0.247}   # measured in futures_cost_retest (bbo-1m + $0.61/side)
CFD_SYM = {"NQ.c.0": "NASDAQ100", "ES.c.0": "SP500"}
EVAL0, EVAL1, HOLD1, SPLIT = "2012-01-01", "2026-11-20", "2012-01-01", "2022-01-01"
ALPHA = 0.05 / 4 / 2


def boot_ci(x: np.ndarray) -> list[float]:
    rng = np.random.default_rng(20261121)
    m = x[rng.integers(0, len(x), size=(10_000, len(x)))].mean(axis=1)
    return np.quantile(m, [ALPHA, 1 - ALPHA]).tolist()


def side_frac(entry: pd.Series, pts: float) -> pd.Series:
    return pts / entry


def summarize(net: pd.Series) -> dict:
    ev = net[(net.index >= EVAL0) & (net.index < EVAL1)]
    ho = net[net.index < HOLD1]
    lo, hi = boot_ci(ev.to_numpy()) if len(ev) > 20 else (np.nan, np.nan)
    return {"n": len(ev), "mean_bp": float(ev.mean() * 1e4), "ci_bp": [lo * 1e4, hi * 1e4],
            "2012-21": float(ev[ev.index < SPLIT].mean() * 1e4), "2022+": float(ev[ev.index >= SPLIT].mean() * 1e4),
            "holdout_bp": float(ho.mean() * 1e4) if len(ho) else None, "holdout_n": len(ho)}


def evaluate(gross: pd.Series, entry: pd.Series, sym: str, cfd: float) -> dict:
    pts = COST_PTS[sym]
    res = {lab: summarize(gross - 2 * side_frac(entry, p)) for lab, p in
           (("zero", 0.0), ("central", pts), ("pessimistic", 2 * pts))}
    res["maven_cfd"] = summarize(gross - 2 * cfd)
    c = res["central"]
    res["PASS"] = bool(c["ci_bp"][0] > 0 and c["2012-21"] > 0 and c["2022+"] > 0 and res["pessimistic"]["mean_bp"] > 0)
    return res


def last30(f5: pd.DataFrame, rolls: set[str], sym: str, cfd: float) -> dict:
    t = trades_for(f5[["open", "high", "low", "close"]], "15:30", "15:55")
    t = t[~t.index.isin(rolls)]
    t.index = pd.to_datetime(t.index)
    return evaluate(t["gross"], t["entry"], sym, cfd)


def daily_rule(f5: pd.DataFrame, rolls: set[str], sym: str, cfd: float, sim) -> dict:
    daily = resample_nq_daily(f5[["open", "high", "low", "close"]])
    tr = sim(daily)
    roll_ts = pd.to_datetime(sorted(rolls))
    ent, ext = pd.to_datetime(tr["entry_time"]), pd.to_datetime(tr["exit_time"])
    spans = np.array([((roll_ts >= a) & (roll_ts <= b)).any() for a, b in zip(ent, ext)])
    tr = tr[~spans]
    idx = pd.to_datetime(tr["entry_time"])
    res = evaluate(pd.Series(tr["gross"].to_numpy(), idx), pd.Series(tr["entry"].to_numpy(), idx), sym, cfd)
    res["dropped_roll_span"] = int(spans.sum())
    return res


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    prof = pd.read_csv(PROFILE).set_index("symbol")["real_cost_per_side_central"]
    out = {}
    for sym in ("NQ.c.0", "ES.c.0"):
        f5 = to_5m(load_1m(sym))
        rolls = roll_dates(f5)
        cfd = float(prof[CFD_SYM[sym]])
        k = sym[:2]
        out[f"last30_{k}"] = last30(f5, rolls, sym, cfd)
        out[f"oops_{k}"] = daily_rule(f5, rolls, sym, cfd, simulate_b6)
        out[f"REF_ibs_{k}"] = daily_rule(f5, rolls, sym, cfd, simulate_b7)
        if k == "NQ":
            out["REF_turtle_NQ"] = daily_rule(f5, rolls, sym, cfd, simulate_b5)
    (OUT / "result.json").write_text(json.dumps(out, indent=1))
    for k, v in out.items():
        c = v["central"]
        print(f"{k:16s} zero {v['zero']['mean_bp']:+7.2f} cen {c['mean_bp']:+7.2f} CI [{c['ci_bp'][0]:+.2f},{c['ci_bp'][1]:+.2f}]"
              f" 12-21 {c['2012-21']:+.2f} 22+ {c['2022+']:+.2f} 2x {v['pessimistic']['mean_bp']:+.2f}"
              f" cfd {v['maven_cfd']['mean_bp']:+.2f} hold {c['holdout_bp']} n{c['n']} PASS {v['PASS']}")


if __name__ == "__main__":
    main()
