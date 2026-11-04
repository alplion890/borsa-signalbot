import datetime as dt
import json
from contextlib import nullcontext
from types import SimpleNamespace

from . import mt5_context

NOW = dt.datetime(2026, 9, 29, 16, 45, tzinfo=dt.timezone.utc)


def test_read_only_quote_and_freshness(monkeypatch, tmp_path):
    tick = SimpleNamespace(time=NOW.timestamp())
    fake = SimpleNamespace(
        session=nullcontext,
        account=lambda: {'connected': True, 'currency': 'USD', 'broker': 'MavenTrade', 'balance': 4966.37},
        symbol_meta=lambda key: {'name': {'NASDAQ100': 'US100'}.get(key, key), 'bid': 100.0, 'ask': 100.5},
        mt5=SimpleNamespace(symbol_info_tick=lambda name: tick),
    )
    snapshot = mt5_context.collect(NOW, fake)
    assert snapshot['quotes']['NASDAQ100']['spread'] == 0.5
    state = tmp_path / 'snapshot.json'
    state.write_text(json.dumps(snapshot), encoding='utf-8')
    monkeypatch.setattr(mt5_context, 'STATE', state)
    monkeypatch.setenv('MT5_CONTEXT_PATH', str(state))
    assert 'Bakiye 4966.37 USD' in mt5_context.describe('NASDAQ100', include_balance=True, now=NOW)
    assert 'bayat' in mt5_context.describe('NASDAQ100', now=NOW + dt.timedelta(minutes=3))


def test_fail_closed_without_broker(monkeypatch, tmp_path):
    monkeypatch.setenv('MT5_CONTEXT_PATH', str(tmp_path / 'missing.json'))
    monkeypatch.setattr(mt5_context, 'STATE', tmp_path / 'missing.json')
    assert 'teyidi yok' in mt5_context.describe('NASDAQ100', now=NOW)
