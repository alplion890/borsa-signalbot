"""Fetch WTI, Brent, XAG 5m bid bars from Dukascopy into the history cache (data only, no test).

Run from strategy-lab with the vectorbt-lab venv:
  %USERPROFILE%/vectorbt-lab/.venv/Scripts/python.exe ../HANDOFF/scripts_2026-11-21/fetch_energy_silver.py
"""
from __future__ import annotations

import sys
from datetime import datetime

import pandas as pd

sys.path.insert(0, ".")
from intraday.data import _INTERVALS, _duka_const  # noqa: E402
from intraday.history_fetch import fetch_history  # noqa: E402

DUKA = {"WTIUSD": "INSTRUMENT_CMD_ENERGY_E_LIGHT", "BRENTUSD": "INSTRUMENT_CMD_ENERGY_E_BRENT",
        "XAGUSD": "INSTRUMENT_FX_METALS_XAG_USD"}


def fetch(symbol: str, tf: str, year: int) -> pd.DataFrame:
    import dukascopy_python as dk
    df = dk.fetch(_duka_const(DUKA[symbol]), _INTERVALS[tf], dk.OFFER_SIDE_BID,
                  datetime(year, 1, 1), datetime(year + 1, 1, 1))
    return df if df is not None else pd.DataFrame()


if __name__ == "__main__":
    for s in DUKA:
        r = fetch_history(s, "5m", 2012, datetime.utcnow().year, fetch=fetch, on_progress=print)
        print(s, "inen", r["inen"], "atlanan", r["atlanan"], "bos", r["bos"], flush=True)
