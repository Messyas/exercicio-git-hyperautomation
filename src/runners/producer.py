"""Lê a planilha, executa o cadastro web e publica no DataPool."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from config import get_settings
from src.automation.datapool_gateway import (
    BotCityDatapoolPublisher,
    LocalDatapoolPublisher,
)
from src.utils.excel_source import load_excel_batch
from src.automation.maestro_client import (
    ExecutionResult,
    MaestroClient,
    configure_local_logging,
    write_execution_report,
)
from src.pages import RegistrationRejectedError
from src.automation.playwright_automation import PlaywrightAutomation
from src.reporting.relatorio import gerar_relatorio_erros_fluxo
from src.utils.resilience import close_logger
from src.utils.time_utils import now_local
from src.automation.wait_for_predecessor import TASK_STATUS_COMPLETED, wait_for_predecessor


def _safe_name(value: str) -> str:
    return re.sub(r"[^\w.-]+", "_", value, flags=re.UNICODE).strip("_")


def _context(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "extra": {
            "batch_id": record.get("batch_id"),
            "lote_id": record.get("lote_id") or None,
            "source_row": record.get("source_row"),
        }
    }


def _evidence_fields(path: Path) -> dict[str, str]:
    """Mantem o nome legado e registra o caminho completo da evidencia."""
    return {
        "evidence_name": path.name,
        "evidence_path": path.resolve().as_posix(),
    }


def _publisher(settings, maestro: MaestroClient):
    if settings.datapool_backend == "local":
        return LocalDatapoolPublisher(settings.datapool_local_dir)
    if settings.datapool_backend == "botcity":
        if maestro.sdk is None:
            raise RuntimeError(
                "DATAPOOL_BACKEND=botcity exige MAESTRO_ENABLED=true."
            )
        return BotCityDatapoolPublisher(
            maestro.sdk,
            datapool_label=settings.datapool_label,
            validator_activity_label=settings.validator_activity_label,
            parent_task_id=maestro.task_id,
        )
    raise ValueError(
        "DATAPOOL_BACKEND deve ser 'local' ou 'botcity'."
    )


def _wait_for_collector_if_needed(maestro: MaestroClient, logger) -> None:
    """Garante que Cadastro só prossiga após o Coletor concluir no Maestro."""
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
            f"Tarefa predecessora do coletor terminou em estado inválido: {status}."
        )
    logger.info(
        "CADEIA_S10B_COLETOR_CONFIRMADO parent_task_id=%s status=%s",
        parent_task_id,
        status,
    )


def run_producer() -> int:
    settings = get_settings()
    log_dir = settings.log_dir / "produtor"
    logger = configure_local_logging(
        log_dir,
        execution_id=settings.execution_id,
        bot_id=settings.bot_id,
        logger_name="botcity.produtor",
    )
    maestro = MaestroClient(settings, logger)
    started_at = now_local()
    report_path = log_dir / "resumo_execucao.json"
    evidence_root = settings.playwright_artifacts_dir / settings.execution_id
    evidence_dir = evidence_root / "produtor"
    created_evidence: list[Path] = []
    flow_report_path: Path | None = None
    result: ExecutionResult

    try:
        maestro.connect()
        maestro.register_start()
        _wait_for_collector_if_needed(maestro, logger)
        batch = load_excel_batch(settings.default_input_file)
        records = batch.records()
        evidence_dir = evidence_root / batch.batch_id / "produtor"
        logger.info(
            "PLANILHA_CARREGADA total=%d arquivo=%s",
            len(records),
            batch.source_file,
            extra={"batch_id": batch.batch_id},
        )

        publisher = _publisher(settings, maestro)
        publisher.check_ready()
        logger.info(
            "DESTINO_DATAPOOL_VALIDADO backend=%s label=%s",
            settings.datapool_backend,
            settings.datapool_label,
            extra={"batch_id": batch.batch_id},
        )

        published: list[dict[str, Any]] = []
        flow_errors: list[dict[str, Any]] = []
        credentials = {
            "usuario": settings.web_username,
            "senha": settings.web_password,
        }
        with PlaywrightAutomation(
            settings.playwright_url,
            headless=settings.playwright_headless,
            slow_mo=settings.playwright_slow_mo,
            timeout_ms=settings.playwright_timeout_ms,
        ) as automation:
            automation.login(credentials)
            logger.info(
                "LOGIN_REALIZADO_COM_SUCESSO",
                extra={"batch_id": batch.batch_id},
            )
            for record in records:
                lote_label = str(
                    record.get("lote_id")
                    or f"linha-{record['source_row']}"
                )
                row_label = f"linha-{record['source_row']}"
                evidence_name = (
                    f"comprovante_{row_label}_{_safe_name(lote_label)}.png"
                )
                evidence_path = evidence_dir / evidence_name
                item = dict(record)
                logger.info(
                    "CADASTRO_WEB_INICIADO",
                    **_context(record),
                )
                try:
                    automation.register(record, evidence_path)
                    item.update(
                        {
                            "cadastro_status": "SUCESSO",
                            "cadastro_error": "",
                            "cadastro_error_type": "",
                            **_evidence_fields(evidence_path),
                        }
                    )
                    created_evidence.append(evidence_path)
                    logger.info(
                        "CADASTRO_WEB_CONCLUIDO evidencia=%s",
                        evidence_path,
                        **_context(record),
                    )
                except RegistrationRejectedError as error:
                    error_name = (
                        f"rejeicao_{row_label}_{_safe_name(lote_label)}.png"
                    )
                    error_path = evidence_dir / error_name
                    automation.capture_rejection(error_path)
                    created_evidence.append(error_path)
                    item.update(
                        {
                            "cadastro_status": "REJEITADO_NEGOCIO",
                            "cadastro_error": str(error),
                            "cadastro_error_type": "BUSINESS",
                            **_evidence_fields(error_path),
                        }
                    )
                    logger.warning(
                        "CADASTRO_WEB_REJEITADO evidencia=%s motivo=%s",
                        error_path,
                        error,
                        **_context(record),
                    )
                except PlaywrightTimeoutError as error:
                    error_name = (
                        f"erro_timeout_{row_label}_{_safe_name(lote_label)}.png"
                    )
                    error_path = evidence_dir / error_name
                    automation.capture_error(error_path)
                    created_evidence.append(error_path)
                    item.update(
                        {
                            "cadastro_status": "FALHA_TECNICA",
                            "cadastro_error": f"TIMEOUT: {error}",
                            "cadastro_error_type": "SYSTEM",
                            **_evidence_fields(error_path),
                        }
                    )
                    logger.error(
                        "TIMEOUT_AO_CARREGAR_COMPROVANTE evidencia=%s erro=%s",
                        error_path,
                        error,
                        **_context(record),
                    )
                except Exception as error:
                    error_name = (
                        f"erro_{row_label}_{_safe_name(lote_label)}.png"
                    )
                    error_path = evidence_dir / error_name
                    try:
                        automation.capture_error(error_path)
                        created_evidence.append(error_path)
                    except Exception:
                        logger.exception(
                            "FALHA_AO_CAPTURAR_EVIDENCIA",
                            **_context(record),
                        )
                    item.update(
                        {
                            "cadastro_status": "FALHA_TECNICA",
                            "cadastro_error": str(error),
                            "cadastro_error_type": "SYSTEM",
                            **_evidence_fields(error_path),
                        }
                    )
                    logger.exception(
                        "CADASTRO_WEB_FALHOU erro=%s evidencia=%s",
                        error,
                        error_path,
                        **_context(record),
                    )
                if item["cadastro_status"] == "SUCESSO":
                    published.append(item)
                else:
                    flow_errors.append(item)

        if flow_errors:
            flow_report_path = gerar_relatorio_erros_fluxo(
                flow_errors,
                settings.output_dir,
            )
            logger.warning(
                "ERROS_FLUXO_REGISTRADOS total=%d relatorio=%s",
                len(flow_errors),
                flow_report_path,
                extra={"batch_id": batch.batch_id},
            )

        if not published:
            raise RuntimeError("Nenhum cadastro concluído para publicar no DataPool.")

        for item in published:
            item["batch_total"] = len(published)
            item["producer_execution_id"] = settings.execution_id

        destination = publisher.publish(
            batch_id=batch.batch_id,
            records=published,
            reference_lote_ids=batch.reference_lote_ids,
        )
        successes = len(published)
        rejections = sum(
            item["cadastro_status"] == "REJEITADO_NEGOCIO"
            for item in flow_errors
        )
        technical_failures = sum(
            item["cadastro_status"] == "FALHA_TECNICA"
            for item in flow_errors
        )
        summary = {
            "batch_id": batch.batch_id,
            "source_file": str(batch.source_file),
            "source_hash": batch.source_hash,
            "datapool": destination,
            "total": len(records),
            "itens_publicados_datapool": len(published),
            "erros_fluxo": len(flow_errors),
            "relatorio_erros_fluxo": (
                str(flow_report_path) if flow_report_path else ""
            ),
            "cadastros_sucesso": successes,
            "cadastros_rejeitados": rejections,
            "cadastros_falha_tecnica": technical_failures,
            "cadastros_falha": rejections + technical_failures,
        }
        result_factory = (
            ExecutionResult.partial
            if flow_errors
            else ExecutionResult.success
        )
        result = result_factory(
            started_at=started_at,
            finished_at=now_local(),
            summary=summary,
        )
        logger.info(
            "DATAPOOL_PUBLICADO destino=%s total=%d",
            destination,
            len(published),
            extra={"batch_id": batch.batch_id},
        )
    except Exception as error:
        logger.exception("BOT_PRODUTOR_FALHOU erro=%s", error)
        result = ExecutionResult.failure(
            started_at=started_at,
            finished_at=now_local(),
            message="Bot produtor encerrado com falha.",
            error=type(error).__name__,
        )

    try:
        saved_report = write_execution_report(result, report_path)
        maestro.post_artifact(saved_report, "resumo_produtor.json")
        if flow_report_path is not None:
            maestro.post_artifact(
                flow_report_path,
                "relatorio_erros_fluxo_produtor.xlsx",
            )
        if result.completed and maestro.enabled:
            for evidence in created_evidence:
                maestro.post_artifact(evidence)
        maestro.finish(result)
        print(json.dumps(result.to_dict(), ensure_ascii=False))
        return 0 if result.completed else 1
    finally:
        maestro.close()
        close_logger(logger)


main = run_producer


if __name__ == "__main__":
    raise SystemExit(run_producer())

