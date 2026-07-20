"""Políticas reutilizáveis de retry e fechamento da execução."""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from typing import TypeVar

from requests.exceptions import ConnectionError as RequestsConnectionError
from requests.exceptions import Timeout


T = TypeVar("T")
RETRYABLE_NETWORK_ERRORS = (RequestsConnectionError, Timeout)
MAX_NETWORK_ATTEMPTS = 3
NETWORK_RETRY_DELAY_SECONDS = 1.0


def call_with_network_retry(
    operation: Callable[[], T],
    *,
    logger: logging.Logger,
    context: str,
    attempts: int = MAX_NETWORK_ATTEMPTS,
    delay_seconds: float = NETWORK_RETRY_DELAY_SECONDS,
) -> T:
    """Repete somente falhas transitórias de conexão ou timeout de rede."""
    if not 1 <= attempts <= MAX_NETWORK_ATTEMPTS:
        raise ValueError("A política permite entre 1 e 3 tentativas.")
    if delay_seconds < 0:
        raise ValueError("O intervalo de retry não pode ser negativo.")

    for attempt in range(1, attempts + 1):
        try:
            return operation()
        except RETRYABLE_NETWORK_ERRORS as exc:
            if attempt == attempts:
                raise
            logger.warning(
                "Falha de rede em %s | tentativa=%d/%d | erro=%s",
                context,
                attempt,
                attempts,
                exc,
            )
            time.sleep(delay_seconds)

    raise RuntimeError("A operação terminou sem resultado.")


def close_logger(logger: logging.Logger) -> None:
    """Libera os handlers de arquivo ao final da execução."""
    for handler in logger.handlers[:]:
        try:
            handler.flush()
            handler.close()
        finally:
            logger.removeHandler(handler)

