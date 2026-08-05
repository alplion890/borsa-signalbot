"""mt5_io baglanti korumasi testleri.

Odak: terminal KAPALIYKEN mt5.initialize() cagrilmamali. Cagrilirsa MT5'in
Python API'si terminali kendisi baslatir; Task Scheduler 5 dakikada bir
kostugu icin bu, kullanici MT5'i kapatsa bile surekli geri acilmasina yol
aciyordu (kullanici sikayeti, 2026-08).
"""
from __future__ import annotations

import sys
import types
from unittest.mock import patch

import pytest

# MetaTrader5 paketi CI'da (Linux) yok; import edilebilsin diye stub koy.
if "MetaTrader5" not in sys.modules:  # pragma: no cover
    stub = types.ModuleType("MetaTrader5")
    stub.initialize = lambda *a, **k: True
    stub.shutdown = lambda: None
    stub.last_error = lambda: (0, "ok")
    sys.modules["MetaTrader5"] = stub

from intraday.mt5_bridge import mt5_io  # noqa: E402


class TestTerminalGuard:
    # create=True: baska bir test modulu MetaTrader5 icin attribute'suz bir
    # stub kurmus olabilir (tum set birlikte kosarken). Testin konusu stub'in
    # sekli degil, mt5_io'nun cagirip cagirmadigi.
    def test_initialize_not_called_when_terminal_closed(self):
        """Terminal kapaliysa mt5.initialize() HIC cagrilmamali.

        Bu testin kalbi: initialize cagrilirsa terminal acilir. Sadece
        "hata firlatti mi" bakmak yetmez -- cagrilmadigini kanitlamak gerekir.
        """
        with patch.object(mt5_io, "_terminal_running", return_value=False), \
             patch.object(mt5_io.mt5, "initialize", create=True) as fake_init:
            with pytest.raises(mt5_io.MT5Error, match="kapali"):
                mt5_io.initialize()
            fake_init.assert_not_called()

    def test_initialize_called_when_terminal_running(self):
        with patch.object(mt5_io, "_terminal_running", return_value=True), \
             patch.object(mt5_io.mt5, "initialize", return_value=True,
                          create=True) as fake_init:
            mt5_io.initialize()
            fake_init.assert_called_once()

    def test_connection_failure_still_raises_when_terminal_running(self):
        """Terminal acik ama baglanti kurulamiyorsa eski davranis korunur."""
        with patch.object(mt5_io, "_terminal_running", return_value=True), \
             patch.object(mt5_io.mt5, "initialize", return_value=False, create=True), \
             patch.object(mt5_io.mt5, "last_error", return_value=(-1, "no ipc"),
                          create=True):
            with pytest.raises(mt5_io.MT5Error, match="baglanamadi"):
                mt5_io.initialize()


class TestTerminalRunning:
    def _tasklist(self, stdout: str):
        return types.SimpleNamespace(stdout=stdout)

    def test_detects_running_terminal(self):
        out = "terminal64.exe                8888 Console      1    512.000 K"
        with patch.object(mt5_io.subprocess, "run", return_value=self._tasklist(out)):
            assert mt5_io._terminal_running() is True

    def test_detects_closed_terminal(self):
        out = "INFO: No tasks are running which match the specified criteria."
        with patch.object(mt5_io.subprocess, "run", return_value=self._tasklist(out)):
            assert mt5_io._terminal_running() is False

    def test_fails_open_when_tasklist_unavailable(self):
        """tasklist yoksa/patlarsa eski davranisa don -- sessizce engelleme.

        Yanlis pozitif (terminal acik sanip baglanamamak) anlasilir hata verir;
        yanlis negatif (acikken kapali sanmak) botu sessizce oldururdu.
        """
        with patch.object(mt5_io.subprocess, "run", side_effect=OSError("yok")):
            assert mt5_io._terminal_running() is True
