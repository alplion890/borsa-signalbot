import numpy as np
import pandas as pd
import pytest

from intraday.seffaf_adaylari import (
    btc_donchian_weights,
    simulate_b3,
    simulate_b4,
    simulate_b5,
    simulate_b6,
    simulate_b7,
)


def _daily_df(rows: list[tuple[float, float, float, float]], start: str = "2024-01-01") -> pd.DataFrame:
    idx = pd.date_range(start, periods=len(rows), freq="D")
    return pd.DataFrame(rows, index=idx, columns=["open", "high", "low", "close"])


def test_b7_ibs_six_day_single_trade() -> None:
    df = _daily_df([
        (101.0, 102.0, 100.0, 100.1),  # IBS = 0.05 -> enter long at 100.1
        (100.5, 102.0, 100.0, 101.0),  # IBS = 0.50 -> hold
        (101.0, 101.0, 101.0, 101.0),  # H == L -> skip
        (101.0, 105.0, 100.0, 104.5),  # IBS = 0.90 -> exit at 104.5 (3 nights)
        (103.0, 105.0, 100.0, 102.5),  # IBS = 0.50 -> flat
        (102.5, 105.0, 100.0, 103.0),  # IBS = 0.60 -> flat
    ])
    tr = simulate_b7(df)
    assert len(tr) == 1
    assert tr.iloc[0]["gross"] == pytest.approx(104.5 / 100.1 - 1.0)
    assert tr.iloc[0]["nights"] == 3


def test_b5_turtle_soup_age_filter_and_short_return() -> None:
    base = [(100.0, 101.0, 99.0, 100.0) for _ in range(25)]
    base[10] = (100.0, 105.0, 99.0, 100.0)  # prior 20d high, 10 days before day 20
    base[20] = (104.0, 106.0, 103.0, 104.0)  # breaks 105, closes below 105 -> short @ 104
    base[21] = (103.0, 105.0, 101.0, 102.0)  # no stop (105 < 106), exits @ close 102
    base[22] = (102.0, 103.0, 101.0, 102.0)
    base[23] = (102.0, 103.0, 101.0, 102.0)
    base[24] = (102.0, 103.0, 101.0, 102.0)
    tr = simulate_b5(_daily_df(base))
    assert len(tr) == 1
    assert tr.iloc[0]["direction"] == -1
    assert tr.iloc[0]["gross"] == pytest.approx(1.0 - 102.0 / 104.0)

    too_recent = [(100.0, 101.0, 99.0, 100.0) for _ in range(25)]
    too_recent[18] = (100.0, 105.0, 99.0, 100.0)  # only 2 days before day 20
    too_recent[20] = (104.0, 106.0, 103.0, 104.0)
    assert simulate_b5(_daily_df(too_recent)).empty


def test_b6_williams_oops_fill_and_no_fill() -> None:
    fills = _daily_df([
        (100.0, 102.0, 98.0, 100.0),
        (97.0, 99.0, 96.5, 99.0),  # open < 98, high >= 98 -> long @ 98, exit @ 99
    ])
    tr = simulate_b6(fills)
    assert len(tr) == 1
    assert tr.iloc[0]["direction"] == 1
    assert tr.iloc[0]["entry"] == pytest.approx(98.0)
    assert tr.iloc[0]["gross"] == pytest.approx(99.0 / 98.0 - 1.0)

    no_fill = _daily_df([
        (100.0, 102.0, 98.0, 100.0),
        (97.0, 97.5, 96.5, 97.0),  # high < 98 -> never fills
    ])
    assert simulate_b6(no_fill).empty


def test_b3_breakeven_stop_move_to_entry_plus_0_1r() -> None:
    h1_idx = pd.date_range("2024-01-01", periods=240, freq="1h")
    # Steadily rising D1 closes so D1 EMA100 is strictly rising
    d1_idx = pd.date_range("2024-01-01", periods=10, freq="1D")
    d1 = pd.DataFrame(
        {"open": 100.0, "high": 102.0, "low": 99.0, "close": np.linspace(100.0, 110.0, 10)},
        index=d1_idx,
    )
    o = np.full(240, 100.0)
    h = np.full(240, 101.0)
    l = np.full(240, 99.0)
    c = np.full(240, 100.0)

    # Bar 230 triggers long breakout above 101.0; entry at bar 231 open = 102.0
    c[230] = 102.0
    o[231], h[231], l[231], c[231] = 102.0, 120.0, 102.0, 103.0  # hits +1R easily
    o[232], h[232], l[232], c[232] = 102.5, 102.5, 100.0, 101.0  # retraces through entry + 0.1R
    o[233:], h[233:], l[233:], c[233:] = 100.5, 100.8, 100.2, 100.5

    h1 = pd.DataFrame({"open": o, "high": h, "low": l, "close": c}, index=h1_idx)
    tr = simulate_b3(h1, d1)
    assert len(tr) == 1
    assert tr.iloc[0]["reason"] == "stop"
    assert tr.iloc[0]["exit"] > tr.iloc[0]["entry"]
    # Verify exact entry + 0.1R exit (gross > 0 and < 1R)
    r_pct = tr.iloc[0]["gross"]
    assert 0.004 < r_pct < 0.02


def test_b4_flat_at_18_utc() -> None:
    idx = pd.date_range("2024-01-01 00:00", periods=240, freq="30min")
    # Downtrend then sharp rally at 14:00 UTC (bar closes 14:30) to force EMA20 > EMA50 & close > EMA200
    c = np.linspace(105.0, 95.0, 240)
    o = c.copy()
    h = c + 0.1
    l = c - 0.1
    bar_1400 = int(np.where((idx.day == 5) & (idx.hour == 14) & (idx.minute == 0))[0][0])
    for k in range(bar_1400, 240):
        o[k] = 108.0
        h[k] = 108.2
        l[k] = 107.8
        c[k] = 108.1
    bar_1800 = int(np.where((idx.day == 5) & (idx.hour == 18) & (idx.minute == 0))[0][0])
    o[bar_1800] = 110.0

    m30 = pd.DataFrame({"open": o, "high": h, "low": l, "close": c}, index=idx)
    tr = simulate_b4(m30)
    assert len(tr) >= 1
    first = tr.iloc[0]
    assert first["reason"] == "flat_18utc"
    assert pd.Timestamp(first["exit_time"]) == idx[bar_1800]
    assert first["exit"] == pytest.approx(110.0)


def test_b2_weights_capped_at_2_and_zero_turnover_when_constant() -> None:
    # Monotonically rising series with tiny alternating positive steps -> all 9 models always long,
    # realized vol > 0 and very small -> leverage capped at 2.0, turnover == 0 after warmup
    steps = np.array([0.0001 if i % 2 == 0 else 0.0002 for i in range(420)])
    close = pd.Series(100.0 * np.cumprod(1.0 + steps), index=pd.date_range("2023-01-01", periods=420, freq="D"))
    w = btc_donchian_weights(close)
    total = w.sum(axis=1)
    assert np.allclose(total.iloc[-30:], 2.0)
    turnover = (w - w.shift(1)).abs().sum(axis=1).iloc[-30:]
    assert np.allclose(turnover, 0.0)
