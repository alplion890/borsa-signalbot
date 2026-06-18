import numpy as np
import pandas as pd

from intraday.signalbot import btc_absorption


def test_detector_returns_none_without_warmup():
    idx = pd.date_range("2026-01-01", periods=20, freq="1h", tz="UTC")
    p = np.arange(20.0) + 100
    df = pd.DataFrame(
        {"open": p, "high": p + 1, "low": p - 1, "close": p, "volume": 10},
        index=idx,
    )
    assert btc_absorption.detect(df) is None


def test_module_identity():
    mod = btc_absorption.module()
    assert mod.name == "BTCUSDT_OF_ABSORPTION"
    assert mod.symbol_key == "BTC"
    assert mod.tf == "1H"
    assert mod.weight == 0.11
