"""Ponto de entrada independente do bot Playwright."""

from __future__ import annotations

import sys
from pathlib import Path


TEST_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TEST_DIR))

from src.runner import run_bot  # noqa: E402
from web_automation import PlaywrightAutomation  # noqa: E402


DATAPOOL_PATH = Path(__file__).with_name("datapool.json")


if __name__ == "__main__":
    raise SystemExit(
        run_bot("Playwright", DATAPOOL_PATH, PlaywrightAutomation)
    )
