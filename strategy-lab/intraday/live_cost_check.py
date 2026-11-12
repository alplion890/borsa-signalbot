"""Diagnostic: live/paper module backtests under config vs Maven-measured cost.

Measured cost = reality_profiler per-side spread + p90 slippage at today's price, held
constant in PRICE POINTS across history (charged per trade against its own stop).
Run reality_profiler first (MT5 open).

    python -m intraday.live_cost_check
"""
from pathlib import Path

import numpy as np
import pandas as pd

from . import donchian_xau_lab as dx
from .config import INSTRUMENTS, Instrument
from .data_quality import clean
from .history_fetch import load_history
from .honest_engine import simulate_trades
from .long_history_ab import _atr_rank, spec_by_name

ROOT = Path(__file__).resolve().parent.parent
prof = pd.read_csv(ROOT / "outputs/intraday/mt5_bridge/reality_profile.csv").set_index("symbol")


# Maven FX commission: $1 per lot per side (deal history 2026: EURUSD, USDJPY) ~ 1e-5 of notional.
# Index CFDs showed zero commission (US30). XAU commission not observed -> treated as zero (unknown).
FX_COMMISSION = 0.00001
FX = {"EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "USDCHF", "EURJPY", "GBPJPY"}


def pts(sym):  # per-side cost in price points, measured at today's price
    r = prof.loc[sym]
    comm = FX_COMMISSION if sym in FX else 0.0
    return (float((r.spread_one_side_now + r.slippage_p90 + comm) * r.price_now),
            float((r.spread_one_side_now + comm) * r.price_now))


def zero(sym):
    b = INSTRUMENTS[sym]
    return Instrument(b.key, b.duka, 0.0, b.session_utc, b.pip)


def report(name, sym, df, le, se, lsl, ltp, ssl, stp, **kw):
    r0 = simulate_trades(df, le, se, lsl, ltp, ssl, stp, zero(sym), **kw)
    entry = df["close"].reindex(r0.index)
    risk = np.where(le.reindex(r0.index), entry - lsl.reindex(r0.index), ssl.reindex(r0.index) - entry)
    cfg = INSTRUMENTS[sym].cost_per_side
    full, spread_only = pts(sym)
    out = {"modul": name, "n": len(r0), "maliyetsiz": r0.mean(),
           "config": (r0 - 2 * cfg * entry / risk).mean(),
           "olculen(spread+kayma)": (r0 - 2 * full / risk).mean(),
           "yalniz_spread": (r0 - 2 * spread_only / risk).mean(),
           "medyan_stop_puan": float(np.median(risk))}
    for lab, a, b in (("<2022", None, "2022"), (">=2022", "2022", None)):
        m = (r0.index < pd.Timestamp(b)) if b else (r0.index >= pd.Timestamp(a))
        out[f"olculen {lab}"] = (r0[m] - 2 * full / risk[m]).mean()
        out[f"config {lab}"] = (r0[m] - 2 * cfg * entry[m] / risk[m]).mean()
    return out


def main() -> None:
    rows = []
    nq15 =clean(load_history("NASDAQ100", "15m", start_year=2012))
    sp = spec_by_name("SWEEP_CORE")
    le, se, lsl, ltp, ssl, stp = sp.build(nq15)
    rank = _atr_rank(nq15)
    cap = pd.Series(np.select([rank < .33, rank < .67], [4., 6.], default=8.), index=nq15.index)
    ltp = pd.Series(np.minimum(ltp, nq15.close + (nq15.close - lsl) * cap), index=nq15.index)
    stp = pd.Series(np.maximum(stp, nq15.close - (ssl - nq15.close) * cap), index=nq15.index)
    ok = rank.notna()
    rows.append(report("SWEEP_CORE (LIVE)", "NASDAQ100", nq15, le & ok, se & ok, lsl, ltp, ssl, stp,
                       min_rr=sp.min_rr, max_rr=sp.max_rr, max_hold=sp.max_hold))

    nq5 = clean(load_history("NASDAQ100", "5m", start_year=2012))
    so = spec_by_name("NQ_ORB")
    rows.append(report("NQ_ORB adx28 (~CAND_RT_NQ_ORB)", "NASDAQ100", nq5, *so.build(nq5),
                       min_rr=so.min_rr, max_rr=so.max_rr, max_hold=so.max_hold))

    for name, sym in (("EUR_LONDON", "EURUSD"), ("GBP_LONDON", "GBPUSD"), ("GOLD_ORB", "XAUUSD")):
        d5 = clean(load_history(sym, "5m", start_year=2012))
        sx = spec_by_name(name)
        rows.append(report(f"{name} (emekli)", sym, d5, *sx.build(d5),
                           min_rr=sx.min_rr, max_rr=sx.max_rr, max_hold=sx.max_hold))

    x1 = dx._resample_1h(clean(load_history("XAUUSD", "5m", start_year=2012)))
    rows.append(report("DONCHIAN XAU N20 1H", "XAUUSD", x1, *dx.build_signals(x1, dx.DonchianCase(20)),
                       min_rr=dx.RR - 0.01, max_rr=dx.RR, max_hold=dx.MAX_HOLD_BARS))

    pd.set_option("display.width", 250)
    print(pd.DataFrame(rows).round(3).T.to_string())
    print({s: pts(s) for s in ("NASDAQ100", "XAUUSD", "EURUSD", "GBPUSD")})


if __name__ == "__main__":
    main()
