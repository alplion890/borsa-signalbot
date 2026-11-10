"""ET range bar, first close break, stop/target geometry and one trade per day."""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import mnq_orb_video_lab as lab


def _day(date: str, utc_offset_h: int) -> pd.DataFrame:
    """One ET session 09:00-16:30 with a 9:15 range 100-101, long break at 9:45."""
    et = pd.date_range(f"{date} 09:00", f"{date} 16:30", freq="15min")
    idx = et + pd.Timedelta(hours=utc_offset_h)        # to naive UTC
    n = len(idx)
    df = pd.DataFrame({"open": 100.5, "high": 100.8, "low": 100.2, "close": 100.5, "volume": 1.0}, index=idx)
    hm = et.strftime("%H:%M")
    df.loc[hm == "09:15", ["high", "low"]] = [101.0, 100.0]
    df.loc[hm == "09:45", ["open", "high", "low", "close"]] = [100.6, 101.6, 100.4, 101.4]
    df.loc[hm == "10:00", ["high", "low"]] = [102.0, 101.2]   # hits 0.5R target 101.9
    df.loc[hm == "10:15", ["close"]] = [99.0]                 # later break below must be ignored
    df.loc[hm == "10:15", ["low"]] = [98.9]
    assert n > 20
    return df


def test_dst_aware_range_and_single_trade():
    for date, off in (("2026-01-15", 5), ("2026-07-15", 4)):   # EST vs EDT
        df = _day(date, off)
        sig = lab.signals(df)
        assert sig["le"].sum() == 1 and sig["se"].sum() == 0
        i = sig["le"].to_numpy().nonzero()[0][0]
        assert np.isclose(sig["lsl"].iloc[i], 100.4)
        assert np.isclose(sig["ltp"].iloc[i], 101.4 + 0.5 * 1.0)


def test_target_hit_gives_half_r_before_cost():
    df = _day("2026-07-15", 4)
    r = lab.run(df, lab.signals(df), cost_mult=0.0)
    assert len(r) == 1 and np.isclose(r.iloc[0], 0.5)


def test_eod_flat_mask_marks_close_bar():
    df = _day("2026-07-15", 4)
    flat = lab.signals(df)["flat"]
    et_hm = (df.index.tz_localize("UTC").tz_convert("America/New_York")).strftime("%H:%M")
    assert flat[et_hm == "15:45"].all() and not flat[et_hm == "12:00"].any()
