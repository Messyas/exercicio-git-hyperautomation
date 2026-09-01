"""Cria uma vez o schema do DataPool usado pelo pipeline no BotCity."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))

from botcity.maestro import DataPool, FieldType, SchemaField

from config import get_settings
from src.automation.datapool_gateway import DATAPOOL_FIELDS
from src.automation.maestro_client import MaestroClient, configure_local_logging
from src.utils.resilience import close_logger


def main() -> int:
    settings = get_settings()
    logger = configure_local_logging(
        settings.log_dir / "setup",
        execution_id=settings.execution_id,
        bot_id="setup-datapool-lotes",
        logger_name="botcity.setup_datapool",
    )
    maestro = MaestroClient(settings, logger)
    try:
        if not settings.maestro_enabled:
            raise RuntimeError(
                "Defina MAESTRO_ENABLED=true para criar o DataPool remoto."
            )
        maestro.connect()
        if maestro.sdk is None:
            raise RuntimeError("Não foi possível conectar ao BotCity.")

        schema = [
            SchemaField(
                label=field_name,
                type=(
                    FieldType.INTEGER
                    if field_name in {"source_row", "batch_total"}
                    else FieldType.TEXT
                ),
                unique_id=field_name == "item_id",
                display_value=field_name in {"item_id", "lote_id"},
            )
            for field_name in DATAPOOL_FIELDS
        ]
        datapool = DataPool(
            label=settings.datapool_label,
            name="Lotes para validação das novas MK7",
            schema=schema,
            auto_retry=True,
            max_auto_retry=2,
            abort_on_error=True,
            max_errors_before_inactive=5,
            enable_processing_time=True,
            item_max_processing_time=10,
        )
        maestro.sdk.create_datapool(datapool)
        logger.info(
            "DATAPOOL_CRIADO label=%s campos=%d",
            settings.datapool_label,
            len(schema),
        )
        return 0
    finally:
        maestro.close()
        close_logger(logger)


if __name__ == "__main__":
    raise SystemExit(main())
