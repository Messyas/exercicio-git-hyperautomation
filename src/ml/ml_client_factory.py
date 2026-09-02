import logging
from typing import Any, Optional
import httpx

from src.ml.ml_client import MLClient


def create_ml_client(
    settings: Any,
    logger: logging.Logger,
    *,
    transport: Optional[httpx.BaseTransport] = None,
) -> MLClient:
    """Factory para criar e instanciar MLClient a partir das configurações da aplicação."""
    base_url = getattr(settings, "ml_api_url", "http://127.0.0.1:8000")
    timeout_ms = getattr(settings, "ml_timeout_ms", 1000)
    failure_threshold = getattr(settings, "ml_failure_threshold", 5)

    if transport is not None:
        timeout_sec = max(0.001, timeout_ms / 1000.0)
        client = httpx.Client(
            base_url=base_url.rstrip("/"),
            transport=transport,
            timeout=httpx.Timeout(timeout=timeout_sec, connect=min(0.20, timeout_sec)),
        )
        return MLClient(
            base_url=base_url,
            timeout_ms=timeout_ms,
            failure_threshold=failure_threshold,
            client=client,
            logger_instance=logger,
        )

    return MLClient(
        base_url=base_url,
        timeout_ms=timeout_ms,
        failure_threshold=failure_threshold,
        logger_instance=logger,
    )


get_ml_client = create_ml_client

