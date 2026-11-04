"""Literatur tabanli seans ici momentum backtesti.

Ilk 30 dakika getirisi onceki seans kapanisina gore yonu belirler. Son 30
dakikada ayni yone girilir ve seans kapanisinda cikilir. Yuksek ilk-30-dakika
araligi ve hacmi onceden tanimli kosullardir.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from .config import INSTRUMENTS
from .history_fetch import load_history
from .macro_context_ab import _summary
from .overfit_stats import (align_trials, deflated_from_trials,
                            probability_of_backtest_overfitting)

OUT = (Path(__file__).resolve().parent.parent / "outputs" / "intraday" /
       "intraday_momentum_research_lab")
VARIANTS = ("all_days", "high_range", "high_volume", "high_range_volume")


@dataclass(frozen=True)
class Session:
    symbol: str
    timezone: str
    open_minute: int
    close_minute: int


SESSIONS = {
    "NQ": Session("NASDAQ100", "America/New_York", 9 * 60 + 30, 16 * 60),
    "GOLD": Session("XAUUSD", "America/New_York", 8 * 60 + 20, 13 * 60 + 30),
    "EUR": Session("EURUSD", "Europe/London", 8 * 60, 16 * 60 + 30),
    "GBP": Session("GBPUSD", "Europe/London", 8 * 60, 16 * 60 + 30),
}


def session_observations(df: pd.DataFrame, session: Session) -> pd.DataFrame:
    local = pd.DatetimeIndex(df.index).tz_localize("UTC").tz_convert(session.timezone)
    minute = local.hour * 60 + local.minute
    in_session = (minute >= session.open_minute) & (minute < session.close_minute)
    work = df.loc[in_session].copy()
    work["local_date"] = local[in_session].date
    work["local_minute"] = minute[in_session]
    rows = []
    for date, day in work.groupby("local_date", sort=True):
        first = day[(day["local_minute"] >= session.open_minute) &
                    (day["local_minute"] < session.open_minute + 30)]
        last = day[(day["local_minute"] >= session.close_minute - 30) &
                   (day["local_minute"] < session.close_minute)]
        if len(first) < 5 or len(last) < 5:
            continue
        rows.append({
            "date": date,
            "entry_utc": last.index[0],
            "first_close": float(first["close"].iloc[-1]),
            "first_range": float(first["high"].max() - first["low"].min()),
            "first_volume": float(first["volume"].sum()),
            "entry": float(last["open"].iloc[0]),
            "exit": float(last["close"].iloc[-1]),
            "last_high": float(last["high"].max()),
            "last_low": float(last["low"].min()),
            "session_close": float(day["close"].iloc[-1]),
        })
    out = pd.DataFrame(rows).set_index("entry_utc").sort_index()
    out["previous_close"] = out["session_close"].shift(1)
    out["signal"] = np.sign(out["first_close"] - out["previous_close"])
    out["range_median20"] = out["first_range"].shift(1).rolling(20).median()
    out["volume_median20"] = out["first_volume"].shift(1).rolling(20).median()
    out["high_range"] = out["first_range"] > out["range_median20"]
    out["high_volume"] = out["first_volume"] > out["volume_median20"]
    return out.dropna()


def returns_r(obs: pd.DataFrame, session: Session, variant: str) -> pd.Series:
    mask = obs["signal"] != 0
    if variant in {"high_range", "high_range_volume"}:
        mask &= obs["high_range"]
    if variant in {"high_volume", "high_range_volume"}:
        mask &= obs["high_volume"]
    x = obs.loc[mask]
    risk = x["first_range"]
    direction = x["signal"]
    stopped = (((direction > 0) & (x["last_low"] <= x["entry"] - risk)) |
               ((direction < 0) & (x["last_high"] >= x["entry"] + risk)))
    raw = direction * (x["exit"] - x["entry"]) / risk
    raw.loc[stopped] = -1.0
    cost = INSTRUMENTS[session.symbol].cost_per_side
    raw -= 2.0 * cost / (risk / x["entry"])
    return raw.replace([np.inf, -np.inf], np.nan).dropna().sort_index()


def run() -> dict:
    OUT.mkdir(parents=True, exist_ok=True)
    report = {
        "design": {
            "signal": "previous session close to first 30m close direction",
            "trade": "same direction during final 30m; exit at session close",
            "risk": "first 30m range; stop-loss-first; measured costs",
            "filters": list(VARIANTS), "discovery": "2012-2021", "oos": "2022-2026",
        }, "assets": {},
    }
    for label, session in SESSIONS.items():
        df = load_history(session.symbol, "5m", start_year=2012)
        obs = session_observations(df, session)
        trials = {name: returns_r(obs, session, name) for name in VARIANTS}
        discovery = {k: v[v.index.year <= 2021] for k, v in trials.items()}
        rows = []
        folder = OUT / label
        folder.mkdir(parents=True, exist_ok=True)
        for name, result in trials.items():
            is_r = result[result.index.year <= 2021]
            oos_r = result[result.index.year >= 2022]
            rows.append({"variant": name,
                         **{f"is_{k}": v for k, v in _summary(is_r).items()},
                         **{f"oos_{k}": v for k, v in _summary(oos_r).items()},
                         **{f"full_{k}": v for k, v in _summary(result).items()}})
            result.rename("R").to_csv(folder / f"trades_{name}.csv",
                                      index_label="entry_utc")
        pd.DataFrame(rows).to_csv(folder / "variants.csv", index=False)
        report["assets"][label] = {
            "session": session.__dict__,
            "discovery_multiple_test": deflated_from_trials(discovery),
            "pbo": probability_of_backtest_overfitting(align_trials(discovery)),
            "variants": rows,
        }
    (OUT / "report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False, default=str), encoding="utf-8"
    )
    return report


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, ensure_ascii=False, default=str))
