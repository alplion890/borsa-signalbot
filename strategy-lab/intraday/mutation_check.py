"""Mutation check for money/risk code: inject realistic bugs, confirm the tests catch each one.

Run from strategy-lab:  python -m intraday.mutation_check
A mutant that "ESCAPED" means no test notices that bug -> add a property test until it is caught.
When you change prop_fit rules, add a mutant here for the new rule.
"""
from __future__ import annotations

import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
TARGET = HERE / "prop_fit.py"
TESTS = [str(HERE / "test_prop_fit.py"), str(HERE / "test_prop_fit_properties.py")]

# name -> (original snippet, buggy replacement); each snippet must occur exactly once.
MUTANTS: dict[str, tuple[str, str]] = {
    "challenge drawdown doubled": ("if bal <= peak - rules.static_dd:", "if bal <= peak - rules.static_dd * 2:"),
    "daily loss limit check removed": ("if lo[i] <= -rules.daily_limit or bal + lo[i] <= floor():", "if bal + lo[i] <= floor():"),
    "payout not deducted from balance": ("paid, bal, n = paid + amount, bal - amount, n + 1", "paid, bal, n = paid + amount, bal, n + 1"),
    "locked floor keeps trailing buffer": ("return 0.0 if locked else", "return -rules.trail_dd if locked else"),
    "consistency vs total balance": ("best <= rules.consistency * profit", "best <= rules.consistency * bal"),
    "trailing peak ignores intraday high": ("peak = max(peak, bal + hi[i])", "peak = max(peak, bal)"),
}


def _tests_fail() -> bool:
    cmd = [sys.executable, "-m", "pytest", "-q", "-x", "--no-header", "-p", "no:cacheprovider", *TESTS]
    return subprocess.run(cmd, cwd=HERE.parent, capture_output=True, text=True).returncode == 1


def main() -> int:
    original = TARGET.read_text(encoding="utf-8")
    escaped = []
    try:
        for name, (good, bad) in MUTANTS.items():
            if original.count(good) != 1:
                print(f"STALE   {name}: snippet not found once in prop_fit.py, update the mutant")
                escaped.append(name)
                continue
            TARGET.write_text(original.replace(good, bad), encoding="utf-8")
            caught = _tests_fail()
            print(f"{'caught ' if caught else 'ESCAPED'} {name}")
            if not caught:
                escaped.append(name)
    finally:
        TARGET.write_text(original, encoding="utf-8")
    print(f"\n{len(MUTANTS) - len(escaped)}/{len(MUTANTS)} mutants caught")
    return 1 if escaped else 0


if __name__ == "__main__":
    raise SystemExit(main())
