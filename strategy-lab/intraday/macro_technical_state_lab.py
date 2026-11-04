"""Mevcut edge'lerden bagimsiz makro + 1s durum + 5d giris stratejileri.

Ornek hipotez: DXY yukari, Gold 1s EMA20 ve rolling VWAP20 altinda,
ADX>25; 5d EMA20 asagi yeniden kiriliminda short.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from .config import INSTRUMENTS
from .cross_asset_positioning_ab import (_daily_context, _macro_sources,
                                          _positioning_sources)
from .edge_lab import _adx
from .hierarchical_edge_lab import asof_weekly
from .history_fetch import load_history
from .honest_engine import simulate_trades
from .indicators import atr, ema
from .macro_context_ab import _summary
from .overfit_stats import (align_trials, deflated_from_trials,
                            probability_of_backtest_overfitting)

OUT = (Path(__file__).resolve().parent.parent / "outputs" / "intraday" /
       "macro_technical_state_lab")
ASSETS = {
    "NQ_STATE": ("NASDAQ100", "NQ_ORB", "nq"),
    "GOLD_STATE": ("XAUUSD", "GOLD_ORB", "gold"),
    "EUR_STATE": ("EURUSD", "EUR_LONDON", "eur"),
    "GBP_STATE": ("GBPUSD", "GBP_LONDON", "gbp"),
}
CONTEXTS = ("technical", "dxy", "macro", "macro_cot", "macro_cot_oi")


def rolling_vwap(frame: pd.DataFrame, window: int = 20) -> pd.Series:
    typical = (frame["high"] + frame["low"] + frame["close"]) / 3.0
    volume = frame["volume"].clip(lower=1e-9)
    return ((typical * volume).rolling(window).sum() /
            volume.rolling(window).sum())


def hourly_frame(df: pd.DataFrame) -> pd.DataFrame:
    return df.resample("1h", closed="left", label="right").agg({
        "open": "first", "high": "max", "low": "min", "close": "last",
        "volume": "sum",
    }).dropna()


def hourly_setup(df: pd.DataFrame, adx_min: float = 25.0) -> tuple[pd.Series, pd.Series]:
    """Yalniz kapanmis 1s bar: EMA20 + rolling VWAP20 + ADX durumu."""
    hourly = hourly_frame(df)
    e20 = ema(hourly["close"], 20)
    vw20 = rolling_vwap(hourly, 20)
    strong = _adx(hourly, 14) > adx_min
    long = strong & (hourly["close"] > e20) & (hourly["close"] > vw20)
    short = strong & (hourly["close"] < e20) & (hourly["close"] < vw20)
    return (long.reindex(df.index, method="ffill").fillna(False).astype(bool),
            short.reindex(df.index, method="ffill").fillna(False).astype(bool))


def five_minute_trigger(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    e20 = ema(df["close"], 20)
    long = ((df["close"].shift(1) <= e20.shift(1)) & (df["close"] > e20) &
            (df["close"] > df["open"]))
    short = ((df["close"].shift(1) >= e20.shift(1)) & (df["close"] < e20) &
             (df["close"] < df["open"]))
    return long, short


def _session(index: pd.DatetimeIndex, symbol: str) -> pd.Series:
    start, end = INSTRUMENTS[symbol].session_utc
    hour = index.hour
    return pd.Series((hour >= start) & (hour < end), index=index)


def _simulate(symbol: str, df: pd.DataFrame, long: pd.Series,
              short: pd.Series, max_hold: int = 24) -> pd.Series:
    risk = atr(df, 14)
    price = df["close"]
    return simulate_trades(
        df, long, short,
        price - risk, price + 1.5 * risk,
        price + risk, price - 1.5 * risk,
        INSTRUMENTS[symbol], min_rr=1.49, max_rr=1.5, max_hold=max_hold,
    )


def run(refresh: bool = False) -> dict:
    OUT.mkdir(parents=True, exist_ok=True)
    sources = _macro_sources(refresh)
    positioning = _positioning_sources(refresh, 2026)
    report = {
        "design": {
            "strategy": "macro regime + closed 1h EMA20/VWAP20/ADX + 5m EMA20 recross",
            "adx": ">25", "exit": "1 ATR stop, 1.5R target, 24x5m max hold",
            "discovery": "2012-2021", "oos": "2022-2026",
            "contexts": list(CONTEXTS),
            "entries": ["5m EMA20 recross", "first closed 1h state"],
        }, "assets": {},
    }
    for label, (symbol, module, market) in ASSETS.items():
        df = load_history(symbol, "5m", start_year=2012)
        setup_l, setup_s = hourly_setup(df)
        trigger_l, trigger_s = five_minute_trigger(df)
        weekly = asof_weekly(df.index, positioning, market)
        dates = pd.DatetimeIndex(df.index.normalize().unique())
        daily = _daily_context(module, dates, sources)
        macro = daily.reindex(df.index.normalize()).set_axis(df.index)
        valid = (weekly[["oi_change", "cot_change"]].notna().all(axis=1) &
                 macro["valid"].fillna(False) & _session(df.index, symbol))
        base_l, base_s = valid & setup_l & trigger_l, valid & setup_s & trigger_s
        dxy_l, dxy_s = macro["dxy"] <= 0, macro["dxy"] >= 0
        macro_l, macro_s = macro["score"] > 0, macro["score"] < 0
        cot_l, cot_s = weekly["cot_change"] >= 0, weekly["cot_change"] <= 0
        oi = weekly["oi_change"] >= 0
        masks_5m = {
            "technical": (base_l, base_s),
            "dxy": (base_l & dxy_l, base_s & dxy_s),
            "macro": (base_l & macro_l, base_s & macro_s),
            "macro_cot": (base_l & macro_l & cot_l,
                          base_s & macro_s & cot_s),
            "macro_cot_oi": (base_l & macro_l & cot_l & oi,
                             base_s & macro_s & cot_s & oi),
        }
        trials = {f"m5_{name}": _simulate(symbol, df, lm, sm)
                  for name, (lm, sm) in masks_5m.items()}

        # Kullanıcının doğrudan örneği: bütün durum ilk kez oluştuğunda,
        # kapanmış 1s mumda tek giriş. 5d yeniden kırılımı beklenmez.
        h = hourly_frame(df)
        h_e20, h_vw20 = ema(h["close"], 20), rolling_vwap(h, 20)
        h_strong = _adx(h, 14) > 25.0
        h_setup_l = h_strong & (h["close"] > h_e20) & (h["close"] > h_vw20)
        h_setup_s = h_strong & (h["close"] < h_e20) & (h["close"] < h_vw20)
        h_weekly = asof_weekly(h.index, positioning, market)
        h_macro = daily.reindex(h.index.normalize()).set_axis(h.index)
        h_valid = (h_weekly[["oi_change", "cot_change"]].notna().all(axis=1) &
                   h_macro["valid"].fillna(False) & _session(h.index, symbol))
        h_dxy_l, h_dxy_s = h_macro["dxy"] <= 0, h_macro["dxy"] >= 0
        h_macro_l, h_macro_s = h_macro["score"] > 0, h_macro["score"] < 0
        h_cot_l = h_weekly["cot_change"] >= 0
        h_cot_s = h_weekly["cot_change"] <= 0
        h_oi = h_weekly["oi_change"] >= 0
        h_contexts = {
            "technical": (h_valid & h_setup_l, h_valid & h_setup_s),
            "dxy": (h_valid & h_setup_l & h_dxy_l,
                    h_valid & h_setup_s & h_dxy_s),
            "macro": (h_valid & h_setup_l & h_macro_l,
                      h_valid & h_setup_s & h_macro_s),
            "macro_cot": (h_valid & h_setup_l & h_macro_l & h_cot_l,
                          h_valid & h_setup_s & h_macro_s & h_cot_s),
            "macro_cot_oi": (h_valid & h_setup_l & h_macro_l & h_cot_l & h_oi,
                             h_valid & h_setup_s & h_macro_s & h_cot_s & h_oi),
        }
        for name, (lm, sm) in h_contexts.items():
            le = lm & ~lm.shift(1, fill_value=False)
            se = sm & ~sm.shift(1, fill_value=False)
            trials[f"h1_{name}"] = _simulate(symbol, h, le, se, max_hold=8)
        if label == "GOLD_STATE":
            false_5m = pd.Series(False, index=df.index)
            trials["m5_exact_gold_short"] = _simulate(
                symbol, df, false_5m, masks_5m["dxy"][1]
            )
            false_1h = pd.Series(False, index=h.index)
            gold_short_state = h_contexts["dxy"][1]
            gold_short_entry = gold_short_state & ~gold_short_state.shift(
                1, fill_value=False
            )
            trials["h1_exact_gold_short"] = _simulate(
                symbol, h, false_1h, gold_short_entry, max_hold=8
            )
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
            "symbol": symbol,
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
