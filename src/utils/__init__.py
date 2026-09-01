"""Módulo de Utilitários Genéricos e Resiliência (The DX Way)."""

from src.utils.dead_letter import (
    DEFAULT_DEAD_LETTER_DIR,
    DeadLetterItem,
    DeadLetterQueue,
)
from src.utils.excel_source import ExcelBatch, load_excel_batch
from src.utils.resilience import (
    RETRYABLE_NETWORK_ERRORS,
    call_with_network_retry,
    close_logger,
    with_network_retry,
)
from src.utils.structured_logging import (
    configure_structured_logging,
)
from src.utils.time_utils import (
    DEFAULT_TIMEZONE,
    now_local,
    operational_timezone,
)

__all__ = [
    "DEFAULT_DEAD_LETTER_DIR",
    "DeadLetterItem",
    "DeadLetterQueue",
    "ExcelBatch",
    "load_excel_batch",
    "RETRYABLE_NETWORK_ERRORS",
    "call_with_network_retry",
    "close_logger",
    "with_network_retry",
    "configure_structured_logging",
    "DEFAULT_TIMEZONE",
    "now_local",
    "operational_timezone",
]
