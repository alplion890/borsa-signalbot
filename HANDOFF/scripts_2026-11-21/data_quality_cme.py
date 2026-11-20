"""Data-quality check: Dukascopy CFD 5m vs CME futures (Databento ohlcv-1m resampled to 5m).

Metrics fixed before looking at results (not a strategy test):
  1. coverage: share of NY cash-session 5m bars present in each source
  2. return agreement: correlation of 5m log returns (cash session), daily 21:00 UTC returns
  3. clock check: correlation at lags -2..+2 bars (peak must be at 0; else time offset / DST bug)
  4. artifacts: zero-range bars and |5m return| > 10 sigma present in one source but not the other
  5. per-year table of 1-3
Roll days (instrument_id change in the continuous series) are dropped from return comparisons.
Run from repo root with the vectorbt-lab venv:
  python HANDOFF/scripts_2026-11-21/data_quality_cme.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import databento as db
import numpy as np
import pandas as pd

sys.path.insert(0, "strategy-lab")
from intraday.data_quality import clean  # noqa: E402
from intraday.history_fetch import load_history  # noqa: E402

SRC = Path("strategy-lab/outputs/databento")
OUT = Path("strategy-lab/outputs/intraday/data_quality_cme")
PAIRS = {"NQ.c.0": ("NASDAQ100", "5m"), "ES.c.0": ("SP500", "5m")}
NY = "America/New_York"


def load_cme() -> pd.DataFrame:
    files = sorted(SRC.rglob("*ohlcv-1m*.dbn.zst"))
    if not files:
        raise SystemExit("no ohlcv-1m dbn file under strategy-lab/outputs/databento")
    df = pd.concat(db.DBNStore.from_file(f).to_df() for f in files)
    df.index = df.index.tz_convert("UTC").tz_localize(None)
    return df


def to_5m(g: pd.DataFrame) -> pd.DataFrame:
    r = g.resample("5min", label="left", closed="left")
    out = pd.DataFrame({"open": r["open"].first(), "high": r["high"].max(), "low": r["low"].min(),
                        "close": r["close"].last(), "iid": r["instrument_id"].last()})
    return out.dropna(subset=["close"])


def cash_mask(idx: pd.DatetimeIndex) -> np.ndarray:
    ny = idx.tz_localize("UTC").tz_convert(NY)
    m = ny.hour * 60 + ny.minute
    return (ny.dayofweek < 5) & (m >= 9 * 60 + 30) & (m < 16 * 60)


def compare(cme: pd.DataFrame, duka: pd.DataFrame) -> dict:
    roll_days = set(cme.index[cme["iid"].ne(cme["iid"].shift())].normalize())
    c_cash = cme[cash_mask(cme.index)]
    d_cash = duka[cash_mask(duka.index)]
    days = c_cash.index.normalize().unique().intersection(d_cash.index.normalize().unique())
    days = days.difference(pd.DatetimeIndex(sorted(roll_days)))
    res = {"common_days": len(days)}
    # 1 coverage (per day 78 bars expected in a full cash session)
    cc = c_cash.index.normalize().value_counts().reindex(days).fillna(0)
    dc = d_cash.index.normalize().value_counts().reindex(days).fillna(0)
    res["coverage_cme"] = float((cc / 78).clip(upper=1).mean())
    res["coverage_duka"] = float((dc / 78).clip(upper=1).mean())
    # 2 returns on common bars, same day only
    j = pd.concat({"c": np.log(c_cash["close"]), "d": np.log(d_cash["close"])}, axis=1, join="inner")
    j = j[j.index.normalize().isin(days)]
    r = j.groupby(j.index.normalize()).diff().dropna()
    res["n_5m_returns"] = len(r)
    res["corr_5m"] = float(r["c"].corr(r["d"]))
    res["lag_corr"] = {k: float(r["c"].corr(r["d"].groupby(r.index.normalize()).shift(-k)))
                       for k in (-2, -1, 0, 1, 2)}
    # daily 21:00 UTC snapshot returns
    def snap(x: pd.DataFrame) -> pd.Series:
        k = x[x.index.hour < 21]
        return np.log(k["close"].groupby(k.index.normalize()).last())
    dd = pd.concat({"c": snap(cme).diff(), "d": snap(duka).diff()}, axis=1, join="inner").dropna()
    dd = dd[dd.index.isin(days)]
    res["corr_daily"] = float(dd["c"].corr(dd["d"]))
    res["daily_abs_diff_bp_median"] = float((dd["c"] - dd["d"]).abs().median() * 1e4)
    # 4 artifacts
    res["zero_range_cash_bars"] = {"cme": int((c_cash["high"] == c_cash["low"]).sum()),
                                   "duka": int((d_cash["high"] == d_cash["low"]).sum())}
    sd = r.std()
    big_d = r.index[(r["d"].abs() > 10 * sd["d"]) & (r["c"].abs() < 3 * sd["c"])]
    big_c = r.index[(r["c"].abs() > 10 * sd["c"]) & (r["d"].abs() < 3 * sd["d"])]
    res["spikes_only_in_duka"] = [str(t) for t in big_d[:50]]
    res["spikes_only_in_cme"] = [str(t) for t in big_c[:50]]
    res["n_spikes_only_duka"], res["n_spikes_only_cme"] = len(big_d), len(big_c)
    # 5 per year
    yr = {}
    for y, g in r.groupby(r.index.year):
        lag = {k: g["c"].corr(g["d"].groupby(g.index.normalize()).shift(-k)) for k in (-1, 0, 1)}
        yr[int(y)] = {"corr_5m": round(float(g["c"].corr(g["d"])), 3), "n": len(g),
                      "best_lag": int(max(lag, key=lambda k: lag[k]))}
    res["per_year"] = yr
    return res


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    cme_all = load_cme()
    out = {}
    for sym, (dsym, tf) in PAIRS.items():
        g = cme_all[cme_all["symbol"] == sym]
        cme = to_5m(g)
        duka = clean(load_history(dsym, tf, start_year=2010))
        out[sym] = compare(cme, duka)
        print(sym, json.dumps({k: v for k, v in out[sym].items() if not k.startswith("spikes")}, indent=1))
    (OUT / "result.json").write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
