"""Persistent-host observation cycle; never invokes an order executor."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
from pathlib import Path

import pandas as pd
import requests

from . import continuous_scan, free_data
from .scan_schedule import is_open
from ..forward_ea import cloud_runner


def data_age(frame, now: dt.datetime) -> float:
    if frame is None or len(frame) < 2:
        raise ValueError('NQ data missing')
    index = pd.DatetimeIndex(frame.index)
    index = index.tz_localize('UTC') if index.tz is None else index.tz_convert('UTC')
    ends = index + pd.Timedelta(minutes=15)
    closed = ends[ends <= pd.Timestamp(now)]
    if len(closed) == 0:
        raise ValueError('NQ closed data missing')
    return (pd.Timestamp(now) - closed.max()).total_seconds() / 60


def run(now=None, *, dry_run=False) -> dict:
    now = now or dt.datetime.now(dt.timezone.utc)
    if not is_open(now):
        return {'status': 'closed'}
    health = {'at': now.isoformat(), 'status': 'error'}
    try:
        if not dry_run and any(not os.environ.get(key) for key in
                               ('TELEGRAM_BOT_TOKEN', 'TELEGRAM_CHAT_ID', 'FINNHUB_API_KEY')):
            raise RuntimeError('Required production credentials missing')
        age = data_age(free_data.ohlcv('NASDAQ100', '15m', days=5), now)
        health['data_age_minutes'] = age
        if age > 15:
            raise ValueError('NQ closed bar more than 15 minutes late')
        stages = continuous_scan.scan_once(now, dry_run=dry_run)
        health['stages'] = stages
        if not dry_run:
            summary = cloud_runner.run_once(state_dir=Path('.signalbot/forward'))
            health['forward'] = summary
            if summary['skipped']:
                raise RuntimeError('Forward data stage failed')
        if any(value != 'ok' for value in stages.values()):
            raise RuntimeError('Observation stage failed')
        health['status'] = 'ok'
    except Exception as exc:
        health['error_type'] = type(exc).__name__
        # Never expose provider URLs or credential-bearing exception messages.
    if not dry_run:
        path = Path('.signalbot/production_health.json')
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix('.tmp')
        temporary.write_text(json.dumps(health), encoding='utf-8')
        temporary.replace(path)
        url = os.environ.get('HEARTBEAT_URL', '')
        if health['status'] == 'ok' and url.startswith('https://'):
            try:
                requests.get(url, timeout=10).raise_for_status()
            except requests.RequestException:
                health['heartbeat'] = 'failed'
    print('PRODUCTION_HEALTH ' + json.dumps(health), flush=True)
    return health


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    health = run(dry_run=args.dry_run)
    raise SystemExit(0 if health['status'] in {'ok', 'closed'} else 1)


if __name__ == '__main__':
    main()
