"""Logging estruturado independente de integrações externas."""

from __future__ import annotations

import logging
from pathlib import Path


class _ContextFilter(logging.Filter):
    """Injeta campos mínimos de rastreabilidade em cada evento."""

    def __init__(self, execution_id: str, bot_id: str):
        super().__init__()
        self.execution_id = execution_id
        self.bot_id = bot_id

    def filter(self, record: logging.LogRecord) -> bool:
        record.execution_id = self.execution_id  # type: ignore[attr-defined]
        record.bot_id = self.bot_id  # type: ignore[attr-defined]
        for field_name in ("batch_id", "lote_id", "source_row"):
            if not hasattr(record, field_name):
                setattr(record, field_name, None)
        return True


def configure_structured_logging(
    log_dir: Path,
    *,
    execution_id: str = "local",
    bot_id: str = "bot-conferencia-lotes",
    logger_name: str = "auditoria",
    log_filename: str = "execucao.log",
) -> logging.Logger:
    """Configura JSON Lines em arquivo e console, sem depender do SDK BotCity."""
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / log_filename
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.INFO)
    logger.propagate = False

    try:
        from pythonjsonlogger.json import JsonFormatter

        formatter: logging.Formatter = JsonFormatter(
            fmt=(
                "%(asctime)s %(levelname)s %(name)s %(execution_id)s "
                "%(bot_id)s %(batch_id)s %(lote_id)s %(source_row)s "
                "%(message)s"
            ),
            datefmt="%Y-%m-%dT%H:%M:%S%z",
            rename_fields={"asctime": "timestamp", "levelname": "level"},
        )
    except ImportError:
        formatter = logging.Formatter(
            fmt=(
                "%(asctime)s | %(levelname)s | execution_id=%(execution_id)s | "
                "bot_id=%(bot_id)s | batch_id=%(batch_id)s | lote_id=%(lote_id)s | "
                "source_row=%(source_row)s | %(message)s"
            ),
            datefmt="%Y-%m-%d %H:%M:%S%z",
        )

    handler_path = str(log_path.resolve())
    if not any(
        isinstance(handler, logging.FileHandler)
        and getattr(handler, "baseFilename", "") == handler_path
        for handler in logger.handlers
    ):
        handler = logging.FileHandler(log_path, encoding="utf-8")
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    if not any(
        isinstance(handler, logging.StreamHandler)
        and not isinstance(handler, logging.FileHandler)
        for handler in logger.handlers
    ):
        console = logging.StreamHandler()
        console.setFormatter(formatter)
        logger.addHandler(console)

    for existing in logger.filters[:]:
        if isinstance(existing, _ContextFilter):
            logger.removeFilter(existing)
    logger.addFilter(_ContextFilter(execution_id, bot_id))
    return logger
