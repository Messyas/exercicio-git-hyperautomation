"""Primeiro bot S10-B: valida a entrada e dispara o bot de cadastro."""

from __future__ import annotations

import json

from config import get_settings
from src.excel_source import load_excel_batch
from src.maestro_client import (
    ExecutionResult,
    MaestroClient,
    configure_local_logging,
    write_execution_report,
)
from src.orchestrator import PipelineOrchestrator
from src.resilience import close_logger
from src.time_utils import now_local


def run_collector() -> int:
    """Valida o lote e cria a tarefa do cadastro, preservando a cadeia."""
    settings = get_settings()
    log_dir = settings.log_dir / "coletor"
    logger = configure_local_logging(
        log_dir,
        execution_id=settings.execution_id,
        bot_id=settings.bot_id,
        logger_name="botcity.coletor",
    )
    maestro = MaestroClient(settings, logger)
    started_at = now_local()
    report_path = log_dir / "resumo_execucao.json"

    try:
        maestro.connect()
        maestro.register_start()
        batch = load_excel_batch(settings.default_input_file)
        task_id = PipelineOrchestrator(
            settings=settings,
            maestro_client=maestro,
            logger_instance=logger,
        ).disparar_bot_cadastro(batch.batch_id, parent_task_id=maestro.task_id)
        if maestro.enabled and not task_id:
            raise RuntimeError("Não foi possível criar a tarefa do bot de cadastro.")
        logger.info(
            "CADEIA_S10B_COLETOR_PARA_CADASTRO batch_id=%s task_id=%s",
            batch.batch_id,
            task_id,
            extra={"batch_id": batch.batch_id},
        )
        result = ExecutionResult.success(
            started_at=started_at,
            finished_at=now_local(),
            summary={
                "batch_id": batch.batch_id,
                "total_registros": len(batch.records()),
                "next_bot": "messyas-bot-cadastro-v1",
                "next_task_id": task_id,
                "triggered_by": "messyas-bot-coletor-v1",
                "parent_task_id": maestro.task_id or "local",
            },
        )
    except Exception as exc:
        logger.exception("BOT_COLETOR_FALHOU erro=%s", exc)
        result = ExecutionResult.failure(
            started_at=started_at,
            finished_at=now_local(),
            message="Bot coletor encerrado com falha.",
            error=type(exc).__name__,
        )

    try:
        saved_report = write_execution_report(result, report_path)
        maestro.post_artifact(saved_report, "resumo_coletor.json")
        maestro.finish(result)
        print(json.dumps(result.to_dict(), ensure_ascii=False))
        return 0 if result.completed else 1
    finally:
        maestro.close()
        close_logger(logger)


if __name__ == "__main__":
    raise SystemExit(run_collector())
