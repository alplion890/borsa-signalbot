"""Futures-cost retest of Noise Band ES (H1) and EMA12 first-5m NQ (H2).

Prereg: HANDOFF/futures_maliyet_onkayit_2026-11-21.md (commit 57bf0ba). Rules unchanged (imported engines).
Run from strategy-lab with the vectorbt-lab venv:
  python ../HANDOFF/scripts_2026-11-21/futures_cost_retest.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import databento as db
import numpy as np
import pandas as pd

sys.path.insert(0, ".")
from intraday.ema12_first5m_14y import trades as ema12_trades  # noqa: E402
from intraday.noise_band_research import simulate  # noqa: E402

SRC = Path("outputs/databento")
OUT = Path("outputs/intraday/futures_cost_retest")
PROFILE = Path("outputs/intraday/mt5_bridge/reality_profile.csv")
MULT = {"MES": 5.0, "MNQ": 2.0}
COMMISSION_SIDE_USD = 0.61          # Topstep help-center MES all-in $1.22 round turn
EVAL = ("2012-01-01", "2026-11-20")
HOLDOUT = ("2010-06-06", "2012-01-01")
SPLIT = "2022-01-01"
SEED = 20261121
Q_LO = 0.05 / 2 / 2                 # Bonferroni 2 tests, two-sided


def load_1m(sym: str) -> pd.DataFrame:
    files = sorted((SRC / "nq1m").glob("*.dbn.zst"))
    df = pd.concat(db.DBNStore.from_file(f).to_df() for f in files)
    df = df[df["symbol"] == sym].sort_index()
    df = df[~df.index.duplicated()]
    return df[["open", "high", "low", "close", "volume", "instrument_id"]]


def to_5m(m: pd.DataFrame) -> pd.DataFrame:
    r = m.resample("5min", label="left", closed="left")
    out = pd.DataFrame({"open": r["open"].first(), "high": r["high"].max(), "low": r["low"].min(),
                        "close": r["close"].last(), "volume": r["volume"].sum(),
                        "iid": r["instrument_id"].last()})
    return out.dropna(subset=["close"])


def roll_dates(f5: pd.DataFrame) -> set[str]:
    ny = f5.index.tz_convert("America/New_York")
    iid = f5["iid"].groupby(ny.strftime("%Y-%m-%d")).last()
    return set(iid.index[iid.ne(iid.shift())][1:])


def half_spread_pts(micro: str) -> dict:
    files = sorted((SRC / "bbo1m").glob("*.dbn.zst"))
    q = pd.concat(db.DBNStore.from_file(f).to_df() for f in files)
    q = q[q["symbol"] == f"{micro}.c.0"]
    ny = q.index.tz_convert("America/New_York")
    mins = ny.hour * 60 + ny.minute
    q = q[(mins >= 570) & (mins < 960) & (ny.dayofweek < 5)]
    hs = (q["ask_px_00"] - q["bid_px_00"]) / 2
    hs = hs[hs > 0]
    return {"median": float(hs.median()), "p90": float(hs.quantile(0.9)), "n": int(len(hs)),
            "from": str(q.index.min().date()), "to": str(q.index.max().date())}


def boot_ci(x: np.ndarray) -> list[float]:
    rng = np.random.default_rng(SEED)
    n = len(x)
    st = rng.integers(0, n, size=(10_000, (n + 4) // 5))
    ix = ((st[:, :, None] + np.arange(5)) % n).reshape(10_000, -1)[:, :n]
    return np.quantile(x[ix].mean(axis=1), [Q_LO, 1 - Q_LO]).tolist()


def nb_daily(tr: pd.DataFrame, dates: list[str], cost_pts: float, cfd_frac: float | None = None) -> pd.Series:
    d = pd.Series(0.0, index=dates)
    if tr.empty:
        return d
    ratio = tr.exit / tr.entry
    frac = (cost_pts / tr.entry) if cfd_frac is None else cfd_frac
    net = tr.direction * (ratio - 1) - frac * (1 + ratio)
    d.update(net.groupby(tr.date).sum())
    return d


def summarize(x: pd.Series, scale: float) -> dict:
    x = x.dropna()
    lo, hi = boot_ci(x.to_numpy()) if len(x) > 20 else (np.nan, np.nan)
    return {"n": len(x), "mean": float(x.mean() * scale), "ci_bonf": [lo * scale, hi * scale],
            "2012-21": float(x[x.index < SPLIT].mean() * scale), "2022+": float(x[x.index >= SPLIT].mean() * scale)}


def run_nb(sym: str, micro: str, cost_pts: float, cfd: float, rolls: set[str], f5: pd.DataFrame) -> dict:
    frame = f5[["open", "high", "low", "close", "volume"]]
    tr, dates = simulate(frame)
    tr = tr[~tr.date.isin(rolls)]
    dates = [d for d in dates if d not in rolls]
    res = {"trades": len(tr)}
    for label, kw in (("zero", dict(cost_pts=0.0)), ("central", dict(cost_pts=cost_pts)),
                      ("pessimistic", dict(cost_pts=2 * cost_pts)), ("maven_cfd", dict(cost_pts=0.0, cfd_frac=cfd))):
        d = nb_daily(tr, dates, **kw)
        ev, ho = d.loc[EVAL[0]:EVAL[1]], d.loc[HOLDOUT[0]:HOLDOUT[1]]
        ev.index, ho.index = ev.index.astype(str), ho.index.astype(str)
        res[label] = {"eval": summarize(ev, 1e4), "holdout_mean_bp": float(ho.mean() * 1e4), "holdout_n": len(ho)}
    c = res["central"]["eval"]
    res["PASS"] = bool(c["ci_bonf"][0] > 0 and c["2012-21"] > 0 and c["2022+"] > 0
                       and res["pessimistic"]["eval"]["mean"] > 0)
    return res


def run_ema(cost_pts: float, cfd: float, rolls: set[str], f5: pd.DataFrame) -> dict:
    frame = f5[["open", "high", "low", "close"]].copy()
    frame.index = frame.index.tz_convert("UTC").tz_localize(None)
    t = ema12_trades(frame)
    t = t[~t.date.isin(rolls)].set_index("date")
    res = {"trades": len(t)}
    for label, cp, frac in (("zero", 0.0, None), ("central", cost_pts, None), ("pessimistic", 2 * cost_pts, None),
                            ("maven_cfd", None, cfd)):
        side = (cp / t["entry"]) if frac is None else frac
        r = t["r_gross"] - 2 * side * t["entry"] / t["risk"]
        ev, ho = r.loc[(r.index >= EVAL[0])], r.loc[(r.index < HOLDOUT[1])]
        res[label] = {"eval": summarize(ev, 1.0), "holdout_mean_R": float(ho.mean()), "holdout_n": len(ho)}
    c = res["central"]["eval"]
    res["PASS"] = bool(c["ci_bonf"][0] > 0 and c["2012-21"] > 0 and c["2022+"] > 0
                       and res["pessimistic"]["eval"]["mean"] > 0)
    res["median_risk_pts"] = float(t["risk"].median())
    return res


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    prof = pd.read_csv(PROFILE).set_index("symbol")["real_cost_per_side_central"]
    out = {"commission_side_usd": COMMISSION_SIDE_USD}
    data = {s: to_5m(load_1m(s)) for s in ("ES.c.0", "NQ.c.0")}
    rolls = {s: roll_dates(f) for s, f in data.items()}
    cost = {}
    for micro, s in (("MES", "ES.c.0"), ("MNQ", "NQ.c.0")):
        hs = half_spread_pts(micro)
        cost[s] = hs["median"] + COMMISSION_SIDE_USD / MULT[micro]
        out[f"spread_{micro}"] = hs
        out[f"cost_side_pts_{micro}"] = cost[s]
        out[f"data_{s}"] = [str(data[s].index.min()), str(data[s].index.max()), len(data[s]), len(rolls[s])]
    out["H1_NB_ES"] = run_nb("ES.c.0", "MES", cost["ES.c.0"], float(prof["SP500"]), rolls["ES.c.0"], data["ES.c.0"])
    out["H2_EMA12_NQ"] = run_ema(cost["NQ.c.0"], float(prof["NASDAQ100"]), rolls["NQ.c.0"], data["NQ.c.0"])
    out["REF_NB_NQ"] = run_nb("NQ.c.0", "MNQ", cost["NQ.c.0"], float(prof["NASDAQ100"]), rolls["NQ.c.0"], data["NQ.c.0"])
    (OUT / "result.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
