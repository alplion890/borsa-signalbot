"""NQ EMA12 first-5m rule, 14-year backtest with measured Maven cost.

Preregistered: HANDOFF/ema12_ilk5dk_14y_onkayit_2026-11-17.md.
Rule identical to forward_ea.modules.ema12_first5m_detector (CAND_EMA12_FIRST5M).

    python -m intraday.ema12_first5m_14y
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from .history_fetch import load_history

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "outputs" / "intraday" / "ema12_first5m" / "14y"
PROFILE = ROOT / "outputs" / "intraday" / "mt5_bridge" / "reality_profile.csv"
SPLIT = "2022-01-01"
HOLD_BARS = 72


def trades(frame: pd.DataFrame) -> pd.DataFrame:
    """One trade per NY session: signal on the 09:30 bar close, stop or 72-bar timeout."""
    ny = frame.index.tz_localize("UTC").tz_convert("America/New_York")
    ema = frame["close"].ewm(span=12, adjust=False).mean().to_numpy()
    o, h, l, c = (frame[k].to_numpy() for k in ("open", "high", "low", "close"))
    sig_idx = np.flatnonzero((ny.hour == 9) & (ny.minute == 30) & (ny.weekday < 5))
    rows = []
    for i in sig_idx:
        entry, dist = c[i], h[i] - l[i]
        if dist <= 0 or entry == ema[i] or i + HOLD_BARS >= len(c):
            continue
        d = 1 if entry > ema[i] else -1
        stop = entry - d * dist
        seg = slice(i + 1, i + 1 + HOLD_BARS)
        hit = np.flatnonzero((l[seg] <= stop) if d == 1 else (h[seg] >= stop))
        if len(hit):
            j, px, why = i + 1 + hit[0], stop, "sl"
        else:
            j, px, why = i + HOLD_BARS, c[i + HOLD_BARS], "timeout"
        rows.append({"date": ny[i].strftime("%Y-%m-%d"), "dir": d, "entry": entry, "risk": dist,
                     "exit": px, "reason": why, "bars": j - i,
                     "r_gross": d * (px - entry) / dist})
    return pd.DataFrame(rows)


def r_net(t: pd.DataFrame, cost: float) -> pd.Series:
    return t["r_gross"] - 2 * cost * t["entry"] / t["risk"]


def block_ci(r: pd.Series, reps: int = 10_000, block: int = 5) -> list[float]:
    rng = np.random.default_rng(20261117)
    x, n = r.to_numpy(), len(r)
    starts = rng.integers(0, n, size=(reps, (n + block - 1) // block))
    idx = ((starts[:, :, None] + np.arange(block)) % n).reshape(reps, -1)[:, :n]
    return np.quantile(x[idx].mean(axis=1), [0.025, 0.975]).tolist()


def stats(r: pd.Series, dates: pd.Series) -> dict:
    eq = r.cumsum()
    losing = (r <= 0).astype(int)
    streak = losing.groupby((losing == 0).cumsum()).sum().max()
    months = max((pd.to_datetime(dates.iloc[-1]) - pd.to_datetime(dates.iloc[0])).days / 30.44, 1)
    return {"n": int(len(r)), "mean_R": float(r.mean()), "wr_pct": float((r > 0).mean() * 100),
            "avg_win_R": float(r[r > 0].mean()), "avg_loss_R": float(r[r <= 0].mean()),
            "trades_per_month": float(len(r) / months), "R_per_year": float(r.mean() * len(r) / months * 12),
            "max_dd_R": float((eq.cummax() - eq).max()), "max_loss_streak": int(streak)}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    cost = float(pd.read_csv(PROFILE).set_index("symbol").loc["NASDAQ100", "real_cost_per_side_central"])
    frame = load_history("NASDAQ100", "5m", start_year=2012)
    t = trades(frame)
    t.to_csv(OUT / "trades.csv", index=False)
    is_ = t["date"] < SPLIT
    res = {"cost_central": cost, "first": t["date"].iloc[0], "last": t["date"].iloc[-1],
           "sl_pct": float((t["reason"] == "sl").mean() * 100),
           "median_risk_pts": float(t["risk"].median())}
    for label, c in (("zero", 0.0), ("central", cost), ("pessimistic", 2 * cost)):
        r = r_net(t, c)
        res[label] = {"all": stats(r, t["date"]), "ci95": block_ci(r),
                      "2012-21": stats(r[is_], t["date"][is_]), "2022+": stats(r[~is_], t["date"][~is_]),
                      "yearly_R": {y: float(g.sum()) for y, g in r.groupby(t["date"].str[:4])}}
    c = res["central"]
    res["PASS"] = bool(c["ci95"][0] > 0 and c["2012-21"]["mean_R"] > 0 and c["2022+"]["mean_R"] > 0
                       and res["pessimistic"]["all"]["mean_R"] > 0)
    (OUT / "result.json").write_text(json.dumps(res, indent=2), encoding="utf8")
    print(f"n={len(t)} {res['first']}..{res['last']} PASS={res['PASS']} stop%={res['sl_pct']:.0f} "
          f"medyan risk {res['median_risk_pts']:.1f} puan")
    for m in ("zero", "central", "pessimistic"):
        a = res[m]["all"]
        print(f"  {m:11s} R={a['mean_R']:+.4f} CI {[round(x, 4) for x in res[m]['ci95']]} WR%{a['wr_pct']:.1f} "
              f"kaz {a['avg_win_R']:+.2f} kay {a['avg_loss_R']:+.2f} ay {a['trades_per_month']:.1f} "
              f"R/yil {a['R_per_year']:+.1f} DD {a['max_dd_R']:.1f}R seri {a['max_loss_streak']} | "
              f"IS {res[m]['2012-21']['mean_R']:+.4f} OOS {res[m]['2022+']['mean_R']:+.4f} "
              f"(WR OOS %{res[m]['2022+']['wr_pct']:.1f})")
    print("  yillik R (merkez):", {k: round(v, 1) for k, v in c["yearly_R"].items()})


if __name__ == "__main__":
    main()
