import os
import pytest
from intraday.signalbot import telegram_notify as tn


def test_send_with_env_vars(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "TESTTOKEN")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "999")

    calls = []

    def mock_post(url, data=None, timeout=None):
        calls.append((url, data))
        class MockResp:
            def raise_for_status(self):
                pass
        return MockResp()

    monkeypatch.setattr(tn.requests, "post", mock_post)
    tn.send("merhaba")

    assert len(calls) == 1
    url, data = calls[0]
    assert "TESTTOKEN" in url
    assert data["chat_id"] == "999"
    assert data["text"] == "merhaba"


def test_send_missing_token_raises(monkeypatch):
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)

    with pytest.raises(RuntimeError):
        tn.send("x")
