"""Mutation check for money/risk code: inject realistic bugs, confirm the tests catch each one.

Run from strategy-lab:  python -m intraday.mutation_check
A mutant that "ESCAPED" means no test notices that bug -> add a property test until it is caught.
When you change a money rule in one of these files, add a mutant here for the new rule.
"""
from __future__ import annotations

import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent

# file -> tests that guard it
GUARDS: dict[str, list[str]] = {
    "prop_fit.py": ["test_prop_fit.py", "test_prop_fit_properties.py"],
    "prop_equity.py": ["test_prop_equity_properties.py"],
    "portfolio_ab.py": ["test_portfolio_ab.py", "test_portfolio_ab_properties.py"],
}

# (file, name, original snippet, buggy replacement); each snippet must occur exactly once in its file.
MUTANTS: list[tuple[str, str, str, str]] = [
    ("prop_fit.py", "challenge drawdown doubled",
     "if bal <= peak - rules.static_dd:", "if bal <= peak - rules.static_dd * 2:"),
    ("prop_fit.py", "daily loss limit check removed",
     "if lo[i] <= -rules.daily_limit or bal + lo[i] <= floor():", "if bal + lo[i] <= floor():"),
    ("prop_fit.py", "payout not deducted from balance",
     "paid, bal, n = paid + amount, bal - amount, n + 1", "paid, bal, n = paid + amount, bal, n + 1"),
    ("prop_fit.py", "locked floor keeps trailing buffer",
     "return 0.0 if locked else", "return -rules.trail_dd if locked else"),
    ("prop_fit.py", "consistency vs total balance",
     "best <= rules.consistency * profit", "best <= rules.consistency * bal"),
    ("prop_fit.py", "trailing peak ignores intraday high",
     "peak = max(peak, bal + hi[i])", "peak = max(peak, bal)"),
    ("prop_equity.py", "combine: dip ignores earlier trades",
     "low = np.minimum(low, close + q[:, 1])", "low = np.minimum(low, q[:, 1])"),
    ("prop_equity.py", "combine: spike ignores earlier trades",
     "high = np.maximum(high, close + q[:, 2])", "high = np.maximum(high, q[:, 2])"),
    ("prop_equity.py", "challenge breach on close not intraday low",
     "if bal + lo[i] <= -rules.static_dd:", "if bal + c[i] <= -rules.static_dd:"),
    ("prop_equity.py", "challenge target 1.5x",
     "if bal >= rules.target:", "if bal >= rules.target * 1.5:"),
    ("portfolio_ab.py", "risk doubles after breakeven too",
     "prev_win = float(r) > 0", "prev_win = float(r) >= 0"),
    ("portfolio_ab.py", "challenge stop doubled",
     "bust = live & (eq <= 1.0 + CH_STOP)", "bust = live & (eq <= 1.0 + CH_STOP * 2)"),
    ("portfolio_ab.py", "funded daily limit doubled (scalar)",
     "if float(d) <= -FU_DAILY_LOSS:", "if float(d) <= -FU_DAILY_LOSS * 2:"),
    ("portfolio_ab.py", "funded trailing measured from start (scalar)",
     "peak = max(peak, eq)", "peak = 1.0"),
    ("portfolio_ab.py", "funded daily limit doubled (simulation)",
     "alive &= ~(day <= -FU_DAILY_LOSS)", "alive &= ~(day <= -FU_DAILY_LOSS * 2)"),
    ("portfolio_ab.py", "funded trailing from start (simulation)",
     "peak = np.maximum(peak, eq)", "peak = np.ones(n_paths)"),
    ("portfolio_ab.py", "one-slot rule lets trades overlap",
     'if busy_until is None or row["entry_time"] >= busy_until:', "if True:"),
]


def _tests_fail(tests: list[str]) -> bool:
    cmd = [sys.executable, "-m", "pytest", "-q", "-x", "--no-header", "-p", "no:cacheprovider",
           *[str(HERE / t) for t in tests if (HERE / t).exists()]]
    return subprocess.run(cmd, cwd=HERE.parent, capture_output=True, text=True).returncode == 1


def main() -> int:
    originals = {f: (HERE / f).read_text(encoding="utf-8") for f in GUARDS}
    escaped = []
    try:
        for file, name, good, bad in MUTANTS:
            src = originals[file]
            if src.count(good) != 1:
                print(f"STALE   {file}: {name} (snippet not found exactly once, update the mutant)")
                escaped.append(name)
                continue
            (HERE / file).write_text(src.replace(good, bad), encoding="utf-8")
            try:
                caught = _tests_fail(GUARDS[file])
            finally:
                (HERE / file).write_text(src, encoding="utf-8")
            print(f"{'caught ' if caught else 'ESCAPED'} {file}: {name}", flush=True)
            if not caught:
                escaped.append(name)
    finally:
        for f, src in originals.items():
            (HERE / f).write_text(src, encoding="utf-8")
    print(f"\n{len(MUTANTS) - len(escaped)}/{len(MUTANTS)} mutants caught")
    return 1 if escaped else 0


if __name__ == "__main__":
    raise SystemExit(main())
