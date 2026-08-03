"""Entrypoint BotCity do consumidor/validador."""

from __future__ import annotations

import os


os.environ.setdefault("MAESTRO_ENABLED", "true")
os.environ.setdefault("DATAPOOL_BACKEND", "botcity")
os.environ.setdefault("BOT_ID", "bot-lotes-validacao-mk7")
os.environ.setdefault("APP_TIMEZONE", "America/Manaus")

from consumer import run_consumer  # noqa: E402


def main() -> int:
    return run_consumer()


if __name__ == "__main__":
    raise SystemExit(main())
