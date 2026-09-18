import datetime as dt
from io import BytesIO

import pandas as pd
from PIL import Image

from intraday.signalbot import mobile_chart, mobile_watch, telegram_notify


def _bars():
    end = dt.datetime(2026, 9, 18, 15, 30, tzinfo=dt.timezone.utc)
    index = pd.date_range(end=end, periods=15 * 96, freq="15min", tz="UTC")
    return pd.DataFrame({"open": 100.0, "high": 101.0, "low": 99.0,
                         "close": 100.0, "volume": 20.0}, index=index)


def test_render_phone_chart_png():
    png = mobile_chart.render_chart(_bars(), level=101)
    image = Image.open(BytesIO(png))
    assert image.format == "PNG"
    assert image.size == (900, 560)
    assert len(png) > 5_000


def test_watch_default_delivery_sends_chart_with_caption(monkeypatch, tmp_path):
    frame = _bars()
    frame.loc[frame.index[-1], "close"] = 101.0
    sent = []
    monkeypatch.setattr(telegram_notify, "send_photo", lambda png, caption: sent.append((png, caption)))
    monkeypatch.setattr(telegram_notify, "send", lambda text: (_ for _ in ()).throw(
        AssertionError("text fallback should not be needed")))

    message = mobile_watch.run(
        now=dt.datetime(2026, 9, 18, 15, 45, tzinfo=dt.timezone.utc),
        state_path=tmp_path / "watch.json",
        fetch=lambda *args, **kwargs: frame,
    )

    assert len(sent) == 1
    assert sent[0][0].startswith(b"\x89PNG")
    assert sent[0][1] == message
    assert len(message) <= 1024


def test_photo_failure_falls_back_to_text(monkeypatch, tmp_path):
    frame = _bars()
    frame.loc[frame.index[-1], "close"] = 101.0
    texts = []
    monkeypatch.setattr(telegram_notify, "send_photo", lambda *_: (_ for _ in ()).throw(
        RuntimeError("photo unavailable")))
    monkeypatch.setattr(telegram_notify, "send", texts.append)

    mobile_watch.run(
        now=dt.datetime(2026, 9, 18, 15, 45, tzinfo=dt.timezone.utc),
        state_path=tmp_path / "watch.json",
        fetch=lambda *args, **kwargs: frame,
    )

    assert len(texts) == 1


def test_telegram_photo_upload_uses_configured_chat(monkeypatch):
    class Response:
        def raise_for_status(self):
            pass

        def json(self):
            return {"ok": True}

    calls = []
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test-token")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "123")
    monkeypatch.setattr(telegram_notify.requests, "post", lambda *a, **kw: (
        calls.append((a, kw)) or Response()))

    telegram_notify.send_photo(b"\x89PNGfake", "watch")

    assert calls[0][0][0].endswith("/sendPhoto")
    assert calls[0][1]["data"]["chat_id"] == "123"
    assert calls[0][1]["files"]["photo"][0] == "nq-watch.png"
