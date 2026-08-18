"""Executa produtor e consumidor no serviço bot-conferencia."""

from __future__ import annotations

import logging
import os
from pathlib import Path

from consumer import run_consumer
from producer import run_producer


def _signal_finished() -> None:
    """Tenta registrar o fim sem sobrescrever o resultado do bot."""
    shutdown_file = os.getenv("SHUTDOWN_FILE")
    if not shutdown_file:
        return
    path = Path(shutdown_file)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.touch()
    except OSError as exc:
        logging.getLogger("botcity.pipeline").warning(
            "Não foi possível registrar o marcador de término %s: %s", path, exc
        )


def main() -> int:
    try:
        os.environ["BOT_ID"] = "bot-lotes-cadastro-playwright-mk7"
        producer_status = run_producer()
        if producer_status:
            return producer_status

        os.environ["BOT_ID"] = "bot-lotes-validacao-mk7"
        return run_consumer()
    finally:
        _signal_finished()


if __name__ == "__main__":
    raise SystemExit(main())
