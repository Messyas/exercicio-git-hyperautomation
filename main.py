"""Ponto de entrada do bot corporativo.

Nesta etapa, o launcher delega o fluxo legado para ``bot.py``. A separação
permite adicionar as integrações BotCity nas próximas issues sem quebrar as
regras de negócio e os testes existentes.
"""

from __future__ import annotations

import json
from datetime import datetime

from bot import executar_bot_cli
from config import get_settings
from src.maestro_client import (
    ExecutionResult,
    MaestroClient,
    configure_local_logging,
    write_execution_report,
)


def _print_execution_result(result: ExecutionResult) -> None:
    """Exibe o mesmo resultado padronizado usado no artefato JSON."""
    print(json.dumps(result.to_dict(), ensure_ascii=False))


def main(argumentos: list[str] | None = None) -> int:
    """Executa o bot com rastreabilidade local e no Maestro."""
    settings = get_settings()
    logger = configure_local_logging(settings.log_dir)
    started_at = datetime.now().astimezone()
    maestro = MaestroClient(settings, logger)

    logger.info("Iniciando auditoria de acessos")
    try:
        maestro.connect()
        maestro.register_start()
    except Exception as exc:
        logger.error("Não foi possível inicializar o Maestro: %s", exc)

    if not settings.input_dir.is_dir():
        message = f"Pasta de entrada não encontrada: {settings.input_dir}"
        logger.error(message)
        maestro.alert_missing_input(settings.input_dir)
        finished_at = datetime.now().astimezone()
        result = ExecutionResult.failure(
            started_at=started_at,
            finished_at=finished_at,
            message=message,
            summary={"input_dir": str(settings.input_dir)},
            error="INPUT_DIRECTORY_NOT_FOUND",
        )
        report_path = write_execution_report(result, settings.execution_report_file)
        maestro.post_report(report_path)
        maestro.finish(result)
        _print_execution_result(result)
        return 1

    try:
        bot_summary = executar_bot_cli(argumentos)
        finished_at = datetime.now().astimezone()
        success = bot_summary.get("status_execucao") == "SUCESSO"
        if success:
            result = ExecutionResult.success(
                started_at=started_at,
                finished_at=finished_at,
                summary={str(key): str(value) for key, value in bot_summary.items()},
            )
            logger.info("Auditoria de acessos concluída com sucesso.")
        else:
            result = ExecutionResult.failure(
                started_at=started_at,
                finished_at=finished_at,
                message="Auditoria de acessos encerrada com erro.",
                summary={str(key): str(value) for key, value in bot_summary.items()},
                error=str(bot_summary.get("status_execucao", "UNKNOWN_ERROR")),
            )
            logger.error("Auditoria encerrada com status %s.", result.error)
    except Exception as exc:
        finished_at = datetime.now().astimezone()
        logger.exception("Erro não tratado durante a auditoria.")
        result = ExecutionResult.failure(
            started_at=started_at,
            finished_at=finished_at,
            message="Auditoria de acessos encerrada por exceção.",
            error=str(exc),
        )

    report_path = write_execution_report(result, settings.execution_report_file)
    logger.info("Resumo de execução salvo em %s.", report_path)
    maestro.post_report(report_path)
    maestro.finish(result)
    _print_execution_result(result)
    return 0 if result.succeeded else 1


if __name__ == "__main__":
    raise SystemExit(main())
