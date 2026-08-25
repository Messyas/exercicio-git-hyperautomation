"""Entrypoint BotCity do coletor S10-B."""

from __future__ import annotations

import os


os.environ.setdefault("MAESTRO_ENABLED", "true")
os.environ.setdefault("BOT_ID", "messyas-bot-coletor-v1")
os.environ.setdefault("APP_TIMEZONE", "America/Manaus")

from coletor import run_collector  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(run_collector())
