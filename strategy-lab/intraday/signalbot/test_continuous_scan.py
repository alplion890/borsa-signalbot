import datetime as dt

import pytest

from . import continuous_scan as worker

NOW = dt.datetime(2026, 10, 1, 15, 35, tzinfo=dt.timezone.utc)


@pytest.fixture(autouse=True)
def _no_network_macro(monkeypatch):
    """Stage tests must never hit the real calendar or price feeds."""
    monkeypatch.setattr(worker.makro_olcum, 'run', lambda **kwargs: None)


def test_stage_failure_does_not_block_other_stages(monkeypatch, capsys):
    calls = []
    monkeypatch.setattr(worker, 'local_active', lambda now: False)
    def fail(**kwargs):
        raise RuntimeError('private-token')
    monkeypatch.setattr(worker.signal_scan, 'run', fail)
    for name in ('finnhub_news',):
        monkeypatch.setattr(getattr(worker, name), 'run',
                            lambda **kwargs: calls.append(kwargs))
    result = worker.scan_once(NOW, dry_run=True)
    assert result['sweep'] == 'RuntimeError'
    assert result['finnhub'] == 'ok'
    assert len(calls) == 1
    assert 'private-token' not in capsys.readouterr().out


def test_closed_market_does_not_scan(monkeypatch):
    monkeypatch.setattr(worker, 'local_active', lambda now: 1 / 0)
    assert worker.scan_once(NOW.replace(hour=2), dry_run=True) == {}


def test_local_lease_suppresses_cloud_duplicates(monkeypatch, tmp_path):
    calls = {}
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(worker, 'local_active', lambda now: True)
    for name in ('signal_scan', 'finnhub_news'):
        monkeypatch.setattr(getattr(worker, name), 'run',
                            lambda _name=name, **kwargs: calls.update({_name: kwargs}))
    result = worker.scan_once(NOW)
    assert calls['signal_scan']['dry_run']
    assert not calls['finnhub_news']['dry_run']


def test_ema12_is_measured_on_maven_not_in_cloud(monkeypatch):
    """2026-11-05: EMA12 PAPER moved to the Maven forward EA."""
    monkeypatch.setattr(worker, 'local_active', lambda now: False)
    for name in ('signal_scan', 'finnhub_news'):
        monkeypatch.setattr(getattr(worker, name), 'run', lambda **kwargs: None)
    assert 'ema12' not in worker.scan_once(NOW, dry_run=True)


def test_macro_measurement_runs_as_its_own_stage(monkeypatch):
    seen = []
    monkeypatch.setattr(worker, 'local_active', lambda now: False)
    for name in ('signal_scan', 'finnhub_news'):
        monkeypatch.setattr(getattr(worker, name), 'run', lambda **kwargs: None)
    monkeypatch.setattr(worker.makro_olcum, 'run',
                        lambda **kwargs: seen.append(kwargs))
    result = worker.scan_once(NOW, dry_run=True)
    assert result['makro'] == 'ok'
    assert seen == [{'now': NOW, 'dry_run': True}]


def test_discretionary_mobile_watch_is_not_a_cloud_stage(monkeypatch):
    """2026-11-05: discretionary rail removed; its level alerts went with it."""
    monkeypatch.setattr(worker, 'local_active', lambda now: False)
    for name in ('signal_scan', 'finnhub_news'):
        monkeypatch.setattr(getattr(worker, name), 'run', lambda **kwargs: None)
    assert 'mobile' not in worker.scan_once(NOW, dry_run=True)


def test_cloud_sweep_alert_is_dry_during_execution_trial(monkeypatch):
    """2026-11-09..22: alerts come only from the Maven-fed local bot."""
    calls = {}
    monkeypatch.setattr(worker, 'local_active', lambda now: False)
    monkeypatch.setattr(worker.signal_scan, 'run', lambda **kw: calls.update(kw))
    monkeypatch.setattr(worker.finnhub_news, 'run', lambda **kw: None)
    worker.scan_once(dt.datetime(2026, 11, 12, 15, 0, tzinfo=dt.timezone.utc))
    assert calls['dry_run'] is True
    worker.scan_once(dt.datetime(2026, 11, 24, 15, 0, tzinfo=dt.timezone.utc))
    assert calls['dry_run'] is False
