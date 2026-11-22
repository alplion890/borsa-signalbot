import sys
sys.path.insert(0, "."); sys.path.insert(0, "../HANDOFF/scripts_2026-11-23"); sys.path.insert(0, "../HANDOFF/scripts_2026-11-20")
import numpy as np, pandas as pd
import relaxed_fast_payout_audit as A
from cheap_sizing import paths, SEED
CAP = A.OPEN_RISK_CAP
def sim(R, S, b, trail, daily, mindays, minday, cycle, ondemand, cap, buffer, split, lock):
    n, H, m = R.shape
    bal = np.zeros(n); peak = np.zeros(n); alive = np.ones(n, bool); qd = np.zeros(n, int); since = np.zeros(n, int)
    first = np.full(n, -1); blew = np.zeros(n, bool); npay = np.zeros(n, int); paid = np.zeros(n)
    for t in range(H):
        floor = np.minimum(peak - trail, 0.0) if lock else peak - trail
        buf = (bal - floor) / trail; want = b * np.clip(buf, 0, 1)
        rf = np.repeat(want[:, None], m, axis=1) * (S[:, t, :] > 0)
        for j in range(m - 1, 0, -1):
            over = rf.sum(axis=1) > CAP + 1e-12; rf[over, j] = 0.0
        pnl = (rf * R[:, t, :]).sum(axis=1); low = np.minimum(pnl, 0) * 1.5
        dead = ((bal + low <= floor) | ((low <= -daily) if daily else False)) & alive
        blew |= dead & (npay == 0); alive &= ~dead
        bal = np.where(alive, bal + pnl, bal); peak = np.maximum(peak, bal)
        qd += alive & (pnl >= minday); since += 1
        prof = bal - buffer
        ok = alive & (prof >= 0.01) & (qd >= mindays) & ((since >= cycle) | (bal >= ondemand))
        amt = np.where(ok, np.minimum(prof, cap) if cap else prof, 0)
        paid += amt * split; npay += ok
        first = np.where(ok & (first < 0), t + 1, first)
        bal = np.where(ok, bal - amt, bal); peak = np.where(ok, np.minimum(peak, bal) if False else bal, peak)
        qd[ok] = 0; since[ok] = 0
    fp = first[first > 0]
    return dict(med=int(np.median(fp)) if len(fp) else None, p30=round(np.mean((first > 0) & (first <= 21)) * 100, 1),
                p90=round(np.mean((first > 0) & (first <= 64)) * 100, 1), blow=round(blew.mean() * 100, 1), pay12=round(paid.mean() * 100, 2))
tt = A.build_prop_modules()
ALL = ["SWEEP", "NB", "BTC_21_23", "B7_IBS_NQ", "B2_BTC_DON", "BTC_GECE"]
NOBTC = ["SWEEP", "NB", "B7_IBS_NQ"]
FIRMS = {"FN Stellar": (ALL, dict(trail=0.06, daily=None, mindays=0, minday=0, cycle=10, ondemand=0.05, cap=None, buffer=0, split=0.70, lock=True)),
         "Aqua Flex": (ALL, dict(trail=0.04, daily=0.02, mindays=7, minday=0.005, cycle=10, ondemand=9, cap=0.05, buffer=0, split=0.90, lock=False)),
         "Atlas Zero(BTCsiz)": (NOBTC, dict(trail=0.04, daily=None, mindays=5, minday=0.01, cycle=10, ondemand=9, cap=0.05, buffer=0.03, split=0.90, lock=False))}
cal = pd.bdate_range("2013-01-01", "2026-11-17")
def mat(mods):
    R0 = np.zeros((len(cal), len(mods))); S0 = np.zeros_like(R0)
    for j, md in enumerate(mods):
        g = tt[tt["mod"] == md].groupby("day").agg(R=("R", "sum"), sf=("sf", "max")).reindex(cal)
        R0[:, j] = g["R"].fillna(0); S0[:, j] = g["sf"].fillna(0)
    return R0, S0
M = {k: mat(v[0]) for k, v in FIRMS.items()}
for reg, (lo, hi) in {"2022+": ("2022-01-01", "2026-11-17"), "2018-21": ("2018-01-01", "2021-12-31"), "2013-17": ("2013-01-01", "2017-12-31")}.items():
    ix = paths(cal, lo, hi, np.random.default_rng(SEED))
    for fn, (mods, kw) in FIRMS.items():
        R0, S0 = M[fn]
        for b in (0.005, 0.01):
            r = sim(R0[ix], S0[ix], b, **kw)
            print(f"{reg:7s} {fn:18s} B{b*100:.1f} med {str(r['med']):>4s}g 1ay {r['p30']:5.1f}% 3ay {r['p90']:5.1f}% patlama {r['blow']:5.1f}% 12ay odenen %{r['pay12']:5.2f} hesap", flush=True)
