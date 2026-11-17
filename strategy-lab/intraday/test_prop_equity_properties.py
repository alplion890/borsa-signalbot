"""Property tests for prop_equity: intraday (equity-based) path building and challenge simulation."""
import numpy as np
import pandas as pd
from hypothesis import given, settings, strategies as st

from intraday.prop_equity import combine, run
from intraday.prop_fit import Rules

EPS = 1e-9
pnl = st.floats(-0.03, 0.03)
excursion = st.floats(0.0, 0.03)


@st.composite
def strategy_parts(draw):
    """1-3 strategies over the same days: (close, low, high) with low <= min(close,0), high >= max(close,0)."""
    n = draw(st.integers(1, 15))
    idx = pd.date_range("2024-01-01", periods=n, freq="D")
    parts = []
    for _ in range(draw(st.integers(1, 3))):
        c = np.array(draw(st.lists(pnl, min_size=n, max_size=n)))
        dn = np.array(draw(st.lists(excursion, min_size=n, max_size=n)))
        up = np.array(draw(st.lists(excursion, min_size=n, max_size=n)))
        df = pd.DataFrame({"close": c, "low": np.minimum(c, 0) - dn, "high": np.maximum(c, 0) + up}, index=idx)
        parts.append((df, draw(st.sampled_from([0.5, 1.0, 2.0]))))
    return parts


def _combine_reference(parts):
    """Strategies run one after another inside the day: each one's dip/spike sits on top of the
    P&L already closed by the earlier ones."""
    days = parts[0][0].index
    rows = []
    for d in days:
        closed, low, high = 0.0, 0.0, 0.0
        for df, k in parts:
            c, lo, hi = (df.loc[d, col] * k for col in ("close", "low", "high"))
            low, high = min(low, closed + lo), max(high, closed + hi)
            closed += c
        rows.append((closed, low, high))
    return np.array(rows)


@settings(max_examples=200, deadline=None)
@given(strategy_parts())
def test_combine_matches_sequential_rulebook(parts):
    got = combine(parts)[["close", "low", "high"]].to_numpy()
    assert np.allclose(got, _combine_reference(parts), atol=EPS)


@settings(max_examples=200, deadline=None)
@given(strategy_parts())
def test_combined_day_envelope_contains_close(parts):
    got = combine(parts)
    assert (got["low"] <= 0 + EPS).all() and (got["high"] >= 0 - EPS).all()
    assert (got["low"] <= got["close"] + EPS).all() and (got["close"] <= got["high"] + EPS).all()


@st.composite
def equity_path(draw):
    n = draw(st.integers(21, 45))  # run() starts a challenge at every day except the last 20
    c = np.array(draw(st.lists(st.floats(-0.04, 0.04), min_size=n, max_size=n)))
    dn = np.array(draw(st.lists(st.floats(0.0, 0.05), min_size=n, max_size=n)))
    up = np.array(draw(st.lists(excursion, min_size=n, max_size=n)))
    return pd.DataFrame({"close": c, "low": np.minimum(c, 0) - dn, "high": np.maximum(c, 0) + up})


def _challenge_reference(c, lo, rules):
    """Phase 1 on equity: breach if the intraday low touches the static floor, pass on close >= target."""
    out = []
    for s in range(max(len(c) - 20, 1)):
        bal, res = 0.0, 0
        for i in range(s, min(s + rules.horizon_days, len(c))):
            if bal + lo[i] <= -rules.static_dd:
                res = -1
                break
            bal += c[i]
            if bal >= rules.target:
                res = 1
                break
        out.append(res)
    return np.array(out)


@settings(max_examples=60, deadline=None)
@given(equity_path())
def test_equity_challenge_matches_rulebook(path):
    rules = Rules()
    got = run(path, rules, equity=True)
    ref = _challenge_reference(path["close"].to_numpy(), path["low"].to_numpy(), rules)
    assert abs(got["challenge_pass"] - (ref == 1).mean() * 100) < EPS
    assert abs(got["challenge_fail"] - (ref == -1).mean() * 100) < EPS


@settings(max_examples=60, deadline=None)
@given(equity_path())
def test_equity_view_never_fails_less_than_closed_view(path):
    # intraday lows are <= closed lows, so the equity model can only breach earlier, never later
    rules = Rules()
    eq, closed = run(path, rules, equity=True), run(path, rules, equity=False)
    assert eq["challenge_fail"] + EPS >= closed["challenge_fail"]
    assert eq["funded_breach"] + EPS >= closed["funded_breach"]
