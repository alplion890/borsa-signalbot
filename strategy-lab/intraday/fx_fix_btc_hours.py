"""FX fix reversal (H1-H4) and BTC hour seasonality (H5-H6).

Preregistered: HANDOFF/fx_fix_btc_saat_onkayit_2026-11-17.md.

    python -m intraday.fx_fix_btc_hours
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from .history_fetch import load_history

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "outputs" / "intraday" / "fx_fix_btc"
PROFILE = ROOT / "outputs" / "intraday" / "mt5_bridge" / "reality_profile.csv"
BTC = ROOT / "outputs" / "intraday" / "cache" / "binance" / "BTCUSDT_1h.csv"
PAIRS = {"EURUSD": -1, "GBPUSD": -1, "AUDUSD": -1, "USDJPY": 1, "USDCAD": 1, "USDCHF": 1}  # +1: pair long = USD long
FX_TESTS = {"H1_london_pre": ("Europe/London", "15:00", "16:00", 1),
            "H2_london_post": ("Europe/London", "16:00", "17:00", -1),
            "H3_tokyo_pre": ("Asia/Tokyo", "08:55", "09:55", 1),
            "H4_tokyo_post": ("Asia/Tokyo", "09:55", "10:55", -1)}
BTC_TESTS = {"H5_btc_22_00": (22, 2), "H6_btc_21_23": (21, 2)}
N_TESTS = 6
ALPHA = 0.05 / N_TESTS / 2


def window_returns(frame: pd.DataFrame, tz: str, t0: str, t1: str) -> pd.Series:
    """Per local date: open of bar at t1 / open of bar at t0 - 1 (weekdays only)."""
    local = frame.index.tz_localize("UTC").tz_convert(tz)
    hm = local.strftime("%H:%M")
    day = local.strftime("%Y-%m-%d")
    o = frame["open"].to_numpy()
    a = pd.Series(o[hm == t0], index=day[hm == t0])
    b = pd.Series(o[hm == t1], index=day[hm == t1])
    a, b = a[~a.index.duplicated()], b[~b.index.duplicated()]
    common = a.index.intersection(b.index)
    r = b[common] / a[common] - 1
    return r[pd.to_datetime(r.index).weekday < 5]


def fx_daily(tests_cost: dict[str, float]) -> dict[str, pd.Series]:
    frames = {p: load_history(p, "5m", start_year=2012) for p in PAIRS}
    out = {}
    for name, (tz, t0, t1, usd_dir) in FX_TESTS.items():
        legs = {p: usd_dir * PAIRS[p] * window_returns(f, tz, t0, t1) - 2 * tests_cost[p]
                for p, f in frames.items()}
        out[name] = pd.DataFrame(legs).mean(axis=1, skipna=True).dropna().sort_index()
    return out


def btc_daily(cost: float) -> dict[str, pd.Series]:
    df = pd.read_csv(BTC, parse_dates=["ts"]).set_index("ts")
    o = df["open"]
    out = {}
    for name, (h0, hold) in BTC_TESTS.items():
        start = o[o.index.hour == h0]
        end = o.reindex(start.index + pd.Timedelta(hours=hold))
        r = (end.to_numpy() / start.to_numpy() - 1) - 2 * cost
        s = pd.Series(r, index=start.index.strftime("%Y-%m-%d")).dropna()
        out[name] = s[~s.index.duplicated()]
    return out


def ci(d: pd.Series, reps: int = 10_000) -> list[float]:
    rng = np.random.default_rng(20261117)
    n = len(d)
    starts = rng.integers(0, n, size=(reps, (n + 4) // 5))
    idx = ((starts[:, :, None] + np.arange(5)) % n).reshape(reps, -1)[:, :n]
    return (np.quantile(d.to_numpy()[idx].mean(axis=1), [ALPHA, 1 - ALPHA]) * 1e4).tolist()


def summarize(d: pd.Series, split: str) -> dict:
    a, b = d[d.index < split], d[d.index >= split]
    years = (pd.to_datetime(d.index[-1]) - pd.to_datetime(d.index[0])).days / 365.25
    return {"n": len(d), "mean_bp": float(d.mean() * 1e4), "win_pct": float((d > 0).mean() * 100),
            "ann_pct": float(d.sum() / years * 100), "ci_bp": ci(d),
            "is_bp": float(a.mean() * 1e4), "oos_bp": float(b.mean() * 1e4),
            "yearly_pct": {y: float(g.sum() * 100) for y, g in d.groupby(d.index.str[:4])}}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    prof = pd.read_csv(PROFILE).set_index("symbol")["real_cost_per_side_central"]
    res: dict[str, dict] = {}
    runs = []
    for label, k in (("zero", 0.0), ("central", 1.0), ("pessimistic", 2.0)):
        fx = fx_daily({p: k * float(prof[p]) for p in PAIRS})
        bt = btc_daily(k * float(prof["BTCUSDT"]))
        for name, d in {**fx, **bt}.items():
            split = "2022-01-01" if name.startswith("H") and "btc" not in name else "2022-03-01"
            res.setdefault(name, {})[label] = summarize(d, split)
            if label == "central":
                d.to_csv(OUT / f"daily_{name}.csv", header=["ret"])
    for name, r in res.items():
        c = r["central"]
        r["PASS"] = bool(c["ci_bp"][0] > 0 and c["is_bp"] > 0 and c["oos_bp"] > 0
                         and r["pessimistic"]["mean_bp"] > 0)
        print(f"{name}: n={c['n']} PASS={r['PASS']}")
        for lab in ("zero", "central", "pessimistic"):
            x = r[lab]
            print(f"  {lab:11s} {x['mean_bp']:+.2f}bp/gun win%{x['win_pct']:.1f} yil%{x['ann_pct']:+.1f} "
                  f"CI {[round(v, 2) for v in x['ci_bp']]} IS {x['is_bp']:+.2f} OOS {x['oos_bp']:+.2f}")
        print("  yillik% (merkez):", {k: round(v, 1) for k, v in c["yearly_pct"].items()})
    (OUT / "result.json").write_text(json.dumps(res, indent=2), encoding="utf8")


if __name__ == "__main__":
    main()
