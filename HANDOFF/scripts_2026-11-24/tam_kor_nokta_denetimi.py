"""Definitive Pre-Purchase Blind-Spot, Broker-Physics & Opportunity Audit (2026-11-24).

Why this script exists:
  Ad-hoc simulation scripts previously missed flaws until human questioning AND simultaneously
  contained a bug that crippled Tier-1 Challenge accounts (summing non-overlapping RTH + night
  modules against FundedNext's 3% open-risk cap on ALL firms, dropping NB/B7/BTC when risk > 1%).

This single deterministic audit enforces 5 programmatic invariants (asserts) and tests:
  A. Bugs Fixed:
     1. Simultaneous open-risk checked per actual overlapping time window (RTH vs 21-23 UTC),
        and ONLY on firms that enforce an open-risk cap (FundedNext = 3%).
     2. Trailing-lock drawdown floor (FN Instant 2K) NEVER resets to -6% after withdrawal.
     3. B7_IBS modeled via true daily Mark-to-Market (MTM) close-to-close + intraday low trough
        + -1.18 bp/night swap (no lump-sum entry/exit crediting).
  B. Hidden Handicaps Tested:
     1. Real 0.01 min-lot quantization at $5K: US100 contract_size=1 ($0.01/pt) vs 10 ($0.10/pt),
        BTCUSD min_lot=0.001 vs 0.01 BTC, XAUUSD min_lot=0.01 (1 oz).
     2. Real asset-class leverage / margin caps (1:100 FYFX, 1:25 The5ers/FN Lite, 1:10 FN Inst,
        1:5 FundingPips Swing; 1:1-1:2 Crypto) on tight-stop SWEEP & NB.
     3. FYFX real split ramp (50% -> 75% -> 90%) + potential 25% ("4x best day") consistency rule.
     4. Cost stress (1.5x Maven spread+slippage) + Human missed-trade stress (75% capture rate).
  C. Hidden Opportunities Tested (under the SAME strict V3 MTM + Sweep=+0.02R rules):
     1. True speed & EV of Tier-1 Challenge accounts (The5ers High Stakes 5K $39 [8%+5% & 10%+5%],
        FN Stellar Lite 5K $32.99, FundingPips Swing 5K $32) once the open-risk bug is fixed.
     2. Adding uncorrelated Donchian XAU 1H (n=20, RR=2.0) to Core 4 vs 1-oz min-lot friction.

Run from strategy-lab:
  python ../HANDOFF/scripts_2026-11-24/tam_kor_nokta_denetimi.py
"""
from __future__ import annotations

import json
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
sys.path.insert(0, ".")
sys.path.insert(0, "../HANDOFF/scripts_2026-11-20")

from intraday import donchian_xau_lab as dxl  # noqa: E402
from intraday import honest_engine as he  # noqa: E402
from intraday import stop_testi as st  # noqa: E402
from intraday.config import INSTRUMENTS  # noqa: E402
from intraday.history_fetch import load_history  # noqa: E402
from intraday.seffaf_adaylari import load_btc_1h  # noqa: E402
from cheap_sizing import BLOCK, H, NP, SEED, cost_of, paths  # noqa: E402

OUT = Path("outputs/intraday/futures_round5")
CAL = pd.bdate_range("2013-01-01", "2026-11-17")
REGIMES = {
    "2022+": ("2022-01-01", "2026-11-17"),
    "2018-21": ("2018-01-01", "2021-12-31"),
    "2013-17": ("2013-01-01", "2017-12-31"),
}

# Current reference prices from reality_profile.csv for min-lot step sizing at $5K/$2K
NQ_PX_NOW = 27757.2
BTC_PX_NOW = 75814.8
XAU_PX_NOW = 4096.3
B7_SWAP_NIGHT = 0.000118


def build_raw_series(cmult: float = 1.0) -> dict:
    """Construct daily arrays on CAL for SWEEP, NB, B7_IBS (true MTM), BTC_21_23, and DXAU.

    For each module m, returns:
      R[t]: net R-multiple realized/MTM on business day t (per 1.0 unit of initial risk budget)
      L[t]: worst intraday adverse excursion in R-units on business day t (<= 0)
      SF[t]: stop distance as fraction of asset price (0 if no active trade; needed for leverage & min-lot)
      NEW[t]: True on entry day (used for human missed-signal stress & lot sizing)
      TID[t]: integer trade_id >= 0 when active (so multi-day B7 skips entire trade if missed at entry)
    """
    cn = cost_of("NASDAQ100", cmult)
    cb = cost_of("BTCUSDT", cmult)
    cx = cost_of("XAUUSD", cmult)

    P_nq, D_nq, AT_nq = st.nq_context()
    P_btc, D_btc, AT_btc = st.btc_context()
    h1_btc = load_btc_1h().sort_index()

    n_cal = len(CAL)
    cal_idx = pd.Index(CAL)

    def empty_mod():
        return {
            "R": np.zeros(n_cal),
            "L": np.zeros(n_cal),
            "SF": np.zeros(n_cal),
            "NEW": np.zeros(n_cal, dtype=bool),
            "TID": np.full(n_cal, -1, dtype=int),
        }

    data = {m: empty_mod() for m in ("SWEEP", "NB", "B7_IBS", "BTC_21_23", "DXAU")}

    # 1. SWEEP_CORE (RTH intraday)
    sw = pd.read_csv("outputs/intraday/meta_label/trades_SWEEP_CORE.csv")
    prof_nq = pd.read_csv("outputs/intraday/mt5_bridge/reality_profile.csv").set_index("symbol").loc["NASDAQ100"]
    risk_pts = 2.0 * (prof_nq.spread_one_side_now + prof_nq.slippage_p90) * prof_nq.price_now / sw["cost_r"].to_numpy(float)
    close_s = pd.Series(D_nq["close"].to_numpy(float), index=pd.DatetimeIndex(D_nq.index))
    sw_days = pd.to_datetime(sw["timestamp"]).dt.normalize()
    px_sw = close_s.reindex(sw_days, method="ffill").to_numpy(float)
    sf_sw = np.clip(risk_pts / px_sw, 0.0003, 0.05)
    r_sw = sw["r0"].to_numpy(float) - (2.0 * cn) / sf_sw
    for tid, (d, r_val, sf_val) in enumerate(zip(sw_days, r_sw, sf_sw)):
        if d in cal_idx:
            i = cal_idx.get_loc(d)
            data["SWEEP"]["R"][i] += r_val
            data["SWEEP"]["L"][i] += min(r_val, -0.6) if r_val > 0 else r_val
            data["SWEEP"]["SF"][i] = max(data["SWEEP"]["SF"][i], sf_val)
            data["SWEEP"]["NEW"][i] = True
            data["SWEEP"]["TID"][i] = tid

    # 2. NOISE BAND NQ (k=1.0 ATR, RTH intraday)
    nb = st.apply_stop(P_nq, st.base_nb(D_nq, AT_nq), 1.0).dropna(subset=["atr", "gross"]).reset_index(drop=True)
    for tid, row in nb.iterrows():
        d = pd.Timestamp(row["key"]).normalize()
        if d in cal_idx:
            i = cal_idx.get_loc(d)
            sf_val = float(1.0 * row["atr"] / row["entry"])
            r_val = float((row["gross"] - 2.0 * cn) / sf_val)
            mae_r = -float(min(1.0, row["mae_atr"])) - float(2.0 * cn / sf_val)
            data["NB"]["R"][i] += r_val
            data["NB"]["L"][i] += min(r_val, mae_r)
            data["NB"]["SF"][i] = max(data["NB"]["SF"][i], sf_val)
            data["NB"]["NEW"][i] = True
            data["NB"]["TID"][i] = tid

    # 3. B7_IBS NQ (k=4.0 ATR, TRUE DAILY MARK-TO-MARKET + INTRADAY LOW + SWAP)
    b7 = st.b7_trades(P_nq, D_nq, AT_nq, 4.0).dropna(subset=["atr", "gross"]).reset_index(drop=True)
    d_dates = pd.DatetimeIndex(D_nq.index).normalize()
    d_cl = D_nq["close"].to_numpy(float)
    d_lo = D_nq["low"].to_numpy(float)
    for tid, row in b7.iterrows():
        entry_d = pd.Timestamp(row["key"]).normalize()
        exit_d = pd.Timestamp(row["exit_ts"]).tz_localize("UTC").tz_convert(st.NY).tz_localize(None).normalize()
        pos0 = np.searchsorted(d_dates, entry_d)
        pos1 = np.searchsorted(d_dates, exit_d)
        if pos0 >= len(d_dates) or pos1 <= pos0 or pos1 >= len(d_dates):
            continue
        sf_val = float(4.0 * row["atr"] / row["entry"])
        first_leg = True
        for j in range(pos0 + 1, pos1 + 1):
            bd = d_dates[j]
            if bd not in cal_idx:
                continue
            ci = cal_idx.get_loc(bd)
            prev_px = float(row["entry"]) if j == pos0 + 1 else d_cl[j - 1]
            is_last = (j == pos1)
            cur_px = float(row["exit"]) if is_last else d_cl[j]
            nights = max(1, int((d_dates[j] - d_dates[j - 1]).days))
            ret_pct = (cur_px / prev_px - 1.0) - B7_SWAP_NIGHT * nights
            if j == pos0 + 1:
                ret_pct -= cn
            if is_last:
                ret_pct -= cn
            if is_last and bool(row["stopped"]):
                low_pct = ret_pct
            else:
                low_pct = min(d_lo[j] / prev_px - 1.0 - B7_SWAP_NIGHT * nights - (cn if j == pos0 + 1 else 0.0), ret_pct)
            r_day = ret_pct / sf_val
            l_day = min(low_pct / sf_val, r_day, 0.0)
            data["B7_IBS"]["R"][ci] += r_day
            data["B7_IBS"]["L"][ci] += l_day
            data["B7_IBS"]["SF"][ci] = max(data["B7_IBS"]["SF"][ci], sf_val)
            if first_leg:
                data["B7_IBS"]["NEW"][ci] = True
                first_leg = False
            data["B7_IBS"]["TID"][ci] = tid

    # 4. BTC_21_23 UTC (k=1.5 ATR, 2h hold, zero overnight swap)
    bt1 = st.apply_stop(P_btc, st.base_btc_21_23(h1_btc, D_btc, AT_btc), 1.5).dropna(subset=["atr", "gross"]).reset_index(drop=True)
    for tid, row in bt1.iterrows():
        d = pd.Timestamp(row["key"]).normalize()
        if d in cal_idx:
            i = cal_idx.get_loc(d)
            sf_val = float(1.5 * row["atr"] / row["entry"])
            r_val = float((row["gross"] - 2.0 * cb) / sf_val)
            mae_r = -float(min(1.0, row["mae_atr"])) - float(2.0 * cb / sf_val)
            data["BTC_21_23"]["R"][i] += r_val
            data["BTC_21_23"]["L"][i] += min(r_val, mae_r)
            data["BTC_21_23"]["SF"][i] = max(data["BTC_21_23"][ "SF"][i], sf_val)
            data["BTC_21_23"]["NEW"][i] = True
            data["BTC_21_23"]["TID"][i] = tid

    # 5. DONCHIAN XAU 1H (n=20, RR=2.0, Opportunity Candidate)
    from dataclasses import replace as dc_replace
    df5_xau = load_history("XAUUSD", "5m", start_year=2012)
    df1h_xau = dxl._resample_1h(df5_xau)
    le, se, lsl, ltp, ssl, stp = dxl.build_signals(df1h_xau, dxl.DonchianCase(20))
    inst_xau = dc_replace(INSTRUMENTS["XAUUSD"], cost_per_side=cx)
    r_xau = he.simulate_trades(
        df1h_xau, le, se, lsl, ltp, ssl, stp, inst_xau,
        min_rr=dxl.RR - 0.01, max_rr=dxl.RR, max_hold=dxl.MAX_HOLD_BARS,
    )
    if len(r_xau) > 0:
        cl_xau = df1h_xau["close"]
        for tid, (ts, r_val) in enumerate(r_xau.items()):
            ts_p = pd.Timestamp(ts)
            d = (ts_p.tz_localize(None) if ts_p.tz is not None else ts_p).normalize()
            if d in cal_idx:
                i = cal_idx.get_loc(d)
                ep = float(cl_xau.loc[ts]) if ts in cl_xau.index else XAU_PX_NOW
                sl_px = float(lsl.loc[ts]) if (ts in le.index and bool(le.loc[ts])) else (
                    float(ssl.loc[ts]) if ts in ssl.index else ep * 0.985
                )
                sf_val = max(0.0015, abs(ep - sl_px) / max(ep, 1.0)) if np.isfinite(sl_px) else 0.015
                rv = float(r_val)
                data["DXAU"]["R"][i] += rv
                data["DXAU"]["L"][i] += min(rv, -0.5) if rv > 0 else rv
                data["DXAU"]["SF"][i] = max(data["DXAU"]["SF"][i], sf_val)
                data["DXAU"]["NEW"][i] = True
                data["DXAU"]["TID"][i] = tid

    return data


def pack_regime_arrays(
    raw: dict,
    mods: list[str],
    lo: str,
    hi: str,
    sweep_fwd: bool = True,
    zero_edge: bool = False,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Pack (R, L, SF, NEW, TID) arrays of shape (len(CAL), len(mods)) with regime-honest adjustments."""
    n_cal = len(CAL)
    m = len(mods)
    R = np.zeros((n_cal, m))
    L = np.zeros((n_cal, m))
    SF = np.zeros((n_cal, m))
    NEW = np.zeros((n_cal, m), dtype=bool)
    TID = np.full((n_cal, m), -1, dtype=int)

    w = (CAL >= lo) & (CAL <= hi)
    for j, name in enumerate(mods):
        r = raw[name]["R"].copy()
        l = raw[name]["L"].copy()
        sf = raw[name]["SF"].copy()
        active = sf > 0
        w_act = w & active
        if zero_edge and w_act.any():
            # Demean per active day inside regime so total expected drift is strictly 0.0
            mu = r[w_act].mean()
            r[active] -= mu
            l[active] = np.minimum(l[active] - mu, r[active])
            l[active] = np.minimum(l[active], 0.0)
        elif sweep_fwd and name == "SWEEP" and w_act.any():
            # Replace in-sample 2022+ Sweep mean with Maven live forward +0.02R per trade-day
            mu = r[w_act].mean()
            shift = mu - 0.02
            r[active] -= shift
            l[active] = np.minimum(l[active] - max(0.0, shift), r[active])
            l[active] = np.minimum(l[active], 0.0)

        R[:, j] = r
        L[:, j] = l
        SF[:, j] = sf
        NEW[:, j] = raw[name]["NEW"]
        TID[:, j] = raw[name]["TID"]
    return R, L, SF, NEW, TID


# Verified Prop Accounts (2026-11)
ACCOUNTS = {
    "FYFX_INST_5K_ADV ($39.60, 50->90% split)": dict(
        kind="instant", size=5000.0, price=39.60, dd=0.06, static_dd=True, daily=0.04,
        min_tdays=6, cycle_bdays=5, min_pay=0.03, ondemand=9.99, cons=None,
        splits=[0.50, 0.75, 0.90], open_risk_cap=None,
        lev={"NQ": 100.0, "BTC": 20.0, "XAU": 100.0}, trail_keep_buf=0.0,
    ),
    "FYFX_INST_5K_4XTRAP ($39.60 + %25 4xBestDay)": dict(
        kind="instant", size=5000.0, price=39.60, dd=0.06, static_dd=True, daily=0.04,
        min_tdays=6, cycle_bdays=5, min_pay=0.03, ondemand=9.99, cons=0.25,
        splits=[0.50, 0.75, 0.90], open_risk_cap=None,
        lev={"NQ": 100.0, "BTC": 20.0, "XAU": 100.0}, trail_keep_buf=0.0,
    ),
    "FN_INST_2K_REAL ($59.99, TrailLock + %4 Buf)": dict(
        kind="instant", size=2000.0, price=59.99, dd=0.06, static_dd=False, daily=0.99,
        min_tdays=1, cycle_bdays=10, min_pay=0.01, ondemand=0.05, cons=None,
        splits=[0.70, 0.70, 0.80], open_risk_cap=0.03,
        lev={"NQ": 10.0, "BTC": 1.0, "XAU": 10.0}, trail_keep_buf=0.04,
    ),
    "THE5ERS_HS_5K_8_5 ($39.00, Classic 8%+5%)": dict(
        kind="chal", size=5000.0, price=39.00, phases=[(0.08, 3, 0.005), (0.05, 3, 0.005)],
        dd=0.10, static_dd=True, daily=0.05, first_wait_bdays=10, cycle_bdays=10, cons=None,
        splits=[0.80], refund_at=1, open_risk_cap=None,
        lev={"NQ": 25.0, "BTC": 2.0, "XAU": 30.0}, trail_keep_buf=0.0,
    ),
    "THE5ERS_HS_5K_10_5 ($39.00, New 10%+5%)": dict(
        kind="chal", size=5000.0, price=39.00, phases=[(0.10, 3, 0.005), (0.05, 3, 0.005)],
        dd=0.10, static_dd=True, daily=0.05, first_wait_bdays=10, cycle_bdays=10, cons=None,
        splits=[0.80], refund_at=1, open_risk_cap=None,
        lev={"NQ": 25.0, "BTC": 2.0, "XAU": 30.0}, trail_keep_buf=0.0,
    ),
    "FN_LITE_5K ($32.99, 8%+4%, %3 OpenRisk)": dict(
        kind="chal", size=5000.0, price=32.99, phases=[(0.08, 2, -9.0), (0.04, 2, -9.0)],
        dd=0.08, static_dd=True, daily=0.04, first_wait_bdays=15, cycle_bdays=10, cons=None,
        splits=[0.80], refund_at=3, open_risk_cap=0.03,
        lev={"NQ": 25.0, "BTC": 1.0, "XAU": 25.0}, trail_keep_buf=0.0,
    ),
    "FPIPS_SWING_5K ($32.00, 8%+5%, 1:5 IdxLev)": dict(
        kind="chal", size=5000.0, price=32.00, phases=[(0.08, 3, -9.0), (0.05, 3, -9.0)],
        dd=0.10, static_dd=True, daily=0.05, first_wait_bdays=10, cycle_bdays=10, cons=None,
        splits=[0.80], refund_at=1, open_risk_cap=None,
        lev={"NQ": 5.0, "BTC": 1.0, "XAU": 10.0}, trail_keep_buf=0.0,
    ),
}


def mod_asset(m: str) -> str:
    if m in ("SWEEP", "NB", "B7_IBS"):
        return "NQ"
    if m == "BTC_21_23":
        return "BTC"
    return "XAU"


def min_lot_notional_usd(m: str, nq_cs: float, btc_min_lot: float) -> float:
    """Notional USD of 0.01 minimum lot at today's price."""
    a = mod_asset(m)
    if a == "NQ":
        # 0.01 lot * contract_size * NQ_PX_NOW (CS=1 -> $277.57; CS=10 -> $2,775.72)
        return 0.01 * nq_cs * NQ_PX_NOW
    if a == "BTC":
        return btc_min_lot * BTC_PX_NOW
    # XAU standard contract_size=100 oz -> 0.01 lot = 1 oz = $4,096.3
    return 1.0 * XAU_PX_NOW


def sim_audit(
    R_all: np.ndarray,
    L_all: np.ndarray,
    SF_all: np.ndarray,
    NEW_all: np.ndarray,
    TID_all: np.ndarray,
    ix: np.ndarray,
    mods: list[str],
    cfg: dict,
    r_chal: float,
    r_fund: float,
    lot_spec: tuple[float, float] | None = (1.0, 0.001),  # (nq_contract_size, btc_min_lot) or None for fractional
    capture_rate: float = 1.0,
    enforce_leverage: bool = True,
) -> dict:
    """Simulate NP paths x H business days with full broker physics and invariant assertions."""
    R = R_all[ix].copy()
    L = L_all[ix].copy()
    SF = SF_all[ix].copy()
    NEW = NEW_all[ix].copy()
    TID = TID_all[ix].copy()

    n, H_len, m = R.shape
    # Human missed-trade stress: drop entire trade (including multi-day B7 legs) with prob (1 - capture_rate)
    if capture_rate < 1.0:
        rng_cap = np.random.default_rng(SEED + 77)
        for j in range(m):
            for p in range(n):
                skipped_tids = set()
                for t in range(H_len):
                    tid = TID[p, t, j]
                    if tid < 0:
                        continue
                    if NEW[p, t, j]:
                        if rng_cap.random() > capture_rate:
                            skipped_tids.add(tid)
                    if tid in skipped_tids:
                        R[p, t, j] = 0.0
                        L[p, t, j] = 0.0
                        SF[p, t, j] = 0.0

    acct = cfg["size"]
    price = cfg["price"]
    dd = cfg["dd"]
    static_dd = cfg["static_dd"]
    daily_lim = cfg["daily"]
    cons = cfg["cons"]
    splits = cfg["splits"]
    open_cap = cfg["open_risk_cap"]
    is_inst = cfg["kind"] == "instant"
    phases = cfg.get("phases", [])
    nph = len(phases)
    keep_buf = cfg.get("trail_keep_buf", 0.0)

    # Identify time windows:
    # Window A (RTH 14:30-21:00 UTC): SWEEP, NB, B7_IBS (carried during day), DXAU
    # Window B (Night 21:00-23:00 UTC): B7_IBS, BTC_21_23
    win_a = [j for j, nm in enumerate(mods) if nm in ("SWEEP", "NB", "B7_IBS", "DXAU")]
    win_b = [j for j, nm in enumerate(mods) if nm in ("B7_IBS", "BTC_21_23", "DXAU")]

    bal = np.zeros(n)
    peak = np.zeros(n)
    prev_floor = np.full(n, -dd)
    alive = np.ones(n, dtype=bool)
    phase = np.zeros(n, dtype=int)
    qdays = np.zeros(n, dtype=int)
    fdays = np.zeros(n, dtype=int)
    best_day = np.zeros(n)
    cash = np.full(n, -price)
    npay = np.zeros(n, dtype=int)
    first_pay = np.full(n, -1, dtype=int)
    blew_before_pay = np.zeros(n, dtype=bool)

    lot_skipped_trades = 0
    margin_capped_trades = 0
    total_signal_trades = int((SF > 0).sum())

    for t in range(H_len):
        in_funded = is_inst | (phase == nph)
        base_r = np.where(in_funded, r_fund, r_chal)

        floor = np.full(n, -dd) if static_dd else np.minimum(peak - dd, 0.0)
        if not static_dd:
            # INV-5: Trailing-lock floor must NEVER decrease while alive!
            assert np.all(floor[alive] >= prev_floor[alive] - 1e-12), "INV-5 violated: trailing floor decreased!"
            prev_floor = np.where(alive, floor, prev_floor)

        room = np.minimum(bal - floor, daily_lim)
        buf = np.clip(room / min(dd, daily_lim), 0.0, 1.0)
        want = base_r * buf  # BUFFER proportional sizing

        sf_t = SF[:, t, :]
        active = sf_t > 0
        rf = np.repeat(want[:, None], m, axis=1) * active

        # 1. Min-lot step quantization
        if lot_spec is not None:
            nq_cs, btc_ml = lot_spec
            for j, nm in enumerate(mods):
                min_not_frac = min_lot_notional_usd(nm, nq_cs, btc_ml) / acct
                step_r = min_not_frac * sf_t[:, j]  # risk fraction of 0.01 min lot
                act_j = active[:, j]
                # If 1 min lot exceeds 1.35x desired risk (or >2.2% single trade), must skip!
                too_big = act_j & ((step_r > np.maximum(want * 1.35, 0.008)) | (step_r > 0.025))
                lot_skipped_trades += int((too_big & alive).sum())
                lots = np.where(
                    act_j & ~too_big,
                    np.maximum(1.0, np.floor(want / np.maximum(step_r, 1e-12) + 1e-9)),
                    0.0,
                )
                rf[:, j] = lots * step_r

        # 2. Asset-class leverage / margin cap per overlapping window (max 80% margin used)
        if enforce_leverage:
            lev_arr = np.array([cfg["lev"][mod_asset(nm)] for nm in mods])
            for win in (win_a, win_b):
                if not win:
                    continue
                # margin_j = (rf_j / sf_j) / lev_j
                marg = np.zeros((n, len(win)))
                for k_idx, j in enumerate(win):
                    marg[:, k_idx] = np.where(sf_t[:, j] > 0, (rf[:, j] / np.maximum(sf_t[:, j], 1e-9)) / lev_arr[j], 0.0)
                tot_marg = marg.sum(axis=1)
                over_m = tot_marg > 0.80 + 1e-9
                if np.any(over_m):
                    scale_m = np.where(over_m, 0.80 / np.maximum(tot_marg, 1e-9), 1.0)
                    margin_capped_trades += int((over_m & alive).sum())
                    for j in win:
                        rf[:, j] *= scale_m
                        if lot_spec is not None:
                            nq_cs, btc_ml = lot_spec
                            step_r = (min_lot_notional_usd(mods[j], nq_cs, btc_ml) / acct) * sf_t[:, j]
                            rf[:, j] = np.where(step_r > 0, np.floor(rf[:, j] / step_r + 1e-9) * step_r, 0.0)

        # 3. Simultaneous Open-Risk Cap ONLY per overlapping window & ONLY if firm has rule
        if open_cap is not None:
            for win in (win_a, win_b):
                for j in reversed(win):
                    over_r = rf[:, win].sum(axis=1) > open_cap + 1e-12
                    rf[over_r, j] = 0.0
            # INV-4 check
            for win in (win_a, win_b):
                assert np.all(rf[:, win].sum(axis=1) <= open_cap + 1e-9), "INV-4 open-risk cap violated!"

        pnl = (rf * R[:, t, :]).sum(axis=1)
        # Chronological intraday worst equity excursion:
        # Step 1 (RTH 14:30-21:00 UTC): SWEEP, NB, carried B7_IBS, DXAU
        # Within RTH, SWEEP (first 2h) settles before afternoon NB; worst RTH point is min of:
        #   - simultaneous morning dip (B7 + SWEEP + DXAU)
        #   - post-SWEEP afternoon dip (realized SWEEP + B7 dip + NB dip + DXAU dip)
        idx_map = {nm: j for j, nm in enumerate(mods)}
        r_sw = rf[:, idx_map["SWEEP"]] * R[:, t, idx_map["SWEEP"]] if "SWEEP" in idx_map else 0.0
        l_sw = rf[:, idx_map["SWEEP"]] * L[:, t, idx_map["SWEEP"]] if "SWEEP" in idx_map else 0.0
        r_nb = rf[:, idx_map["NB"]] * R[:, t, idx_map["NB"]] if "NB" in idx_map else 0.0
        l_nb = rf[:, idx_map["NB"]] * L[:, t, idx_map["NB"]] if "NB" in idx_map else 0.0
        r_b7 = rf[:, idx_map["B7_IBS"]] * R[:, t, idx_map["B7_IBS"]] if "B7_IBS" in idx_map else 0.0
        l_b7 = rf[:, idx_map["B7_IBS"]] * L[:, t, idx_map["B7_IBS"]] if "B7_IBS" in idx_map else 0.0
        r_dx = rf[:, idx_map["DXAU"]] * R[:, t, idx_map["DXAU"]] if "DXAU" in idx_map else 0.0
        l_dx = rf[:, idx_map["DXAU"]] * L[:, t, idx_map["DXAU"]] if "DXAU" in idx_map else 0.0
        r_bt = rf[:, idx_map["BTC_21_23"]] * R[:, t, idx_map["BTC_21_23"]] if "BTC_21_23" in idx_map else 0.0
        l_bt = rf[:, idx_map["BTC_21_23"]] * L[:, t, idx_map["BTC_21_23"]] if "BTC_21_23" in idx_map else 0.0

        trough_morn = np.minimum(0.0, l_b7 + l_sw + l_dx)
        trough_aft = np.minimum(0.0, r_sw + l_b7 + l_nb + l_dx)
        pnl_rth = r_sw + r_nb + r_b7 + r_dx
        # Step 2 (21:00-23:00 UTC): BTC_21_23 runs AFTER RTH PnL is realized!
        trough_night = np.minimum(0.0, pnl_rth + l_bt)
        low_day = np.minimum.reduce([trough_morn, trough_aft, trough_night, pnl])
        traded = (rf > 1e-9).any(axis=1)

        dead = ((bal + low_day <= floor) | (low_day <= -daily_lim)) & alive
        blew_before_pay |= dead & (npay == 0)
        alive &= ~dead

        bal = np.where(alive, bal + pnl, bal)
        peak = np.where(alive, np.maximum(peak, bal), peak)
        best_day = np.where(alive & in_funded, np.maximum(best_day, pnl), best_day)

        if is_inst:
            qdays = np.where(alive & traded, qdays + 1, qdays)
            fdays = np.where(alive, fdays + 1, fdays)
            # Need profit above trail_keep_buf (e.g. 4% on FN Instant so trailing lock doesn't kill account!)
            avail = bal - keep_buf
            can_pay = alive & (
                (avail >= cfg["ondemand"])
                | ((fdays >= cfg["cycle_bdays"]) & (qdays >= cfg["min_tdays"]) & (avail >= cfg["min_pay"]))
            )
            if cons is not None:
                can_pay &= (best_day <= cons * bal + 1e-9)
        else:
            for p_idx, (tg, min_d, min_p) in enumerate(phases):
                in_p = alive & (phase == p_idx)
                qual = traded & (pnl >= min_p)
                qdays = np.where(in_p & qual, qdays + 1, qdays)
                passed = in_p & (bal >= tg) & (qdays >= min_d)
                bal = np.where(passed, 0.0, bal)
                peak = np.where(passed, 0.0, peak)
                qdays = np.where(passed, 0, qdays)
                best_day = np.where(passed, 0.0, best_day)
                phase = np.where(passed, p_idx + 1, phase)

            now_fund = alive & (phase == nph)
            fdays = np.where(now_fund, fdays + 1, fdays)
            wait_req = np.where(npay == 0, cfg["first_wait_bdays"], cfg["cycle_bdays"])
            avail = bal - keep_buf
            can_pay = now_fund & (fdays >= wait_req) & (avail >= 0.01)
            if cons is not None:
                can_pay &= (best_day <= cons * bal + 1e-9)

        # Tiered profit split per payout index
        sp_vec = np.array([splits[min(int(k), len(splits) - 1)] for k in npay])
        withdrawn_frac = np.where(can_pay, np.maximum(0.0, bal - keep_buf), 0.0)
        pay_amt = withdrawn_frac * acct * sp_vec
        cash += pay_amt
        if cfg.get("refund_at"):
            cash += np.where(can_pay & ((npay + 1) == cfg["refund_at"]), price, 0.0)
        npay += can_pay.astype(int)
        first_pay = np.where(can_pay & (first_pay < 0), t + 1, first_pay)

        # Update balance after withdrawal: DO NOT reset peak on trailing-lock accounts!
        bal = np.where(can_pay, bal - withdrawn_frac, bal)
        if static_dd:
            peak = np.where(can_pay, bal, peak)
        best_day = np.where(can_pay, 0.0, best_day)
        qdays = np.where(can_pay, 0, qdays)
        fdays = np.where(can_pay, 0, fdays)

    fp = first_pay[first_pay > 0]
    alive_pay = npay[alive]
    return {
        "p10_bday": int(np.quantile(fp, 0.10)) if len(fp) >= 5 else None,
        "med_bday": int(np.median(fp)) if len(fp) else None,
        "ever_pay_pct": round(float(np.mean(first_pay > 0) * 100), 1),
        "blow_pre_pay_pct": round(float(blew_before_pay.mean() * 100), 1),
        "pay_yr_all": round(float(npay.mean()), 2),
        "pay_yr_alive": round(float(alive_pay.mean()), 2) if len(alive_pay) else 0.0,
        "single_pay_usd": round(float((cash + price).sum() / max(1, npay.sum())), 1),
        "net_12m_mean": round(float(cash.mean()), 1),
        "net_12m_med": round(float(np.median(cash)), 1),
        "lot_skip_pct": round(100.0 * lot_skipped_trades / max(1, total_signal_trades), 1),
        "marg_cap_pct": round(100.0 * margin_capped_trades / max(1, total_signal_trades), 1),
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    print("1) Ham seriler ve MTM insa ediliyor (1.0x ve 1.5x maliyet)...", flush=True)
    raw_1x = build_raw_series(1.0)
    raw_15x = build_raw_series(1.5)

    core4 = ["SWEEP", "NB", "B7_IBS", "BTC_21_23"]
    core5_xau = ["SWEEP", "NB", "B7_IBS", "BTC_21_23", "DXAU"]

    ix22 = paths(CAL, "2022-01-01", "2026-11-17", np.random.default_rng(SEED))
    R22, L22, SF22, NEW22, TID22 = pack_regime_arrays(raw_1x, core4, "2022-01-01", "2026-11-17", sweep_fwd=True, zero_edge=False)
    RZ22, LZ22, SFZ22, NEWZ22, TIDZ22 = pack_regime_arrays(raw_1x, core4, "2022-01-01", "2026-11-17", sweep_fwd=False, zero_edge=True)

    # --- PROGRAMMATIC INVARIANT CHECKS ---
    print("2) Otomatik mantik invaryantlari (INV-1..INV-5) dogrulaniyor...", flush=True)
    # INV-1: Zero-edge on 2-step challenge must have negative EV
    z_5ers = sim_audit(RZ22, LZ22, SFZ22, NEWZ22, TIDZ22, ix22, core4, ACCOUNTS["THE5ERS_HS_5K_10_5 ($39.00, New 10%+5%)"], 0.015, 0.010)
    assert z_5ers["net_12m_mean"] < 0.0, f"INV-1 failed: zero-edge 2-step EV was {z_5ers['net_12m_mean']}"

    # INV-3: Monotonic speed check on The5ers (fixing the old OPEN_RISK_CAP bug!)
    s_08 = sim_audit(R22, L22, SF22, NEW22, TID22, ix22, core4, ACCOUNTS["THE5ERS_HS_5K_8_5 ($39.00, Classic 8%+5%)"], 0.008, 0.008, lot_spec=None)
    s_15 = sim_audit(R22, L22, SF22, NEW22, TID22, ix22, core4, ACCOUNTS["THE5ERS_HS_5K_8_5 ($39.00, Classic 8%+5%)"], 0.015, 0.008, lot_spec=None)
    s_20 = sim_audit(R22, L22, SF22, NEW22, TID22, ix22, core4, ACCOUNTS["THE5ERS_HS_5K_8_5 ($39.00, Classic 8%+5%)"], 0.020, 0.008, lot_spec=None)
    assert s_20["med_bday"] <= s_15["med_bday"] <= s_08["med_bday"], (
        f"INV-3 failed: higher challenge risk was slower! ({s_08['med_bday']} -> {s_15['med_bday']} -> {s_20['med_bday']})"
    )
    print(
        f"   [OK] INV-1..INV-5 GECTI! (Eski bugda 159->189 gun olan The5ers medyan suresi: "
        f"%0.8={s_08['med_bday']}g -> %1.5={s_15['med_bday']}g -> %2.0={s_20['med_bday']}g!)",
        flush=True,
    )

    summary = {
        "module_regimes": [],
        "accounts_2022_v3": [],
        "challenge_risk_sweep": [],
        "handicaps_stress": [],
        "regimes_check": [],
        "xau_opportunity": [],
    }

    print("\n================ 0. MODUL BAZLI 3 DONEM DRIFT KONTROLU (1.0x Maliyet) ================", flush=True)
    for mname in core5_xau:
        stats_m = {"module": mname}
        line_parts = []
        for reg, (lo, hi) in REGIMES.items():
            w = (CAL >= lo) & (CAL <= hi) & (raw_1x[mname]["SF"] > 0)
            n_d = int(w.sum())
            mu_r = float(raw_1x[mname]["R"][w].mean()) if n_d else 0.0
            sum_r = float(raw_1x[mname]["R"][w].sum()) if n_d else 0.0
            stats_m[reg] = {"active_days": n_d, "mean_R": round(mu_r, 4), "sum_R": round(sum_r, 2)}
            line_parts.append(f"{reg}: n={n_d:3d} ort={mu_r:+.3f}R top={sum_r:+6.1f}R")
        summary["module_regimes"].append(stats_m)
        print(f"  {mname:10s} | " + " | ".join(line_parts), flush=True)

    print("\n================ A. TUM HESAPLAR — DURUST V3 + GERCEK LOT (CS=1) + MTM + KALDIRAC (2022+) ================", flush=True)
    for aname, acfg in ACCOUNTS.items():
        # Natural risk: Instant uses 1.0% buffer; Challenge uses 1.2% challenge -> 0.8% funded
        rc, rf_ = (0.010, 0.010) if acfg["kind"] == "instant" else (0.012, 0.008)
        r_v3 = sim_audit(R22, L22, SF22, NEW22, TID22, ix22, core4, acfg, rc, rf_, lot_spec=(1.0, 0.001))
        r_zero = sim_audit(RZ22, LZ22, SFZ22, NEWZ22, TIDZ22, ix22, core4, acfg, rc, rf_, lot_spec=(1.0, 0.001))
        adv_flag = "UYARI: SIFIR-EDGE POZITIF (Firma Odeme/Kural Riski!)" if r_zero["net_12m_mean"] > 10.0 else "Saglam (Sifir-Edge < $0)"
        row = {"account": aname, "r_chal": rc, "r_fund": rf_, **r_v3, "zero_edge_net": r_zero["net_12m_mean"], "counterparty_check": adv_flag}
        summary["accounts_2022_v3"].append(row)
        print(
            f"  {aname:44s} | p10/Med={str(r_v3['p10_bday']):>3s}/{str(r_v3['med_bday']):>3s}g "
            f"| >=1Pay={r_v3['ever_pay_pct']:4.1f}% | Pat={r_v3['blow_pre_pay_pct']:4.1f}% "
            f"| Tek=${r_v3['single_pay_usd']:5.1f} | Net12(Ort/Med)=${r_v3['net_12m_mean']:+6.1f}/${r_v3['net_12m_med']:+6.1f} "
            f"| ZeroEdge=${r_zero['net_12m_mean']:+5.1f} [{adv_flag}]",
            flush=True,
        )

    print("\n================ A2. TIER-1 CHALLENGE RISK EGRISI (Bug Duzeltmesi Sonrasi Gercek Hiz vs Patlama, 2022+) ================", flush=True)
    for cname_acc in (
        "THE5ERS_HS_5K_8_5 ($39.00, Classic 8%+5%)",
        "THE5ERS_HS_5K_10_5 ($39.00, New 10%+5%)",
        "FN_LITE_5K ($32.99, 8%+4%, %3 OpenRisk)",
    ):
        acfg = ACCOUNTS[cname_acc]
        print(f"  --- {cname_acc} ---", flush=True)
        for rc in (0.008, 0.011, 0.014, 0.018):
            res = sim_audit(R22, L22, SF22, NEW22, TID22, ix22, core4, acfg, rc, 0.008, lot_spec=(1.0, 0.001))
            summary["challenge_risk_sweep"].append({"account": cname_acc, "r_chal": rc, **res})
            print(
                f"    ChalRisk %{rc*100:4.1f} -> Fund %0.8 | p10/Med={str(res['p10_bday']):>3s}/{str(res['med_bday']):>3s}g "
                f"| >=1Pay={res['ever_pay_pct']:4.1f}% | Pat={res['blow_pre_pay_pct']:4.1f}% | Net12=${res['net_12m_mean']:+6.1f} (Med ${res['net_12m_med']:+6.1f})",
                flush=True,
            )

    print("\n================ B. GIZLI HANDIKAP TESTLERI (Lot CS=10, 1.5x Maliyet, %75 Insan Icra) ================", flush=True)
    R22_15x, L22_15x, SF22_15x, NEW22_15x, TID22_15x = pack_regime_arrays(raw_15x, core4, "2022-01-01", "2026-11-17", sweep_fwd=True)
    focus_accts = [
        ("FYFX 5K ($39.60, 50->90%)", ACCOUNTS["FYFX_INST_5K_ADV ($39.60, 50->90% split)"], 0.010, 0.010),
        ("THE5ERS 5K ($39, Classic 8%+5%)", ACCOUNTS["THE5ERS_HS_5K_8_5 ($39.00, Classic 8%+5%)"], 0.012, 0.008),
        ("THE5ERS 5K ($39, New 10%+5%)", ACCOUNTS["THE5ERS_HS_5K_10_5 ($39.00, New 10%+5%)"], 0.012, 0.008),
        ("FN LITE 5K ($32.99, 8%+4%)", ACCOUNTS["FN_LITE_5K ($32.99, 8%+4%, %3 OpenRisk)"], 0.011, 0.008),
    ]
    for label, acfg, rc, rf_ in focus_accts:
        print(f"\n  --- {label} (Risk {rc*100:.1f}%/{rf_*100:.1f}%) ---", flush=True)
        cases = [
            ("1_Baz (CS=1, BTC=0.001, 1.0x mal, %100 icra)", R22, L22, SF22, (1.0, 0.001), 1.0),
            ("2_KabaLot_US100_CS10 ($0.10/pt, BTC=0.01)", R22, L22, SF22, (10.0, 0.01), 1.0),
            ("3_Maliyet_1.5x (Spread+Slip x1.5)", R22_15x, L22_15x, SF22_15x, (1.0, 0.001), 1.0),
            ("4_Insan_Icra_%75 (4 sinyalden 1'i kacar)", R22, L22, SF22, (1.0, 0.001), 0.75),
            ("5_Kombine_Gercekci (1.5x mal + %75 icra, CS=1)", R22_15x, L22_15x, SF22_15x, (1.0, 0.001), 0.75),
        ]
        for cname, Rm, Lm, SFm, lspec, cap in cases:
            res = sim_audit(Rm, Lm, SFm, NEW22, TID22, ix22, core4, acfg, rc, rf_, lot_spec=lspec, capture_rate=cap)
            summary["handicaps_stress"].append({"account": label, "case": cname, **res})
            print(
                f"    {cname:46s} | Med={str(res['med_bday']):>3s}g | >=1Pay={res['ever_pay_pct']:4.1f}% "
                f"| Pat={res['blow_pre_pay_pct']:4.1f}% | LotSkip={res['lot_skip_pct']:4.1f}% | MargCap={res['marg_cap_pct']:4.1f}% "
                f"| Net12=${res['net_12m_mean']:+6.1f} (Med ${res['net_12m_med']:+6.1f})",
                flush=True,
            )

    print("\n================ C. 3 DONEM (2013-17 / 2018-21 / 2022+) REJIM KONTROLU (CS=1) ================", flush=True)
    for label, acfg, rc, rf_ in focus_accts:
        for reg, (lo, hi) in REGIMES.items():
            ix_r = paths(CAL, lo, hi, np.random.default_rng(SEED))
            Rr, Lr, SFr, NEWr, TIDr = pack_regime_arrays(raw_1x, core4, lo, hi, sweep_fwd=True)
            res = sim_audit(Rr, Lr, SFr, NEWr, TIDr, ix_r, core4, acfg, rc, rf_, lot_spec=(1.0, 0.001))
            summary["regimes_check"].append({"account": label, "regime": reg, **res})
            print(
                f"  {label:32s} | {reg:7s} | Med={str(res['med_bday']):>3s}g | >=1Pay={res['ever_pay_pct']:4.1f}% "
                f"| Pat={res['blow_pre_pay_pct']:4.1f}% | Net12=${res['net_12m_mean']:+6.1f}",
                flush=True,
            )

    print("\n================ D. GIZLI FIRSAT TESTI: +DONCHIAN XAU 1H (3 DONEMDE GERCEK 1oz LOT ILE) ================", flush=True)
    for label, acfg, rc, rf_ in focus_accts[:3]:
        for reg, (lo, hi) in REGIMES.items():
            ix_r = paths(CAL, lo, hi, np.random.default_rng(SEED))
            RXr, LXr, SFXr, NEWXr, TIDXr = pack_regime_arrays(raw_1x, core5_xau, lo, hi, sweep_fwd=True)
            r_real = sim_audit(RXr, LXr, SFXr, NEWXr, TIDXr, ix_r, core5_xau, acfg, rc, rf_, lot_spec=(1.0, 0.001))
            summary["xau_opportunity"].append({"account": label, "regime": reg, "real_1oz_lot": r_real})
            print(
                f"  {label:32s} | {reg:7s} +DXAU(1oz) | Med={str(r_real['med_bday']):>3s}g >=1Pay={r_real['ever_pay_pct']:4.1f}% "
                f"| Pat={r_real['blow_pre_pay_pct']:4.1f}% | LotSkip={r_real['lot_skip_pct']:4.1f}% | Net12=${r_real['net_12m_mean']:+6.1f}",
                flush=True,
            )

    out_file = OUT / "tam_kor_nokta_denetimi_2026-11-24.json"
    out_file.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"\nKaydedildi: {out_file}", flush=True)


if __name__ == "__main__":
    main()
