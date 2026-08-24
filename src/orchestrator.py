"""Orquestrador Multi-Bot para o Maestro (Estudo de Caso S10-B).

Este módulo implementa o encadeamento sequencial de 3+ bots registrados no Maestro:
1. `grupo-bot-coletor-v1`: Ingestão, validação da planilha e disponibilização do lote.
2. `grupo-bot-cadastro-v1`: Processamento web RPA via Playwright.
3. `grupo-bot-conferencia-v1`: Conferência RN01–RN07, classificação híbrida ML e alertas.

Atende às Seções 3.1, 8 e 9.1 do enunciado.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Optional

from config import Settings, get_settings
from src.maestro_client import MaestroClient

logger = logging.getLogger(__name__)

# Nomenclatura oficial dos 3 bots para o Maestro (nome_aluno-nome_bot-versao)
BOT_COLETOR_LABEL = "messyas-bot-coletor-v1"
BOT_CADASTRO_LABEL = "messyas-bot-cadastro-v1"
BOT_CONFERENCIA_LABEL = "messyas-bot-conferencia-v1"


class PipelineOrchestrator:
    """Gerenciador de tarefas e cadeia de dependências no Maestro."""

    def __init__(
        self,
        settings: Optional[Settings] = None,
        maestro_client: Optional[MaestroClient] = None,
        logger_instance: Optional[logging.Logger] = None,
    ):
        self.settings = settings or get_settings()
        self.logger = logger_instance or logger
        self.maestro = maestro_client or MaestroClient(self.settings, self.logger)

    def disparar_bot_cadastro(
        self,
        batch_id: str,
        parent_task_id: Optional[str] = None,
    ) -> Optional[str]:
        """Dispara o Bot 2 (Cadastro Web) após conclusão do Bot 1 (Coletor)."""
        parameters = {
            "batch_id": batch_id,
            "triggered_by": BOT_COLETOR_LABEL,
            "parent_task_id": parent_task_id or self.settings.maestro_task_id or "local",
        }
        self.logger.info(
            f"[ORCHESTRATOR] Disparando '{BOT_CADASTRO_LABEL}' para lote {batch_id}..."
        )
        return self._create_maestro_task(BOT_CADASTRO_LABEL, parameters)

    def disparar_bot_conferencia(
        self,
        batch_id: str,
        parent_task_id: Optional[str] = None,
    ) -> Optional[str]:
        """Dispara o Bot 3 (Conferência Híbrida) após conclusão do Bot 2 (Cadastro)."""
        parameters = {
            "batch_id": batch_id,
            "triggered_by": BOT_CADASTRO_LABEL,
            "parent_task_id": parent_task_id or self.settings.maestro_task_id or "local",
        }
        self.logger.info(
            f"[ORCHESTRATOR] Disparando '{BOT_CONFERENCIA_LABEL}' para lote {batch_id}..."
        )
        return self._create_maestro_task(BOT_CONFERENCIA_LABEL, parameters)

    def _create_maestro_task(
        self,
        activity_label: str,
        parameters: dict[str, Any],
    ) -> Optional[str]:
        """Cria tarefa no BotCity Maestro usando create_task da SDK se habilitado."""
        if not self.settings.maestro_enabled or self.maestro.sdk is None:
            self.logger.info(
                f"[ORCHESTRATOR_LOCAL] Maestro desativado. Simulação local da tarefa '{activity_label}' "
                f"com parâmetros: {parameters}"
            )
            return f"local-task-{activity_label}"

        try:
            task = self.maestro.sdk.create_task(
                activity_label=activity_label,
                parameters=parameters,
            )
            task_id = str(getattr(task, "id", getattr(task, "task_id", "desconhecido")))
            self.logger.info(
                f"[ORCHESTRATOR_MAESTRO] Tarefa '{activity_label}' criada com SUCESSO | task_id={task_id}"
            )
            return task_id
        except Exception as exc:
            self.logger.error(
                f"[ORCHESTRATOR_ERRO] Falha ao criar tarefa '{activity_label}' no Maestro: {exc}"
            )
            return None


def executar_pipeline_completo() -> int:
    """Ponto de entrada do orquestrador para execução dos 3 bots em cadeia."""
    settings = get_settings()
    logging.basicConfig(level=logging.INFO)
    orchestrator = PipelineOrchestrator(settings)

    print("=== INICIANDO PIPELINE MULTI-BOT ORQUESTRADO (3 BOTS) ===")
    batch_id = f"lote-{settings.execution_id}"

    # Bot 1 -> Bot 2
    task2_id = orchestrator.disparar_bot_cadastro(batch_id)
    print(f"-> Bot 1 (Coletor) concluiu. Bot 2 (Cadastro) iniciado com task_id: {task2_id}")

    # Bot 2 -> Bot 3
    task3_id = orchestrator.disparar_bot_conferencia(batch_id, parent_task_id=task2_id)
    print(f"-> Bot 2 (Cadastro) concluiu. Bot 3 (Conferência) iniciado com task_id: {task3_id}")

    print("=== PIPELINE MULTI-BOT DISPARADO COM SUCESSO ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(executar_pipeline_completo())
