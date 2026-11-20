"""Cheap-account sizing/gate test (prereg HANDOFF/ucuz_hesap_boyutlama_onkayit_2026-11-20.md, commit d01912b).

Self-contained: depends only on committed strategy-lab modules + data (no scratchpad files).
Run from strategy-lab:  python ../HANDOFF/scripts_2026-11-20/cheap_sizing.py [--quick]
"""
from __future__ import annotations

import sys
import warnings

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
sys.path.insert(0, ".")
from intraday import stop_testi as st  # noqa: E402
from intraday.seffaf_adaylari import load_btc_1h  # noqa: E402

SEED, NP, H = 20261120, 300, 260          # paths, business days (~365 calendar)
BLOCK = 20
NQ_PX = 27757.0                            # Maven US100 price at reality_profile time (lot step at today's level)
OPEN_RISK_CAP = 0.03
REGIMES = {"2013-17": ("2013-01-01", "2017-12-31"), "2018-21": ("2018-01-01", "2021-12-31"),
           "2022-23": ("2022-01-01", "2023-12-31"), "2024-26": ("2024-01-01", "2026-11-17")}
MODS = ["SWEEP", "NB", "BTC"]


def cost_of(sym: str, mult: float) -> float:
    p = pd.read_csv("outputs/intraday/mt5_bridge/reality_profile.csv").set_index("symbol")
    return float(p.loc[sym, "real_cost_per_side_central"]) * mult


def trade_table(cmult: float) -> pd.DataFrame:
    """One row per trade: day, module, R (net, 1R = stop distance), stop fraction of price."""
    cn, cb = cost_of("NASDAQ100", cmult), cost_of("BTCUSDT", cmult)
    sw = pd.read_csv("outputs/intraday/meta_label/trades_SWEEP_CORE.csv")
    # cost_r = 2 * (today's measured cost in POINTS at today's price) / risk_pts. Carrying today's points back to
    # 2013 (NQ ~3000) inflates old cost ~9x; prop_fit's extra x(cn/0.00009) adds 23%. Fix: proportional cost.
    prof = pd.read_csv("outputs/intraday/mt5_bridge/reality_profile.csv").set_index("symbol").loc["NASDAQ100"]
    risk_pts = 2 * (prof.spread_one_side_now + prof.slippage_p90) * prof.price_now / sw["cost_r"]
    P0, D0, _ = st.nq_context()
    close = pd.Series(D0["close"].to_numpy(), index=pd.DatetimeIndex(D0.index))
    px = close.reindex(pd.to_datetime(sw["timestamp"]).dt.normalize(), method="ffill").to_numpy()
    sw_r = sw["r0"] - 2 * cn * px / risk_pts
    rows = [pd.DataFrame(dict(day=pd.to_datetime(sw["timestamp"]).dt.normalize(), mod="SWEEP", R=sw_r, sf=1.0))]  # sf: presence marker only
    P, D, AT = st.nq_context()
    nb = st.apply_stop(P, st.base_nb(D, AT), 1.0).dropna(subset=["atr", "gross"])
    sf = 1.0 * nb["atr"] / nb["entry"]
    rows.append(pd.DataFrame(dict(day=pd.to_datetime(nb["key"]).dt.normalize(), mod="NB",
                                  R=(nb["gross"] - 2 * cn) / sf, sf=sf)))
    bp, bd, bat = st.btc_context()
    bt = st.apply_stop(bp, st.base_btc_21_23(load_btc_1h(), bd, bat), 1.5).dropna(subset=["atr", "gross"])
    sfb = 1.5 * bt["atr"] / bt["entry"]
    rows.append(pd.DataFrame(dict(day=pd.to_datetime(bt["key"]).dt.normalize(), mod="BTC",
                                  R=(bt["gross"] - 2 * cb) / sfb, sf=sfb)))
    return pd.concat(rows, ignore_index=True)


def day_arrays(tt: pd.DataFrame, zero: bool, lo: str = "", hi: str = "") -> tuple[pd.DatetimeIndex, np.ndarray, np.ndarray]:
    """zero=True: demean each module's R over trades INSIDE [lo, hi] (the regime being sampled).
    Full-sample demeaning was a bug: Sweep is negative pre-2022, so it injected positive drift into 2022+."""
    t = tt.copy()
    if zero:
        w = (t["day"] >= lo) & (t["day"] <= hi)
        mu = t[w].groupby("mod")["R"].mean()
        t["R"] = t["R"] - t["mod"].map(mu).fillna(0.0)
    cal = pd.bdate_range("2013-01-01", "2026-11-17")
    R = np.zeros((len(cal), 3)); S = np.zeros((len(cal), 3))
    for j, m in enumerate(MODS):
        g = t[t["mod"] == m].groupby("day").agg(R=("R", "sum"), sf=("sf", "max"))
        g = g.reindex(cal)
        R[:, j] = g["R"].fillna(0).to_numpy(); S[:, j] = g["sf"].fillna(0).to_numpy()
    return cal, R, S


def paths(cal: pd.DatetimeIndex, lo: str, hi: str, rng) -> np.ndarray:
    pool = np.flatnonzero((cal >= lo) & (cal <= hi))
    starts = rng.choice(pool[: len(pool) - BLOCK], size=(NP, H // BLOCK + 1))
    return (starts[:, :, None] + np.arange(BLOCK)).reshape(NP, -1)[:, :H]


FIRMS = {
    "I2K": dict(kind="instant", size=2000, price=41.99, trail=0.06, split=0.70),
    "L5K": dict(kind="chal", size=5000, price=29.99, phases=[(0.08, 2), (0.04, 2)], daily=0.04, static=0.08,
                first_wait=10, split=0.80, refund_at=3),
    "S2_6K": dict(kind="chal", size=6000, price=34.99, phases=[(0.08, 5), (0.05, 5)], daily=0.05, static=0.10,
                  first_wait=15, split=0.80, refund_at=1),
    "S1_6K": dict(kind="chal", size=6000, price=44.99, phases=[(0.10, 2)], daily=0.03, static=0.06,
                  first_wait=5, split=0.80, refund_at=3),
}
METHODS = [("F", 0.005), ("F", 0.010), ("F", 0.015), ("B", 0.005), ("B", 0.010), ("B", 0.015),
           ("BT", 0.010), ("BT", 0.015), ("R", 0.005), ("R", 0.010)]


def size_day(want: np.ndarray, S: np.ndarray, acct: float) -> np.ndarray:
    """Per-module risk fraction after lot quantization (NB) and the 3% open-risk gate. want: (NP,)"""
    rf = np.repeat(want[:, None], 3, axis=1) * (S > 0)
    step = 0.1 * NQ_PX * S[:, 1] / acct                       # risk of one 0.01 lot NB, account fraction
    with np.errstate(divide="ignore", invalid="ignore"):
        rf[:, 1] = np.where(S[:, 1] > 0, np.floor(want / step + 1e-9) * step, 0.0)
    for j in (1, 2):                                          # drop NB first, then BTC
        over = rf.sum(axis=1) > OPEN_RISK_CAP + 1e-12
        rf[over, j] = 0.0
    return rf


def simulate(firm: dict, meth: tuple[str, float], R: np.ndarray, S: np.ndarray) -> dict:
    """R, S: (NP, H, 3). Single account, no rebuy."""
    kind, b = meth
    n = R.shape[0]; acct = firm["size"]
    bal = np.zeros(n); peak = np.zeros(n); alive = np.ones(n, bool)
    phase = np.zeros(n, int); pdays = np.zeros(n, int); fdays = np.zeros(n, int)
    cash = np.full(n, -firm["price"]); npay = np.zeros(n, int); first = np.full(n, -1)
    blew_before = np.zeros(n, bool)
    nph = len(firm.get("phases", []))
    for t in range(H):
        if kind_is_instant := firm["kind"] == "instant":
            floor = np.minimum(peak - firm["trail"], 0.0); buf = (bal - floor) / firm["trail"]; tgt_left = np.inf
        else:
            room = np.minimum(bal + firm["static"], firm["daily"]); buf = room / min(firm["static"], firm["daily"])
            inch = phase < nph
            tgt = np.array([firm["phases"][min(p, nph - 1)][0] for p in phase])
            tgt_left = np.where(inch, tgt - bal, np.inf)
        want = np.full(n, b)
        if kind in ("B", "BT"):
            want = b * np.clip(buf, 0, 1)
        if kind == "R":                                       # addendum: profit-buffer ratchet
            want = b * np.where(bal <= 0.015, 1.0, np.where(bal <= 0.035, 1.7, 2.2))
        if kind == "BT":
            want = np.minimum(want, np.maximum(tgt_left, 0) / 2)
        rf = size_day(want, S[:, t, :], acct)
        pnl = (rf * R[:, t, :]).sum(axis=1); low = np.minimum(pnl, 0) * 1.5
        if kind_is_instant:
            dead = bal + low <= floor
        else:
            dead = (low <= -firm["daily"]) | (bal + low <= -firm["static"])
        dead &= alive
        blew_before |= dead & (npay == 0)
        alive &= ~dead
        bal = np.where(alive, bal + pnl, bal); peak = np.maximum(peak, bal)
        if kind_is_instant:
            fdays += alive
            pay = alive & ((bal >= 0.05) | ((fdays >= 10) & (bal >= 0.01)))
        else:
            pdays += alive & (pnl != 0)
            for p, (tg, md) in enumerate(firm["phases"]):
                ok = alive & (phase == p) & (bal >= tg) & (pdays >= md)
                bal[ok] = 0; peak[ok] = 0; pdays[ok] = 0; phase[ok] = p + 1
            fund = alive & (phase == nph)
            fdays += fund
            wait = np.where(npay == 0, firm["first_wait"], 10)
            pay = fund & (fdays >= wait) & (bal >= 0.01)
        amt = np.where(pay, bal * acct * firm["split"], 0.0)
        cash += amt; npay += pay
        if not kind_is_instant:
            cash += np.where(pay & (npay == firm["refund_at"]), firm["price"], 0.0)
        first = np.where(pay & (first < 0), t + 1, first)
        bal = np.where(pay, 0.0, bal); peak = np.where(pay, 0.0, peak); fdays = np.where(pay, 0, fdays)
    return dict(p30=np.mean((first > 0) & (first <= 21)), p90=np.mean((first > 0) & (first <= 64)),
                blow=np.mean(blew_before), net_mean=cash.mean(), net_med=float(np.median(cash)))


def main() -> None:
    quick = "--quick" in sys.argv
    global NP
    if quick:
        NP = 100
    out = []
    for cm in (1.0, 2.0):
        tt = trade_table(cm)
        for zero in (False, True):
            if zero and cm == 2.0:
                continue
            regs = dict(REGIMES); regs["2022+"] = ("2022-01-01", "2026-11-17")
            for rn, (lo, hi) in regs.items():
                cal, R0, S0 = day_arrays(tt, zero, lo, hi)
                ix = paths(cal, lo, hi, np.random.default_rng(SEED))
                R, S = R0[ix], S0[ix]
                for fn, f in FIRMS.items():
                    for m in METHODS:
                        r = simulate(f, m, R, S)
                        out.append(dict(cost=cm, zero=zero, regime=rn, firm=fn, method=f"{m[0]}{m[1]*100:.1f}", **r))
    df = pd.DataFrame(out)
    df.to_csv("../HANDOFF/scripts_2026-11-20/cheap_sizing_results.csv", index=False)
    real = df[(~df.zero) & (df.cost == 1.0)]
    blocks = real[real.regime.isin(REGIMES)]
    summ = blocks.groupby(["firm", "method"]).agg(worst=("net_mean", "min"), best=("net_mean", "max")).reset_index()
    a22 = real[real.regime == "2022+"].set_index(["firm", "method"])
    z = df[df.zero & (df.regime == "2022+")].set_index(["firm", "method"])["net_mean"].rename("zero22")
    zw = df[df.zero & df.regime.isin(REGIMES)].groupby(["firm", "method"])["net_mean"].max().rename("zero_maxblk")
    c2 = df[(df.cost == 2.0) & df.regime.isin(REGIMES)].groupby(["firm", "method"])["net_mean"].min().rename("worst_2x")
    summ = summ.set_index(["firm", "method"]).join(a22[["p30", "p90", "blow", "net_mean"]]).join(z).join(zw).join(c2)
    price = pd.Series({k: v["price"] for k, v in FIRMS.items()})
    summ["lottery"] = summ["zero22"] > 0  # prereg rule 1 (2022+ zero-edge mean > 0)
    summ["ok_2x"] = summ["worst_2x"] >= -summ.index.get_level_values(0).map(price).to_numpy()
    pd.set_option("display.width", 200)
    print(summ.round(2).sort_values("worst", ascending=False).to_string())


if __name__ == "__main__":
    main()
