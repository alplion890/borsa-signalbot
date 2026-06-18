"""Optional native-speed core for honest_engine.

This module is intentionally tiny: if numba is installed, the hottest
bar-by-bar trade simulation loop runs as compiled machine code. If numba is
missing, honest_engine simply keeps using its pure Python implementation.
"""
from __future__ import annotations

import numpy as np

try:
    from numba import njit
except Exception:  # pragma: no cover - optional dependency
    njit = None


FAST_CORE_AVAILABLE = njit is not None


if FAST_CORE_AVAILABLE:

    @njit(cache=True)
    def simulate_trades_core(
        price,
        high,
        low,
        long_entry,
        short_entry,
        long_sl,
        long_tp,
        short_sl,
        short_tp,
        cost,
        min_rr,
        max_rr,
        max_hold,
    ):
        n = price.shape[0]
        out_i = np.empty(n, dtype=np.int64)
        out_r = np.empty(n, dtype=np.float64)
        out_n = 0
        last_exit = -1

        for i in range(n):
            is_long = long_entry[i]
            is_short = short_entry[i]
            if (not (is_long or is_short)) or i <= last_exit:
                continue

            entry = price[i]
            if is_long:
                sl_px = long_sl[i]
                tp_px = long_tp[i]
            else:
                sl_px = short_sl[i]
                tp_px = short_tp[i]

            if not (np.isfinite(sl_px) and np.isfinite(tp_px)):
                continue

            if is_long:
                risk = entry - sl_px
                reward = tp_px - entry
            else:
                risk = sl_px - entry
                reward = entry - tp_px

            if risk <= 0.0 or reward <= 0.0:
                continue

            rr = reward / risk
            if rr < min_rr:
                continue

            if rr > max_rr:
                if is_long:
                    tp_px = entry + max_rr * risk
                else:
                    tp_px = entry - max_rr * risk
                rr = max_rr

            outcome = np.nan
            end_j = i + 1 + max_hold
            if end_j > n:
                end_j = n

            for j in range(i + 1, end_j):
                if is_long:
                    if low[j] <= sl_px:
                        outcome = -1.0
                        last_exit = j
                        break
                    if high[j] >= tp_px:
                        outcome = rr
                        last_exit = j
                        break
                else:
                    if high[j] >= sl_px:
                        outcome = -1.0
                        last_exit = j
                        break
                    if low[j] <= tp_px:
                        outcome = rr
                        last_exit = j
                        break

            if np.isnan(outcome):
                jx = i + max_hold
                if jx >= n:
                    jx = n - 1
                exitp = price[jx]
                if is_long:
                    move = exitp - entry
                else:
                    move = entry - exitp
                outcome = move / risk
                last_exit = jx

            slf = risk / entry
            outcome -= 2.0 * cost / slf
            out_i[out_n] = i
            out_r[out_n] = outcome
            out_n += 1

        return out_i[:out_n], out_r[:out_n]

else:
    simulate_trades_core = None
