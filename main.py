"""Ponto de entrada do bot corporativo com resiliência e rastreabilidade."""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path

from bot import executar_bot_cli
from config import get_settings
from src.maestro_client import (
    ExecutionResult,
    MaestroClient,
    configure_local_logging,
    write_execution_report,
)
from src.resilience import (
    RETRYABLE_NETWORK_ERRORS,
    close_logger,
)
from src.time_utils import now_local


def _print_execution_result(result: ExecutionResult) -> None:
    """Exibe o mesmo resultado padronizado usado no artefato JSON."""
    print(json.dumps(result.to_dict(), ensure_ascii=False))


def _failure_result(
    *,
    started_at: datetime,
    message: str,
    error: str,
) -> ExecutionResult:
    return ExecutionResult.failure(
        started_at=started_at,
        finished_at=now_local(),
        message=message,
        error=error,
    )


def _persist_report(
    result: ExecutionResult,
    report_path: Path,
    logger: logging.Logger,
) -> Path | None:
    """Salva a evidência e transforma falhas de escrita em resultado controlado."""
    try:
        return write_execution_report(result, report_path)
    except (OSError, TypeError, ValueError) as exc:
        result.status = "FAILED"
        result.message = "Não foi possível salvar o relatório de execução."
        result.error = "REPORT_WRITE_ERROR"
        logger.error(
            "Falha ao salvar relatório | lote_id=N/A | erro=%s",
            exc,
        )
        return None


def main(argumentos: list[str] | None = None) -> int:
    """Executa o bot e garante o fechamento dos recursos em qualquer saída."""
    settings = get_settings()
    logger = configure_local_logging(
        settings.log_dir,
        execution_id=settings.execution_id,
        bot_id=settings.bot_id,
    )
    started_at = now_local()
    maestro = MaestroClient(settings, logger)

    try:
        logger.info("Iniciando auditoria de acessos | lote_id=N/A")
        try:
            maestro.connect()
            maestro.register_start()
        except RETRYABLE_NETWORK_ERRORS as exc:
            logger.error(
                "Falha de rede ao inicializar Maestro após 3 tentativas "
                "| lote_id=N/A | erro=%s",
                exc,
            )
        except (OSError, RuntimeError, ValueError, TypeError) as exc:
            logger.error(
                "Falha ao inicializar Maestro | lote_id=N/A | erro=%s",
                exc,
            )
        except Exception as exc:
            logger.exception(
                "Erro inesperado ao inicializar Maestro "
                "| lote_id=N/A | erro=%s",
                exc,
            )

        if not settings.input_dir.is_dir():
            message = f"Pasta de entrada não encontrada: {settings.input_dir}"
            logger.error("%s | lote_id=N/A", message)
            maestro.alert_missing_input(settings.input_dir)
            result = _failure_result(
                started_at=started_at,
                message=message,
                error="INPUT_DIRECTORY_NOT_FOUND",
            )
            report_path = _persist_report(
                result, settings.execution_report_file, logger
            )
            if report_path is not None:
                maestro.post_report(report_path)
            maestro.finish(result)
            _print_execution_result(result)
            return 1

        try:
            bot_summary = executar_bot_cli(argumentos, logger=logger)
            finished_at = now_local()
            summary = {
                str(key): str(value) for key, value in bot_summary.items()
            }
            if bot_summary.get("status_execucao") == "SUCESSO":
                result = ExecutionResult.success(
                    started_at=started_at,
                    finished_at=finished_at,
                    summary=summary,
                )
                logger.info("Auditoria de acessos concluída com sucesso.")
            else:
                result = ExecutionResult.failure(
                    started_at=started_at,
                    finished_at=finished_at,
                    message="Auditoria de acessos encerrada com erro.",
                    summary=summary,
                    error=str(bot_summary.get("status_execucao", "UNKNOWN_ERROR")),
                )
                logger.error(
                    "Auditoria encerrada com status %s | lote_id=N/A.",
                    result.error,
                )
        except (OSError, ValueError, ImportError, KeyError, TypeError, RuntimeError) as exc:
            logger.error(
                "Falha no processamento da auditoria "
                "| lote_id=N/A | erro=%s",
                exc,
            )
            result = _failure_result(
                started_at=started_at,
                message="Auditoria de acessos encerrada por falha tratada.",
                error=type(exc).__name__,
            )
        except Exception as exc:
            logger.exception(
                "Erro inesperado durante a auditoria "
                "| lote_id=N/A | erro=%s",
                exc,
            )
            result = _failure_result(
                started_at=started_at,
                message="Auditoria de acessos encerrada por exceção inesperada.",
                error=type(exc).__name__,
            )

        report_path = _persist_report(
            result, settings.execution_report_file, logger
        )
        if report_path is not None:
            logger.info("Resumo de execução salvo em %s.", report_path)
            maestro.post_report(report_path)
        maestro.finish(result)
        _print_execution_result(result)
        return 0 if report_path is not None and result.succeeded else 1
    finally:
        maestro.close()
        close_logger(logger)


if __name__ == "__main__":
    raise SystemExit(main())
