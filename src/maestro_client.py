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
            message="Auditoria de acessos concluída.",
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


def configure_local_logging(log_dir: Path) -> logging.Logger:
    """Configura o log local padronizado em ``logs/execucao.log``."""
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / "execucao.log"
    logger = logging.getLogger("botcity.auditoria")
    logger.setLevel(logging.INFO)
    logger.propagate = False

    handler_path = str(log_path.resolve())
    already_configured = any(
        isinstance(handler, logging.FileHandler)
        and getattr(handler, "baseFilename", "") == handler_path
        for handler in logger.handlers
    )
    if not already_configured:
        handler = logging.FileHandler(log_path, encoding="utf-8")
        handler.setFormatter(
            logging.Formatter(
                fmt="%(asctime)s | %(levelname)s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S%z",
            )
        )
        logger.addHandler(handler)

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

        missing = [
            name
            for name, value in {
                "MAESTRO_SERVER": self.settings.maestro_server,
                "MAESTRO_LOGIN": self.settings.maestro_login,
                "MAESTRO_KEY": self.settings.maestro_key,
            }.items()
            if not value
        ]
        if missing:
            raise ValueError(
                "Integração Maestro habilitada, mas faltam variáveis: "
                + ", ".join(missing)
            )

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
        if not self.enabled:
            return
        if not self.task_id:
            self.logger.warning(
                "Relatório não publicado: MAESTRO_TASK_ID não foi informado."
            )
            return
        self._call(
            "publicar relatório como artefato",
            lambda: self.sdk.post_artifact(
                int(self.task_id), "resumo_execucao.json", str(report_path)
            ),
        )

    def finish(self, result: ExecutionResult) -> None:
        """Atualiza o status da tarefa no Maestro, quando houver task id."""
        if not self.enabled or not self.task_id:
            return

        status = (
            AutomationTaskFinishStatus.SUCCESS
            if result.succeeded
            else AutomationTaskFinishStatus.FAILED
        )
        self._call(
            "finalizar tarefa",
            lambda: self.sdk.finish_task(
                self.task_id,
                status,
                message=result.message,
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
                title="Auditoria de acessos",
                message="Iniciando auditoria de acessos",
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
                "timestamp": datetime.now().astimezone().isoformat(),
                "mensagem": "Iniciando auditoria de acessos",
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
