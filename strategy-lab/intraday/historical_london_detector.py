"""Historical London detector mirror for research only; no runtime registration."""
import numpy as np
import pandas as pd
from .edge_lab import _adx
from .internet_seed_strategies import LondonCase, _build_london
from .forward_ea.modules import Signal

def _london_detector(case: LondonCase, adx_min: float = 0.0,
                     adx_max: float = 0.0, dow: int | None = None,
                     range_regime: str | None = None):
    """Genel London breakout dedektoru (EUR/GBP).

    Filtreler final ledger'dan birebir geri cikarildi:
      EUR: adx<20 (chop) + Persembe (dow=3)
      GBP: Persembe (dow=3) + ema (case icinde)
    """
    def detect(df: pd.DataFrame) -> Signal | None:
        if len(df) < 200:
            return None
        le, se, lsl, ltp, ssl, stp = _build_london(df, case)
        i = -1
        if dow is not None and df.index[i].dayofweek != dow:
            return None
        if range_regime is not None:
            h = df.index.hour + df.index.minute / 60.0
            in_range = (h >= case.range_start) & (h < case.range_end)
            daily_hi = df["high"].where(in_range).groupby(df.index.date).transform("max")
            daily_lo = df["low"].where(in_range).groupby(df.index.date).transform("min")
            range_pct = (daily_hi - daily_lo) / df["close"]
            daily_range = range_pct.groupby(df.index.date).last()
            rank = daily_range.rolling(20, min_periods=10).rank(pct=True).iloc[-1]
            current_regime = (
                "tight_range" if rank <= 0.33
                else "normal_range" if rank <= 0.67
                else "wide_range"
            )
            if pd.isna(rank) or current_regime != range_regime:
                return None
        adx_val = _adx(df, 14).iloc[i]
        if adx_min > 0 and not (adx_val > adx_min):
            return None
        if adx_max > 0 and not (adx_val < adx_max):
            return None
        if bool(le.iloc[i]):
            return Signal(1, float(df["close"].iloc[i]), float(lsl.iloc[i]), float(ltp.iloc[i]))
        if bool(se.iloc[i]):
            return Signal(-1, float(df["close"].iloc[i]), float(ssl.iloc[i]), float(stp.iloc[i]))
        return None
    return detect


