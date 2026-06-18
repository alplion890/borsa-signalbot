"""Repository entrypoint for GitHub Actions."""
from __future__ import annotations

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "strategy-lab"))

from intraday.signalbot.signal_scan import main


if __name__ == "__main__":
    main()
