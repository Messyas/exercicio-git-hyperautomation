"""Integração com o BotCity Maestro e resultado padronizado da execução."""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from botcity.maestro import BotMaestroSDK, Column
from botcity.maestro.model import (
    AlertType,
    AutomationTaskFinishStatus,
)

from config import Settings
from src.resilience import RETRYABLE_NETWORK_ERRORS, call_with_network_retry
from src.time_utils import now_local


@dataclass
class ExecutionResult:
    """Contrato único para representar o resultado do processamento."""

    status: str
    message: str
    started_at: str
    finished_at: str
    summary: dict[str, Any] = field(default_factory=dict)
    report_path: str | None = None
    error: str | None = None

    @property
    def succeeded(self) -> bool:
        """Indica se a execução terminou sem erro fatal."""
        return self.status == "SUCCESS"

    @property
    def completed(self) -> bool:
        """Indica término controlado, inclusive com falhas parciais."""
        return self.status in {"SUCCESS", "PARTIALLY_COMPLETED"}

    def to_dict(self) -> dict[str, Any]:
        """Converte o resultado para o formato serializável do artefato."""
        return asdict(self)

    @classmethod
    def success(
        cls,
        *,
        started_at: datetime,
        finished_at: datetime,
        summary: dict[str, Any],
    ) -> "ExecutionResult":
        return cls(
            status="SUCCESS",
            message="Execução concluída com sucesso.",
            started_at=started_at.isoformat(),
            finished_at=finished_at.isoformat(),
            summary=summary,
        )

    @classmethod
    def failure(
        cls,
        *,
        started_at: datetime,
        finished_at: datetime,
        message: str,
        summary: dict[str, Any] | None = None,
        error: str | None = None,
    ) -> "ExecutionResult":
        return cls(
            status="FAILED",
            message=message,
            started_at=started_at.isoformat(),
            finished_at=finished_at.isoformat(),
            summary=summary or {},
            error=error,
        )

    @classmethod
    def partial(
        cls,
        *,
        started_at: datetime,
        finished_at: datetime,
        summary: dict[str, Any],
        message: str = "Execução concluída parcialmente.",
    ) -> "ExecutionResult":
        return cls(
            status="PARTIALLY_COMPLETED",
            message=message,
            started_at=started_at.isoformat(),
            finished_at=finished_at.isoformat(),
            summary=summary,
        )


class _ContextFilter(logging.Filter):
    """Injeta execution_id e bot_id em todas as mensagens de log."""

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


def configure_local_logging(
    log_dir: Path,
    *,
    execution_id: str = "local",
    bot_id: str = "bot-conferencia-lotes",
    logger_name: str = "botcity.auditoria",
    log_filename: str = "execucao.log",
) -> logging.Logger:
    """Configura o log local estruturado em JSON em ``logs/execucao.log``.

    Cada linha de log contém ``execution_id`` e ``bot_id`` para
    rastreabilidade em ambientes orquestrados (Maestro / BotCity).
    """
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
                "%(asctime)s | %(levelname)s | "
                "execution_id=%(execution_id)s | bot_id=%(bot_id)s | "
                "batch_id=%(batch_id)s | lote_id=%(lote_id)s | "
                "source_row=%(source_row)s | %(message)s"
            ),
            datefmt="%Y-%m-%d %H:%M:%S%z",
        )

    handler_path = str(log_path.resolve())
    already_configured = any(
        isinstance(handler, logging.FileHandler)
        and getattr(handler, "baseFilename", "") == handler_path
        for handler in logger.handlers
    )
    if not already_configured:
        handler = logging.FileHandler(log_path, encoding="utf-8")
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    has_console = any(
        isinstance(handler, logging.StreamHandler)
        and not isinstance(handler, logging.FileHandler)
        for handler in logger.handlers
    )
    if not has_console:
        console = logging.StreamHandler()
        console.setFormatter(formatter)
        logger.addHandler(console)

    # Adiciona o filtro de contexto (idempotente: remove filtros antigos)
    for existing in logger.filters[:]:
        if isinstance(existing, _ContextFilter):
            logger.removeFilter(existing)
    logger.addFilter(_ContextFilter(execution_id, bot_id))

    return logger


def write_execution_report(result: ExecutionResult, path: Path) -> Path:
    """Persiste o resumo final que será enviado ao Maestro como artefato."""
    path.parent.mkdir(parents=True, exist_ok=True)
    result.report_path = str(path)
    path.write_text(
        json.dumps(result.to_dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return path


class MaestroClient:
    """Adaptador pequeno para manter o fluxo principal independente do SDK."""

    def __init__(self, settings: Settings, logger: logging.Logger):
        self.settings = settings
        self.logger = logger
        self.sdk: BotMaestroSDK | None = None
        self.task_id = settings.maestro_task_id

    @property
    def enabled(self) -> bool:
        return self.settings.maestro_enabled

    def connect(self) -> None:
        """Conecta ao Maestro somente quando a integração estiver habilitada."""
        if not self.enabled:
            return

        self.sdk = call_with_network_retry(
            lambda: BotMaestroSDK.from_sys_args(
                default_server=self.settings.maestro_server or "",
                default_login=self.settings.maestro_login or "",
                default_key=self.settings.maestro_key or "",
            ),
            logger=self.logger,
            context="conexao com o Maestro | lote_id=N/A",
        )
        self.task_id = self.task_id or str(self.sdk.task_id or "") or None
        self.logger.info("Conexão com o Maestro estabelecida.")

    def register_start(self) -> None:
        """Registra no Maestro o início da auditoria."""
        self._call("registrar início", self._register_start)

    def alert_missing_input(self, input_dir: Path) -> None:
        """Envia o alerta exigido quando a pasta de entrada não existe."""
        message = f"Pasta de entrada não encontrada: {input_dir}"
        self._call(
            "enviar alerta de pasta ausente",
            lambda: self._send_alert(
                title="Entrada ausente",
                message=message,
                alert_type=AlertType.WARN,
            ),
        )

    def post_report(self, report_path: Path) -> None:
        """Publica o relatório JSON como artefato no Maestro."""
        self.post_artifact(report_path)

    def post_artifact(
        self,
        artifact_path: Path,
        artifact_name: str | None = None,
    ) -> None:
        """Publica um arquivo produzido pelo bot como artefato da tarefa."""
        if not self.enabled:
            return
        if not self.task_id:
            self.logger.warning(
                "Artefato não publicado: MAESTRO_TASK_ID não foi informado."
            )
            return
        name = artifact_name or artifact_path.name
        self._call(
            f"publicar artefato {name}",
            lambda: self.sdk.post_artifact(
                int(self.task_id), name, str(artifact_path)
            ),
        )
        if not self.sdk.access_token:
            raise ValueError(
                "Maestro habilitado sem autenticação: execute pelo BotRunner "
                "ou configure MAESTRO_SERVER, MAESTRO_LOGIN e MAESTRO_KEY."
            )

    def finish(
        self,
        result: ExecutionResult,
        *,
        total_items: int | None = None,
        processed_items: int | None = None,
        failed_items: int | None = None,
    ) -> None:
        """Finaliza a tarefa e reporta seus indicadores de eficiência."""
        if not self.enabled or not self.task_id:
            return

        statuses = {
            "SUCCESS": AutomationTaskFinishStatus.SUCCESS,
            "PARTIALLY_COMPLETED": (
                AutomationTaskFinishStatus.PARTIALLY_COMPLETED
            ),
            "FAILED": AutomationTaskFinishStatus.FAILED,
        }
        status = statuses.get(
            result.status, AutomationTaskFinishStatus.FAILED
        )
        if total_items is None:
            total_items = result.summary.get("total_items")
        if total_items is None:
            total_items = result.summary.get("total")
        if total_items is None:
            total_items = result.summary.get("total_registros", 0)

        if failed_items is None:
            failed_items = result.summary.get("failed_items")
        if failed_items is None:
            failed_items = result.summary.get("cadastros_falha")
        if failed_items is None:
            failed_items = result.summary.get("cadastros_falha_tecnica")
        if failed_items is None:
            failed_items = result.summary.get("total_falhas_tecnicas", 0)

        if processed_items is None:
            processed_items = result.summary.get("processed_items")
        if processed_items is None:
            processed_items = int(total_items) - int(failed_items)

        self._call(
            "finalizar tarefa",
            lambda: self.sdk.finish_task(
                task_id=int(self.task_id),
                status=status,
                message=result.message,
                total_items=int(total_items),
                processed_items=int(processed_items),
                failed_items=int(failed_items),
            ),
        )

    def close(self) -> None:
        """Encerra a sessão local do SDK mesmo após uma falha."""
        if self.sdk is None:
            return
        try:
            self.sdk.logoff()
        except (OSError, RuntimeError, ValueError) as exc:
            self.logger.error(
                "Falha ao encerrar sessao do Maestro | lote_id=N/A | erro=%s",
                exc,
            )
        finally:
            self.sdk = None

    def _register_start(self) -> None:
        if self.task_id:
            self._send_alert(
                title="Execução do bot",
                message="Iniciando processamento",
                alert_type=AlertType.INFO,
            )
            return

        # Execuções locais sem task id ainda ficam registradas em um log do
        # Maestro, caso a conta esteja conectada.
        self.sdk.new_log(
            self.settings.maestro_activity_label,
            [
                Column(name="Timestamp", label="timestamp"),
                Column(name="Mensagem", label="mensagem"),
            ],
        )
        self.sdk.new_log_entry(
            self.settings.maestro_activity_label,
            {
                "timestamp": now_local().isoformat(),
                "mensagem": "Iniciando processamento",
            },
        )

    def _send_alert(self, *, title: str, message: str, alert_type: AlertType) -> None:
        if not self.task_id:
            raise ValueError("Task ID é necessário para enviar alerta ao Maestro.")
        self.sdk.alert(str(self.task_id), title, message, alert_type)

    def _call(self, operation: str, callback) -> None:
        if not self.enabled:
            return
        if self.sdk is None:
            self.logger.warning("Maestro indisponível para %s.", operation)
            return
        try:
            call_with_network_retry(
                callback,
                logger=self.logger,
                context=f"{operation} | lote_id=N/A",
            )
        except RETRYABLE_NETWORK_ERRORS as exc:
            self.logger.error(
                "Falha de rede ao %s apos 3 tentativas | lote_id=N/A | erro=%s",
                operation,
                exc,
            )
        except (OSError, RuntimeError, ValueError, TypeError) as exc:
            self.logger.error(
                "Falha ao %s | lote_id=N/A | erro=%s",
                operation,
                exc,
            )
        except Exception as exc:  # integração não deve apagar a evidência local
            self.logger.exception(
                "Erro inesperado ao %s | lote_id=N/A | erro=%s",
                operation,
                exc,
            )
