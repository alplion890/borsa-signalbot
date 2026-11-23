"""Pre-purchase robustness audit of the sub-$50 prop simulation (2026-11-24).

Removes optimistic assumptions one by one:
  1. Module set: drop TOM_NQ (rejected, CI not > 0) and BTC_GECE (needs swap-free; Maven swap kills it).
  2. Multi-day trades (B7, TOM, BTC_GECE): credit PnL on EXIT day instead of entry day (no early crediting).
  3. Sweep: its 2022+ edge is largely in-sample (rule chosen on 3y data); Maven forward n18 = +0.02R.
     Variant SWEEP_FWD: Sweep R demeaned inside the sampled regime + 0.02R.
  4. Regimes: 2022+, 2018-21, 2013-17 (previous sub50 run used only 2022+).
  5. Zero-edge control: every module demeaned inside the regime.

Run from strategy-lab:  python ../HANDOFF/scripts_2026-11-23/satin_alma_oncesi_denetim.py
"""
from __future__ import annotations

import sys
import warnings

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
sys.path.insert(0, ".")
sys.path.insert(0, "../HANDOFF/scripts_2026-11-23")
sys.path.insert(0, "../HANDOFF/scripts_2026-11-20")
import human_delay_and_checklist as HDC  # noqa: E402
import sub50_prop_risk_frontier as SP  # noqa: E402
from cheap_sizing import SEED, paths  # noqa: E402

CAL = HDC.CAL
REGIMES = {"2022+": ("2022-01-01", "2026-11-17"), "2018-21": ("2018-01-01", "2021-12-31"),
           "2013-17": ("2013-01-01", "2017-12-31")}
MULTI_DAY = ("B7_IBS", "TOM_NQ", "BTC_GECE")


def matrix(tables, mods, lo, hi, exit_day, sweep_fwd, zero):
    R0 = np.zeros((len(CAL), len(mods)))
    S0 = np.zeros((len(CAL), len(mods)))
    for j, m in enumerate(mods):
        df = tables[m].copy()
        if exit_day and m in MULTI_DAY and "exit_ts" in df.columns:
            df["day"] = pd.to_datetime(df["exit_ts"]).dt.tz_localize(None).dt.normalize() \
                if pd.to_datetime(df["exit_ts"]).dt.tz is not None else pd.to_datetime(df["exit_ts"]).dt.normalize()
        r = df["R_0"].astype(float)
        w = (df["day"] >= lo) & (df["day"] <= hi)
        if zero:
            r = r - r[w].mean()
        elif sweep_fwd and m == "SWEEP":
            r = r - r[w].mean() + 0.02
        df["R"] = r
        g = df.groupby("day").agg(R=("R", "sum"), sf=("sf", "max")).reindex(CAL)
        R0[:, j] = g["R"].fillna(0).to_numpy()
        S0[:, j] = g["sf"].fillna(0).to_numpy()
    return R0, S0


def main() -> None:
    tables = HDC.build_human_trades()
    full = ["SWEEP", "NB", "B7_IBS", "TOM_NQ", "BTC_21_23", "BTC_GECE"]
    core = ["SWEEP", "NB", "B7_IBS", "BTC_21_23"]
    variants = [
        ("V0 onceki sim (6 modul, giris gunu)", full, False, False, False),
        ("V1 cekirdek (TOM+BTC_GECE yok)", core, False, False, False),
        ("V2 V1 + cikis gunu kaydi", core, True, False, False),
        ("V3 V2 + Sweep forward +0.02R", core, True, True, False),
        ("V4 sifir-edge kontrol (V2 seti)", core, True, False, True),
    ]
    accts = {k: v for k, v in SP.ACCOUNTS.items() if k.startswith(("1_", "2_"))}
    for aname, cfg in accts.items():
        print(f"\n==== {aname} | BUFFER %1.0 ====")
        for reg, (lo, hi) in REGIMES.items():
            ix = paths(CAL, lo, hi, np.random.default_rng(SEED))
            for vname, mods, ex, sf, z in variants:
                R0, S0 = matrix(tables, mods, lo, hi, ex, sf, z)
                r = SP.sim_account(R0[ix], S0[ix], cfg, "BUFFER", 0.010, 0.010)
                print(f"  {reg:7s} {vname:38s} med={str(r['med_first_bday']):>4s}g "
                      f"12ayda_pay=%{r['ever_pay_12m_pct']:5.1f} patlama=%{r['blow_before_pay_pct']:4.1f} "
                      f"pay/yil={r['payouts_per_yr_alive']:.1f} tek=${r['single_payout_avg_usd']:6.1f} "
                      f"net12=${r['net_12m_mean_usd']:+7.1f}", flush=True)


if __name__ == "__main__":
    main()
