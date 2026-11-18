"""Fixed k x ATR14 stop added to stopless modules (preregistration HANDOFF/stop_testi_onkayit_2026-11-18.md).

Entry/exit rules of each module are unchanged; only a fixed stop from entry is added. Stop is checked on every
path bar between entry and exit (NQ 5m incl. overnight, BTC 1h): gap through stop fills at bar open, otherwise
at the stop price. ATR14 (Wilder, daily bars) uses only days completed before the entry date.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from .history_fetch import load_history
from .kaynak_adaylari import NY, SPLIT, boot_bounds, cost_of, nyse_days, us_closes
from .seffaf_adaylari import load_btc_1h, resample_btc_daily, resample_nq_daily, wilder_atr

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "intraday" / "stop_testi"
NB_TRADES = ROOT / "outputs" / "intraday" / "noise_band" / "14y" / "trades.csv"
KS: tuple[float | None, ...] = (None, 0.5, 1.0, 1.5, 2.0, 3.0, 4.0)
N_TESTS = 5
B7_SWAP_PER_NIGHT = 0.000118


# ---------- path & ATR helpers ----------

class Path5:
    """Ordered OHLC path with int64 ns bar-start timestamps (naive UTC)."""

    def __init__(self, df: pd.DataFrame) -> None:
        df = df.sort_index()
        self.t = pd.DatetimeIndex(df.index).asi8
        self.o = df["open"].to_numpy(float)
        self.h = df["high"].to_numpy(float)
        self.l = df["low"].to_numpy(float)

    def span(self, t0: pd.Timestamp, t1: pd.Timestamp) -> slice:
        """Bars whose start is in [t0, t1)."""
        a = np.searchsorted(self.t, pd.Timestamp(t0).value, side="left")
        b = np.searchsorted(self.t, pd.Timestamp(t1).value, side="left")
        return slice(a, b)


def first_stop(o: np.ndarray, h: np.ndarray, l: np.ndarray, direction: int, stop: float) -> float | None:
    """Fill price of the first stop hit on the path, or None. Gap through stop fills at the bar open."""
    hit = np.flatnonzero(l <= stop) if direction == 1 else np.flatnonzero(h >= stop)
    if hit.size == 0:
        return None
    i = hit[0]
    return float(min(o[i], stop)) if direction == 1 else float(max(o[i], stop))


def adverse(o: np.ndarray, h: np.ndarray, l: np.ndarray, direction: int, entry: float) -> float:
    """Maximum adverse excursion as a positive price distance (0 if never adverse)."""
    if o.size == 0:
        return 0.0
    return float(max(0.0, entry - l.min())) if direction == 1 else float(max(0.0, h.max() - entry))


# ---------- trade builders (no stop: reproduce module rules) ----------

def apply_stop(path: Path5, tr: pd.DataFrame, k: float | None) -> pd.DataFrame:
    """Given base trades (entry_ts, exit_ts, direction, entry, exit, atr) apply a fixed k*ATR stop."""
    exits, stopped, mae = [], [], []
    for row in tr.itertuples(index=False):
        sl = path.span(row.entry_ts, row.exit_ts)
        o, h, l = path.o[sl], path.h[sl], path.l[sl]
        mae.append(adverse(o, h, l, row.direction, row.entry))
        px = None
        if k is not None:
            stop = row.entry - row.direction * k * row.atr
            px = first_stop(o, h, l, row.direction, stop)
        exits.append(row.exit if px is None else px)
        stopped.append(px is not None)
    out = tr.copy()
    out["exit"] = exits
    out["stopped"] = stopped
    out["mae_atr"] = np.asarray(mae) / tr["atr"].to_numpy(float)
    out["gross"] = out["direction"] * (out["exit"] / out["entry"] - 1.0)
    return out


def nq_context() -> tuple[Path5, pd.DataFrame, np.ndarray]:
    raw = load_history("NASDAQ100", "5m", start_year=2012)
    daily = resample_nq_daily(raw)
    atr_through = wilder_atr(daily, 14).to_numpy(float)
    return Path5(raw), daily, atr_through


def btc_context() -> tuple[Path5, pd.DataFrame, np.ndarray]:
    h1 = load_btc_1h()
    daily = resample_btc_daily(h1)
    return Path5(h1), daily, wilder_atr(daily, 14).to_numpy(float)


def atr_before(dates: pd.DatetimeIndex, daily: pd.DataFrame, atr_through: np.ndarray) -> np.ndarray:
    """ATR through the last completed daily bar strictly before each date."""
    pos = np.searchsorted(pd.DatetimeIndex(daily.index).asi8, pd.DatetimeIndex(dates).asi8, side="left") - 1
    vals = np.full(len(pos), np.nan)
    ok = pos >= 0
    vals[ok] = atr_through[pos[ok]]
    return vals


def ny_close_utc(d: pd.Timestamp) -> pd.Timestamp:
    """16:00 New York on NY date d, as naive UTC."""
    return (pd.Timestamp(d.date()).tz_localize(NY) + pd.Timedelta(hours=16)).tz_convert("UTC").tz_localize(None)


def base_tom(daily: pd.DataFrame, atr_through: np.ndarray) -> pd.DataFrame:
    cl = us_closes("NASDAQ100")
    rows = []
    for p, d in zip(cl.index[:-1], cl.index[1:]):
        if p.month == d.month:
            continue
        rows.append(dict(key=d, entry_ts=ny_close_utc(p), exit_ts=ny_close_utc(d), direction=1,
                         entry=float(cl[p]), exit=float(cl[d]), nights=(d - p).days))
    tr = pd.DataFrame(rows)
    tr["atr"] = atr_before(pd.DatetimeIndex(tr["key"]), daily, atr_through)
    return tr


def base_nb(daily: pd.DataFrame, atr_through: np.ndarray) -> pd.DataFrame:
    nb = pd.read_csv(NB_TRADES)
    ets = pd.to_datetime(nb["entry_time"], utc=True).dt.tz_localize(None)
    xts = pd.to_datetime(nb["exit_time"], utc=True).dt.tz_localize(None)
    tr = pd.DataFrame(dict(key=pd.to_datetime(nb["date"]), entry_ts=ets, exit_ts=xts,
                           direction=nb["direction"].astype(int), entry=nb["entry"].astype(float),
                           exit=nb["exit"].astype(float), nights=0))
    tr["atr"] = atr_before(pd.DatetimeIndex(tr["key"]), daily, atr_through)
    return tr


def base_btc_21_23(path_df: pd.DataFrame, daily: pd.DataFrame, atr_through: np.ndarray) -> pd.DataFrame:
    o = path_df["open"]
    start = o[o.index.hour == 21]
    end = o.reindex(start.index + pd.Timedelta(hours=2))
    tr = pd.DataFrame(dict(key=start.index.normalize(), entry_ts=start.index, exit_ts=end.index, direction=1,
                           entry=start.to_numpy(), exit=end.to_numpy(), nights=0)).dropna()
    tr = tr[~tr["key"].duplicated()].reset_index(drop=True)
    tr["atr"] = atr_before(pd.DatetimeIndex(tr["key"]), daily, atr_through)
    return tr


def btc_overnight_frame(h1: pd.DataFrame) -> pd.DataFrame:
    """Same rule as kaynak_adaylari.btc_overnight: long NY 16:00 open -> next NYSE day 10:00 open."""
    o = h1["open"]
    utc = pd.DatetimeIndex(o.index)
    days = nyse_days(str(utc[0].date()), str(utc[-1].date()))
    rows = []
    for d, nxt in zip(days[:-1], days[1:]):
        t0 = (pd.Timestamp(d.date()).tz_localize(NY) + pd.Timedelta(hours=16)).tz_convert("UTC").tz_localize(None)
        t1 = (pd.Timestamp(nxt.date()).tz_localize(NY) + pd.Timedelta(hours=10)).tz_convert("UTC").tz_localize(None)
        if t0 in o.index and t1 in o.index:
            rows.append((t0, t1, float(o[t0]), float(o[t1]), (nxt - d).days))
    return pd.DataFrame(rows, columns=["t0", "t1", "entry", "exit", "nights"])


def base_btc_gece(h1: pd.DataFrame, daily: pd.DataFrame, atr_through: np.ndarray) -> pd.DataFrame:
    ov = btc_overnight_frame(h1)
    tr = pd.DataFrame(dict(entry_ts=ov["t0"], exit_ts=ov["t1"], direction=1,
                           entry=ov["entry"].to_numpy(), exit=ov["exit"].to_numpy(),
                           nights=ov["nights"].to_numpy()))
    tr["key"] = pd.DatetimeIndex(tr["entry_ts"]).normalize()
    tr["atr"] = atr_before(pd.DatetimeIndex(tr["key"]), daily, atr_through)
    return tr.reset_index(drop=True)


# ---------- B7 (stop changes the trade set via re-entry) ----------

def b7_trades(raw_path: Path5, daily: pd.DataFrame, atr_through: np.ndarray, k: float | None) -> pd.DataFrame:
    """IBS<0.2 long at close when flat; exit at close of first IBS>0.8 day; optional fixed k*ATR stop."""
    h, l, c = (daily[x].to_numpy(float) for x in ("high", "low", "close"))
    dates = pd.DatetimeIndex(daily.index)
    atr_b = atr_before(dates, daily, atr_through)
    closes = [ny_close_utc(d) for d in dates]
    rows, pos = [], None
    for i in range(len(daily)):
        rng = h[i] - l[i]
        ibs = (c[i] - l[i]) / rng if rng > 0 else np.nan
        if pos is not None:
            sl = raw_path.span(closes[i - 1], closes[i])
            px = None if pos["stop"] is None else first_stop(
                raw_path.o[sl], raw_path.h[sl], raw_path.l[sl], 1, pos["stop"])
            if px is not None or (ibs == ibs and ibs > 0.8):
                rows.append(_b7_close(pos, dates[i], px if px is not None else c[i], px is not None, raw_path))
                pos = None
        if pos is None and ibs == ibs and ibs < 0.2 and atr_b[i] == atr_b[i]:
            stop = None if k is None else c[i] - k * atr_b[i]
            pos = dict(key=dates[i], entry_ts=closes[i], entry=c[i], atr=atr_b[i], stop=stop)
    return pd.DataFrame(rows)


def _b7_close(pos: dict, day: pd.Timestamp, px: float, stopped: bool, path: Path5) -> dict:
    exit_ts = ny_close_utc(day)
    sl = path.span(pos["entry_ts"], exit_ts)
    mae = adverse(path.o[sl], path.h[sl], path.l[sl], 1, pos["entry"])
    return dict(key=pos["key"], entry_ts=pos["entry_ts"], exit_ts=exit_ts, direction=1, entry=pos["entry"],
                exit=float(px), nights=int((day - pos["key"]).days), atr=pos["atr"], stopped=stopped,
                mae_atr=mae / pos["atr"], gross=float(px / pos["entry"] - 1.0))


# ---------- evaluation ----------

def metrics(tr: pd.DataFrame, cost: float, k: float | None, swap_per_night: float = 0.0) -> dict:
    tr = tr.dropna(subset=["atr", "gross"]).sort_values("entry_ts")
    scale = (tr["atr"] / tr["entry"]).to_numpy(float)
    when = pd.DatetimeIndex(tr["entry_ts"])
    swap = swap_per_night * tr["nights"].to_numpy(float)
    out: dict = {"k": k, "n": int(len(tr)), "stop_hit_pct": float(100 * tr["stopped"].mean()),
                 "win_pct": float(100 * (tr["gross"] - 2 * cost > 0).mean())}
    alpha = 0.05 / N_TESTS / 2
    for lab, c in (("zero", 0.0), ("central", cost), ("pessimistic", 2 * cost)):
        net = tr["gross"].to_numpy(float) - 2 * c - swap
        r = net / scale
        pre, post = r[when < SPLIT], r[when >= SPLIT]
        out[lab] = {"mean_R": float(r.mean()), "mean_bp": float(net.mean() * 1e4),
                    "sharpe": float(r.mean() / r.std()) if r.std() > 0 else 0.0,
                    "sharpe_is": float(pre.mean() / pre.std()) if len(pre) > 1 else float("nan"),
                    "pre_R": float(pre.mean()) if len(pre) else float("nan"),
                    "post_R": float(post.mean()) if len(post) else float("nan"),
                    "ci_R": [x / 1e4 for x in boot_bounds(r, alpha, 1)]}
    rk = (tr["gross"].to_numpy(float) - 2 * cost - swap) / (scale * (k if k else 1.0))
    out["worst_Rk"] = float(rk.min())
    out["p1_Rk"] = float(np.quantile(rk, 0.01))
    win = tr["gross"] - 2 * cost > 0
    out["mae_winners_atr_p90_p95"] = [float(x) for x in np.quantile(tr.loc[win, "mae_atr"], [0.9, 0.95])]
    return out


def passes(m: dict) -> bool:
    c = m["central"]
    return bool(c["mean_R"] > 0 and c["ci_R"][0] > 0 and c["pre_R"] > 0 and c["post_R"] > 0
                and m["pessimistic"]["mean_R"] > 0)


def select(rows: list[dict]) -> dict:
    """k* = best in-sample (pre-2022) per-trade Sharpe, central cost; 'no stop' is a candidate."""
    return max(rows, key=lambda m: m["central"]["sharpe_is"])


# ---------- runner ----------

def module_rows(name: str, ctx: dict) -> list[dict]:
    if name == "B7_IBS_NQ":
        p, d, a = ctx["nq"]
        return [metrics(b7_trades(p, d, a, k), ctx["c_nq"], k, 0.0) for k in KS]
    base, path, cost = ctx["base"][name], ctx["path"][name], ctx["cost"][name]
    return [metrics(apply_stop(path, base, k), cost, k) for k in KS]


def build_context(names: list[str]) -> dict:
    ctx: dict = {"base": {}, "path": {}, "cost": {}, "c_nq": cost_of("NASDAQ100")}
    nq_names = {"B7_IBS_NQ", "AY_DONUMU_NQ", "NOISE_BAND"} & set(names)
    if nq_names:
        ctx["nq"] = nq_context()
        p, d, a = ctx["nq"]
        if "AY_DONUMU_NQ" in names:
            ctx["base"]["AY_DONUMU_NQ"] = base_tom(d, a)
        if "NOISE_BAND" in names:
            ctx["base"]["NOISE_BAND"] = base_nb(d, a)
        for n in nq_names - {"B7_IBS_NQ"}:
            ctx["path"][n], ctx["cost"][n] = p, ctx["c_nq"]
    btc_names = {"BTC_21_23", "BTC_GECE"} & set(names)
    if btc_names:
        h1 = load_btc_1h()
        p, d, a = btc_context()
        if "BTC_21_23" in names:
            ctx["base"]["BTC_21_23"] = base_btc_21_23(h1, d, a)
        if "BTC_GECE" in names:
            ctx["base"]["BTC_GECE"] = base_btc_gece(h1, d, a)
        for n in btc_names:
            ctx["path"][n], ctx["cost"][n] = p, cost_of("BTCUSDT")
    return ctx


MODULES = ["B7_IBS_NQ", "AY_DONUMU_NQ", "NOISE_BAND", "BTC_21_23", "BTC_GECE"]


def run(names: list[str]) -> dict:
    ctx = build_context(names)
    OUT.mkdir(parents=True, exist_ok=True)
    res = {}
    for n in names:
        rows = module_rows(n, ctx)
        best = select(rows)
        res[n] = {"rows": rows, "k_star": best["k"], "PASS": passes(best)}
        if n == "B7_IBS_NQ":
            p, d, a = ctx["nq"]
            res[n]["k_star_swap"] = metrics(b7_trades(p, d, a, best["k"]), ctx["c_nq"], best["k"], B7_SWAP_PER_NIGHT)
        (OUT / f"{n}.json").write_text(json.dumps(res[n], indent=2, default=str))
        for m in rows:
            c = m["central"]
            print(f"{n} k={m['k']}: n={m['n']} stop%={m['stop_hit_pct']:.0f} win%={m['win_pct']:.0f} "
                  f"R0/Rc/R2x={m['zero']['mean_R']:+.3f}/{c['mean_R']:+.3f}/{m['pessimistic']['mean_R']:+.3f} "
                  f"bp={c['mean_bp']:+.1f} ci=[{c['ci_R'][0]:+.3f},{c['ci_R'][1]:+.3f}] "
                  f"shIS={c['sharpe_is']:.3f} pre/post={c['pre_R']:+.3f}/{c['post_R']:+.3f} "
                  f"worstRk={m['worst_Rk']:.2f} p1Rk={m['p1_Rk']:.2f}")
        print(f"==> {n}: k*={best['k']} PASS={res[n]['PASS']} MAE winners p90/p95 (ATR, no stop)="
              f"{[round(x, 2) for x in rows[0]['mae_winners_atr_p90_p95']]}")
    return res


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="*", default=MODULES)
    run(ap.parse_args().only)


if __name__ == "__main__":
    main()
