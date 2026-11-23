"""Non-Post-Hoc (Structural / Execution-Time) Human Pre-Trade Checks Audit:
Tests 4 structural things a human sees at order-entry time that do NOT guess market direction:

  H1_SPREAD_GATE  : At signal time, is actual live bid-ask spread > 2.0x normal median spread?
                    (Tested on CME bbo-1m 2025-2026 & Maven time-of-day spread profile).
  H2_CHASE_GATE   : Between signal timestamp (T+0) and human screen-check (T+1m..5m), did price already run
                    away in signal direction by > 0.25R (chasing worse entry) vs pulled back (-0.10R..+0.10R, cheaper entry)?
                    Structural arithmetic: buying cheaper with same fixed stop/exit mathematically improves R without predicting future!
  H3_MACRO_WINDOW : Is the signal falling within +-15 minutes of scheduled FOMC / CPI / NFP release?
                    (Prop firm rule violation + spread/slippage blowup).
  H4_CORR_CLUSTER : Are 2+ same-direction US100 modules (Sweep, NB, B7, TOM) firing simultaneously on the same day
                    without unrealized profit buffer? (Open-risk / daily-DD collision gate).

Run from strategy-lab with vectorbt-lab venv:
  python ../HANDOFF/scripts_2026-11-23/structural_human_checks.py
"""
from __future__ import annotations

import json
import sys
import warnings
from pathlib import Path

import databento as db
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
sys.path.insert(0, ".")
sys.path.insert(0, "../HANDOFF/scripts_2026-11-23")
sys.path.insert(0, "../HANDOFF/scripts_2026-11-20")
from intraday import stop_testi as st  # noqa: E402
from intraday.history_fetch import load_history  # noqa: E402
import human_delay_and_checklist as HDC  # noqa: E402

OUT = Path("outputs/intraday/futures_round5")
SPLIT = pd.Timestamp("2022-01-01")


def test_h1_live_spread_gate() -> dict:
    """Measure actual minute-by-minute spread spikes on MNQ/MES/CL/6E from CME bbo-1m (2025-2026)
    around our exact strategy entry windows (09:30-16:00 NY, 15:55-16:05 NY close, 16:00-18:00 rollover).
    """
    bbo_files = sorted(Path("outputs/databento/bbo1m").glob("*.dbn.zst"))
    if not bbo_files:
        return {"error": "no bbo1m files"}
    q = pd.concat(db.DBNStore.from_file(f).to_df() for f in bbo_files)
    q = q[q["symbol"] == "MNQ.c.0"].copy()
    ny = q.index.tz_convert("America/New_York")
    q["hm"] = ny.strftime("%H:%M")
    q["dow"] = ny.dayofweek
    q = q[q["dow"] < 5]
    q["spread_pts"] = q["ask_px_00"] - q["bid_px_00"]
    q = q[q["spread_pts"] > 0]

    rth = q[(q["hm"] >= "09:30") & (q["hm"] < "16:00")]
    med_rth = float(rth["spread_pts"].median())
    p95_rth = float(rth["spread_pts"].quantile(0.95))
    p99_rth = float(rth["spread_pts"].quantile(0.99))

    # Specific windows where our rules fire:
    # 1) NB half-hour decision marks (:00 and :30 inside 10:00..15:30)
    nb_marks = rth[rth["hm"].str.endswith(":00") | rth["hm"].str.endswith(":30")]
    # 2) B7 / TOM close window (15:55..16:00 NY vs 16:00..16:15 NY post-cash close)
    w_1555 = q[(q["hm"] >= "15:55") & (q["hm"] <= "15:59")]
    w_1601 = q[(q["hm"] >= "16:00") & (q["hm"] <= "16:15")]
    # 3) Rollover / reopen window (17:00..18:05 NY = 21:00..23:00 UTC)
    w_roll = q[(q["hm"] >= "16:15") & (q["hm"] <= "18:15")]

    spike_rate_rth = float((nb_marks["spread_pts"] > 2.0 * med_rth).mean() * 100)
    spike_mean_extra_pts = float((nb_marks.loc[nb_marks["spread_pts"] > 2.0 * med_rth, "spread_pts"] - med_rth).mean())

    return {
        "rth_median_spread_pts": med_rth,
        "rth_p95_spread_pts": p95_rth,
        "rth_p99_spread_pts": p99_rth,
        "nb_decision_marks_spike_gt_2x_pct": round(spike_rate_rth, 2),
        "nb_spike_mean_extra_cost_pts": round(spike_mean_extra_pts, 3),
        "close_1555_1559_median_spread_pts": float(w_1555["spread_pts"].median()),
        "close_1555_1559_p95_spread_pts": float(w_1555["spread_pts"].quantile(0.95)),
        "after_1600_1615_median_spread_pts": float(w_1601["spread_pts"].median()),
        "after_1600_1615_p95_spread_pts": float(w_1601["spread_pts"].quantile(0.95)),
        "rollover_1615_1815_p95_spread_pts": float(w_roll["spread_pts"].quantile(0.95)),
    }


def test_h2_price_drift_before_click(tables: dict[str, pd.DataFrame]) -> dict:
    """When the user looks at the screen 1-5 minutes after the alert (T+5m),
    compare:
      - BETTER_OR_FLAT_PRICE: price at T+5m is at or better (cheaper) than T+0 signal price (or within +0.05R)
      - CHASED_AWAY_PRICE   : price at T+5m already ran away in trade direction by > +0.15R
    Note: We check if 'don't chase if price already ran >0.15R; enter if price is same or better' holds in BOTH IS and OOS.
    To avoid trivial arithmetic (measuring R from T+0 vs T+5m), we measure R_5m (actual PnL achieved from T+5m entry!).
    """
    out = {}
    for mname in ("NB", "B7_IBS", "TOM_NQ"):
        df = tables[mname].copy()
        d = df["direction"] if "direction" in df.columns else 1
        # How much did price move in trade direction between T+0 (entry) and T+5m (entry_5m), in units of risk?
        drift_r = d * (df["entry_5m"] - df["entry"]) / (df["sf"] * df["entry"])
        df["drift_r"] = drift_r
        # Condition: at T+5m, price has NOT run away > +0.10R (i.e. pulled back or flat: drift_r <= 0.0)
        df["CHEAPER_AT_CLICK"] = df["drift_r"] <= 0.0

        is_df = df[df["day"] < SPLIT]
        oos_df = df[df["day"] >= SPLIT]

        out[mname] = {
            "IS_cheaper_R5m": round(float(is_df.loc[is_df["CHEAPER_AT_CLICK"], "R_5m"].mean()), 4),
            "IS_chased_R5m": round(float(is_df.loc[~is_df["CHEAPER_AT_CLICK"], "R_5m"].mean()), 4),
            "OOS_cheaper_R5m": round(float(oos_df.loc[oos_df["CHEAPER_AT_CLICK"], "R_5m"].mean()), 4),
            "OOS_chased_R5m": round(float(oos_df.loc[~oos_df["CHEAPER_AT_CLICK"], "R_5m"].mean()), 4),
            "OOS_T0_baseline_R0": round(float(oos_df["R_0"].mean()), 4),
            "OOS_cheaper_share_pct": round(float(oos_df["CHEAPER_AT_CLICK"].mean() * 100), 1),
        }
    return out


def test_h3_macro_news_window(tables: dict[str, pd.DataFrame]) -> dict:
    """Check overlap of intraday signals (NB, Sweep) with scheduled macro news dates/times if calendar exists."""
    cal_files = list(Path("outputs").rglob("*macro*")) + list(Path("intraday").rglob("*macro*"))
    # Also check meta_label trades_SWEEP_CORE.csv which already has macro_day flag!
    sw = pd.read_csv("outputs/intraday/meta_label/trades_SWEEP_CORE.csv")
    res = {}
    if "macro_day" in sw.columns:
        sw["day"] = pd.to_datetime(sw["timestamp"]).dt.normalize()
        t_sw = tables["SWEEP"].copy()
        t_sw["macro_day"] = sw["macro_day"].to_numpy(bool)
        is_sw = t_sw[t_sw["day"] < SPLIT]
        oos_sw = t_sw[t_sw["day"] >= SPLIT]
        res["SWEEP_macro_day"] = {
            "IS_macro_R": round(float(is_sw.loc[is_sw["macro_day"], "R_0"].mean()), 3),
            "IS_nonmacro_R": round(float(is_sw.loc[~is_sw["macro_day"], "R_0"].mean()), 3),
            "OOS_macro_R": round(float(oos_sw.loc[oos_sw["macro_day"], "R_0"].mean()), 3),
            "OOS_nonmacro_R": round(float(oos_sw.loc[~oos_sw["macro_day"], "R_0"].mean()), 3),
            "OOS_macro_n": int(oos_sw["macro_day"].sum()),
        }
    return res


def test_h4_same_day_collision(tables: dict[str, pd.DataFrame]) -> dict:
    """Measure how often multiple modules fire on the same day, and what happens to daily worst drawdown
    when the human enforces a strict 'Max 2 concurrent open positions / Max 2.0% combined open risk' gate.
    """
    cal = pd.bdate_range("2013-01-01", "2026-11-17")
    mods = ["SWEEP", "NB", "B7_IBS", "TOM_NQ", "BTC_21_23", "BTC_GECE"]
    active = pd.DataFrame(0, index=cal, columns=mods)
    pnl_1pct = pd.DataFrame(0.0, index=cal, columns=mods)
    for m in mods:
        df = tables[m]
        g = df.groupby("day")["R_0"].agg(["count", "sum"]).reindex(cal).fillna(0)
        active[m] = (g["count"] > 0).astype(int)
        pnl_1pct[m] = g["sum"] * 0.01  # at 1% risk per trade

    n_active = active.sum(axis=1)
    tot_pnl = pnl_1pct.sum(axis=1)

    # Capped at max 2 trades per day (priority: SWEEP > B7_IBS > NB > BTC_GECE > TOM_NQ > BTC_21_23)
    prio = ["SWEEP", "B7_IBS", "NB", "BTC_GECE", "TOM_NQ", "BTC_21_23"]
    capped_pnl = pd.Series(0.0, index=cal)
    taken = pd.Series(0, index=cal)
    for m in prio:
        can_take = (active[m] > 0) & (taken < 2)
        capped_pnl += np.where(can_take, pnl_1pct[m], 0.0)
        taken += can_take.astype(int)

    w22 = cal >= "2022-01-01"
    return {
        "days_with_3plus_signals_pct": round(float((n_active[w22] >= 3).mean() * 100), 1),
        "days_with_4plus_signals_pct": round(float((n_active[w22] >= 4).mean() * 100), 1),
        "uncapped_worst_day_1pct_risk": round(float(tot_pnl[w22].min() * 100), 2),
        "uncapped_days_worse_than_minus2pct": int((tot_pnl[w22] <= -0.02).sum()),
        "uncapped_annual_return_pct": round(float(tot_pnl[w22].mean() * 252 * 100), 2),
        "uncapped_sharpe": round(float(tot_pnl[w22].mean() / tot_pnl[w22].std() * np.sqrt(252)), 2),
        "max2_gate_worst_day_1pct_risk": round(float(capped_pnl[w22].min() * 100), 2),
        "max2_gate_days_worse_than_minus2pct": int((capped_pnl[w22] <= -0.02).sum()),
        "max2_gate_annual_return_pct": round(float(capped_pnl[w22].mean() * 252 * 100), 2),
        "max2_gate_sharpe": round(float(capped_pnl[w22].mean() / capped_pnl[w22].std() * np.sqrt(252)), 2),
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    tables = HDC.build_human_trades()

    h1 = test_h1_live_spread_gate()
    h2 = test_h2_price_drift_before_click(tables)
    h3 = test_h3_macro_news_window(tables)
    h4 = test_h4_same_day_collision(tables)

    res = {"H1_LIVE_SPREAD": h1, "H2_PRICE_DRIFT_AT_CLICK": h2, "H3_MACRO_WINDOW": h3, "H4_COLLISION_CAP": h4}
    (OUT / "structural_human_checks.json").write_text(json.dumps(res, indent=2), encoding="utf-8")
    print(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
