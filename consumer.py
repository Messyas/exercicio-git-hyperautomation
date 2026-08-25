"""Consome o DataPool, aplica RN01-RN07 e gera o relatório."""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any

import pandas as pd

try:
    from validation_core import validar_dataframe
except ImportError:  # execução no repositório; o pacote renomeia o módulo
    from bot import validar_dataframe
from config import get_settings
from src.datapool_gateway import (
    BotCityDatapoolConsumer,
    ConsumedBatch,
    LocalDatapoolConsumer,
)
from src.maestro_client import (
    ExecutionResult,
    MaestroClient,
    configure_local_logging,
    write_execution_report,
)
from src.resilience import close_logger
from src.time_utils import now_local
from src.validacao import COLUNAS_ESPERADAS
from src.wait_for_predecessor import TASK_STATUS_COMPLETED, wait_for_predecessor


def _consumer(settings, maestro: MaestroClient):
    if settings.datapool_backend == "local":
        return LocalDatapoolConsumer(settings.datapool_local_dir)
    if settings.datapool_backend == "botcity":
        if maestro.sdk is None:
            raise RuntimeError(
                "DATAPOOL_BACKEND=botcity exige MAESTRO_ENABLED=true."
            )
        return BotCityDatapoolConsumer(
            maestro.sdk,
            datapool_label=settings.datapool_label,
            task_id=maestro.task_id,
        )
    raise ValueError(
        "DATAPOOL_BACKEND deve ser 'local' ou 'botcity'."
    )


def _dataframe(batch: ConsumedBatch) -> pd.DataFrame:
    rows = [
        {
            column: item.values.get(column, "")
            for column in COLUNAS_ESPERADAS
        }
        for item in batch.items
    ]
    return pd.DataFrame(rows, columns=COLUNAS_ESPERADAS)


def _serializable_summary(summary: dict[str, Any]) -> dict[str, Any]:
    excluded = {"indices_divergentes", "divergencias"}
    return {
        key: str(value) if isinstance(value, Path) else value
        for key, value in summary.items()
        if key not in excluded
    }


def _registration_failure(item) -> dict[str, Any]:
    return {
        key: item.values.get(key, "")
        for key in (
            "item_id",
            "source_row",
            "lote_id",
            "cadastro_status",
            "cadastro_error",
            "evidence_name",
            "evidence_path",
        )
    }


def _item_metrics(batch: ConsumedBatch | None) -> dict[str, int]:
    """Monta os indicadores de eficiência exigidos pelo Maestro."""
    if batch is None:
        return {
            "total_items": 0,
            "processed_items": 0,
            "failed_items": 0,
        }

    total_items = len(batch.items)
    processed_items = sum(item.state == "DONE" for item in batch.items)
    return {
        "total_items": total_items,
        "processed_items": processed_items,
        "failed_items": total_items - processed_items,
    }


def _signal_pipeline_finished() -> None:
    """Registra o marcador de término sem invalidar uma execução já concluída."""
    shutdown_file = os.getenv("SHUTDOWN_FILE")
    if not shutdown_file:
        return
    path = Path(shutdown_file)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.touch()
    except OSError as exc:
        logging.getLogger("botcity.validador").warning(
            "Não foi possível registrar o marcador de término %s: %s", path, exc
        )


def _wait_for_cadastro_if_needed(maestro: MaestroClient, logger) -> None:
    """Confere no Maestro a conclusão do Cadastro antes da Conferência."""
    if not maestro.enabled or maestro.sdk is None or not maestro.task_id:
        return
    task = maestro.sdk.get_task(maestro.task_id)
    parameters = getattr(task, "parameters", None) or {}
    parent_task_id = str(parameters.get("parent_task_id") or "")
    if not parent_task_id or parent_task_id == "local":
        return
    status = wait_for_predecessor(
        maestro.sdk,
        parent_task_id,
        logger_instance=logger,
    )
    if status not in TASK_STATUS_COMPLETED:
        raise RuntimeError(
            f"Tarefa predecessora do cadastro terminou em estado inválido: {status}."
        )
    logger.info(
        "CADEIA_S10B_CADASTRO_CONFIRMADO parent_task_id=%s status=%s",
        parent_task_id,
        status,
    )


def run_consumer() -> int:
    settings = get_settings()
    log_dir = settings.log_dir / "validador"
    logger = configure_local_logging(
        log_dir,
        execution_id=settings.execution_id,
        bot_id=settings.bot_id,
        logger_name="botcity.validador",
    )
    maestro = MaestroClient(settings, logger)
    started_at = now_local()
    report_path = log_dir / "resumo_execucao.json"
    batch: ConsumedBatch | None = None
    datapool_consumer = None
    result: ExecutionResult

    try:
        maestro.connect()
        maestro.register_start()
        _wait_for_cadastro_if_needed(maestro, logger)
        datapool_consumer = _consumer(settings, maestro)
        batch = datapool_consumer.consume()
        logger.info(
            "DATAPOOL_CONSUMIDO total=%d",
            len(batch.items),
            extra={"batch_id": batch.batch_id},
        )
        reference_date = str(
            batch.items[0].values.get("reference_date", "")
        )
        rejected_by_index = {
            index: _registration_failure(item)
            for index, item in enumerate(batch.items)
            if item.values.get("cadastro_status") == "REJEITADO_NEGOCIO"
        }
        technical_by_index = {
            index: _registration_failure(item)
            for index, item in enumerate(batch.items)
            if item.values.get("cadastro_status")
            in {"FALHA", "FALHA_TECNICA"}
        }
        validation = validar_dataframe(
            _dataframe(batch),
            lotes_validos=batch.reference_lote_ids,
            diretorio_saida=settings.output_dir,
            data_referencia=reference_date,
            logger=logger,
            indices_excluidos=(
                set(rejected_by_index) | set(technical_by_index)
            ),
            rejeicoes_cadastro=list(rejected_by_index.values()),
            falhas_tecnicas=list(technical_by_index.values()),
        )
        divergences_by_index = {
            int(divergence["_indice"]): divergence
            for divergence in validation["divergencias"]
        }
        for index, item in enumerate(batch.items):
            context = {
                "batch_id": batch.batch_id,
                "lote_id": item.values.get("lote_id") or None,
                "source_row": item.values.get("source_row"),
            }
            divergence = divergences_by_index.get(index)
            if index in technical_by_index:
                message = str(
                    technical_by_index[index].get("cadastro_error")
                    or "Falha técnica durante o cadastro web."
                )
                item.report_system_error(message[:1000])
                logger.error("ITEM_CADASTRO_FALHA_TECNICA", extra=context)
            elif index in rejected_by_index:
                message = str(
                    rejected_by_index[index].get("cadastro_error")
                    or "Cadastro rejeitado pelo formulário."
                )
                item.report_business_error(message[:1000])
                logger.warning("ITEM_CADASTRO_REJEITADO", extra=context)
            elif divergence is None:
                item.report_done("Registro validado sem divergências.")
                logger.info("ITEM_VALIDADO_OK", extra=context)
            else:
                message = (
                    f"{divergence['regra_violada']}: "
                    f"{divergence['descricao_do_erro']}"
                )
                item.report_business_error(message[:1000])
                logger.warning(
                    "ITEM_VALIDADO_NOK regras=%s",
                    divergence["regra_violada"],
                    extra=context,
                )

        state_artifact = datapool_consumer.persist_states(batch)
        summary = {
            "batch_id": batch.batch_id,
            "source_file": batch.source_file,
            **_serializable_summary(validation),
            "total_rejeicoes_cadastro": len(rejected_by_index),
            "total_falhas_tecnicas": len(technical_by_index),
            **_item_metrics(batch),
        }
        if state_artifact is not None:
            summary["datapool_result"] = str(state_artifact)
        result_factory = (
            ExecutionResult.partial
            if technical_by_index
            else ExecutionResult.success
        )
        result = result_factory(
            started_at=started_at,
            finished_at=now_local(),
            summary=summary,
        )
        logger.info(
            "VALIDACAO_CONCLUIDA divergencias=%d relatorio=%s",
            validation["total_divergencias"],
            validation["relatorio"],
            extra={"batch_id": batch.batch_id},
        )
    except Exception as error:
        if batch is not None:
            for item in batch.items:
                if item.state == "PROCESSING":
                    try:
                        item.report_system_error(str(error)[:1000])
                    except Exception:
                        logger.exception(
                            "FALHA_AO_REPORTAR_ERRO_DE_SISTEMA"
                        )
        logger.exception("BOT_CONSUMIDOR_FALHOU erro=%s", error)
        result = ExecutionResult.failure(
            started_at=started_at,
            finished_at=now_local(),
            message="Bot consumidor encerrado com falha.",
            summary=_item_metrics(batch),
            error=type(error).__name__,
        )

    try:
        saved_report = write_execution_report(result, report_path)
        maestro.post_artifact(saved_report, "resumo_validador.json")
        if result.completed:
            report = result.summary.get("relatorio")
            if report:
                maestro.post_artifact(Path(str(report)))
            datapool_result = result.summary.get("datapool_result")
            if datapool_result:
                maestro.post_artifact(Path(str(datapool_result)))
        maestro.finish(result, **_item_metrics(batch))
        print(json.dumps(result.to_dict(), ensure_ascii=False))
        return 0 if result.completed else 1
    finally:
        _signal_pipeline_finished()
        maestro.close()
        close_logger(logger)


if __name__ == "__main__":
    raise SystemExit(run_consumer())
