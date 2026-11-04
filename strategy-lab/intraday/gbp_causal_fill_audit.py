"""Offline preregistered GBP London range and fill diagnostics."""
from dataclasses import replace
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from .config import INSTRUMENTS
from .honest_engine import simulate_trades, FILL_BAR_SL_FIRST, FILL_1M_THEN_SL_FIRST
from .internet_seed_strategies import _build_london
from .long_history_ab import _GBP_LONDON, spec_by_name

LAB = Path(__file__).resolve().parents[1]
DATA = LAB / 'outputs/intraday/research_panel/broker_history/GBPUSD_5m_0e6bc3aa01604047.csv'
OUT = LAB / 'outputs/intraday/fairness_audit/20261027'
EXPECTED = '0e6bc3aa01604047a044d2d5cf99dee119a87ef7d8c67f22b7aa9aa7d3c9fe87'


def build(frame):
    le, se, *levels = _build_london(frame, _GBP_LONDON)
    dates = frame.index.normalize()
    minute = frame.index.hour * 60 + frame.index.minute
    window = frame.loc[(minute >= 0) & (minute < 420)]
    groups = window.groupby(window.index.normalize())
    complete = groups.apply(lambda g: list(g.index.hour * 60 + g.index.minute) == list(range(0, 420, 5)))
    summary = groups.agg(high=('high', 'max'), low=('low', 'min'), close=('close', 'last'))
    values = ((summary.high-summary.low)/summary.close).where(complete).dropna()
    ranks = values.rolling(20, min_periods=10).rank(pct=True)
    eligible = pd.Series(dates.map(ranks).to_numpy(), index=frame.index).between(.33, .67, inclusive='right') & (minute >= 420)
    return le & eligible, se & eligible, *levels


def run():
    raw = DATA.read_bytes()
    if hashlib.sha256(raw).hexdigest() != EXPECTED:
        raise ValueError('Snapshot hash mismatch')
    df = pd.read_csv(DATA, index_col=0, parse_dates=True)
    if not df.index.is_monotonic_increasing or not df.index.is_unique:
        raise ValueError('Invalid timestamps')
    df = df.loc[df.index < '2026-10-15']
    signals = build(df)
    mask = df.index >= '2026-04-16'
    signals = (signals[0] & mask, signals[1] & mask, *signals[2:])
    spec = spec_by_name('GBP_LONDON')
    results, series = [], {}
    for mode in (FILL_BAR_SL_FIRST, FILL_1M_THEN_SL_FIRST):
        for factor in (1, 2, 3):
            inst = replace(INSTRUMENTS['GBPUSD'], cost_per_side=INSTRUMENTS['GBPUSD'].cost_per_side*factor)
            r = simulate_trades(df, *signals, inst, min_rr=spec.min_rr, max_rr=spec.max_rr, max_hold=spec.max_hold, fill_mode=mode)
            results.append(dict(mode=mode, factor=factor, n=len(r), total_r=float(r.sum()), mean_r=float(r.mean()) if len(r) else None))
            series[(mode, factor)] = r
            r.to_csv(OUT / f'GBP_causal_{mode}_{factor}x.csv', header=['net_r'])
    a, b = series[(FILL_BAR_SL_FIRST,1)], series[(FILL_1M_THEN_SL_FIRST,1)]
    common = a.index.intersection(b.index)
    output = dict(data_sha256=EXPECTED, code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), plan_sha256=hashlib.sha256((OUT/'GBP_DUZELTME_ONKAYIT.md').read_bytes()).hexdigest(), period='2026-04-16 through 2026-10-14 UTC', results=results, common_signal_times=len(common), only_close=len(a.index.difference(b.index)), only_next_open=len(b.index.difference(a.index)), mean_r_delta_common=float((b.loc[common]-a.loc[common]).mean()) if len(common) else None, limitations=['No 1-minute data: ambiguity resolves stop-first', 'Historical snapshot, not unseen OOS', 'Next-open reprices target to preserve RR', 'Signal time index is not actual fill timestamp'])
    (OUT/'GBP_causal_fill_results.json').write_text(json.dumps(output, indent=2),encoding='utf-8')
    print(json.dumps(output, indent=2))


if __name__ == '__main__':
    run()
