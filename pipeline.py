"""Ponto de entrada do Pipeline integrado sequencial."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import src.runners.pipeline as _m
from src.runners.pipeline import *

for _attr in dir(_m):
    if not _attr.startswith("__"):
        globals()[_attr] = getattr(_m, _attr)

if __name__ == "__main__":
    raise SystemExit(main())
