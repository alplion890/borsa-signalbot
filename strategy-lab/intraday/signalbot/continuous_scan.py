"""Daytime cloud worker; independent stages and refreshed local handoff."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import time
from pathlib import Path

import requests

from . import ema12_paper, finnhub_news, mobile_watch, signal_scan
from .scan_schedule import is_open

UTC = dt.timezone.utc


def local_active(now: dt.datetime) -> bool:
    token = os.environ.get('GH_TOKEN')
    repo = os.environ.get('GITHUB_REPOSITORY')
    if not token or not repo:
        return False
    try:
        response = requests.get(
            f'https://api.github.com/repos/{repo}/actions/variables/LOCAL_SCANNER_UNTIL',
            headers={'Authorization': f'Bearer {token}'}, timeout=10)
        response.raise_for_status()
        until = dt.datetime.fromisoformat(response.json()['value'])
        return 0 < (until - now).total_seconds() <= 480
    except (requests.RequestException, ValueError, KeyError, TypeError):
        print('Yerel devir okunamadi; bulut bildirimi aktif.', flush=True)
        return False


def scan_once(now: dt.datetime, *, dry_run: bool = False) -> dict:
    if not is_open(now):
        return {}
    lease = local_active(now)
    stages = {
        'sweep': lambda: signal_scan.run(now=now, dry_run=dry_run or lease),
        'mobile': lambda: mobile_watch.run(now=now, dry_run=dry_run),
        'ema12': lambda: ema12_paper.run(now=now, dry_run=dry_run,
                                       suppress_alert=lease, suppress_result=lease),
        'finnhub': lambda: finnhub_news.run(now=now, dry_run=dry_run),
    }
    outcomes = {}
    for name, call in stages.items():
        if name == 'mobile' and lease and not dry_run:
            outcomes[name] = 'local'
            continue
        try:
            call()
            outcomes[name] = 'ok'
        except Exception as exc:
            outcomes[name] = type(exc).__name__
            print(f'CLOUD_STAGE_ERROR {name} {type(exc).__name__}', flush=True)
    record = {'at': now.isoformat(), 'local_active': lease, 'stages': outcomes}
    print('CLOUD_TICK ' + json.dumps(record), flush=True)
    if not dry_run:
        path = Path('.signalbot/cloud_scan_health.jsonl')
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('a', encoding='utf-8') as output:
            output.write(json.dumps(record) + '\n')
    return outcomes


def run(*, minutes: float = 330, dry_run: bool = False, once: bool = False) -> bool:
    deadline = time.monotonic() + minutes * 60
    while time.monotonic() < deadline:
        now = dt.datetime.now(UTC)
        if not is_open(now):
            return False
        scan_once(now, dry_run=dry_run)
        if once:
            return False
        delay = 300 - time.time() % 300
        time.sleep(min(delay, max(0, deadline - time.monotonic())))
    return is_open()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--once', action='store_true')
    args = parser.parse_args()
    rotate = run(dry_run=args.dry_run, once=args.once)
    if os.environ.get('GITHUB_OUTPUT'):
        with open(os.environ['GITHUB_OUTPUT'], 'a', encoding='utf-8') as output:
            output.write(f'continue={str(rotate).lower()}\n')


if __name__ == '__main__':
    main()
