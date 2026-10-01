"""Read-only Maven snapshot. Never imports or calls an order executor."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
from pathlib import Path

STATE = Path(os.environ.get('MT5_CONTEXT_PATH', '.signalbot/mt5_context.json'))
UTC = dt.timezone.utc


def collect(now=None, io=None):
    now = now or dt.datetime.now(UTC)
    if io is None:
        from ..mt5_bridge import mt5_io as io
    with io.session():
        account = io.account()
        if not account.get('connected') or account.get('currency') != 'USD':
            raise ValueError('connected USD account required')
        quotes = {}
        for key in ('NASDAQ100', 'EURUSD', 'GBPUSD'):
            meta = io.symbol_meta(key)
            tick = io.mt5.symbol_info_tick(meta['name'])
            quotes[key] = {'symbol': meta['name'], 'bid': meta['bid'], 'ask': meta['ask'],
                           'spread': meta['ask'] - meta['bid'],
                           'tick_utc': dt.datetime.fromtimestamp(tick.time, UTC).isoformat()}
        return {'status': 'ok', 'updated_at': now.isoformat(),
                'broker': account['broker'], 'balance': account['balance'],
                'currency': account['currency'], 'quotes': quotes}


def load(now=None, path=None):
    now = now or dt.datetime.now(UTC)
    try:
        data = json.loads((path or STATE).read_text(encoding='utf-8'))
        stamp = dt.datetime.fromisoformat(data['updated_at'])
        if data['status'] != 'ok' or not 0 <= (now - stamp).total_seconds() <= 120:
            return None
        return data
    except (OSError, ValueError, TypeError, KeyError):
        return None


def describe(symbol, *, include_balance=False, now=None):
    if not os.environ.get('MT5_CONTEXT_PATH'):
        return ''
    now = now or dt.datetime.now(UTC)
    data = load(now)
    if data is None:
        return 'MT5 teyidi yok/bayat; broker fiyati ve bakiye manuel kontrol edilmeli.'
    quote = data['quotes'].get(symbol)
    if quote is None:
        return 'MT5 sembol teyidi yok.'
    age = (now - dt.datetime.fromisoformat(quote['tick_utc'])).total_seconds()
    if not 0 <= age <= 60:
        return 'MT5 tick bayat; broker fiyati manuel kontrol edilmeli.'
    text = (f"MT5 {quote['symbol']}: bid {quote['bid']:g}, ask {quote['ask']:g}, "
            f"spread {quote['spread']:.5g}; tick {age:.0f} sn once.")
    if include_balance:
        text += f" Bakiye {data['balance']:.2f} USD."
    return text + ' NQ seviyeleri broker fiyatiyla ayni degildir.'


def main():
    parser = argparse.ArgumentParser(description='Read-only MT5 broker context')
    parser.add_argument('--output', type=Path, default=STATE)
    args = parser.parse_args()
    try:
        data = collect()
    except Exception as exc:
        data = {'status': 'unavailable', 'updated_at': dt.datetime.now(UTC).isoformat(),
                'error_type': type(exc).__name__}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_suffix('.tmp')
    temporary.write_text(json.dumps(data), encoding='utf-8')
    temporary.replace(args.output)
    print(f"MT5 read-only context: {data['status']}")


if __name__ == '__main__':
    main()
