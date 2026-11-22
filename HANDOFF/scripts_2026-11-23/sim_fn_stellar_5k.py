import sys
sys.path.insert(0, "."); sys.path.insert(0, "../HANDOFF/scripts_2026-11-23"); sys.path.insert(0, "../HANDOFF/scripts_2026-11-20")
import numpy as np, pandas as pd
import relaxed_fast_payout_audit as A
from cheap_sizing import paths, SEED
CAP = A.OPEN_RISK_CAP; ACCT = 5000; FEE = 149.99; SPLIT = 0.70; TRAIL = 0.06
MODS = ["SWEEP", "NB", "BTC_21_23", "B7_IBS_NQ", "B2_BTC_DON", "BTC_GECE"]
LEV = np.array([10, 10, 1, 10, 1, 1.0]); CRYPTO = np.array([0, 0, 1, 0, 1, 1], bool)
def sim(R, S, b):
    n, H, m = R.shape
    bal = np.zeros(n); peak = np.zeros(n); alive = np.ones(n, bool); since = np.zeros(n, int)
    first = np.full(n, -1); blew_pre = np.zeros(n, bool); blew = np.zeros(n, bool); npay = np.zeros(n, int)
    paid = np.zeros(n); amts = []; gaps = []; last = np.full(n, -1)
    for t in range(H):
        floor = np.minimum(peak - TRAIL, 0.0); want = b * np.clip((bal - floor) / TRAIL, 0, 1)
        sf = S[:, t, :]; on = sf > 0
        rf = np.repeat(want[:, None], m, axis=1) * on
        rf = np.where(on, np.minimum(rf, LEV * sf), 0)           # per-module leverage cap
        notc = np.where(on & CRYPTO, rf / np.where(on, sf, 1), 0).sum(1)   # crypto notional / acct
        scale = np.where(notc > 1, 1 / np.maximum(notc, 1e-12), 1)
        rf = np.where(CRYPTO, rf * scale[:, None], rf)
        for j in range(m - 1, 0, -1):
            over = rf.sum(1) > CAP + 1e-12; rf[over, j] = 0.0
        pnl = (rf * R[:, t, :]).sum(1); low = np.minimum(pnl, 0) * 1.5
        dead = (bal + low <= floor) & alive
        blew_pre |= dead & (npay == 0); blew |= dead; alive &= ~dead
        bal = np.where(alive, bal + pnl, bal); peak = np.maximum(peak, bal); since += 1
        ok = alive & (bal >= 0.01) & ((since >= 10) | (bal >= 0.05))
        amt = np.where(ok, bal * ACCT * SPLIT, 0); paid += amt; npay += ok
        amts += list(amt[ok]); gaps += list((t - last)[ok & (last >= 0)])
        last = np.where(ok, t, last); first = np.where(ok & (first < 0), t + 1, first)
        bal = np.where(ok, 0, bal); peak = np.where(ok, 0, peak); since[ok] = 0
    net = paid - FEE; fp = first[first > 0]
    q = lambda a, p: np.percentile(a, p) if len(a) else float("nan")
    return dict(paid_any=np.mean(first > 0) * 100, fp10=q(fp, 10), fp50=q(fp, 50), fp90=q(fp, 90),
                npay50=np.median(npay), npay_paid=np.median(npay[first > 0]) if len(fp) else 0,
                amt50=q(amts, 50), amt10=q(amts, 10), amt90=q(amts, 90), gap50=q(gaps, 50),
                net10=q(net, 10), net50=q(net, 50), net90=q(net, 90), netmean=net.mean(),
                loss=np.mean(net < 0) * 100, blew_pre=blew_pre.mean() * 100, blew=blew.mean() * 100)
tt = A.build_prop_modules(); cal = pd.bdate_range("2013-01-01", "2026-11-17")
R0 = np.zeros((len(cal), len(MODS))); S0 = np.zeros_like(R0)
for j, md in enumerate(MODS):
    g = tt[tt["mod"] == md].groupby("day").agg(R=("R", "sum"), sf=("sf", "max")).reindex(cal)
    R0[:, j] = g["R"].fillna(0); S0[:, j] = g["sf"].fillna(0)
for reg, (lo, hi) in {"2022+ (iyi)": ("2022-01-01", "2026-11-17"), "2018-21": ("2018-01-01", "2021-12-31"), "2013-17 (kotu)": ("2013-01-01", "2017-12-31")}.items():
    ix = paths(cal, lo, hi, np.random.default_rng(SEED))
    for b in (0.005, 0.01):
        r = sim(R0[ix], S0[ix], b)
        print(f"{reg:14s} B{b*100:.1f} | odeme alan %{r['paid_any']:.0f} | ilk payout g p10/50/90 {r['fp10']:.0f}/{r['fp50']:.0f}/{r['fp90']:.0f} | odeme sayisi med {r['npay_paid']:.0f} aralik {r['gap50']:.0f}g | tek odeme $ p10/50/90 {r['amt10']:.0f}/{r['amt50']:.0f}/{r['amt90']:.0f} | 12ay net $ p10/50/90 {r['net10']:+.0f}/{r['net50']:+.0f}/{r['net90']:+.0f} ort {r['netmean']:+.0f} | zarar %{r['loss']:.0f} | patlama ilk-oncesi %{r['blew_pre']:.1f} 12ay %{r['blew']:.1f}", flush=True)
