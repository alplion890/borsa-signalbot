"""Telegram gonderici. Token/chat_id YALNIZCA env'den. Asla hardcode/log."""
from __future__ import annotations
import os
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
