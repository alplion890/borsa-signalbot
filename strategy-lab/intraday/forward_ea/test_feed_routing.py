"""Veri kaynagi yonlendirmesi: BTC Binance'ten, geri kalani MT5'ten.

Neden gerekli: BTCUSDT_OF_ABSORPTION signalbot uzerinden Telegram'a sinyal
gonderiyordu ama forward defterinde SIFIR kaydi vardi -- olculmuyordu.
Sebep: forward EA tum modulleri mt5_io'dan cekiyordu, Maven broker'inda ise
spot BTC yok. Sonuc: telefona dusen ama sonucu hicbir yere yazilmayan bir
sinyal kaynagi (DeepSeek AI scout'un kapatilma gerekcesinin aynisi).
"""
from __future__ import annotations

import sys
import types
from unittest.mock import patch

import pandas as pd
import pytest

# MetaTrader5 yalnizca Windows'ta kurulu; import zinciri kirilmasin diye stub.
if "MetaTrader5" not in sys.modules:  # pragma: no cover
    stub = types.ModuleType("MetaTrader5")
    stub.initialize = lambda *a, **k: True
    stub.shutdown = lambda: None
    stub.last_error = lambda: (0, "ok")
    sys.modules["MetaTrader5"] = stub

from intraday.forward_ea import live_runner  # noqa: E402


def _frame(n=600, freq="1h"):
    idx = pd.date_range("2026-06-01", periods=n, freq=freq)
    p = pd.Series(range(n), dtype=float) + 60000.0
    return pd.DataFrame(
        {"open": p.values, "high": p.values + 50, "low": p.values - 50,
         "close": p.values, "volume": 10.0},
        index=idx,
    )


class TestFeedRouting:
    @pytest.mark.parametrize("key", ["BTCUSDT", "BTC"])
    def test_btc_uses_binance_not_mt5(self, key):
        with patch.object(live_runner, "_binance_ohlcv", return_value=_frame()) as bnc, \
             patch.object(live_runner.mt5_io, "ohlcv", return_value=_frame()) as m5:
            out = live_runner._fetch_ohlcv(key, "1H", days=40)
        bnc.assert_called_once()
        m5.assert_not_called()
        assert len(out) == 600

    def test_non_btc_uses_mt5(self):
        with patch.object(live_runner, "_binance_ohlcv", return_value=_frame()) as bnc, \
             patch.object(live_runner.mt5_io, "ohlcv", return_value=_frame()) as m5:
            live_runner._fetch_ohlcv("NASDAQ100", "5m", days=40)
        m5.assert_called_once()
        bnc.assert_not_called()

    def test_binance_frame_is_tz_naive(self):
        """Binance feed mt5_io sozlesmesine uymali: UTC ama tz-NAIVE.

        Regression: Binance tz-aware donuyordu; karisik timestamp defter
        yazimini patlatti (`unconverted data remains ... "+00:00"`) ve hata
        _save_state icinde oldugu icin o dongudeki TUM modullerin kaydi
        kayboldu -- BTC eklemek digerlerinin verisini de goturuyordu.
        """
        aware = _frame()
        aware.index = aware.index.tz_localize("UTC")
        with patch("intraday.signalbot.binance_data.klines", return_value=aware):
            out = live_runner._binance_ohlcv("1H", days=40)
        assert out.index.tz is None

    def test_every_module_symbol_key_has_cost(self):
        """Her modulun symbol_key'i INSTRUMENTS'ta OLMALI.

        Regression: CAND_BTC_ABSORPTION symbol_key="BTC" kullaniyordu ama
        INSTRUMENTS'ta anahtar "BTCUSDT" idi -> cost_per_side KeyError firlatti,
        sinyal uretilmesine ragmen forward'a HIC kayit dusmedi (sessiz olum).
        """
        from intraday.forward_ea.modules import forward_test_modules
        for mod in forward_test_modules():
            assert mod.cost_per_side > 0, f"{mod.name}: {mod.symbol_key} maliyeti yok"

    def test_binance_failure_is_skipped_not_fatal(self):
        """Binance patlarsa dongu kirilmamali -- MT5 modulleri islemeye devam etsin.

        Bu repoda sessiz olum tekrar eden hata; ama burada tersi de gecerli:
        tek bir feed'in coken hali TUM forward testi durdurmamali.
        """
        with patch.object(live_runner, "_binance_ohlcv",
                          side_effect=RuntimeError("binance down")):
            with pytest.raises(live_runner.mt5_io.MT5Error, match="Binance"):
                live_runner._fetch_ohlcv("BTC", "1H", days=40)
