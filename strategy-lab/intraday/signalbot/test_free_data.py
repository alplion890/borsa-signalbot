import pandas as pd
import numpy as np
from intraday.signalbot import free_data


def _fake_yf_df():
    idx = pd.date_range("2026-06-18 13:00", periods=5, freq="5min", tz="America/New_York")
    return pd.DataFrame({
        "Open": np.arange(5.0), "High": np.arange(5.0)+1,
        "Low": np.arange(5.0)-1, "Close": np.arange(5.0)+0.5,
        "Volume": np.arange(5.0)*10,
    }, index=idx)


def test_yfinance_normalized_shape(monkeypatch):
    monkeypatch.setattr(free_data, "_yf_download", lambda *a, **k: _fake_yf_df())
    df = free_data.ohlcv("XAUUSD", "5m", days=1)
    assert list(df.columns) == ["open", "high", "low", "close", "volume"]
    assert str(df.index.tz) == "UTC"
    assert len(df) == 5
