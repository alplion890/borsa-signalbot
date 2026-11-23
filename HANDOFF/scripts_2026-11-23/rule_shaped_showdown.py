"""Rule-Shaped Prop System Showdown:
  Motor 1 ('Consistency Grinder' - left-skewed TP-clipped high-WR rules for 15-20% consistency firms)
  vs
  Motor 2 ('Uncapped Sprinter' - right-skewed full-tail rules with aggressive/sprint sizing for FN Stellar Instant)
  + Zero-Edge geometry controls.

Spec: docs/superpowers/specs/2026-11-23-rule-shaped-prop-system-design.md
Run from strategy-lab with vectorbt-lab venv:
  python ../HANDOFF/scripts_2026-11-23/rule_shaped_showdown.py
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
from intraday.ema12_first5m_14y import trades as ema12_trades  # noqa: E402
from intraday.history_fetch import load_history  # noqa: E402
from intraday.seffaf_adaylari import load_btc_1h, run_b2  # noqa: E402
from cheap_sizing import OPEN_RISK_CAP, SEED, cost_of, paths  # noqa: E402

OUT = Path("outputs/intraday/futures_round5")
CAL = pd.bdate_range("2013-01-01", "2026-11-17")


def apply_stop_and_tp(path: st.Path5, tr: pd.DataFrame, k_sl: float, tp_r: float | None) -> pd.DataFrame:
    """True bar-by-bar check along Path5 for both stop (k_sl * ATR) and target (tp_r * k_sl * ATR).
    Honest intra-bar ordering: stop checked before target on the same bar.
    """
    exits, reasons = [], []
    for row in tr.itertuples(index=False):
        sl_slice = path.span(row.entry_ts, row.exit_ts)
        o, h, l = path.o[sl_slice], path.h[sl_slice], path.l[sl_slice]
        d = int(row.direction)
        risk_pts = k_sl * row.atr
        stop_px = row.entry - d * risk_pts
        tp_px = (row.entry + d * tp_r * risk_pts) if tp_r is not None else None

        px_out = float(row.exit)
        rsn = "time_exit"
        if len(o) > 0:
            if d == 1:
                hit_s = np.flatnonzero(l <= stop_px)
                hit_t = np.flatnonzero(h >= tp_px) if tp_px is not None else np.empty(0, int)
            else:
                hit_s = np.flatnonzero(h >= stop_px)
                hit_t = np.flatnonzero(l <= tp_px) if tp_px is not None else np.empty(0, int)
            si = int(hit_s[0]) if len(hit_s) else 10**9
            ti = int(hit_t[0]) if len(hit_t) else 10**9
            if si <= ti and si < 10**9:
                px_out = float(min(o[si], stop_px)) if d == 1 else float(max(o[si], stop_px))
                rsn = "stop"
            elif ti < si and ti < 10**9:
                px_out = float(max(o[ti], tp_px)) if d == 1 else float(min(o[ti], tp_px))
                rsn = "tp"
        exits.append(px_out)
        reasons.append(rsn)

    out = tr.copy()
    out["exit"] = exits
    out["reason"] = reasons
    out["gross"] = out["direction"] * (out["exit"] / out["entry"] - 1.0)
    return out


def build_variant_matrices() -> dict[str, tuple[np.ndarray, np.ndarray, dict]]:
    """Build (R_matrix, S_matrix, stats) across CAL for each TP-clip profile."""
    print("Loading price paths & building TP-clipped variants...", flush=True)
    cn, cb = cost_of("NASDAQ100", 1.0), cost_of("BTCUSDT", 1.0)
    P_nq, D_nq, AT_nq = st.nq_context()
    h1_btc = load_btc_1h()
    P_btc, D_btc, AT_btc = st.btc_context()

    base_nb = st.base_nb(D_nq, AT_nq).dropna(subset=["atr"])
    base_tom = st.base_tom(D_nq, AT_nq).dropna(subset=["atr"])
    base_b7 = st.b7_trades(P_nq, D_nq, AT_nq, None).dropna(subset=["atr"])
    base_bt1 = st.base_btc_21_23(h1_btc, D_btc, AT_btc).dropna(subset=["atr"])
    base_btg = st.base_btc_gece(h1_btc, D_btc, AT_btc).dropna(subset=["atr"])

    # Sweep trades
    sw = pd.read_csv("outputs/intraday/meta_label/trades_SWEEP_CORE.csv")
    prof = pd.read_csv("outputs/intraday/mt5_bridge/reality_profile.csv").set_index("symbol").loc["NASDAQ100"]
    risk_pts = 2 * (prof.spread_one_side_now + prof.slippage_p90) * prof.price_now / sw["cost_r"]
    close_s = pd.Series(D_nq["close"].to_numpy(), index=pd.DatetimeIndex(D_nq.index))
    px = close_s.reindex(pd.to_datetime(sw["timestamp"]).dt.normalize(), method="ffill").to_numpy()
    sw_cost_r = 2 * cn * px / risk_pts
    sw_day = pd.to_datetime(sw["timestamp"]).dt.normalize()

    # EMA12 trades (high frequency intraday candidate)
    nq5 = load_history("NASDAQ100", "5m", start_year=2012)
    em_t = ema12_trades(nq5[["open", "high", "low", "close"]])
    em_cost_r = 2 * cn * em_t["entry"] / em_t["risk"]
    em_day = pd.to_datetime(em_t["date"])

    # B2 BTC Donchian
    _, b2_df = run_b2()
    b2_sub = b2_df[b2_df["total_weight"] > 0].copy()

    variants = {}
    for label, tp_r, include_ema in (
        ("UNCAPPED_FULL", None, False),
        ("CLIP_1.0R", 1.00, False),
        ("CLIP_0.75R", 0.75, False),
        ("CLIP_0.50R", 0.50, False),
        ("CLIP_0.35R", 0.35, False),
        ("CLIP_0.50R_PLUS_EMA12", 0.50, True),
    ):
        mod_frames = []

        # 1. Sweep (clipped if tp_r set: if r0 >= tp_r, cap gross R at tp_r)
        if tp_r is None:
            sw_r = sw["r0"] - sw_cost_r
        else:
            # Honest approximation: any Sweep trade that finished >= tp_r hit tp_r
            sw_r = np.where(sw["r0"] >= tp_r, tp_r, sw["r0"]) - sw_cost_r
        mod_frames.append(("SWEEP", pd.DataFrame(dict(day=sw_day, R=sw_r, sf=0.005))))

        # 2. NB (k_sl = 1.0)
        nb_c = apply_stop_and_tp(P_nq, base_nb, 1.0, tp_r)
        sf_nb = 1.0 * nb_c["atr"] / nb_c["entry"]
        mod_frames.append(("NB", pd.DataFrame(dict(day=pd.to_datetime(nb_c["key"]).dt.normalize(), R=(nb_c["gross"] - 2 * cn) / sf_nb, sf=sf_nb))))

        # 3. BTC 21-23 (k_sl = 1.5)
        bt1_c = apply_stop_and_tp(P_btc, base_bt1, 1.5, tp_r)
        sf_b1 = 1.5 * bt1_c["atr"] / bt1_c["entry"]
        mod_frames.append(("BTC_21_23", pd.DataFrame(dict(day=pd.to_datetime(bt1_c["key"]).dt.normalize(), R=(bt1_c["gross"] - 2 * cb) / sf_b1, sf=sf_b1))))

        # 4. B7 IBS NQ (k_sl = 2.0 when clipped, 4.0 when uncapped)
        k_b7 = 4.0 if tp_r is None else 2.0
        b7_c = apply_stop_and_tp(P_nq, base_b7, k_b7, tp_r)
        sf_b7 = k_b7 * b7_c["atr"] / b7_c["entry"]
        mod_frames.append(("B7_IBS", pd.DataFrame(dict(day=pd.to_datetime(b7_c["key"]).dt.normalize(), R=(b7_c["gross"] - 2 * cn) / sf_b7, sf=sf_b7))))

        # 5. BTC Gece (k_sl = 1.5)
        btg_c = apply_stop_and_tp(P_btc, base_btg, 1.5, tp_r)
        sf_bg = 1.5 * btg_c["atr"] / btg_c["entry"]
        mod_frames.append(("BTC_GECE", pd.DataFrame(dict(day=pd.to_datetime(btg_c["key"]).dt.normalize(), R=(btg_c["gross"] - 2 * cb) / sf_bg, sf=sf_bg))))

        # 6. TOM NQ (k_sl = 2.0 when clipped, 4.0 when uncapped)
        k_tom = 4.0 if tp_r is None else 2.0
        tom_c = apply_stop_and_tp(P_nq, base_tom, k_tom, tp_r)
        sf_tom = k_tom * tom_c["atr"] / tom_c["entry"]
        mod_frames.append(("TOM_NQ", pd.DataFrame(dict(day=pd.to_datetime(tom_c["key"]).dt.normalize(), R=(tom_c["gross"] - 2 * cn) / sf_tom, sf=sf_tom))))

        # 7. B2 BTC Donchian (only in uncapped or capped at daily +tp_r)
        b2_r = b2_sub["net_central"] * 0.5 / 0.005
        if tp_r is not None:
            b2_r = np.clip(b2_r, -1.0, tp_r)
        mod_frames.append(("B2_DON", pd.DataFrame(dict(day=pd.to_datetime(b2_sub["date"]).dt.normalize(), R=b2_r, sf=0.005))))

        # 8. Optional EMA12 clipped
        if include_ema:
            em_r = np.where(em_t["r_gross"] >= tp_r, tp_r, em_t["r_gross"]) - em_cost_r
            mod_frames.append(("EMA12", pd.DataFrame(dict(day=em_day, R=em_r, sf=em_t["risk"] / em_t["entry"]))))

        n_m = len(mod_frames)
        R0 = np.zeros((len(CAL), n_m))
        S0 = np.zeros((len(CAL), n_m))
        all_r_22 = []
        for j, (mname, df_m) in enumerate(mod_frames):
            sub22 = df_m[df_m["day"] >= "2022-01-01"]["R"]
            all_r_22.extend(sub22.tolist())
            g = df_m.groupby("day").agg(R=("R", "sum"), sf=("sf", "max")).reindex(CAL)
            R0[:, j] = g["R"].fillna(0).to_numpy()
            S0[:, j] = g["sf"].fillna(0).to_numpy()

        arr22 = np.array(all_r_22)
        v_stats = {
            "trades_2022+": int(len(arr22)),
            "win_rate_2022+_pct": round(float((arr22 > 0).mean() * 100), 1),
            "mean_R_2022+": round(float(arr22.mean()), 3),
            "p95_R_2022+": round(float(np.quantile(arr22, 0.95)), 3),
        }
        variants[label] = (R0, S0, v_stats)
        print(f"  {label:24s}: WR={v_stats['win_rate_2022+_pct']:4.1f}% | mean_R={v_stats['mean_R_2022+']:+.3f} | p95_R={v_stats['p95_R_2022+']:+.2f}", flush=True)

    return variants


def sim_ticket_economy(
    R: np.ndarray,
    S: np.ndarray,
    firm: dict,
    sizing_mode: str,
    base_risk: float,
    daily_cap: float | None = None,
    rebuy: bool = True,
) -> dict:
    """Simulate 300 paths x 260 business days under ticket/rebuy or single-ticket rules."""
    n, H_len, m = R.shape
    acct = firm["size"]
    price = firm["price"]
    trail = firm["trail"]
    daily_lim = firm["daily"]
    cons = firm["cons"]
    mindays = firm["mindays"]
    minday_pct = firm["minday_pct"]
    min_pay = firm["min_pay"]
    split = firm["split"]
    fn_cycle = firm.get("fn_cycle", False)

    bal = np.zeros(n); peak = np.zeros(n); alive = np.ones(n, bool)
    best = np.zeros(n); qd = np.zeros(n, int); fdays = np.zeros(n, int)
    cash = np.full(n, -price)
    tickets = np.ones(n, int)
    first_pay_day = np.full(n, -1)
    first_ticket_blew = np.zeros(n, bool)
    npay = np.zeros(n, int)

    for t in range(H_len):
        floor = np.minimum(peak - trail, 0.0) if not firm.get("lock_at_start_after_pay") else np.minimum(peak - trail, 0.0)
        buf = np.clip((bal - floor) / trail, 0.0, 1.0)

        if sizing_mode == "FIXED":
            want = np.full(n, base_risk)
        elif sizing_mode == "BUFFER":
            want = base_risk * buf
        elif sizing_mode == "SPRINT_LOCK":
            # Aggressive when far from payout, lock down when close to payout
            want = np.where(bal < min_pay * 0.65, base_risk * 1.35, base_risk * 0.55)
        elif sizing_mode == "CONSISTENCY_PACE":
            # Target daily gain <= cons * min_pay (so best day never exceeds consistency threshold!)
            target_day = (cons * min_pay * 0.92) if cons else base_risk
            want = np.minimum(base_risk, target_day) * np.ones(n)
        else:
            want = np.full(n, base_risk)

        rf = np.repeat(want[:, None], m, axis=1) * (S[:, t, :] > 0)
        for j in range(m - 1, 0, -1):
            over = rf.sum(axis=1) > OPEN_RISK_CAP + 1e-12
            rf[over, j] = 0.0

        pnl = (rf * R[:, t, :]).sum(axis=1)
        if daily_cap is not None:
            pnl = np.minimum(pnl, daily_cap)
        low = np.minimum(pnl, 0.0) * 1.5

        dead = ((bal + low <= floor) | (low <= -daily_lim)) & alive
        first_ticket_blew |= dead & (npay == 0) & (tickets == 1)

        if rebuy:
            # Instant rebuy on next day: pay another ticket, reset account
            cash = np.where(dead, cash - price, cash)
            tickets = np.where(dead, tickets + 1, tickets)
            bal = np.where(dead, 0.0, bal)
            peak = np.where(dead, 0.0, peak)
            best = np.where(dead, 0.0, best)
            qd = np.where(dead, 0, qd)
            fdays = np.where(dead, 0, fdays)
            surv = alive & ~dead
        else:
            alive &= ~dead
            surv = alive

        bal = np.where(surv, bal + pnl, bal)
        peak = np.where(surv, np.maximum(peak, bal), peak)
        best = np.where(surv, np.maximum(best, pnl), best)
        qd = np.where(surv, qd + (pnl >= minday_pct), qd)
        fdays = np.where(surv, fdays + 1, fdays)

        if fn_cycle:
            # FundedNext Stellar Instant: on-demand at >=5%, or 14-day cycle (~10 bdays) at >=1%
            can_pay = surv & ((bal >= 0.05) | ((fdays >= 10) & (bal >= 0.01)))
        else:
            base_ok = surv & (bal >= min_pay) & (qd >= mindays)
            can_pay = base_ok & ((best <= cons * bal + 1e-9) if cons else True)

        pay_usd = np.where(can_pay, bal * acct * split, 0.0)
        cash += pay_usd
        npay += can_pay
        first_pay_day = np.where(can_pay & (first_pay_day < 0), t + 1, first_pay_day)

        # Reset after payout
        for arr in (bal, peak, best):
            arr[can_pay] = 0.0
        qd[can_pay] = 0
        fdays[can_pay] = 0

    fp = first_pay_day[first_pay_day > 0]
    return {
        "med_first_pay_bday": int(np.median(fp)) if len(fp) else 999,
        "p15_pct": round(float(np.mean((first_pay_day > 0) & (first_pay_day <= 15)) * 100), 1),
        "p30_pct": round(float(np.mean((first_pay_day > 0) & (first_pay_day <= 21)) * 100), 1),
        "p60_pct": round(float(np.mean((first_pay_day > 0) & (first_pay_day <= 42)) * 100), 1),
        "first_ticket_blow_pct": round(float(first_ticket_blew.mean() * 100), 1),
        "avg_tickets_12m": round(float(tickets.mean()), 2),
        "avg_payouts_12m": round(float(npay.mean()), 1),
        "net_12m_mean_usd": round(float(cash.mean()), 1),
        "net_12m_med_usd": round(float(np.median(cash)), 1),
        "roi_per_ticket_price": round(float(cash.mean() / price), 2),
    }


FIRMS_SHOWDOWN = {
    "MAVEN_5K ($18, %20 Cons, %3 DD)": dict(
        size=5000, price=18.05, trail=0.03, daily=0.01, cons=0.20, mindays=0, minday_pct=0.0, min_pay=0.03, split=0.80, fn_cycle=False
    ),
    "FTUK_5K ($40, %20 Cons, %6 DD)": dict(
        size=5000, price=40.00, trail=0.06, daily=0.03, cons=0.20, mindays=0, minday_pct=0.0, min_pay=0.03, split=0.80, fn_cycle=False
    ),
    "FTM_5K ($45, %15 Cons+5g, %6 DD)": dict(
        size=5000, price=45.00, trail=0.06, daily=0.03, cons=0.15, mindays=5, minday_pct=0.005, min_pay=0.035, split=0.80, fn_cycle=False
    ),
    "FN_STELLAR_2K ($60, Kuralsiz, %6 DD)": dict(
        size=2000, price=59.99, trail=0.06, daily=0.99, cons=None, mindays=0, minday_pct=0.0, min_pay=0.01, split=0.70, fn_cycle=True
    ),
    "FN_STELLAR_5K ($150, Kuralsiz, %6 DD)": dict(
        size=5000, price=149.99, trail=0.06, daily=0.99, cons=None, mindays=0, minday_pct=0.0, min_pay=0.01, split=0.70, fn_cycle=True
    ),
}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    variants = build_variant_matrices()
    ix22 = paths(CAL, "2022-01-01", "2026-11-17", np.random.default_rng(SEED))
    w22 = (CAL >= "2022-01-01") & (CAL <= "2026-11-17")

    results = []
    for fname, fcfg in FIRMS_SHOWDOWN.items():
        has_cons = fcfg["cons"] is not None
        # Test candidate configurations
        configs = [
            ("UNCAPPED_FULL", "BUFFER", 0.005, None),
            ("UNCAPPED_FULL", "FIXED", 0.010, None),
            ("UNCAPPED_FULL", "SPRINT_LOCK", 0.012, None),
            ("CLIP_0.75R", "FIXED", 0.008, 0.006 if has_cons else None),
            ("CLIP_0.50R", "FIXED", 0.008, 0.0058 if has_cons else None),
            ("CLIP_0.35R", "FIXED", 0.010, 0.0055 if has_cons else None),
            ("CLIP_0.50R_PLUS_EMA12", "FIXED", 0.008, 0.0058 if has_cons else None),
        ]
        for vname, smode, brisk, dcap in configs:
            R0, S0, v_st = variants[vname]
            R_real = R0[ix22]
            S_real = S0[ix22]

            # Demeaned zero-edge inside 2022+
            R0_z = R0.copy()
            for j in range(R0.shape[1]):
                act = w22 & (S0[:, j] > 0)
                if act.sum() > 0:
                    R0_z[:, j] = np.where(S0[:, j] > 0, R0[:, j] - R0[act, j].mean(), 0.0)
            R_zero = R0_z[ix22]

            res_real = sim_ticket_economy(R_real, S_real, fcfg, smode, brisk, dcap, rebuy=True)
            res_zero = sim_ticket_economy(R_zero, S_real, fcfg, smode, brisk, dcap, rebuy=True)

            row = {
                "firm": fname,
                "variant": vname,
                "sizing": f"{smode}_{brisk*100:.1f}%",
                "daily_cap": dcap,
                "WR_22": v_st["win_rate_2022+_pct"],
                **res_real,
                "zero_edge_12m_usd": res_zero["net_12m_mean_usd"],
                "zero_edge_p30_pct": res_zero["p30_pct"],
            }
            results.append(row)

    df = pd.DataFrame(results)
    df.to_csv(OUT / "rule_shaped_showdown.csv", index=False)
    (OUT / "rule_shaped_showdown.json").write_text(json.dumps(results, indent=1), encoding="utf-8")

    pd.set_option("display.width", 240)
    pd.set_option("display.max_columns", 20)
    pd.set_option("display.max_rows", 100)
    for fname in FIRMS_SHOWDOWN:
        print(f"\n==================== {fname} ====================")
        sub = df[df["firm"] == fname].sort_values(["p30_pct", "net_12m_mean_usd"], ascending=False)
        cols = ["variant", "sizing", "daily_cap", "WR_22", "med_first_pay_bday", "p15_pct", "p30_pct", "p60_pct",
                "first_ticket_blow_pct", "avg_tickets_12m", "avg_payouts_12m", "net_12m_mean_usd", "roi_per_ticket_price", "zero_edge_12m_usd"]
        print(sub[cols].to_string(index=False))

    print("\n==================== FN STELLAR 5K ($150) — SIZING CURVE (2022+ vs 2018-21) ====================")
    R0, S0, _ = variants["UNCAPPED_FULL"]
    f5 = FIRMS_SHOWDOWN["FN_STELLAR_5K ($150, Kuralsiz, %6 DD)"]
    for reg, (lo, hi) in (("2022+", ("2022-01-01", "2026-11-17")), ("2018-21", ("2018-01-01", "2021-12-31"))):
        ix = paths(CAL, lo, hi, np.random.default_rng(SEED))
        R_r, S_r = R0[ix], S0[ix]
        w = (CAL >= lo) & (CAL <= hi)
        R0_z = R0.copy()
        for j in range(R0.shape[1]):
            act = w & (S0[:, j] > 0)
            R0_z[:, j] = np.where(S0[:, j] > 0, R0[:, j] - R0[act, j].mean(), 0.0)
        R_z = R0_z[ix]
        print(f"\n--- {reg} ---")
        for mode, rsk in (("BUFFER", 0.005), ("BUFFER", 0.008), ("BUFFER", 0.010), ("BUFFER", 0.012),
                          ("FIXED", 0.005), ("FIXED", 0.008), ("FIXED", 0.010), ("FIXED", 0.012),
                          ("SPRINT_LOCK", 0.010), ("SPRINT_LOCK", 0.012)):
            res = sim_ticket_economy(R_r, S_r, f5, mode, rsk, None, rebuy=True)
            res_s = sim_ticket_economy(R_r, S_r, f5, mode, rsk, None, rebuy=False)
            rz = sim_ticket_economy(R_z, S_r, f5, mode, rsk, None, rebuy=True)
            print(f"  {mode:11s} {rsk*100:4.1f}% | med={res['med_first_pay_bday']:2d}g p15={res['p15_pct']:4.1f}% p30={res['p30_pct']:4.1f}% "
                  f"| 1.bilet_blow={res['first_ticket_blow_pct']:4.1f}% | Rebuy_12m=${res['net_12m_mean_usd']:+6.1f} "
                  f"(bilet={res['avg_tickets_12m']:.2f}x, pay={res['avg_payouts_12m']:.1f}) | TekBilet_12m=${res_s['net_12m_mean_usd']:+6.1f} "
                  f"| Zero_Rebuy=${rz['net_12m_mean_usd']:+6.1f}")


if __name__ == "__main__":
    main()
