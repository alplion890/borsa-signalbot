import datetime as dt

import pandas as pd

from . import production_cycle as worker

NOW = dt.datetime(2026, 10, 7, 18, 0, tzinfo=dt.timezone.utc)


def test_bar_age_measures_from_close_not_open():
    frame = pd.DataFrame(index=pd.to_datetime(['2026-10-07T17:30Z', '2026-10-07T17:45Z']))
    assert worker.data_age(frame, NOW) == 0
    assert worker.data_age(frame, NOW + dt.timedelta(minutes=16)) == 16


def test_stale_data_fails_without_notifications(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    frame = pd.DataFrame(index=pd.to_datetime(['2026-10-07T17:00Z', '2026-10-07T17:15Z']))
    monkeypatch.setattr(worker.free_data, 'ohlcv', lambda *a, **kw: frame)
    monkeypatch.setattr(worker.continuous_scan, 'scan_once', lambda *a, **kw: 1 / 0)
    result = worker.run(NOW, dry_run=True)
    assert result['status'] == 'error'
    assert result['error_type'] == 'ValueError'
    assert not (tmp_path / '.signalbot').exists()


def test_closed_window_does_not_fetch(monkeypatch):
    monkeypatch.setattr(worker.free_data, 'ohlcv', lambda *a, **kw: 1 / 0)
    assert worker.run(NOW.replace(hour=2)) == {'status': 'closed'}
