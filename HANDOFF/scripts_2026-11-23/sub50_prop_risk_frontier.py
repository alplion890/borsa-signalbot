"""Sub-$50 Prop Firm & Risk Frontier Optimization (2026-11-24).
Simulates all verified <= $50 (and ~$59 reference) prop accounts across Instant, 1-Step, and 2-Step models,
and maps the exact Risk Frontier (0.5% -> 2.5% risk) to find:
  1. Absolute earliest possible payout day (Rule-Book Theoretical Minimum vs p10 Fast Streak vs Median)
  2. Pareto-optimal risk setting (Fastest Payout with Lowest Blow-Up Probability)

Verified Accounts Included (as of 2026-11-24):
  1. FYFX_INST_5K       : FundYourFX Instant Classic 5K ($39.60, 6% static DD, 4% daily, min 6 trading days, weekly cycle, 3% target, no consistency)
  2. FN_LITE_5K_2STEP   : FundedNext Stellar Lite 5K ($32.99, P1 8% + P2 4%, 8% static DD, 4% daily, min 2d/phase, 21d first payout wait, 80% split, no consistency)
  3. FN_2STEP_6K        : FundedNext Stellar 2-Step 6K ($34.99 NOVSTR / $59.99 list, P1 8% + P2 5%, 10% static DD, 5% daily, min 5d/phase, 14d first wait, 80% split)
  4. THE5ERS_HS_5K      : The5ers High Stakes 5K ($39.00, P1 8% + P2 5%, 10% static DD, 5% daily, min 3 profitable days >=0.5%/phase, 14d payout, 80% split, no consistency)
  5. FPIPS_2STEP_5K     : FundingPips 2-Step Standard 5K ($29.00-$36.00, P1 8% + P2 5%, 10% static DD, 5% daily, min 3d/phase, 14d bi-weekly payout without consistency)
  6. ALPHA_1STEP_5K     : Alpha Capital / E8 1-Step 5K (~$40-$48, P1 10%, 6% static/trailing DD, 4% daily, 40% best-day in funded, 14d wait, 80% split)
  7. FN_INST_2K_REF     : FundedNext Stellar Instant 2K ($59.99 manual no-EA, 6% trailing DD, no daily, no consistency, on-demand at >=5% [DAY 1 POSSIBLE!] or 14d at >=1%)

Run from strategy-lab with vectorbt-lab venv:
  python ../HANDOFF/scripts_2026-11-23/sub50_prop_risk_frontier.py
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
sys.path.insert(0, "../HANDOFF/scripts_2026-11-23")
sys.path.insert(0, "../HANDOFF/scripts_2026-11-20")
import human_delay_and_checklist as HDC  # noqa: E402
from cheap_sizing import OPEN_RISK_CAP, SEED, paths  # noqa: E402

OUT = Path("outputs/intraday/futures_round5")
CAL = pd.bdate_range("2013-01-01", "2026-11-17")

ACCOUNTS = {
    "1_FYFX_INST_5K ($39.60)": dict(
        kind="instant", size=5000, price=39.60, dd=0.06, static_dd=True, daily=0.04,
        min_tdays=6, cycle_bdays=5, min_pay=0.03, ondemand=9.99, cons=None, split=0.65,
        rule_min_bday=6, rule_note="En erken 6 işlem günü + %3 ($150) kâr şartı (on-demand yok, haftalık döngü)."
    ),
    "2_FN_INST_2K ($59.99 Ref)": dict(
        kind="instant", size=2000, price=59.99, dd=0.06, static_dd=False, daily=0.99,
        min_tdays=1, cycle_bdays=10, min_pay=0.01, ondemand=0.05, cons=None, split=0.75,
        rule_min_bday=1, rule_note="EN ERKEN 1. GÜN! (%5 = $100 kâr yakalanırsa 14 gün beklemeden aynı gün On-Demand çekim; yoksa 14. günde %1 = $20)."
    ),
    "3_THE5ERS_HS_5K ($39.00)": dict(
        kind="chal", size=5000, price=39.00, phases=[(0.08, 3, 0.005), (0.05, 3, 0.005)],
        dd=0.10, static_dd=True, daily=0.05, first_wait_bdays=10, cycle_bdays=10, cons=None, split=0.80, refund=True,
        rule_min_bday=16, rule_note="En erken 16 işgünü (Faz 1 min 3 kârlı gün + Faz 2 min 3 kârlı gün + Funded 14 takvim günü [10 işgünü])."
    ),
    "4_FPIPS_2STEP_5K ($29-$36)": dict(
        kind="chal", size=5000, price=32.00, phases=[(0.08, 3, -9.0), (0.05, 3, -9.0)],
        dd=0.10, static_dd=True, daily=0.05, first_wait_bdays=10, cycle_bdays=10, cons=None, split=0.80, refund=True,
        rule_min_bday=16, rule_note="En erken 16 işgünü (Faz 1 min 3 gün + Faz 2 min 3 gün + Funded 14 takvim günü bi-weekly)."
    ),
    "5_FN_LITE_5K ($32.99)": dict(
        kind="chal", size=5000, price=32.99, phases=[(0.08, 2, -9.0), (0.04, 2, -9.0)],
        dd=0.08, static_dd=True, daily=0.04, first_wait_bdays=15, cycle_bdays=10, cons=None, split=0.80, refund=True,
        rule_min_bday=19, rule_note="En erken 19 işgünü (Faz 1 min 2 gün + Faz 2 min 2 gün + Funded ilk çekim 21 takvim günü [15 işgünü])."
    ),
    "6_FN_2STEP_6K ($34.99-$59)": dict(
        kind="chal", size=6000, price=34.99, phases=[(0.08, 5, -9.0), (0.05, 5, -9.0)],
        dd=0.10, static_dd=True, daily=0.05, first_wait_bdays=15, cycle_bdays=10, cons=None, split=0.80, refund=True,
        rule_min_bday=25, rule_note="En erken 25 işgünü (Faz 1 min 5 gün + Faz 2 min 5 gün + Funded ilk çekim 21 takvim günü [15 işgünü])."
    ),
    "7_ALPHA_E8_1STEP_5K ($40-$48)": dict(
        kind="chal", size=5000, price=45.00, phases=[(0.10, 2, -9.0)],
        dd=0.06, static_dd=False, daily=0.04, first_wait_bdays=10, cycle_bdays=10, cons=0.40, split=0.80, refund=True,
        rule_min_bday=12, rule_note="En erken 12 işgünü (Tek faz %10 hedef min 2 gün + Funded 14 takvim günü [10 işgünü], Funded'da %40 Best Day)."
    ),
}


def sim_account(R: np.ndarray, S: np.ndarray, cfg: dict, mode: str, r_chal: float, r_fund: float) -> dict:
    """Simulate 300 paths x 260 bdays (single ticket, no rebuy) to measure true first-payout speed & blow-up risk."""
    n, H_len, m = R.shape
    acct = cfg["size"]
    price = cfg["price"]
    dd = cfg["dd"]
    static_dd = cfg["static_dd"]
    daily_lim = cfg["daily"]
    cons = cfg["cons"]
    split = cfg["split"]
    is_inst = cfg["kind"] == "instant"
    phases = cfg.get("phases", [])
    nph = len(phases)

    bal = np.zeros(n); peak = np.zeros(n); alive = np.ones(n, bool)
    phase = np.zeros(n, int); qdays = np.zeros(n, int); fdays = np.zeros(n, int)
    best_day = np.zeros(n)
    cash = np.full(n, -price); npay = np.zeros(n, int)
    first_pay = np.full(n, -1); blew_before_pay = np.zeros(n, bool)

    for t in range(H_len):
        in_funded = is_inst | (phase == nph)
        base_r = np.where(in_funded, r_fund, r_chal)

        floor = np.full(n, -dd) if static_dd else np.minimum(peak - dd, 0.0)
        room = np.minimum(bal - floor, daily_lim)
        buf = np.clip(room / min(dd, daily_lim), 0.0, 1.0)

        if mode == "BUFFER":
            want = base_r * buf
        elif mode == "FIXED":
            want = base_r
        elif mode == "FAST_TAPER":
            # Full risk until 60% of target/payout, then taper to protect equity
            tgt_now = np.where(is_inst, cfg.get("min_pay", 0.03), 0.08)
            want = np.where(bal < 0.65 * tgt_now, base_r, base_r * 0.55) * np.clip(buf * 1.25, 0.25, 1.0)
        else:
            want = base_r * buf

        rf = np.repeat(want[:, None], m, axis=1) * (S[:, t, :] > 0)
        for j in range(m - 1, 0, -1):
            over = rf.sum(axis=1) > OPEN_RISK_CAP + 1e-12
            rf[over, j] = 0.0

        pnl = (rf * R[:, t, :]).sum(axis=1)
        low = np.minimum(pnl, 0.0) * 1.5
        traded = np.abs(pnl) > 1e-9

        dead = ((bal + low <= floor) | (low <= -daily_lim)) & alive
        blew_before_pay |= dead & (npay == 0)
        alive &= ~dead

        bal = np.where(alive, bal + pnl, bal)
        peak = np.where(alive, np.maximum(peak, bal), peak)
        best_day = np.where(alive & in_funded, np.maximum(best_day, pnl), best_day)

        if is_inst:
            qdays = np.where(alive & traded, qdays + 1, qdays)
            fdays = np.where(alive, fdays + 1, fdays)
            can_pay = alive & (
                (bal >= cfg["ondemand"])
                | ((fdays >= cfg["cycle_bdays"]) & (qdays >= cfg["min_tdays"]) & (bal >= cfg["min_pay"]))
            )
            if cons:
                can_pay &= (best_day <= cons * bal + 1e-9)
        else:
            # Evaluation phase progression
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
            can_pay = now_fund & (fdays >= wait_req) & (bal >= 0.01)
            if cons:
                can_pay &= (best_day <= cons * bal + 1e-9)

        pay_amt = np.where(can_pay, bal * acct * split, 0.0)
        cash += pay_amt
        if cfg.get("refund"):
            cash += np.where(can_pay & (npay == 0), price, 0.0)
        npay += can_pay
        first_pay = np.where(can_pay & (first_pay < 0), t + 1, first_pay)

        for arr in (bal, peak, best_day):
            arr[can_pay] = 0.0
        qdays[can_pay] = 0
        fdays[can_pay] = 0

    fp = first_pay[first_pay > 0]
    return {
        "rule_min_bday": cfg["rule_min_bday"],
        "p10_fast_bday": int(np.quantile(fp, 0.10)) if len(fp) >= 5 else None,
        "med_first_bday": int(np.median(fp)) if len(fp) else None,
        "p30_pct": round(float(np.mean((first_pay > 0) & (first_pay <= 21)) * 100), 1),
        "p60_pct": round(float(np.mean((first_pay > 0) & (first_pay <= 42)) * 100), 1),
        "p90_pct": round(float(np.mean((first_pay > 0) & (first_pay <= 64)) * 100), 1),
        "ever_pay_12m_pct": round(float(np.mean(first_pay > 0) * 100), 1),
        "blow_before_pay_pct": round(float(blew_before_pay.mean() * 100), 1),
        "net_12m_mean_usd": round(float(cash.mean()), 1),
        "net_12m_med_usd": round(float(np.median(cash)), 1),
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    tables = HDC.build_human_trades()
    chk_dummy = {m: {} for m in tables}
    # Pure honest T+0 (with 2m pre-alert) daily matrix
    R0, S0 = HDC.apply_checklist_sizing(tables, chk_dummy, "EXACT_T0")
    ix22 = paths(CAL, "2022-01-01", "2026-11-17", np.random.default_rng(SEED))
    R, S = R0[ix22], S0[ix22]

    settings = [
        ("A_SAFE_BUFFER_0.5%", "BUFFER", 0.005, 0.005),
        ("B_SWEET_BUFFER_1.0%", "BUFFER", 0.010, 0.010),
        ("C_FAST_TAPER_1.2%", "FAST_TAPER", 0.012, 0.010),
        ("D_CHAL_1.5%_FUND_0.8%", "FAST_TAPER", 0.015, 0.008),
        ("E_AGGR_FIXED_1.2%", "FIXED", 0.012, 0.010),
        ("F_TURBO_CHAL_2.0%", "FAST_TAPER", 0.020, 0.008),
    ]

    all_rows = []
    for aname, acfg in ACCOUNTS.items():
        print(f"\n==================== {aname} ====================")
        print(f"  Kural En Erken Sınır: {acfg['rule_min_bday']} işgünü -> {acfg['rule_note']}")
        for sname, mode, rc, rf in settings:
            res = sim_account(R, S, acfg, mode, rc, rf)
            row = {"account": aname, "setting": sname, **res}
            all_rows.append(row)
            print(
                f"  {sname:22s} | EnErken(p10)={str(res['p10_fast_bday']):>3s}g Med={str(res['med_first_bday']):>3s}g "
                f"| p30={res['p30_pct']:4.1f}% p60={res['p60_pct']:4.1f}% TopPay={res['ever_pay_12m_pct']:4.1f}% "
                f"| Patlama={res['blow_before_pay_pct']:4.1f}% | 12ay_Ort=${res['net_12m_mean_usd']:+6.1f} (Med=${res['net_12m_med_usd']:+6.1f})",
                flush=True,
            )

    (OUT / "sub50_prop_risk_frontier.json").write_text(json.dumps(all_rows, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
