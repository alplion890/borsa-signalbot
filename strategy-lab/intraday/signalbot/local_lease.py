"""Short cloud handoff lease; failure leaves GitHub notifications enabled."""
from __future__ import annotations

import datetime as dt
import subprocess
import json

REPO = 'alplion890/borsa-signalbot'


def cloud_active(command=None):
    execute = command or subprocess.run
    try:
        result = execute(['gh', 'api', f'repos/{REPO}/actions/workflows/signalbot.yml/runs?status=in_progress&per_page=5'],
                         capture_output=True, text=True, timeout=10)
        if result.returncode:
            return False
        for run in json.loads(result.stdout)['workflow_runs']:
            jobs = execute(['gh', 'api', f"repos/{REPO}/actions/runs/{run['id']}/jobs"],
                           capture_output=True, text=True, timeout=10)
            if jobs.returncode:
                continue
            for job in json.loads(jobs.stdout)['jobs']:
                if any(step['name'] == 'Continuous five-minute cloud scan'
                       and step['status'] == 'in_progress' for step in job['steps']):
                    return True
    except (OSError, subprocess.SubprocessError, ValueError, KeyError, TypeError):
        pass
    return False


def publish(now=None, command=None):
    now = now or dt.datetime.now(dt.timezone.utc)
    until = (now + dt.timedelta(minutes=8)).isoformat()
    execute = command or subprocess.run
    result = execute(['gh', 'variable', 'set', 'LOCAL_SCANNER_UNTIL',
                      '--repo', REPO, '--body', until],
                     capture_output=True, text=True, timeout=15)
    if result.returncode != 0:
        raise RuntimeError('GitHub yerel tarayici lease yazilamadi')
    return until


def main():
    try:
        print('Yerel tarama kapsamı GitHub devrine bildirildi:', publish())
    except (OSError, subprocess.SubprocessError, RuntimeError) as exc:
        print('GitHub devri etkinlesmedi; bulut yedegi acik:', type(exc).__name__)


if __name__ == '__main__':
    main()
