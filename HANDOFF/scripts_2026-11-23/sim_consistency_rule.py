import sys
sys.path.insert(0, "."); sys.path.insert(0, "../HANDOFF/scripts_2026-11-23"); sys.path.insert(0, "../HANDOFF/scripts_2026-11-20")
import numpy as np, pandas as pd
import relaxed_fast_payout_audit as A
from cheap_sizing import paths, SEED
CAP = A.OPEN_RISK_CAP

def sim(R, S, b, trail, daily, cons, mindays, minday_pct, price=41.99, split=0.8, acct=2000):
    n, H, m = R.shape
    bal = np.zeros(n); peak = np.zeros(n); alive = np.ones(n, bool)
    best = np.zeros(n); qd = np.zeros(n, int); cash = np.full(n, -price)
    first = np.full(n, -1); blew = np.zeros(n, bool); npay = np.zeros(n, int); blocked = np.zeros(n, bool)
    for t in range(H):
        floor = np.minimum(peak - trail, 0.0); buf = (bal - floor) / trail
        want = b * np.clip(buf, 0, 1)
        rf = np.repeat(want[:, None], m, axis=1) * (S[:, t, :] > 0)
        for j in range(m - 1, 0, -1):
            over = rf.sum(axis=1) > CAP + 1e-12; rf[over, j] = 0.0
        pnl = (rf * R[:, t, :]).sum(axis=1); low = np.minimum(pnl, 0) * 1.5
        dead = ((bal + low <= floor) | (low <= -daily)) & alive
        blew |= dead & (npay == 0); alive &= ~dead
        bal = np.where(alive, bal + pnl, bal); peak = np.maximum(peak, bal)
        best = np.where(alive, np.maximum(best, pnl), best)
        qd += alive & (pnl >= minday_pct)
        base = alive & (bal >= 0.01) & (qd >= mindays)
        ok = base & ((best <= cons * bal) if cons else True)
        blocked |= base & ~ok & (npay == 0)
        cash += np.where(ok, bal * acct * split, 0); npay += ok
        first = np.where(ok & (first < 0), t + 1, first)
        for a in (bal, peak, best): a[ok] = 0
        qd[ok] = 0
    fp = first[first > 0]
    return dict(med=int(np.median(fp)) if len(fp) else None, p90=round(np.mean((first > 0) & (first <= 64)) * 100, 1),
                blow=round(blew.mean() * 100, 1), m12=round(cash.mean(), 1), blk=round(blocked.mean() * 100, 1))

tt = A.build_prop_modules()
mods = ["SWEEP", "NB", "BTC_21_23", "B7_IBS_NQ", "B2_BTC_DON", "BTC_GECE"]
cal = pd.bdate_range("2013-01-01", "2026-11-17")
R0 = np.zeros((len(cal), len(mods))); S0 = np.zeros_like(R0)
for j, md in enumerate(mods):
    g = tt[tt["mod"] == md].groupby("day").agg(R=("R", "sum"), sf=("sf", "max")).reindex(cal)
    R0[:, j] = g["R"].fillna(0); S0[:, j] = g["sf"].fillna(0)
RULES = {"kuralsiz": dict(cons=None, mindays=0, minday_pct=0),
         "FTUK %20": dict(cons=0.20, mindays=0, minday_pct=0),
         "FTM %15+5g": dict(cons=0.15, mindays=5, minday_pct=0.005)}
for reg, (lo, hi) in {"2022+": ("2022-01-01", "2026-11-17"), "2018-21": ("2018-01-01", "2021-12-31"), "2013-17": ("2013-01-01", "2017-12-31")}.items():
    ix = paths(cal, lo, hi, np.random.default_rng(SEED)); R, S = R0[ix], S0[ix]
    for rn, kw in RULES.items():
        r = sim(R, S, 0.005, 0.06, 0.03, **kw)
        print(f"{reg:7s} {rn:11s} med {str(r['med']):>4s}g  3ay {r['p90']:5.1f}%  patlama {r['blow']:4.1f}%  12ay ort {r['m12']:+7.1f}$", flush=True)
