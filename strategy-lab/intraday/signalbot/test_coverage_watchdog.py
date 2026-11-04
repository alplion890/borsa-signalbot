import datetime as dt
import json

from . import coverage_watchdog as watchdog


def test_slots_reject_old_data_and_duplicate_checks(tmp_path):
    path = tmp_path / 'health.jsonl'
    rows = [
        {'evaluated_at': '2026-09-29T18:15:10+03:00', 'age_minutes': 0},
        {'evaluated_at': '2026-09-29T18:16:10+03:00', 'age_minutes': 1},
        {'evaluated_at': '2026-09-29T18:20:10+03:00', 'age_minutes': 50},
        {'evaluated_at': '2026-09-29T20:00:10+03:00', 'age_minutes': 0},
    ]
    path.write_text('\n'.join(json.dumps(row) for row in rows), encoding='utf-8')
    assert watchdog.local_slots(dt.date(2026, 9, 29), path) == {0}


def test_full_local_coverage_needs_no_github(monkeypatch):
    monkeypatch.setattr(watchdog, 'local_slots', lambda day: set(range(21)))
    monkeypatch.setattr(watchdog, 'gh', lambda *args: (_ for _ in ()).throw(AssertionError()))
    assert watchdog.check(dt.date(2026, 9, 29)) is None


def test_one_cloud_run_does_not_claim_full_coverage(monkeypatch):
    monkeypatch.setattr(watchdog, 'local_slots', lambda day: {0})
    monkeypatch.setattr(watchdog, 'gh', lambda *args: json.dumps([{
        'createdAt': '2026-09-29T15:44:00Z', 'event': 'schedule',
        'status': 'completed', 'conclusion': 'success',
    }]))
    result = watchdog.check(dt.date(2026, 9, 29))
    assert '1/21' in result and 'Tam kapsam dogrulanamadi' in result
