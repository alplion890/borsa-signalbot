"""Unit tests for intraday.edge5k_adaylari (no network, synthetic data)."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from intraday.edge5k_adaylari import (
    c1_month_endpoints,
    eval_c5,
    is_early_close,
    pre_holiday_days,
    rth_close_hm,
    trades_c2,
    trades_c3,
    trades_c4,
    trades_c6,
    trades_c7,
    trades_c8,
)
from intraday.kaynak_adaylari import NY, nyse_days


def _ny_bars(spec: list[tuple[str, str, float, float, float, float]]) -> pd.DataFrame:
    """Build 5m OHLC DataFrame with naive UTC index from (ny_date, ny_hm, o, h, l, c)."""
    rows = []
    idx = []
    for d, hm, o, h, l, c in spec:
        ts = pd.Timestamp(f"{d} {hm}", tz=NY).tz_convert("UTC").tz_localize(None)
        idx.append(ts)
        rows.append({"open": o, "high": h, "low": l, "close": c, "volume": 100.0})
    return pd.DataFrame(rows, index=pd.DatetimeIndex(idx, name="timestamp")).sort_index()


def _rth_day_bars(d: str, o: float, h: float, l: float, c: float, close_hm: str = "15:55") -> list[tuple[str, str, float, float, float, float]]:
    return [
        (d, "09:30", o, h, l, o),
        (d, "09:35", o, h, l, o),
        (d, "09:40", o, h, l, o),
        (d, "09:45", o, h, l, o),
        (d, close_hm, o, h, l, c),
    ]


def test_c1_month_endpoints_good_friday_and_december() -> None:
    days = nyse_days("2022-11-01", "2024-04-30")
    eps = {ex.strftime("%Y-%m"): (en.strftime("%Y-%m-%d"), ex.strftime("%Y-%m-%d"))
           for _, _, en, ex in c1_month_endpoints(days)}
    # 2024-03: Good Friday is 2024-03-29 -> last trading day 2024-03-28, 5th-to-last 2024-03-22
    assert eps["2024-03"] == ("2024-03-22", "2024-03-28")
    # 2022-12: Dec 26 observed Christmas -> last trading day 2022-12-30, 5th-to-last 2022-12-23
    assert eps["2022-12"] == ("2022-12-23", "2022-12-30")


def test_pre_holiday_detection_and_early_close() -> None:
    pre = set(pre_holiday_days("2024-06-01", "2025-02-01").strftime("%Y-%m-%d"))
    assert "2024-07-03" in pre
    assert "2024-11-27" in pre
    assert "2024-12-24" in pre
    assert "2025-01-08" in pre  # day before SPECIAL_CLOSED 2025-01-09
    assert "2024-11-29" not in pre

    assert is_early_close(pd.Timestamp("2024-07-03"))
    assert is_early_close(pd.Timestamp("2024-11-29"))
    assert is_early_close(pd.Timestamp("2024-12-24"))
    assert rth_close_hm(pd.Timestamp("2024-07-03")) == "12:55"

    # C2 exit on 2024-07-03 must use 12:55 ET close (not 15:55)
    spec = (
        _rth_day_bars("2024-07-02", 100.0, 101.0, 99.0, 100.0)
        + [("2024-07-03", "09:30", 100.0, 102.0, 100.0, 100.5),
           ("2024-07-03", "12:55", 101.0, 102.0, 101.0, 102.0),
           ("2024-07-03", "15:55", 99.0, 99.0, 99.0, 99.0)]
    )
    tr = trades_c2(_ny_bars(spec))
    assert len(tr) == 1
    assert tr.loc[0, "entry"] == pytest.approx(100.0)
    assert tr.loc[0, "exit"] == pytest.approx(102.0)
    assert tr.loc[0, "nights"] == 1


def test_c3_third_friday_window() -> None:
    # 2024-05-17 is the 3rd Friday of May 2024; Thursday is 2024-05-16
    spec = (
        _rth_day_bars("2024-05-15", 100.0, 101.0, 99.0, 100.0)
        + _rth_day_bars("2024-05-16", 100.0, 102.0, 99.0, 100.0)
        + [("2024-05-17", "09:30", 100.5, 101.5, 100.0, 101.0),
           ("2024-05-17", "09:35", 101.0, 102.0, 101.0, 102.0),
           ("2024-05-17", "15:55", 102.0, 103.0, 102.0, 103.0)]
    )
    df = _ny_bars(spec)
    tr_long = trades_c3(df, direction=1)
    tr_short = trades_c3(df, direction=-1)
    assert len(tr_long) == 1
    assert tr_long.loc[0, "entry"] == pytest.approx(100.0)
    assert tr_long.loc[0, "exit"] == pytest.approx(101.0)  # close of 09:30 bar (09:35 ET)
    assert tr_long.loc[0, "gross"] == pytest.approx(0.01)
    assert tr_short.loc[0, "gross"] == pytest.approx(-0.01)


def test_c6_synthetic_fill_both_hit_and_large_gap() -> None:
    # Prior days give ATR14 = 10.0 (high-low = 10.0 each day) -> 0.25*ATR = 2.5
    spec = (
        _rth_day_bars("2024-06-03", 100.0, 105.0, 95.0, 100.0)
        + _rth_day_bars("2024-06-04", 100.0, 105.0, 95.0, 100.0)
        # Day 1 (2024-06-05): small gap up (+1.0 < 2.5) + red first 15m candle -> short at 09:45 open, target 100.0 hit
        + [("2024-06-05", "09:30", 101.0, 101.5, 100.8, 100.9),
           ("2024-06-05", "09:35", 100.9, 101.2, 100.5, 100.6),
           ("2024-06-05", "09:40", 100.6, 100.8, 100.3, 100.4),  # candle = 100.4 - 101.0 < 0; stop = 101.5
           ("2024-06-05", "09:45", 100.4, 100.5, 99.8, 100.1),   # hits target 100.0 without touching stop 101.5
           ("2024-06-05", "15:55", 100.1, 101.0, 100.0, 100.5)]
        # Day 2 (2024-06-06): small gap up (+1.0 from 100.5) + red candle, 09:45 bar touches BOTH stop and target -> STOP
        + [("2024-06-06", "09:30", 101.5, 102.0, 101.2, 101.3),
           ("2024-06-06", "09:35", 101.3, 101.5, 101.0, 101.1),
           ("2024-06-06", "09:40", 101.1, 101.2, 100.9, 101.0),  # stop = 102.0, target = 100.5
           ("2024-06-06", "09:45", 101.0, 102.2, 100.3, 100.8),  # touches both 102.0 and 100.5 -> stop fills at 102.0
           ("2024-06-06", "15:55", 100.8, 101.0, 100.5, 100.6)]
        # Day 3 (2024-06-07): large gap (+5.0 >= 2.5) -> no trade
        + [("2024-06-07", "09:30", 105.6, 106.0, 105.0, 105.2),
           ("2024-06-07", "09:35", 105.2, 105.5, 104.8, 105.0),
           ("2024-06-07", "09:40", 105.0, 105.1, 104.5, 104.6),
           ("2024-06-07", "09:45", 104.6, 104.8, 104.0, 104.2),
           ("2024-06-07", "15:55", 104.2, 104.5, 104.0, 104.3)]
    )
    tr = trades_c6(_ny_bars(spec))
    assert len(tr) == 2
    assert tr.loc[0, "direction"] == -1
    assert tr.loc[0, "entry"] == pytest.approx(100.4)
    assert tr.loc[0, "exit"] == pytest.approx(100.0)
    assert tr.loc[0, "gross"] > 0
    assert tr.loc[1, "exit"] == pytest.approx(102.0)
    assert tr.loc[1, "gross"] < 0


def test_c7_direction_opposite_gap() -> None:
    spec = (
        _rth_day_bars("2024-06-10", 100.0, 101.0, 99.0, 100.0)
        + _rth_day_bars("2024-06-11", 102.0, 103.0, 100.0, 101.0)  # gap up -> short (-1)
        + _rth_day_bars("2024-06-12", 99.0, 101.0, 98.0, 100.0)   # gap down -> long (+1)
    )
    tr = trades_c7(_ny_bars(spec))
    assert list(tr["direction"]) == [-1, 1]


def test_c8_window_and_condition() -> None:
    # Mon 2024-06-03 and Tue 2024-06-04 UTC
    idx = pd.to_datetime([
        "2024-06-03 00:00", "2024-06-03 07:55",
        "2024-06-04 00:00", "2024-06-04 07:55",
        "2024-06-05 00:00", "2024-06-05 07:55",
    ])
    df = pd.DataFrame({
        "open": [100.0, 101.0, 100.5, 101.5, 101.0, 101.5],
        "high": [101.0, 102.0, 101.5, 102.5, 102.0, 102.5],
        "low": [99.5, 100.5, 100.0, 101.0, 100.5, 101.0],
        "close": [100.5, 102.0, 101.0, 102.5, 101.5, 102.0],
        "volume": [10.0] * 6,
    }, index=idx)
    tr, full24 = trades_c8(df)
    assert len(tr) == 3
    assert tr.loc[0, "entry_ts"] == pd.Timestamp("2024-06-03 00:00")
    assert tr.loc[0, "exit_ts"] == pd.Timestamp("2024-06-03 08:00")
    assert tr.loc[0, "gross"] == pytest.approx(102.0 / 100.0 - 1.0)
    assert len(full24) == 2  # 2024-06-03 -> 06-04, 2024-06-04 -> 06-05
    assert tr["gross"].mean() > (8.0 / 24.0) * full24.mean()


def test_c5_filter_value_sign() -> None:
    nb = pd.DataFrame({
        "key": pd.to_datetime(["2024-06-04", "2024-06-05"]),
        "gross": [-0.01, 0.02],  # 06-04 losing trade (skipped), 06-05 kept
    })
    vix = pd.Series([25.0, 15.0], index=pd.to_datetime(["2024-06-03", "2024-06-04"]))
    vix3m = pd.Series([20.0, 20.0], index=pd.to_datetime(["2024-06-03", "2024-06-04"]))
    res, skipped = eval_c5(vix, vix3m, cost=0.0001, nb_trades=nb)
    assert res["n_all"] == 2
    assert res["n_skipped"] == 1
    assert len(skipped) == 1
    # -(gross - 2*c) = -(-0.01 - 0.0002) = +0.0102 -> +102 bp
    assert res["central"]["all"]["mean_bp"] == pytest.approx(102.0)


def test_c4_no_lookahead_shift() -> None:
    spec = (
        _rth_day_bars("2024-06-03", 100.0, 101.0, 99.0, 100.0)
        + _rth_day_bars("2024-06-04", 100.0, 102.0, 99.0, 101.0)
    )
    df = _ny_bars(spec)
    idx = pd.to_datetime(["2024-06-03", "2024-06-04"])
    # Prev day (06-03) VIX < VIX3M -> 06-04 trades even if 06-04 VIX > VIX3M
    vix_a = pd.Series([15.0, 30.0], index=idx)
    vix3m = pd.Series([20.0, 20.0], index=idx)
    tr_a, ns_a = trades_c4(df, vix_a, vix3m)
    assert len(tr_a) == 1 and len(ns_a) == 0

    # Changing 06-03 VIX above VIX3M removes 06-04 from signal set
    vix_b = pd.Series([25.0, 10.0], index=idx)
    tr_b, ns_b = trades_c4(df, vix_b, vix3m)
    assert len(tr_b) == 0 and len(ns_b) == 1


def test_c6_target_already_passed_fills_at_open_not_target() -> None:
    # Gap up +1.0 (prev close 100.0); first 15m red and already below target -> short at 09:45 open 99.6.
    # Buy-limit at 100.0 fills immediately at the better open price 99.6 (no fake loss at 100.0).
    spec = (
        _rth_day_bars("2024-06-03", 100.0, 105.0, 95.0, 100.0)
        + _rth_day_bars("2024-06-04", 100.0, 105.0, 95.0, 100.0)
        + [("2024-06-05", "09:30", 101.0, 101.3, 99.7, 100.2),
           ("2024-06-05", "09:35", 100.2, 100.3, 99.6, 99.8),
           ("2024-06-05", "09:40", 99.8, 99.9, 99.5, 99.6),
           ("2024-06-05", "09:45", 99.6, 99.9, 99.4, 99.7),
           ("2024-06-05", "15:55", 99.7, 100.0, 99.5, 99.8)]
    )
    tr = trades_c6(_ny_bars(spec))
    assert len(tr) == 1
    assert tr.loc[0, "direction"] == -1
    assert tr.loc[0, "exit"] == pytest.approx(99.6)
    assert tr.loc[0, "gross"] == pytest.approx(0.0)


def test_pre_holiday_not_flagged_at_data_end() -> None:
    # 2026-11-16 (Mon) is followed by a normal trading day; it must not be a pre-holiday even if data ends there
    assert "2026-11-16" not in set(pre_holiday_days("2026-11-01", "2026-11-16").strftime("%Y-%m-%d"))
