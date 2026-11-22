"""Audit all tested candidates under relaxed statistical gates (maintaining honest measured cost),
and simulate fast-payout prop performance (2022+ regime) comparing strict-pass vs relaxed-pass sets.

NO live rule change; exploratory sensitivity audit requested by user.
Run from strategy-lab with vectorbt-lab venv:
  python ../HANDOFF/scripts_2026-11-23/relaxed_fast_payout_audit.py
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
from intraday.seffaf_adaylari import load_btc_1h, run_b2  # noqa: E402
from cheap_sizing import FIRMS, H, NP, OPEN_RISK_CAP, SEED, NQ_PX, cost_of, paths, simulate  # noqa: E402

OUT = Path("outputs/intraday/futures_round5")


def load_json(rel: str) -> dict:
    p = Path("outputs/intraday") / rel
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def audit_candidates() -> list[dict]:
    """Collect all major tested candidates across CFD & Futures rounds and check which gates they pass."""
    rows = []

    def add(name: str, family: str, unit: str, n: int, zero: float, cen: float, pess: float,
            pre22: float, post22: float, ci_bonf_lo: float, se_approx: float | None = None, note: str = "") -> None:
        # Uncorrected 95% CI lower bound approx: if se_approx known, cen - 1.96*se; else from bonf width
        ci95_lo = (cen - 1.96 * se_approx) if se_approx is not None else ci_bonf_lo
        g_strict = (cen > 0 and ci_bonf_lo > 0 and pre22 > 0 and post22 > 0 and pess > 0)
        g_no_bonf = (cen > 0 and ci95_lo > 0 and pre22 > 0 and post22 > 0)
        g_2022_only = (cen > 0 and post22 > 0 and ci95_lo > 0)
        g_2022_pos_any = (post22 > 0 and cen > 0)
        rows.append({
            "name": name, "family": family, "unit": unit, "n": n,
            "zero": round(zero, 3), "central": round(cen, 3), "2x": round(pess, 3),
            "2012-21": round(pre22, 3) if not np.isnan(pre22) else None,
            "2022+": round(post22, 3) if not np.isnan(post22) else None,
            "ci_bonf_lo": round(ci_bonf_lo, 3),
            "ci95_lo_est": round(ci95_lo, 3),
            "G0_STRICT": bool(g_strict),
            "G1_NO_BONF_NO_2X": bool(g_no_bonf),
            "G2_2022_CI95": bool(g_2022_only),
            "G3_2022_MEAN_POS": bool(g_2022_pos_any),
            "note": note,
        })

    # 1. Futures Cost Retest (Round 1)
    r1 = load_json("futures_cost_retest/result.json")
    for k, label, u in (("REF_NB_NQ", "NB NQ (CME)", "bp/d"), ("H1_NB_ES", "NB ES (CME)", "bp/d"), ("H2_EMA12_NQ", "EMA12 5m NQ (CME)", "R")):
        if k in r1:
            v = r1[k]
            c, z, p = v["central"]["eval"], v["zero"]["eval"], v["pessimistic"]["eval"]
            hw = (c["ci_bonf"][1] - c["ci_bonf"][0]) / 2.0
            se = hw / 2.24  # Bonf 2 tests -> z=2.24
            add(label, "Futures R1", u, v["trades"], z["mean"], c["mean"], p["mean"], c["2012-21"], c["2022+"], c["ci_bonf"][0], se)

    # 2. Futures Transfer Retest (Round 2)
    r2 = load_json("futures_transfer_retest/result.json")
    for k, label in (
        ("REF_ibs_NQ", "IBS NQ (CME)"), ("REF_ibs_ES", "IBS ES (CME)"),
        ("REF_turtle_NQ", "Turtle Soup NQ (CME)"), ("oops_NQ", "Williams Oops NQ (CME)"),
        ("oops_ES", "Williams Oops ES (CME)"), ("last30_NQ", "Baltussen Last30 NQ (CME)"),
        ("last30_ES", "Baltussen Last30 ES (CME)"),
    ):
        if k in r2:
            v = r2[k]
            c, z, p = v["central"], v["zero"], v["pessimistic"]
            hw = (c["ci_bp"][1] - c["ci_bp"][0]) / 2.0
            se = hw / 2.50  # Bonf 4 tests -> z=2.50
            add(label, "Futures R2", "bp", c["n"], z["mean_bp"], c["mean_bp"], p["mean_bp"], c["2012-21"], c["2022+"], c["ci_bp"][0], se)

    # 3. Futures Transfer 3 (Round 3)
    r3 = load_json("futures_transfer3/result.json")
    for k, label in (("T1_SWEEP_NQ", "Sweep NQ (CME)"), ("T2_DONCHIAN_GC", "Donchian GC 1h (CME)"), ("T3_SWEEP_RTY", "Sweep RTY (CME)")):
        if k in r3:
            v = r3[k]
            c, z, p = v["central"], v["zero"], v["pessimistic"]
            hw = (c["ci_bonf"][1] - c["ci_bonf"][0]) / 2.0
            se = hw / 2.39  # Bonf 3 tests
            add(label, "Futures R3", "R", c["n"], z["mean_R"], c["mean_R"], p["mean_R"], c["2012-21"], c["2022+"], c["ci_bonf"][0], se)

    # 4. Futures Round 4 (Volume & Carry)
    r4 = load_json("futures_round4/result.json")
    for sym in ("NQ.c.0", "ES.c.0"):
        if sym in r4:
            for rule in ("B1", "B2"):
                v = r4[sym][rule]
                c, z, p = v["central"], v["zero"], v["pessimistic"]
                hw = (c["ci_bonf"][1] - c["ci_bonf"][0]) / 2.0
                se = hw / 2.58  # Bonf 5
                add(f"Vol {rule} {sym[:2]} (CME)", "Futures R4", "bp", c["n"], z["mean"], c["mean"], p["mean"], c["2012-21"], c["2022+"], c["ci_bonf"][0], se)
    if "A1_CARRY" in r4:
        v = r4["A1_CARRY"]
        c, z, p = v["central"], v["zero"], v["pessimistic"]
        hw = (c["ci_bonf"][1] - c["ci_bonf"][0]) / 2.0
        add("Carry 23 Futures (CME)", "Futures R4", "bp/mo", c["n"], z["mean"], c["mean"], p["mean"], c["2012-21"], c["2022+"], c["ci_bonf"][0], hw / 2.58)

    # 5. Futures Round 5 (Opex, Cross-asset, Order Flow)
    r5_oc = load_json("futures_round5/opex_cross_result.json")
    for k, u in (("O1_NQ", "bp"), ("O1_ES", "bp"), ("X1_CL", "bp"), ("X1_ZN", "bp"), ("X1_6E", "bp"), ("X2_CL", "R"), ("X2_ZN", "R"), ("X2_6E", "R")):
        if k in r5_oc:
            v = r5_oc[k]
            c, z, p = v["central"], v["zero"], v["pessimistic"]
            hw = (c["ci_bonf"][1] - c["ci_bonf"][0]) / 2.0
            se = hw / 2.84  # Bonf 11 tests -> z=2.84
            add(f"{k} (CME)", "Futures R5", u, c["n"], z["mean"], c["mean"], p["mean"], c["2012-21"], c["2022+"], c["ci_bonf"][0], se)

    r5_of = load_json("futures_round5/orderflow_result.json")
    for k in ("OF2_STACK", "OF3_DDIV"):
        if k in r5_of and r5_of[k]["n"] > 0:
            v = r5_of[k]
            c, z, p = v["central"], v["zero"], v["pessimistic"]
            hw = (c["ci_bonf_R"][1] - c["ci_bonf_R"][0]) / 2.0
            add(f"{k} NQ (CME)", "OrderFlow R5", "R", v["n"], z["mean_R"], c["mean_R"], p["mean_R"], c["half1_R"], c["half2_R"], c["ci_bonf_R"][0], hw / 2.84)

    # 6. CFD Transparent / Source / Edge5K candidates
    for b_id, label, z_z in (
        ("B7", "B7 IBS NQ (CFD)", 2.77), ("B2", "B2 BTC Donchian (CFD, swap0)", 2.77),
        ("B3", "B3 Gold Breakout H1 (CFD)", 2.77), ("B4", "B4 Gold EMA M30 (CFD)", 2.77),
        ("B5_NQ", "B5 Turtle Soup NQ (CFD)", 2.77), ("B5_XAU", "B5 Turtle Soup XAU (CFD)", 2.77),
        ("B6_NQ", "B6 Oops NQ (CFD)", 2.77),
    ):
        bj = load_json(f"seffaf_adaylari/{b_id}.json")
        if bj and bj.get("central", {}).get("all"):
            c, z, p = bj["central"], bj["zero"], bj["pessimistic"]
            hw = (c["ci_bp"][1] - c["ci_bp"][0]) / 2.0
            add(label, "Seffaf CFD", "bp", c["all"]["n"], z["all"]["mean_bp"], c["all"]["mean_bp"], p["all"]["mean_bp"],
                c["pre2022"]["mean_bp"], c["2022+"]["mean_bp"], c["ci_bp"][0], hw / z_z)

    ka3 = load_json("kaynak_adaylari/A3.json")
    for sym in ("NASDAQ100", "SP500"):
        if sym in ka3:
            v = ka3[sym]
            c, z, p = v["central"], v["zero"], v["pessimistic"]
            hw = (c["ci_bp"][1] - c["ci_bp"][0]) / 2.0
            add(f"A3 TOM+1 {sym} (CFD)", "Kaynak CFD", "bp", c["all"]["n"], z["all"]["mean_bp"], c["all"]["mean_bp"], p["all"]["mean_bp"],
                c["pre2022"]["mean_bp"], c["2022+"]["mean_bp"], c["ci_bp"][0], hw / 2.24)

    ka4 = load_json("kaynak_adaylari/A4.json")
    if ka4 and ka4.get("central", {}).get("all"):
        c, z, p = ka4["central"], ka4["zero"], ka4["pessimistic"]
        hw = (c["ci_bp"][1] - c["ci_bp"][0]) / 2.0
        add("A4 BTC Gece (CFD, swap0)", "Kaynak CFD", "bp", c["all"]["n"], z["all"]["mean_bp"], c["all"]["mean_bp"], p["all"]["mean_bp"],
            c["pre2022"]["mean_bp"], c["2022+"]["mean_bp"], c["ci_bp"][0], hw / 1.96, note="Maven swapla elendi; swap-free'de gecer")

    e5k = load_json("edge5k_adaylari/results.json")
    for k, label in (("C1_SP500", "C1 AySonu Rebal SP500"), ("C1_NASDAQ100", "C1 AySonu Rebal NQ"),
                     ("C2_SP500", "C2 Tatil Oncesi SP500"), ("C2_NASDAQ100", "C2 Tatil Oncesi NQ")):
        if k in e5k and "central" in e5k[k]:
            v = e5k[k]
            c, z, p = v["central"], v["zero"], v["pessimistic"]
            hw = (c["ci_bp"][1] - c["ci_bp"][0]) / 2.0
            add(f"{label} (CFD)", "Edge5K CFD", "bp", c["all"]["n"], z["all"]["mean_bp"], c["all"]["mean_bp"], p["all"]["mean_bp"],
                c["pre2022"]["mean_bp"], c["2022+"]["mean_bp"], c["ci_bp"][0], hw / 2.96)

    # Fintek BTC
    fb = load_json("fintek_btc_fvg_st/result.json")
    if "LONG_PRIMARY" in fb:
        v = fb["LONG_PRIMARY"]
        c, z, p = v["central"], v["zero"], v["pessimistic"]
        add("Fintek BTC FVG+ST Long", "YouTube BTC", "R", v["n"], z["mean_R"], c["mean_R"], p["mean_R"],
            c["year1_R"], c["year2_R"], c["ci95_R"][0], (c["ci95_R"][1] - c["ci95_R"][0]) / 3.92)

    return rows


def build_prop_modules() -> pd.DataFrame:
    """Build daily (day, mod, R, sf) table including both Strict-Pass and Relaxed-Pass candidates."""
    cn, cb, cx = cost_of("NASDAQ100", 1.0), cost_of("BTCUSDT", 1.0), cost_of("XAUUSD", 1.0)
    P, D, AT = st.nq_context()
    rows = []

    # 1. SWEEP (Live, 2022+ strong)
    sw = pd.read_csv("outputs/intraday/meta_label/trades_SWEEP_CORE.csv")
    prof = pd.read_csv("outputs/intraday/mt5_bridge/reality_profile.csv").set_index("symbol").loc["NASDAQ100"]
    risk_pts = 2 * (prof.spread_one_side_now + prof.slippage_p90) * prof.price_now / sw["cost_r"]
    close = pd.Series(D["close"].to_numpy(), index=pd.DatetimeIndex(D.index))
    px = close.reindex(pd.to_datetime(sw["timestamp"]).dt.normalize(), method="ffill").to_numpy()
    sw_r = sw["r0"] - 2 * cn * px / risk_pts
    rows.append(pd.DataFrame(dict(day=pd.to_datetime(sw["timestamp"]).dt.normalize(), mod="SWEEP", R=sw_r, sf=0.005)))

    # 2. NB (Strict pass)
    nb = st.apply_stop(P, st.base_nb(D, AT), 1.0).dropna(subset=["atr", "gross"])
    sf_nb = 1.0 * nb["atr"] / nb["entry"]
    rows.append(pd.DataFrame(dict(day=pd.to_datetime(nb["key"]).dt.normalize(), mod="NB", R=(nb["gross"] - 2 * cn) / sf_nb, sf=sf_nb)))

    # 3. BTC 21-23 (Strict pass)
    h1_btc = load_btc_1h()
    bp, bd, bat = st.btc_context()
    bt = st.apply_stop(bp, st.base_btc_21_23(h1_btc, bd, bat), 1.5).dropna(subset=["atr", "gross"])
    sf_bt = 1.5 * bt["atr"] / bt["entry"]
    rows.append(pd.DataFrame(dict(day=pd.to_datetime(bt["key"]).dt.normalize(), mod="BTC_21_23", R=(bt["gross"] - 2 * cb) / sf_bt, sf=sf_bt)))

    # 4. B7 IBS NQ (Strict pass, k=4 disaster stop for risk sizing)
    b7 = st.b7_trades(P, D, AT, 4.0).dropna(subset=["atr", "gross"])
    sf_b7 = 4.0 * b7["atr"] / b7["entry"]
    rows.append(pd.DataFrame(dict(day=pd.to_datetime(b7["key"]).dt.normalize(), mod="B7_IBS_NQ", R=(b7["gross"] - 2 * cn) / sf_b7, sf=sf_b7)))

    # 5. B2 BTC Donchian (Strict pass, swap 0)
    _, b2_df = run_b2()
    b2_sub = b2_df[b2_df["total_weight"] > 0].copy()
    # Treat daily return at 0.5x scale as R with sf=0.01
    rows.append(pd.DataFrame(dict(day=pd.to_datetime(b2_sub["date"]).dt.normalize(), mod="B2_BTC_DON", R=b2_sub["net_central"] * 0.5 / 0.005, sf=0.005)))

    # --- RELAXED CANDIDATES ---
    # 6. TOM+1 NQ (Relaxed: positive both halves & >base rate, failed CI width due to n=178)
    tom = st.apply_stop(P, st.base_tom(D, AT), 4.0).dropna(subset=["atr", "gross"])
    sf_tom = 4.0 * tom["atr"] / tom["entry"]
    rows.append(pd.DataFrame(dict(day=pd.to_datetime(tom["key"]).dt.normalize(), mod="TOM_NQ", R=(tom["gross"] - 2 * cn) / sf_tom, sf=sf_tom)))

    # 7. A4 BTC Gece (Relaxed: passed stats, rejected on Maven swap; works on swap-free FN)
    bgece = st.apply_stop(bp, st.base_btc_gece(h1_btc, bd, bat), 1.5).dropna(subset=["atr", "gross"])
    sf_bg = 1.5 * bgece["atr"] / bgece["entry"]
    rows.append(pd.DataFrame(dict(day=pd.to_datetime(bgece["key"]).dt.normalize(), mod="BTC_GECE", R=(bgece["gross"] - 2 * cb) / sf_bg, sf=sf_bg)))

    # 8. B3 Gold Breakout H1 (Relaxed 2022+: +161bp in 2022+, failed CI/pre2022)
    b3_tr = pd.read_csv("outputs/intraday/seffaf_adaylari/B3_trades.csv")
    b3_r = (b3_tr["gross"] - 2 * cx) / 0.01  # 1% approximate risk unit
    rows.append(pd.DataFrame(dict(day=pd.to_datetime(b3_tr["entry_time"]).dt.tz_localize(None).dt.normalize(), mod="B3_XAU_H1", R=b3_r, sf=0.008)))

    # 9. EMA12 first 5m NQ (Relaxed 2022+: +0.109R on CME / +0.064R CFD in 2022+, failed pre-2022 & 2x)
    from intraday.ema12_first5m_14y import trades as ema12_trades
    from intraday.history_fetch import load_history
    nq5 = load_history("NASDAQ100", "5m", start_year=2012)
    em_t = ema12_trades(nq5[["open", "high", "low", "close"]])
    em_r = em_t["r_gross"] - 2 * cn * em_t["entry"] / em_t["risk"]
    rows.append(pd.DataFrame(dict(day=pd.to_datetime(em_t["date"]), mod="EMA12_NQ", R=em_r, sf=em_t["risk"] / em_t["entry"])))

    return pd.concat(rows, ignore_index=True)


def sim_portfolio_set(tt: pd.DataFrame, mods: list[str], lo: str, hi: str) -> dict:
    cal = pd.bdate_range("2013-01-01", "2026-11-17")
    R0 = np.zeros((len(cal), len(mods)))
    S0 = np.zeros((len(cal), len(mods)))
    for j, m in enumerate(mods):
        g = tt[tt["mod"] == m].groupby("day").agg(R=("R", "sum"), sf=("sf", "max")).reindex(cal)
        R0[:, j] = g["R"].fillna(0).to_numpy()
        S0[:, j] = g["sf"].fillna(0).to_numpy()

    # Active trades per year in [lo, hi]
    w_cal = (cal >= lo) & (cal <= hi)
    yrs = w_cal.sum() / 252.0
    trades_per_yr = float((S0[w_cal] > 0).sum() / yrs)

    ix = paths(cal, lo, hi, np.random.default_rng(SEED))
    R, S = R0[ix], S0[ix]

    # Fast-payout simulation across I2K ($41.99), S1_6K (1-Step 6K $44.99), S2_6K (2-Step 6K $34.99), L5K (Lite 5K $29.99)
    out = {"trades_per_year": round(trades_per_yr, 1), "trades_per_day": round(trades_per_yr / 252.0, 2)}
    for fn_key, f_base, meth in (
        ("I2K_B05", "I2K", ("B", 0.005)),
        ("I2K_B10", "I2K", ("B", 0.010)),
        ("S1_6K_BT10", "S1_6K", ("BT", 0.010)),
        ("S1_6K_BT15", "S1_6K", ("BT", 0.015)),
        ("S2_6K_BT15", "S2_6K", ("BT", 0.015)),
        ("L5K_BT15", "L5K", ("BT", 0.015)),
    ):
        firm = FIRMS[f_base]
        res = simulate_multi(firm, meth, R, S)
        out[fn_key] = res
    return out


def simulate_multi(firm: dict, meth: tuple[str, float], R: np.ndarray, S: np.ndarray) -> dict:
    kind, b = meth
    n, H_len, n_mods = R.shape
    acct = firm["size"]
    bal = np.zeros(n); peak = np.zeros(n); alive = np.ones(n, bool)
    phase = np.zeros(n, int); pdays = np.zeros(n, int); fdays = np.zeros(n, int)
    cash = np.full(n, -firm["price"]); npay = np.zeros(n, int); first = np.full(n, -1)
    blew_before = np.zeros(n, bool)
    nph = len(firm.get("phases", []))
    for t in range(H_len):
        kind_is_instant = firm["kind"] == "instant"
        if kind_is_instant:
            floor = np.minimum(peak - firm["trail"], 0.0); buf = (bal - floor) / firm["trail"]; tgt_left = np.inf
        else:
            room = np.minimum(bal + firm["static"], firm["daily"]); buf = room / min(firm["static"], firm["daily"])
            inch = phase < nph
            tgt = np.array([firm["phases"][min(p, nph - 1)][0] for p in phase])
            tgt_left = np.where(inch, tgt - bal, np.inf)
        want = np.full(n, b)
        if kind in ("B", "BT"):
            want = b * np.clip(buf, 0, 1)
        if kind == "BT":
            want = np.minimum(want, np.maximum(tgt_left, 0) / 2)

        # Size per module with 3% open risk cap
        rf = np.repeat(want[:, None], n_mods, axis=1) * (S[:, t, :] > 0)
        for j in range(n_mods - 1, 0, -1):
            over = rf.sum(axis=1) > OPEN_RISK_CAP + 1e-12
            rf[over, j] = 0.0

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

    valid_fp = first[first > 0]
    return {
        "med_first_pay_bday": int(np.median(valid_fp)) if len(valid_fp) else None,
        "p30_pct": round(float(np.mean((first > 0) & (first <= 21)) * 100), 1),
        "p60_pct": round(float(np.mean((first > 0) & (first <= 42)) * 100), 1),
        "p90_pct": round(float(np.mean((first > 0) & (first <= 64)) * 100), 1),
        "blow_before_pay_pct": round(float(np.mean(blew_before) * 100), 1),
        "net_12m_mean_usd": round(float(cash.mean()), 1),
        "net_12m_med_usd": round(float(np.median(cash)), 1),
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    cand = audit_candidates()
    cdf = pd.DataFrame(cand)
    cdf.to_csv(OUT / "relaxed_gate_audit.csv", index=False)

    print("=== 1. GATE AUDIT: WHICH CANDIDATES PASS WHEN FILTERS ARE RELAXED? ===")
    print(f"Total audited: {len(cdf)}")
    print(f"  G0 Strict (Bonf + Both Halves + 2x):       {cdf['G0_STRICT'].sum()}")
    print(f"  G1 Drop Bonferroni & 2x (95% CI + Halves): {cdf['G1_NO_BONF_NO_2X'].sum()}")
    print(f"  G2 Drop Pre-2022 (2022+ & 95% CI > 0):     {cdf['G2_2022_CI95'].sum()}")
    print(f"  G3 2022+ & Central Mean > 0 (Any CI):      {cdf['G3_2022_MEAN_POS'].sum()}\n")

    rescued = cdf[cdf["G3_2022_MEAN_POS"]].sort_values(["G0_STRICT", "G1_NO_BONF_NO_2X", "G2_2022_CI95"], ascending=False)
    print(rescued[["name", "unit", "n", "central", "2x", "2012-21", "2022+", "ci_bonf_lo", "ci95_lo_est", "G0_STRICT", "G1_NO_BONF_NO_2X", "G2_2022_CI95"]].to_string(index=False))

    print("\n=== 2. FAST-PAYOUT PROP SIMULATION: STRICT vs RELAXED SETS ===")
    tt = build_prop_modules()
    sets = {
        "S0_STRICT_CORE (Sweep+NB+BTC21_23+B7+B2)": ["SWEEP", "NB", "BTC_21_23", "B7_IBS_NQ", "B2_BTC_DON"],
        "S1_RELAX_CI (+TOM_NQ +BTC_GECE swap0)": ["SWEEP", "NB", "BTC_21_23", "B7_IBS_NQ", "B2_BTC_DON", "TOM_NQ", "BTC_GECE"],
        "S2_RELAX_2022 (+B3_XAU_H1 +EMA12_NQ)": ["SWEEP", "NB", "BTC_21_23", "B7_IBS_NQ", "B2_BTC_DON", "TOM_NQ", "BTC_GECE", "B3_XAU_H1", "EMA12_NQ"],
    }
    sim_out = {}
    for regime_name, (lo, hi) in (("2022+ (Son 4.8 Yil)", ("2022-01-01", "2026-11-17")), ("2018-21 (Pre-2022 Stress)", ("2018-01-01", "2021-12-31"))):
        print(f"\n--- REGIME: {regime_name} ---")
        sim_out[regime_name] = {}
        for sname, mlist in sets.items():
            r = sim_portfolio_set(tt, mlist, lo, hi)
            sim_out[regime_name][sname] = r
            print(f"\n{sname} -> {r['trades_per_year']} islem/yil ({r['trades_per_day']}/isgunu):")
            for fk, fv in r.items():
                if fk.startswith("trades"):
                    continue
                print(f"  {fk:18s}: ilk_pay_med={str(fv['med_first_pay_bday']):>4s}g | p30=%{fv['p30_pct']:4.1f} p60=%{fv['p60_pct']:4.1f} p90=%{fv['p90_pct']:4.1f} | patlama=%{fv['blow_before_pay_pct']:4.1f} | 12ay_ort=${fv['net_12m_mean_usd']:+6.1f} (med=${fv['net_12m_med_usd']:+6.1f})")

    (OUT / "relaxed_fast_payout_audit.json").write_text(json.dumps({"candidates": cand, "simulations": sim_out}, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
