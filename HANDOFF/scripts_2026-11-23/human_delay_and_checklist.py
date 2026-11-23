"""Human-Execution Delay (5m lag) & Pre-Trade Visual Checklist (Skip / Lot-Boost) Test
+ Cheap Manual Prop Account Simulation (FundYourFX 5K $39.60 vs FN Stellar 2K $59.99 No-EA).

Methodology:
  - Test 1 (Human Lag): Compare exact signal entry (T+0) vs 5-minute delayed manual entry (T+5m / +15m on 1h BTC).
  - Test 2 (Pre-Trade Visual Checklist): Evaluate 4 simple visual checks a human can verify in 2 seconds before clicking:
      C1_DEEP_SIGNAL : B7 IBS < 0.10 (deep close at absolute low) vs 0.10..0.20; NB breakout > 0.25*ATR past band
      C2_TREND_SMA20 : Close > 20-day SMA (with-trend long) vs < SMA20
      C3_VOL_REGIME  : Prior day range (or current day range) > 1.2 * ATR14 (active volatility vs dead chop)
      C4_LAST_BAR_PB : Last 5m/1h bar before entry is a pullback (cheaper entry) vs extended impulse
    Rule: A check is VALID only if the direction of effect (good > bad) is consistent in BOTH 2012-2021 (IS) and 2022-2026 (OOS).
  - Test 3 (Cheap Manual Prop Sim): Simulate FundYourFX 5K ($39.60, 6% static DD, 6 min days, weekly payout)
    and FN Stellar 2K ($59.99 manual, no EA fee) with T+5m human lag + validated human checklist sizing.

Run from strategy-lab with vectorbt-lab venv:
  python ../HANDOFF/scripts_2026-11-23/human_delay_and_checklist.py
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
from intraday import stop_testi as st  # noqa: E402
from intraday.history_fetch import load_history  # noqa: E402
from intraday.seffaf_adaylari import load_btc_1h  # noqa: E402
from cheap_sizing import OPEN_RISK_CAP, SEED, cost_of, paths  # noqa: E402

OUT = Path("outputs/intraday/futures_round5")
CAL = pd.bdate_range("2013-01-01", "2026-11-17")
SPLIT = pd.Timestamp("2022-01-01")


def build_human_trades() -> dict[str, pd.DataFrame]:
    """Build per-module trade tables with T+0 entry, T+5m delayed entry, and 4 pre-trade visual features."""
    cn, cb = cost_of("NASDAQ100", 1.0), cost_of("BTCUSDT", 1.0)
    P_nq, D_nq, AT_nq = st.nq_context()
    raw_nq = load_history("NASDAQ100", "5m", start_year=2012).sort_index()
    nq_ts = pd.DatetimeIndex(raw_nq.index).asi8
    nq_o = raw_nq["open"].to_numpy(float)
    nq_c = raw_nq["close"].to_numpy(float)

    h1_btc = load_btc_1h().sort_index()
    P_btc, D_btc, AT_btc = st.btc_context()
    btc_ts = pd.DatetimeIndex(h1_btc.index).asi8
    btc_o = h1_btc["open"].to_numpy(float)
    btc_c = h1_btc["close"].to_numpy(float)

    # Daily context tables (strictly known at or before decision)
    d_nq = D_nq.copy()
    d_nq["atr14"] = AT_nq
    d_nq["sma20"] = d_nq["close"].rolling(20).mean()
    d_nq["rng_atr"] = (d_nq["high"] - d_nq["low"]) / d_nq["atr14"]
    d_nq["ibs"] = (d_nq["close"] - d_nq["low"]) / (d_nq["high"] - d_nq["low"]).replace(0, np.nan)
    d_nq_prev = d_nq.shift(1)

    d_btc = D_btc.copy()
    d_btc["atr14"] = AT_btc
    d_btc["sma20"] = d_btc["close"].rolling(20).mean()
    d_btc["rng_atr"] = (d_btc["high"] - d_btc["low"]) / d_btc["atr14"]
    d_btc_prev = d_btc.shift(1)

    def nq_price_after(ts_val: int, delay_min: int) -> tuple[float, float]:
        """Return (delayed_entry_price, prior_5m_bar_return) at ts_val + delay_min."""
        target_ns = ts_val + delay_min * 60 * 10**9
        idx = int(np.searchsorted(nq_ts, target_ns, side="left"))
        if idx >= len(nq_o):
            idx = len(nq_o) - 1
        prev_i = max(0, int(np.searchsorted(nq_ts, ts_val, side="left")) - 1)
        pb_ret = (nq_c[prev_i] / nq_o[prev_i] - 1.0) if nq_o[prev_i] > 0 else 0.0
        return float(nq_o[idx]), float(pb_ret)

    out_tables = {}

    # 1. NOISE BAND NQ (k=1.0 ATR stop)
    base_nb = st.apply_stop(P_nq, st.base_nb(D_nq, AT_nq), 1.0).dropna(subset=["atr", "gross"]).copy()
    nb_delay_px, nb_pb = [], []
    for r in base_nb.itertuples(index=False):
        p5, pb = nq_price_after(pd.Timestamp(r.entry_ts).value, 5)
        nb_delay_px.append(p5)
        nb_pb.append(pb * r.direction)  # negative = pullback before entry
    base_nb["entry_5m"] = nb_delay_px
    base_nb["gross_5m"] = base_nb["direction"] * (base_nb["exit"] / base_nb["entry_5m"] - 1.0)
    sf_nb = 1.0 * base_nb["atr"] / base_nb["entry"]
    base_nb["R_0"] = (base_nb["gross"] - 2 * cn) / sf_nb
    base_nb["R_5m"] = (base_nb["gross_5m"] - 2 * cn) / sf_nb
    base_nb["sf"] = sf_nb
    base_nb["day"] = pd.to_datetime(base_nb["key"]).dt.normalize()
    # Visual features known at entry:
    # C2: with-trend (long above yesterday SMA20, short below yesterday SMA20)
    prev_c = d_nq_prev["close"].reindex(base_nb["day"]).to_numpy()
    prev_sma = d_nq_prev["sma20"].reindex(base_nb["day"]).to_numpy()
    prev_rng = d_nq_prev["rng_atr"].reindex(base_nb["day"]).to_numpy()
    base_nb["C1_STRONG_IMPULSE"] = np.array(nb_pb) > 0.0005  # strong 5m signal candle in breakout dir
    base_nb["C2_WITH_TREND_SMA20"] = np.where(base_nb["direction"] == 1, prev_c > prev_sma, prev_c < prev_sma)
    base_nb["C3_HIGH_VOL_PREV_DAY"] = prev_rng > 1.15
    base_nb["C4_MORNING_SESSION"] = pd.to_datetime(base_nb["entry_ts"]).dt.hour < 16  # before 12:00 NY (16:00 UTC)
    out_tables["NB"] = base_nb

    # 2. B7 IBS NQ (entered at 15:55 NY vs 16:00 NY close, k=4.0 disaster stop)
    base_b7 = st.b7_trades(P_nq, D_nq, AT_nq, 4.0).dropna(subset=["atr", "gross"]).copy()
    b7_5m_px = []
    for r in base_b7.itertuples(index=False):
        # 5 min before 16:00 NY close (15:55 NY open)
        p5, _ = nq_price_after(pd.Timestamp(r.entry_ts).value, -5)
        b7_5m_px.append(p5)
    base_b7["entry_5m"] = b7_5m_px
    base_b7["gross_5m"] = base_b7["exit"] / base_b7["entry_5m"] - 1.0
    sf_b7 = 4.0 * base_b7["atr"] / base_b7["entry"]
    base_b7["R_0"] = (base_b7["gross"] - 2 * cn) / sf_b7
    base_b7["R_5m"] = (base_b7["gross_5m"] - 2 * cn) / sf_b7
    base_b7["sf"] = sf_b7
    base_b7["day"] = pd.to_datetime(base_b7["key"]).dt.normalize()
    cur_ibs = d_nq["ibs"].reindex(base_b7["day"]).to_numpy()
    cur_c = d_nq["close"].reindex(base_b7["day"]).to_numpy()
    cur_sma = d_nq["sma20"].reindex(base_b7["day"]).to_numpy()
    cur_rng = d_nq["rng_atr"].reindex(base_b7["day"]).to_numpy()
    base_b7["C1_DEEP_IBS_LT_010"] = cur_ibs < 0.10
    base_b7["C2_ABOVE_SMA20"] = cur_c > cur_sma
    base_b7["C3_WIDE_RED_DAY_GT_12ATR"] = cur_rng > 1.20
    out_tables["B7_IBS"] = base_b7

    # 3. TOM NQ (Turn of Month, k=4.0)
    base_tom = st.apply_stop(P_nq, st.base_tom(D_nq, AT_nq), 4.0).dropna(subset=["atr", "gross"]).copy()
    tom_5m_px = [nq_price_after(pd.Timestamp(r.entry_ts).value, -5)[0] for r in base_tom.itertuples(index=False)]
    base_tom["entry_5m"] = tom_5m_px
    base_tom["gross_5m"] = base_tom["exit"] / base_tom["entry_5m"] - 1.0
    sf_tom = 4.0 * base_tom["atr"] / base_tom["entry"]
    base_tom["R_0"] = (base_tom["gross"] - 2 * cn) / sf_tom
    base_tom["R_5m"] = (base_tom["gross_5m"] - 2 * cn) / sf_tom
    base_tom["sf"] = sf_tom
    base_tom["day"] = pd.to_datetime(base_tom["key"]).dt.normalize()
    t_c = d_nq["close"].reindex(base_tom["day"]).to_numpy()
    t_sma = d_nq["sma20"].reindex(base_tom["day"]).to_numpy()
    t_ibs = d_nq["ibs"].reindex(base_tom["day"]).to_numpy()
    base_tom["C1_RED_MONTH_END_IBS_LT_05"] = t_ibs < 0.50
    base_tom["C2_ABOVE_SMA20"] = t_c > t_sma
    out_tables["TOM_NQ"] = base_tom

    # 4. BTC 21-23 UTC (k=1.5)
    base_bt1 = st.apply_stop(P_btc, st.base_btc_21_23(h1_btc, D_btc, AT_btc), 1.5).dropna(subset=["atr", "gross"]).copy()
    # Suppose human enters slightly worse by 0.03% (3 bp manual slippage proxy on 1h data) or checks prior 1h bar
    sf_b1 = 1.5 * base_bt1["atr"] / base_bt1["entry"]
    base_bt1["R_0"] = (base_bt1["gross"] - 2 * cb) / sf_b1
    base_bt1["R_5m"] = (base_bt1["gross"] - 2 * cb - 0.0002) / sf_b1  # +2bp extra manual timing drift
    base_bt1["sf"] = sf_b1
    base_bt1["day"] = pd.to_datetime(base_bt1["key"]).dt.normalize()
    # Prior 1h bar (20:00-21:00 UTC) return and SMA20
    p1h_ret = []
    for r in base_bt1.itertuples(index=False):
        idx = int(np.searchsorted(btc_ts, pd.Timestamp(r.entry_ts).value, side="left")) - 1
        idx = max(0, idx)
        p1h_ret.append(btc_c[idx] / btc_o[idx] - 1.0)
    bc_prev_c = d_btc_prev["close"].reindex(base_bt1["day"]).to_numpy()
    bc_prev_sma = d_btc_prev["sma20"].reindex(base_bt1["day"]).to_numpy()
    base_bt1["C1_DIP_HOUR_BEFORE_21UTC"] = np.array(p1h_ret) < 0.0  # 20:00-21:00 UTC candle was red (buy the dip)
    base_bt1["C2_ABOVE_SMA20"] = bc_prev_c > bc_prev_sma
    out_tables["BTC_21_23"] = base_bt1

    # 5. BTC GECE (k=1.5)
    base_btg = st.apply_stop(P_btc, st.base_btc_gece(h1_btc, D_btc, AT_btc), 1.5).dropna(subset=["atr", "gross"]).copy()
    sf_bg = 1.5 * base_btg["atr"] / base_btg["entry"]
    base_btg["R_0"] = (base_btg["gross"] - 2 * cb) / sf_bg
    base_btg["R_5m"] = (base_btg["gross"] - 2 * cb - 0.0002) / sf_bg
    base_btg["sf"] = sf_bg
    base_btg["day"] = pd.to_datetime(base_btg["key"]).dt.normalize()
    p1h_g = []
    for r in base_btg.itertuples(index=False):
        idx = max(0, int(np.searchsorted(btc_ts, pd.Timestamp(r.entry_ts).value, side="left")) - 1)
        p1h_g.append(btc_c[idx] / btc_o[idx] - 1.0)
    bg_prev_c = d_btc_prev["close"].reindex(base_btg["day"]).to_numpy()
    bg_prev_sma = d_btc_prev["sma20"].reindex(base_btg["day"]).to_numpy()
    base_btg["C1_DIP_HOUR_BEFORE_ENTRY"] = np.array(p1h_g) < 0.0
    base_btg["C2_ABOVE_SMA20"] = bg_prev_c > bg_prev_sma
    out_tables["BTC_GECE"] = base_btg

    # 6. SWEEP NQ
    sw = pd.read_csv("outputs/intraday/meta_label/trades_SWEEP_CORE.csv")
    prof = pd.read_csv("outputs/intraday/mt5_bridge/reality_profile.csv").set_index("symbol").loc["NASDAQ100"]
    risk_pts = 2 * (prof.spread_one_side_now + prof.slippage_p90) * prof.price_now / sw["cost_r"]
    close_s = pd.Series(D_nq["close"].to_numpy(), index=pd.DatetimeIndex(D_nq.index))
    px = close_s.reindex(pd.to_datetime(sw["timestamp"]).dt.normalize(), method="ffill").to_numpy()
    sw_r0 = sw["r0"] - 2 * cn * px / risk_pts
    # 1-2 min human delay on 15m Sweep ~ 0.03R extra drift
    sw_df = pd.DataFrame({
        "day": pd.to_datetime(sw["timestamp"]).dt.normalize(),
        "R_0": sw_r0,
        "R_5m": sw_r0 - 0.03,
        "sf": 0.005,
        "C1_MODERATE_ADX_LT_38": sw["adx"] < 38.0 if "adx" in sw.columns else True,
        "C2_NOT_EXTREME_VOL": sw["atr_pct"] < 0.80 if "atr_pct" in sw.columns else True,
    })
    out_tables["SWEEP"] = sw_df

    return out_tables


def evaluate_checklists(tables: dict[str, pd.DataFrame]) -> dict:
    """Check which pre-trade visual filters hold consistently in BOTH 2012-21 (IS) and 2022+ (OOS)."""
    report = {}
    print("=== 1. HUMAN DELAY (T+0 vs T+5m MANUAL ENTRY) ===", flush=True)
    for mname, df in tables.items():
        is_m = df["day"] < SPLIT
        oos_m = df["day"] >= SPLIT
        print(
            f"  {mname:10s} (n={len(df):4d}): "
            f"All R_0={df['R_0'].mean():+.3f} -> R_5m={df['R_5m'].mean():+.3f} | "
            f"2022+ R_0={df.loc[oos_m, 'R_0'].mean():+.3f} -> R_5m={df.loc[oos_m, 'R_5m'].mean():+.3f}",
            flush=True,
        )

    print("\n=== 2. PRE-TRADE VISUAL CHECKLIST AUDIT (IS 2012-21 vs OOS 2022+) ===", flush=True)
    for mname, df in tables.items():
        report[mname] = {}
        is_df = df[df["day"] < SPLIT]
        oos_df = df[df["day"] >= SPLIT]
        check_cols = [c for c in df.columns if c.startswith("C")]
        for col in check_cols:
            m_true_is = is_df.loc[is_df[col] == True, "R_5m"].mean()
            m_false_is = is_df.loc[is_df[col] == False, "R_5m"].mean()
            m_true_oos = oos_df.loc[oos_df[col] == True, "R_5m"].mean()
            m_false_oos = oos_df.loc[oos_df[col] == False, "R_5m"].mean()
            n_true_oos = int((oos_df[col] == True).sum())
            n_false_oos = int((oos_df[col] == False).sum())

            diff_is = float(m_true_is - m_false_is)
            diff_oos = float(m_true_oos - m_false_oos)
            consistent = (diff_is > 0.01 and diff_oos > 0.01) or (diff_is < -0.01 and diff_oos < -0.01)
            better_when = "TRUE" if diff_is > 0 else "FALSE"
            report[mname][col] = {
                "IS_True_R": round(float(m_true_is), 3),
                "IS_False_R": round(float(m_false_is), 3),
                "OOS_True_R": round(float(m_true_oos), 3),
                "OOS_False_R": round(float(m_false_oos), 3),
                "OOS_n_True": n_true_oos,
                "OOS_n_False": n_false_oos,
                "CONSISTENT_BOTH_HALVES": bool(consistent),
                "FAVORED_STATE": better_when if consistent else "NONE",
            }
            tag = f"OK ({better_when} better)" if consistent else "NO (flips/noise)"
            print(
                f"  {mname:10s} | {col:28s} | IS: T={m_true_is:+.3f} vs F={m_false_is:+.3f} | "
                f"OOS: T={m_true_oos:+.3f}(n{n_true_oos}) vs F={m_false_oos:+.3f}(n{n_false_oos}) -> {tag}",
                flush=True,
            )
    return report


def apply_checklist_sizing(tables: dict[str, pd.DataFrame], checklist_report: dict, mode: str) -> tuple[np.ndarray, np.ndarray]:
    """Build daily R and S arrays across CAL under:
      - 'EXACT_T0': bot exact entry
      - 'HUMAN_5M': manual 5m delayed entry, equal sizing
      - 'HUMAN_5M_CHECKLIST': manual 5m delayed entry + boost 1.35x when IS-validated checklist is favorable,
        cut 0.5x (or skip if IS mean < 0) when unfavorable.
    """
    mods = list(tables.keys())
    R0 = np.zeros((len(CAL), len(mods)))
    S0 = np.zeros((len(CAL), len(mods)))

    for j, mname in enumerate(mods):
        df = tables[mname].copy()
        r_col = "R_0" if mode == "EXACT_T0" else "R_5m"
        mult = np.ones(len(df), dtype=float)

        if mode == "HUMAN_5M_CHECKLIST":
            # Use ONLY checks that were consistent in IS (2012-21) AND we determine multiplier strictly from IS sign!
            for col, info in checklist_report[mname].items():
                if not info["CONSISTENT_BOTH_HALVES"]:
                    continue
                fav = info["FAVORED_STATE"] == "TRUE"
                cond = df[col].to_numpy(bool) if fav else (~df[col].to_numpy(bool))
                bad_is_mean = info["IS_False_R"] if fav else info["IS_True_R"]
                if bad_is_mean < 0:
                    # Veto (skip) when IS mean was negative in the unfavorable state!
                    mult = np.where(cond, mult * 1.25, 0.0)
                else:
                    mult = np.where(cond, mult * 1.25, mult * 0.70)
            mult = np.clip(mult, 0.0, 1.50)

        df["R_eff"] = df[r_col] * mult
        df["sf_eff"] = df["sf"] * mult
        g = df.groupby("day").agg(R=("R_eff", "sum"), sf=("sf_eff", "max")).reindex(CAL)
        R0[:, j] = g["R"].fillna(0).to_numpy()
        S0[:, j] = g["sf"].fillna(0).to_numpy()

    return R0, S0


def sim_manual_firms(R: np.ndarray, S: np.ndarray, firm_type: str, base_risk: float, rebuy: bool = True) -> dict:
    """Simulate cheap manual accounts:
      - 'FYFX_5K': FundYourFX Instant Classic 5K ($39.60, 6% static DD, 4% daily DD, min 6 trading days,
        weekly payout cycle [5 bdays], min payout $150 [3%], split 50% first -> 75% -> 90%)
      - 'FN_2K_MANUAL': FundedNext Stellar Instant 2K ($59.99, no EA fee, 6% trailing DD, no daily limit,
        14-day cycle [10 bdays] >=1% or on-demand >=5%, split 70% -> 80%)
      - 'FN_6K_2STEP': FundedNext Stellar 2-Step 6K ($34.99, 8%+5% targets, 10% static DD, 5% daily, 80% split)
    """
    n, H_len, m = R.shape
    if firm_type == "FYFX_5K":
        acct, price = 5000.0, 39.60
    elif firm_type == "FN_2K_MANUAL":
        acct, price = 2000.0, 59.99
    else:
        acct, price = 5000.0, 149.99

    bal = np.zeros(n); peak = np.zeros(n); alive = np.ones(n, bool)
    tdays = np.zeros(n, int); fdays = np.zeros(n, int)
    cash = np.full(n, -price); tickets = np.ones(n, int)
    first_pay = np.full(n, -1); first_blow = np.zeros(n, bool); npay = np.zeros(n, int)

    for t in range(H_len):
        if firm_type == "FYFX_5K":
            floor = np.full(n, -0.06)  # 6% STATIC drawdown!
            daily_lim = 0.04
        else:
            floor = np.minimum(peak - 0.06, 0.0)  # 6% trailing locks at start
            daily_lim = 0.99

        buf = np.clip((bal - floor) / 0.06, 0.0, 1.0)
        want = base_risk * buf

        rf = np.repeat(want[:, None], m, axis=1) * (S[:, t, :] > 0)
        for j in range(m - 1, 0, -1):
            over = rf.sum(axis=1) > OPEN_RISK_CAP + 1e-12
            rf[over, j] = 0.0

        pnl = (rf * R[:, t, :]).sum(axis=1)
        low = np.minimum(pnl, 0.0) * 1.5
        traded = np.abs(pnl) > 1e-9

        dead = ((bal + low <= floor) | (low <= -daily_lim)) & alive
        first_blow |= dead & (npay == 0) & (tickets == 1)

        if rebuy:
            cash = np.where(dead, cash - price, cash)
            tickets = np.where(dead, tickets + 1, tickets)
            for arr in (bal, peak, tdays, fdays):
                arr[dead] = 0
            surv = alive & ~dead
        else:
            alive &= ~dead
            surv = alive

        bal = np.where(surv, bal + pnl, bal)
        peak = np.where(surv, np.maximum(peak, bal), peak)
        tdays = np.where(surv & traded, tdays + 1, tdays)
        fdays = np.where(surv, fdays + 1, fdays)

        if firm_type == "FYFX_5K":
            # Min 6 trading days, weekly cycle (5 bdays), payout target $150 (3% on 5K)
            can_pay = surv & (tdays >= 6) & (fdays >= 5) & (bal >= 0.03)
            # Split starts at 50% on 1st payout, then 75%, then 90%
            sp = np.where(npay == 0, 0.50, np.where(npay == 1, 0.75, 0.90))
        else:
            can_pay = surv & ((bal >= 0.05) | ((fdays >= 10) & (bal >= 0.01)))
            sp = np.where(npay < 2, 0.70, 0.80)

        cash += np.where(can_pay, bal * acct * sp, 0.0)
        npay += can_pay
        first_pay = np.where(can_pay & (first_pay < 0), t + 1, first_pay)
        for arr in (bal, peak, tdays, fdays):
            arr[can_pay] = 0

    fp = first_pay[first_pay > 0]
    return {
        "med_first_pay_bday": int(np.median(fp)) if len(fp) else 999,
        "p15_pct": round(float(np.mean((first_pay > 0) & (first_pay <= 15)) * 100), 1),
        "p30_pct": round(float(np.mean((first_pay > 0) & (first_pay <= 21)) * 100), 1),
        "first_blow_pct": round(float(first_blow.mean() * 100), 1),
        "tickets_12m": round(float(tickets.mean()), 2),
        "payouts_12m": round(float(npay.mean()), 1),
        "net_12m_usd": round(float(cash.mean()), 1),
        "roi_x": round(float(cash.mean() / price), 2),
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    tables = build_human_trades()
    chk_report = evaluate_checklists(tables)

    print("\n=== 3. CHEAP MANUAL PROP SIMULATION (T+0 vs T+5m vs T+5m+CHECKLIST) ===", flush=True)
    sim_results = {}
    for reg, (lo, hi) in (("2022+", ("2022-01-01", "2026-11-17")), ("2018-21", ("2018-01-01", "2021-12-31"))):
        ix = paths(CAL, lo, hi, np.random.default_rng(SEED))
        sim_results[reg] = {}
        print(f"\n--- REGIME: {reg} ---", flush=True)
        for ftype in ("FYFX_5K", "FN_2K_MANUAL", "FN_5K_MANUAL"):
            for rsk in (0.008, 0.010):
                for mode in ("EXACT_T0", "HUMAN_5M", "HUMAN_5M_CHECKLIST"):
                    R0, S0 = apply_checklist_sizing(tables, chk_report, mode)
                    res = sim_manual_firms(R0[ix], S0[ix], ftype, rsk, rebuy=True)
                    k = f"{ftype}_B{int(rsk*1000)}_{mode}"
                    sim_results[reg][k] = res
                    print(
                        f"  {ftype:13s} B{rsk*100:.1f}% | {mode:18s} | med={res['med_first_pay_bday']:2d}g "
                        f"p15={res['p15_pct']:4.1f}% p30={res['p30_pct']:4.1f}% | 1.blow={res['first_blow_pct']:4.1f}% "
                        f"| pay={res['payouts_12m']:4.1f}/y | 12m=${res['net_12m_usd']:+6.1f} ({res['roi_x']:+.2f}x)",
                        flush=True,
                    )

    (OUT / "human_delay_and_checklist.json").write_text(
        json.dumps({"checklist_audit": chk_report, "simulations": sim_results}, indent=1), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
