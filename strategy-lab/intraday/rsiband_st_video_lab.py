"""YouTube 'ücretsiz al-sat sistemi' testi: RSI Bands + Supertrend + RSI (+TDI), Heikin Ashi.

Ön-kayıt: HANDOFF/rsiband_supertrend_video_onkayit_2026-11-07.md (koşumdan önce commit).
Göstergeler HA mumlarından hesaplanır (video grafiği HA); dolumlar gerçek OHLC'den
`honest_engine.simulate_trades` ile yapılır. Parametreler ön-kayıtta sabittir.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from .btc_data import load_btc
from .config import INSTRUMENTS
from .data import load_ohlcv
from .honest_engine import metrics, simulate_trades
from .indicators import atr

OUT = Path(__file__).resolve().parent.parent / "outputs" / "intraday" / "rsiband_st_video"

RSIB_LEN, RSIB_OB, RSIB_OS = 12, 70.0, 30.0
ST_ATR, ST_MULT = 10, 0.8
TDI_RSI, TDI_SLOW = 11, 9
RSI_LEN, RSI_MA = 10, 14
ARM_BARS = 30
BUFFERS = (0.0, 0.5, 1.0)
PRIMARY_BUFFER = 0.5
MIN_RR, MAX_RR, MAX_HOLD = 0.01, 20.0, 480


# ---------------------------------------------------------------- göstergeler
def heikin_ashi(df: pd.DataFrame) -> pd.DataFrame:
    o, h, l, c = (df[k].to_numpy(dtype=float) for k in ("open", "high", "low", "close"))
    hc = (o + h + l + c) / 4.0
    ho = np.empty_like(hc)
    ho[0] = (o[0] + c[0]) / 2.0
    for i in range(1, len(hc)):
        ho[i] = (ho[i - 1] + hc[i - 1]) / 2.0
    hh = np.maximum.reduce([h, ho, hc])
    hl = np.minimum.reduce([l, ho, hc])
    return pd.DataFrame({"open": ho, "high": hh, "low": hl, "close": hc}, index=df.index)


def rsi_tv(src: pd.Series, n: int) -> pd.Series:
    """TradingView RSI (RMA)."""
    d = src.diff()
    up = d.clip(lower=0).ewm(alpha=1 / n, adjust=False).mean()
    dn = (-d).clip(lower=0).ewm(alpha=1 / n, adjust=False).mean()
    rs = up / dn.replace(0, np.nan)
    return (100 - 100 / (1 + rs)).fillna(100.0)


def rsi_bands(src: pd.Series, n: int, ob: float, os_: float) -> tuple[pd.Series, pd.Series]:
    """LazyBear RSIBANDS_LB: RSI'ın ob/os seviyesine ulaşacağı fiyat."""
    ep = 2 * n - 1
    d = src.diff()
    auc = d.clip(lower=0).ewm(span=ep, adjust=False).mean()
    adc = (-d).clip(lower=0).ewm(span=ep, adjust=False).mean()

    def level(lv: float) -> pd.Series:
        x = (n - 1) * (adc * lv / (100 - lv) - auc)
        return pd.Series(np.where(x >= 0, src + x, src + x * (100 - lv) / lv), index=src.index)

    return level(ob), level(os_)


def supertrend_dir(ha: pd.DataFrame, period: int, mult: float) -> np.ndarray:
    """Kivanc Supertrend (hl2, RMA ATR) yön dizisi: +1 / -1."""
    a = atr(ha, period).to_numpy()
    src = ((ha["high"] + ha["low"]) / 2).to_numpy()
    c = ha["close"].to_numpy()
    n = len(c)
    up = src - mult * a
    dn = src + mult * a
    trend = np.ones(n, dtype=int)
    for i in range(1, n):
        if c[i - 1] > up[i - 1]:
            up[i] = max(up[i], up[i - 1])
        if c[i - 1] < dn[i - 1]:
            dn[i] = min(dn[i], dn[i - 1])
        prev = trend[i - 1]
        if prev == -1 and c[i] > dn[i - 1]:
            trend[i] = 1
        elif prev == 1 and c[i] < up[i - 1]:
            trend[i] = -1
        else:
            trend[i] = prev
    return trend


def _cross_up(a: pd.Series, b: pd.Series) -> np.ndarray:
    return ((a > b) & (a.shift() <= b.shift())).to_numpy()


def _cross_dn(a: pd.Series, b: pd.Series) -> np.ndarray:
    return ((a < b) & (a.shift() >= b.shift())).to_numpy()


# ---------------------------------------------------------------- sinyaller
def _sequence(arm: np.ndarray, cross: np.ndarray, tdi: np.ndarray, flip: np.ndarray,
              need_tdi: bool) -> np.ndarray:
    """silahlan -> RSI kesişimi -> ilk Supertrend dönüşü. Her dönüş durumu sıfırlar."""
    n = len(arm)
    sig = np.zeros(n, dtype=bool)
    armed, crossed, tdi_ok = -1, False, False
    for i in range(n):
        if arm[i]:
            armed, crossed, tdi_ok = i, False, False
        if armed >= 0 and i - armed > ARM_BARS:
            armed, crossed, tdi_ok = -1, False, False
        if armed >= 0:
            crossed = crossed or bool(cross[i])
            tdi_ok = tdi_ok or bool(tdi[i])
        if flip[i]:
            if armed >= 0 and crossed and (tdi_ok or not need_tdi):
                sig[i] = True
            armed, crossed, tdi_ok = -1, False, False
    return sig


def build(df: pd.DataFrame) -> dict:
    """Gerçek OHLC -> HA göstergeleri, iki varyant için long/short sinyal ve bantlar."""
    ha = heikin_ashi(df)
    ub, lb = rsi_bands(ha["close"], RSIB_LEN, RSIB_OB, RSIB_OS)
    trend = supertrend_dir(ha, ST_ATR, ST_MULT)
    buy = np.r_[False, (trend[1:] == 1) & (trend[:-1] == -1)]
    sell = np.r_[False, (trend[1:] == -1) & (trend[:-1] == 1)]
    r = rsi_tv(ha["close"], RSI_LEN)
    r_ma = r.rolling(RSI_MA).mean()
    t = rsi_tv(ha["close"], TDI_RSI)
    t_slow = t.rolling(TDI_SLOW).mean()
    arm_l = (ha["low"] < lb).to_numpy()
    arm_s = (ha["high"] > ub).to_numpy()
    out = {"ub": ub, "lb": lb, "atr": atr(df, 14)}
    for name, need in (("A", False), ("B", True)):
        out[name] = (
            pd.Series(_sequence(arm_l, _cross_up(r, r_ma), _cross_up(t, t_slow), buy, need), index=df.index),
            pd.Series(_sequence(arm_s, _cross_dn(r, r_ma), _cross_dn(t, t_slow), sell, need), index=df.index),
        )
    return out


def run_one(df: pd.DataFrame, key: str, sig: dict, variant: str, buf: float,
            cost_mult: float = 1.0, side: str = "both") -> pd.Series:
    base = INSTRUMENTS[key]
    inst = type(base)(base.key, base.duka, base.cost_per_side * cost_mult, base.session_utc, base.pip)
    le, se = sig[variant]
    if side == "long":
        se = se & False
    elif side == "short":
        le = le & False
    lsl = sig["lb"] - buf * sig["atr"]
    ssl = sig["ub"] + buf * sig["atr"]
    return simulate_trades(df, le, se, lsl, sig["ub"], ssl, sig["lb"], inst,
                           min_rr=MIN_RR, max_rr=MAX_RR, max_hold=MAX_HOLD)


def _halves(r: pd.Series, df: pd.DataFrame) -> tuple[float, float]:
    mid = df.index[0] + (df.index[-1] - df.index[0]) / 2
    a, b = r[r.index < mid], r[r.index >= mid]
    f = lambda s: round(float(s.mean()), 3) if len(s) else float("nan")
    return f(a), f(b)


def _resample(df: pd.DataFrame, rule: str) -> pd.DataFrame:
    agg = {"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"}
    return df[list(agg)].resample(rule, label="left", closed="left").agg(agg).dropna()


def universe() -> list[tuple[str, str, pd.DataFrame, bool]]:
    b15 = load_btc("15m", 1080)[["open", "high", "low", "close", "volume"]]
    b1h = load_btc("1h", 1080)[["open", "high", "low", "close", "volume"]]
    rows = [("BTCUSDT", "15m", b15, True), ("BTCUSDT", "1h", b1h, True),
            ("BTCUSDT", "4h", _resample(b1h, "4h"), True)]
    for k in ("EURUSD", "GBPUSD", "XAUUSD", "NASDAQ100"):
        d15 = load_ohlcv(k, "15m", 1080)
        rows += [(k, "15m", d15, False), (k, "1h", _resample(d15, "1h"), False)]
    return rows


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    rows = []
    for key, tf, df, primary in universe():
        sig = build(df)
        for variant in ("A", "B"):
            for buf in BUFFERS:
                r1 = run_one(df, key, sig, variant, buf, 1.0)
                r2 = run_one(df, key, sig, variant, buf, 2.0)
                h1, h2 = _halves(r1, df)
                m = metrics(r1)
                row = {"sym": key, "tf": tf, "primary": primary, "var": variant, "buf": buf,
                       "n": m["trades"], "exp_r": m["exp_r"], "wr": m["win_rate"], "pf": m["pf"],
                       "exp_r_2x": metrics(r2)["exp_r"], "half1": h1, "half2": h2,
                       "start": str(df.index[0].date()), "end": str(df.index[-1].date())}
                if variant == "A" and buf == PRIMARY_BUFFER:
                    for side in ("long", "short"):
                        ms = metrics(run_one(df, key, sig, variant, buf, 1.0, side))
                        row[f"{side}_n"], row[f"{side}_exp_r"] = ms["trades"], ms["exp_r"]
                    row["avg_win"], row["avg_loss"] = m.get("avg_win"), m.get("avg_loss")
                    row["candidate"] = bool(
                        m["trades"] >= 30 and m["exp_r"] > 0 and row["exp_r_2x"] > 0
                        and h1 > 0 and h2 > 0)
                rows.append(row)
    res = pd.DataFrame(rows)
    res.to_csv(OUT / "result_2026-11-07.csv", index=False)
    prim = res[(res["var"] == "A") & (res["buf"] == PRIMARY_BUFFER)]
    verdict = "ADAY" if prim[prim["primary"]]["candidate"].any() else "ELENDI"
    (OUT / "result_2026-11-07.json").write_text(json.dumps(
        {"verdict": verdict, "primary": prim.to_dict("records")}, indent=1, default=str), encoding="utf8")
    with pd.option_context("display.width", 250, "display.max_columns", 30, "display.max_rows", 200):
        print(prim.drop(columns=["primary"]).to_string(index=False))
        print()
        print(res[["sym", "tf", "var", "buf", "n", "exp_r", "exp_r_2x", "half1", "half2"]].to_string(index=False))
    print("\nKARAR (ön-kayıt):", verdict)


if __name__ == "__main__":
    main()
