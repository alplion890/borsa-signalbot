"""Telegram gonderici. Token/chat_id YALNIZCA env'den. Asla hardcode/log."""
from __future__ import annotations
import os
from io import BytesIO
import requests

_API = "https://api.telegram.org/bot{token}/sendMessage"


def send(text: str) -> None:
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        raise RuntimeError("TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID env eksik")
    resp = requests.post(_API.format(token=token),
                         data={"chat_id": chat_id, "text": text}, timeout=15)
    resp.raise_for_status()


def send_photo(png: bytes, caption: str) -> None:
    """Send one phone-readable chart with its context in a single message."""
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        raise RuntimeError("TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID env eksik")
    if len(caption) > 1024:
        raise ValueError("Telegram fotograf aciklamasi 1024 karakteri asti")
    resp = requests.post(
        f"https://api.telegram.org/bot{token}/sendPhoto",
        data={"chat_id": chat_id, "caption": caption},
        files={"photo": ("nq-watch.png", BytesIO(png), "image/png")},
        timeout=25,
    )
    resp.raise_for_status()
    if not resp.json().get("ok"):
        raise RuntimeError("Telegram fotograf teslimatini reddetti")
