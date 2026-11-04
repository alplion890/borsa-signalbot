"""Independent local check for missing GitHub mobile-watch coverage."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import subprocess
from pathlib import Path
from zoneinfo import ZoneInfo

from .telegram_notify import send

TR = ZoneInfo("Europe/Istanbul")
ROOT = Path(__file__).resolve().parents[3]
REPO = "alplion890/borsa-signalbot"


def gh(*args: str) -> str:
    result = subprocess.run(["gh", *args], capture_output=True, text=True,
                            encoding="utf-8", timeout=60, check=True)
    return result.stdout


def load_telegram_env() -> None:
    for path in (ROOT / ".signalbot/local.env", ROOT / "strategy-lab/.env"):
        if path.exists():
            for line in path.read_text(encoding="utf-8-sig").splitlines():
                key, sep, value = line.strip().partition("=")
                if sep and key in {"TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID"}:
                    os.environ.setdefault(key, value.strip().strip("\"'"))


def local_slots(day: dt.date, path: Path | None = None) -> set[int]:
    path = path or ROOT / '.signalbot/mobile_health.jsonl'
    slots = set()
    if not path.exists():
        return slots
    for line in path.read_text(encoding='utf-8').splitlines():
        try:
            item = json.loads(line)
            stamp = dt.datetime.fromisoformat(item['evaluated_at']).astimezone(TR)
            minute = stamp.hour * 60 + stamp.minute
            if (stamp.date() == day and 18 * 60 + 15 <= minute < 20 * 60
                    and 0 <= float(item['age_minutes']) <= 35):
                slots.add((minute - (18 * 60 + 15)) // 5)
        except (ValueError, KeyError, TypeError):
            continue
    return slots


def check(day: dt.date) -> str | None:
    covered = local_slots(day)
    if len(covered) == 21:
        return None
    runs = json.loads(gh("run", "list", "--repo", REPO, "--workflow",
                         "signalbot.yml", "--limit", "100", "--json",
                         "databaseId,createdAt,event,status,conclusion"))
    window = []
    for run in runs:
        stamp = dt.datetime.fromisoformat(run["createdAt"].replace("Z", "+00:00")).astimezone(TR)
        if (run["event"] == "schedule" and stamp.date() == day
                and dt.time(18, 15) <= stamp.time() < dt.time(20)):
            window.append(run)
    # Cloud run counts alone do not certify fresh-data coverage.
    return (f"{day}: 18:15–20:00 TR penceresinde yerel guncel veri kontrolu "
            f"{len(covered)}/21 zaman diliminde dogrulandi; bulutta {len(window)} kosu var. "
            'Tam kapsam dogrulanamadi. PC/oturum/internet ve local_scanner.log kontrol edilmeli. '
            'Bildirim yoklugu firsat yok demek degildir.')


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", type=dt.date.fromisoformat)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    now = dt.datetime.now(TR)
    day = args.date or now.date()
    if day.weekday() >= 5 or (not args.date and now.time() < dt.time(20, 10)):
        print("Coverage watchdog: karar seansi henuz tamamlanmadi veya hafta sonu.")
        return
    state_path = ROOT / ".signalbot/coverage_watchdog.json"
    try:
        state = json.loads(state_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        state = {}
    try:
        problem = check(day)
    except (subprocess.SubprocessError, OSError, ValueError) as exc:
        problem = f"{day}: bagimsiz seans kontrolu yapilamadi ({type(exc).__name__}). Tarama sagligi bilinmiyor."
    if not problem:
        print("Coverage watchdog: seans ici NQ kontrolu dogrulandi.")
        return
    text = "SIGNALBOT TARAMA EKSIK\n" + problem
    print(text)
    if args.dry_run or state.get("last_alert") == str(day):
        return
    load_telegram_env()
    send(text)
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps({"last_alert": str(day)}), encoding="utf-8")
    print("Coverage watchdog: Telegram uyarisi gonderildi.")


if __name__ == "__main__":
    main()
