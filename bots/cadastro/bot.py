"""Entrypoint BotCity do produtor Playwright."""

from __future__ import annotations

import os


os.environ.setdefault("MAESTRO_ENABLED", "true")
os.environ.setdefault("DATAPOOL_BACKEND", "botcity")
os.environ.setdefault("BOT_ID", "messyas-bot-cadastro-v1")
os.environ.setdefault("VALIDATOR_ACTIVITY_LABEL", "messyas-bot-conferencia-v1")
os.environ.setdefault("BOT_URL", "http://localhost:3000")
os.environ.setdefault("APP_TIMEZONE", "America/Manaus")

from producer import run_producer  # noqa: E402


def main() -> int:
    return run_producer()


if __name__ == "__main__":
    raise SystemExit(main())
