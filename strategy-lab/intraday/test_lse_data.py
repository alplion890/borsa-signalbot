from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd
import pytest

from . import lse_data


UTC = timezone.utc


def _frame(end: str, rows: int = 4) -> pd.DataFrame:
    index = pd.date_range(end=end, periods=rows, freq="15min", tz="UTC")
    return pd.DataFrame({
        "open": 1.0, "high": 2.0, "low": .5, "close": 1.5, "volume": 10.0,
    }, index=index)


def test_candles_normalizes_lse_payload():
    def getter(path, params, timeout):
        assert path == "/api/candles"
        assert params["symbol"] == "NQ.F"
        return {"candles": [[1_789_344_000, 1, 2, .5, 1.5, 10]]}

    out = lse_data.candles("NASDAQ100", getter=getter)

    assert list(out.columns) == lse_data.COLUMNS
    assert str(out.index.tz) == "UTC"
    assert out.attrs["source"] == "lse-terminal"


def test_remote_ohlcv_resmi_sdk_satirlarini_normalize_eder():
    class Client:
        def candles(self, symbol, timeframe, **kwargs):
            assert symbol == "NQ.F"
            assert timeframe == "15m"
            return [{
                "timestamp": "2026-09-15T15:00:00Z",
                "open": 1, "high": 2, "low": .5, "close": 1.5, "volume": 10,
            }]

    out = lse_data.remote_ohlcv(
        "NASDAQ100", client_factory=lambda: Client(),
    )

    assert out.attrs["source"] == "lse-cloud"
    assert out.index[0] == pd.Timestamp("2026-09-15 15:00", tz="UTC")


def test_arastirma_sepeti_uzun_gecmisli_sembolleri_icerir():
    assert lse_data.SYMBOLS["SP500"][:2] == ("ES.F", "futures")
    assert lse_data.SYMBOLS["GOLD"][:2] == ("GC.F", "futures")
    assert lse_data.SYMBOLS["BTCUSD"][:2] == ("BTC/USD", "crypto")


def test_15dk_veriden_ust_zaman_dilimi_uretilir():
    index = pd.date_range("2026-01-01", periods=16, freq="15min", tz="UTC")
    close = pd.Series(range(16), index=index, dtype=float)
    frame = pd.DataFrame({
        "open": close, "high": close + 1, "low": close - 1,
        "close": close + .5, "volume": 10.0,
    })

    hourly = lse_data.resample_ohlcv(frame, "1H")
    four_hour = lse_data.resample_ohlcv(frame, "4H")

    assert len(hourly) == 4
    assert len(four_hour) == 1
    assert four_hour.iloc[0]["volume"] == 160.0


def test_bayat_birincilden_guncel_lse_yedege_gecer():
    now = datetime(2026, 9, 15, 16, 0, tzinfo=UTC)
    old = _frame("2026-09-15 13:00")
    fresh = _frame("2026-09-15 15:45")

    out = lse_data.ohlcv_with_backup(
        "NASDAQ100", "15m", 59, now=now,
        primary=lambda *a: old, backup=lambda *a: fresh,
        min_rows=4,
    )

    assert out.attrs["fallback_role"] == "LSE yedek"


def test_iki_kaynak_da_bayatsa_fail_closed():
    now = datetime(2026, 9, 15, 16, 0, tzinfo=UTC)
    old = _frame("2026-09-15 13:00")

    with pytest.raises(lse_data.LSEDataError, match="LSE yedek"):
        lse_data.ohlcv_with_backup(
            "NASDAQ100", "15m", 59, now=now,
            primary=lambda *a: old, backup=lambda *a: old,
            min_rows=4,
        )


def test_acik_gelecek_bari_varken_son_kapanmis_bari_kullanir():
    now = datetime(2026, 9, 15, 16, 7, tzinfo=UTC)
    frame = _frame("2026-09-15 16:15", rows=4)

    ok, reason = lse_data._is_fresh(
        frame, "15m", now, max_age_minutes=45, min_rows=4,
    )

    assert ok
    assert reason == "guncel"


def test_fetch_range_sayfalarken_ayni_bari_tekrarlamaz():
    calls = []

    def page(symbol, tf, limit, start, end):
        calls.append(pd.Timestamp(start))
        if len(calls) == 1:
            return _frame("2026-02-22 01:45", rows=5000)
        if len(calls) == 2:
            return _frame("2026-02-22 02:45", rows=4)
        return pd.DataFrame(columns=lse_data.COLUMNS)

    out = lse_data.fetch_range(
        "NASDAQ100", "15m", pd.Timestamp("2026-01-01", tz="UTC"),
        pd.Timestamp("2026-04-01", tz="UTC"), fetch_page=page,
        pause_seconds=0,
    )

    assert len(out) == 5004
    assert calls[1] == pd.Timestamp("2026-02-22 02:00", tz="UTC")


def test_uzak_tarih_araligi_aylik_parcalanir():
    calls = []

    def page(symbol, tf, limit, start, end):
        calls.append((pd.Timestamp(start), pd.Timestamp(end)))
        return _frame(pd.Timestamp(end) - pd.Timedelta(minutes=15), rows=2)

    out = lse_data.fetch_remote_range(
        "BTCUSD", "15m", pd.Timestamp("2026-01-01", tz="UTC"),
        pd.Timestamp("2026-03-15", tz="UTC"), fetch_page=page,
        chunk_days=30, pause_seconds=0,
    )

    assert len(calls) == 3
    assert calls[0][1] == pd.Timestamp("2026-01-31", tz="UTC")
    assert not out.empty

