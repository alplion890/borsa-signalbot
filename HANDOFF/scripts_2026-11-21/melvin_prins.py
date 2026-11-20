"""Melvin-Prins month-end FX hedging test (prereg HANDOFF/melvin_prins_onkayit_2026-11-21.md, commit 0d6b456).

Run from strategy-lab with the vectorbt-lab venv:
  python ../HANDOFF/scripts_2026-11-21/melvin_prins.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, ".")
from intraday.data_quality import clean  # noqa: E402
from intraday.history_fetch import load_history  # noqa: E402

OUT = Path("outputs/intraday/melvin_prins")
LON = "Europe/London"
FX = {"EUR": ("EURUSD", 1), "GBP": ("GBPUSD", 1), "JPY": ("USDJPY", -1)}   # sign: foreign-currency return
EQ = {"US": ["SP500"], "EUR": ["GER40", "FRA40"], "GBP": ["UK100"], "JPY": ["JAP225"]}
COST = {"EUR": 0.233e-4, "GBP": 0.189e-4, "JPY": 0.220e-4}   # Maven reality_profile 2026-11-12, central, per side
BLOCKS = {"2013-17": ("2013", "2017"), "2018-21": ("2018", "2021"), "2022-23": ("2022", "2023"), "2024-26": ("2024", "2026")}
SEED = 20261121


def snap_close(df: pd.DataFrame) -> pd.Series:
    x = df["close"]
    day = x.index.normalize()
    keep = x.index.hour < 21
    s = x[keep].groupby(day[keep]).last()
    return s[s.index.dayofweek < 5]


def london_px(df: pd.DataFrame, day: pd.Timestamp, hhmm: str) -> float:
    """Open of the 5m bar starting at hh:mm London time on `day` (index is naive UTC)."""
    t = pd.Timestamp(f"{day.date()} {hhmm}", tz=LON).tz_convert("UTC").tz_localize(None)
    return float(df["open"].get(t, np.nan))


def equity_logret(closes: dict[str, pd.Series], country: str, d0: pd.Timestamp, d1: pd.Timestamp) -> float:
    rs = [np.log(closes[s].get(d1, np.nan) / closes[s].get(d0, np.nan)) for s in EQ[country]]
    return float(np.mean(rs))


def build() -> pd.DataFrame:
    fx = {k: clean(load_history(sym, "5m", start_year=2012)) for k, (sym, _) in FX.items()}
    syms = sorted({s for v in EQ.values() for s in v})
    closes = {s: snap_close(clean(load_history(s, "5m", start_year=2012))) for s in syms}
    common = closes["SP500"].index
    for s in syms:
        common = common.intersection(closes[s].index)
    fxdays = fx["EUR"].index.normalize().unique()
    rows = []
    for (y, m), days in pd.Series(fxdays, index=fxdays).groupby([fxdays.year, fxdays.month]):
        days = days[days.dt.dayofweek < 5]
        if y < 2013 or len(days) < 10:
            continue
        T = days.iloc[-1]
        eqd = common[(common.year == y) & (common.month == m) & (common < T)]
        if len(eqd) < 10:
            continue
        d0, d1 = eqd[0], eqd[-1]           # first trading day close -> T-1 close
        nxt = fxdays[fxdays > T]
        for c, (sym, sgn) in FX.items():
            p15, p16 = london_px(fx[c], T, "15:00"), london_px(fx[c], T, "16:00")
            p12n = london_px(fx[c], nxt[0], "12:00") if len(nxt) else np.nan
            s = equity_logret(closes, c, d0, d1) - equity_logret(closes, "US", d0, d1)
            rows.append(dict(T=T, ccy=c, s=s, r_pre=sgn * (p16 / p15 - 1), r_post=sgn * (p12n / p16 - 1)))
    return pd.DataFrame(rows)


def pnl(df: pd.DataFrame, cmult: float) -> pd.Series:
    pos = -np.sign(df["s"])
    cost = df["ccy"].map(COST) * 2 * cmult * (pos != 0)
    x = pos * df["r_pre"] - cost
    return x.groupby(df["T"]).mean()


def boot_p(x: pd.Series) -> float:
    a = x.to_numpy()
    rng = np.random.default_rng(SEED)
    means = (a - a.mean())[rng.integers(0, len(a), size=(10000, len(a)))].mean(axis=1)
    return float((means >= a.mean()).mean())


def blocks(x: pd.Series) -> dict:
    return {k: float(x.loc[a:b].mean() * 1e4) for k, (a, b) in BLOCKS.items()}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    df = build()
    miss = int(df["r_pre"].isna().sum())
    df = df.dropna(subset=["r_pre", "s"])
    df.to_csv(OUT / "month_ends.csv", index=False)
    res = {"n_months": int(df["T"].nunique()), "n_trades": len(df), "missing_fix_bars": miss,
           "period": [str(df["T"].min().date()), str(df["T"].max().date())]}
    for name, cm in (("c0", 0.0), ("c1", 1.0), ("c2", 2.0)):
        x = pnl(df, cm)
        res[name] = {"mean_bp": float(x.mean() * 1e4), "se_bp": float(x.std() / np.sqrt(len(x)) * 1e4),
                     "hit": float((x > 0).mean()), "blocks_bp": blocks(x)}
    x1 = pnl(df, 1.0)
    res["p_1x"] = boot_p(x1)
    res["pos_blocks_1x"] = int(sum(v > 0 for v in res["c1"]["blocks_bp"].values()))
    res["PASS"] = bool(res["p_1x"] <= 0.05 and res["pos_blocks_1x"] >= 3 and res["c2"]["mean_bp"] > 0)
    gross = -np.sign(df["s"]) * df["r_pre"]
    res["by_ccy_gross_bp"] = {c: float(g.mean() * 1e4) for c, g in gross.groupby(df["ccy"])}
    res["slope_rpre_on_s"] = float(np.polyfit(df["s"], df["r_pre"], 1)[0])   # paper: -0.0142 (demeaned panel)
    k1 = df.dropna(subset=["r_post"])
    res["K1_post_fix_reversal_gross_bp"] = float((-np.sign(k1["r_pre"]) * k1["r_post"]).mean() * 1e4)
    w = -df["s"] / df["s"].abs().mean()
    res["K2_linear_weight_gross_bp"] = float((w * df["r_pre"]).groupby(df["T"]).mean().mean() * 1e4)
    (OUT / "result.json").write_text(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
