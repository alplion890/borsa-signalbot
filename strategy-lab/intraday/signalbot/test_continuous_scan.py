import datetime as dt

from . import continuous_scan as worker

NOW = dt.datetime(2026, 10, 1, 15, 35, tzinfo=dt.timezone.utc)


def test_stage_failure_does_not_block_ema(monkeypatch, capsys):
    calls = []
    monkeypatch.setattr(worker, 'local_active', lambda now: False)
    def fail(**kwargs):
        raise RuntimeError('private-token')
    monkeypatch.setattr(worker.signal_scan, 'run', fail)
    for name in ('mobile_watch', 'ema12_paper', 'finnhub_news'):
        monkeypatch.setattr(getattr(worker, name), 'run',
                            lambda **kwargs: calls.append(kwargs))
    result = worker.scan_once(NOW, dry_run=True)
    assert result['sweep'] == 'RuntimeError'
    assert result['ema12'] == 'ok'
    assert len(calls) == 3
    assert 'private-token' not in capsys.readouterr().out


def test_closed_market_does_not_scan(monkeypatch):
    monkeypatch.setattr(worker, 'local_active', lambda now: 1 / 0)
    assert worker.scan_once(NOW.replace(hour=2), dry_run=True) == {}


def test_local_lease_suppresses_cloud_duplicates(monkeypatch, tmp_path):
    calls = {}
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(worker, 'local_active', lambda now: True)
    for name in ('signal_scan', 'mobile_watch', 'ema12_paper', 'finnhub_news'):
        monkeypatch.setattr(getattr(worker, name), 'run',
                            lambda _name=name, **kwargs: calls.update({_name: kwargs}))
    result = worker.scan_once(NOW)
    assert result['mobile'] == 'local'
    assert 'mobile_watch' not in calls
    assert calls['signal_scan']['dry_run']
    assert calls['ema12_paper']['suppress_alert']
    assert calls['ema12_paper']['suppress_result']
    assert not calls['finnhub_news']['dry_run']
