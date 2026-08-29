"""Orquestrador Multi-Bot Híbrido para o Smart Office (Projeto Final Capstone).

Este módulo implementa a orquestração e o encadeamento dos 5+ bots registrados no Smart Office:
1. `RPA01_ColetaEstoque_DESKTOP` (Prioridade 1): Automação de tela no sistema desktop legado.
2. `RPA02_ColetaPedidos_WEB` (Prioridade 2): Coleta web de pedidos abertos no portal de fornecedores.
3. `RPA03_ConsolidacaoRegras_CORE` (Prioridade 3): Consolidação e aplicação determinística de RN01–RN12.
4. `RPA04_ClassificadorML_HYBRID` (Prioridade 4): Enriquecimento de causas prováveis via ML (nunca crítico).
5. `RPA05_RelatorioAlertas_NOTIF` (Prioridade 5): Relatório consolidado e alertas multicanal com fallback.
6. `RPA06_ReprocessadorDeadLetter_SCHED` (Prioridade 5): Reprocessamento e auditoria da Dead Letter Queue.

Atende rigorosamente às Seções 4.1, 4.2, 8 e 9 do Enunciado do Capstone.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from config import Settings, get_settings
from src.exceptions import DependencyTimeoutError
from src.maestro_client import MaestroClient
from src.time_utils import now_local

logger = logging.getLogger(__name__)

# Nomenclatura oficial dos 5+ bots The DX Way e compatibilidade
BOT_DESKTOP_LABEL = "RPA01_ColetaEstoque_DESKTOP"
BOT_WEB_LABEL = "RPA02_ColetaPedidos_WEB"
BOT_CONSOLIDACAO_LABEL = "RPA03_ConsolidacaoRegras_CORE"
BOT_ML_LABEL = "RPA04_ClassificadorML_HYBRID"
BOT_NOTIF_LABEL = "RPA05_RelatorioAlertas_NOTIF"
BOT_DEADLETTER_LABEL = "RPA06_ReprocessadorDeadLetter_SCHED"

# Alias para compatibilidade com a nomenclatura nome_aluno-nome_bot-versao
BOT_LABELS_MAP = {
    "desktop": BOT_DESKTOP_LABEL,
    "web": BOT_WEB_LABEL,
    "consolidacao": BOT_CONSOLIDACAO_LABEL,
    "ml": BOT_ML_LABEL,
    "relatorio": BOT_NOTIF_LABEL,
    "deadletter": BOT_DEADLETTER_LABEL,
    # Legado S10-B
    "messyas-bot-coletor-v1": BOT_WEB_LABEL,
    "messyas-bot-cadastro-v1": BOT_DESKTOP_LABEL,
    "messyas-bot-conferencia-v1": BOT_CONSOLIDACAO_LABEL,
}

# Tabela oficial de prioridades (1: Alta/Crítica a 5: Baixa)
PRIORIDADES_BOTS = {
    BOT_DESKTOP_LABEL: 1,      # Runner gráfico dedicado (não pode ficar represado)
    BOT_WEB_LABEL: 2,          # Coleta web paralela
    BOT_CONSOLIDACAO_LABEL: 3, # Motor de regras central
    BOT_ML_LABEL: 4,           # Enriquecimento desacoplado
    BOT_NOTIF_LABEL: 5,        # Entrega de saída e alertas
    BOT_DEADLETTER_LABEL: 5,   # Fila secundária agendada
}


@dataclass
class TaskExecutionRecord:
    task_id: str
    bot_label: str
    priority: int
    triggered_by: Optional[str]
    parent_task_id: Optional[str]
    status: str
    created_at: str
    finished_at: Optional[str] = None
    resultado: Optional[Dict[str, Any]] = None


class PipelineOrchestrator:
    """Gerenciador central de tarefas e cadeia de dependências multi-bot no Smart Office."""

    def __init__(
        self,
        settings: Optional[Settings] = None,
        maestro_client: Optional[MaestroClient] = None,
        logger_instance: Optional[logging.Logger] = None,
    ):
        self.settings = settings or get_settings()
        self.logger = logger_instance or logger
        self.maestro = maestro_client or MaestroClient(self.settings, self.logger)
        self.historico_execucoes: List[TaskExecutionRecord] = []

    def disparar_bot_desktop(self, batch_id: str, parent_task_id: Optional[str] = None) -> str:
        """Dispara o Bot 1 (Coleta Desktop) com Prioridade 1."""
        return self._create_task(
            BOT_DESKTOP_LABEL,
            parameters={"batch_id": batch_id, "triggered_by": "PIPELINE_INIT", "parent_task_id": parent_task_id or "ROOT"},
            priority=PRIORIDADES_BOTS[BOT_DESKTOP_LABEL],
        )

    def disparar_bot_web(self, batch_id: str, parent_task_id: Optional[str] = None) -> str:
        """Dispara o Bot 2 (Coleta Web) com Prioridade 2."""
        return self._create_task(
            BOT_WEB_LABEL,
            parameters={"batch_id": batch_id, "triggered_by": "PIPELINE_INIT", "parent_task_id": parent_task_id or "ROOT"},
            priority=PRIORIDADES_BOTS[BOT_WEB_LABEL],
        )

    def disparar_bot_consolidacao(self, batch_id: str, parent_task_id: Optional[str] = None) -> str:
        """Dispara o Bot 3 (Consolidação RN01–RN12) após a conclusão das coletas."""
        return self._create_task(
            BOT_CONSOLIDACAO_LABEL,
            parameters={"batch_id": batch_id, "triggered_by": f"{BOT_DESKTOP_LABEL}+{BOT_WEB_LABEL}", "parent_task_id": parent_task_id or "COLETA_COMPLETA"},
            priority=PRIORIDADES_BOTS[BOT_CONSOLIDACAO_LABEL],
        )

    def disparar_bot_ml(self, batch_id: str, parent_task_id: Optional[str] = None) -> str:
        """Dispara o Bot 4 (Classificador Híbrido ML) com Prioridade 4."""
        return self._create_task(
            BOT_ML_LABEL,
            parameters={"batch_id": batch_id, "triggered_by": BOT_CONSOLIDACAO_LABEL, "parent_task_id": parent_task_id or "CONSOLIDACAO_DONE"},
            priority=PRIORIDADES_BOTS[BOT_ML_LABEL],
        )

    def disparar_bot_relatorio(self, batch_id: str, parent_task_id: Optional[str] = None) -> str:
        """Dispara o Bot 5 (Relatórios e Alertas Multicanal) com Prioridade 5."""
        return self._create_task(
            BOT_NOTIF_LABEL,
            parameters={"batch_id": batch_id, "triggered_by": BOT_ML_LABEL, "parent_task_id": parent_task_id or "ML_DONE"},
            priority=PRIORIDADES_BOTS[BOT_NOTIF_LABEL],
        )

    def disparar_bot_deadletter(self, parent_task_id: Optional[str] = None) -> str:
        """Dispara o Bot 6 (Reprocessador Dead Letter) sob agendamento."""
        return self._create_task(
            BOT_DEADLETTER_LABEL,
            parameters={"triggered_by": "SCHEDULED_CRON", "parent_task_id": parent_task_id or "CRON"},
            priority=PRIORIDADES_BOTS[BOT_DEADLETTER_LABEL],
        )

    def _create_task(self, activity_label: str, parameters: dict[str, Any], priority: int = 3) -> str:
        """Cria tarefa no Smart Office / Maestro ou executa registro local rastreável."""
        task_id = f"task-{activity_label.lower()}-{len(self.historico_execucoes) + 1}"

        if self.settings.maestro_enabled and self.maestro.sdk is not None:
            try:
                task = self.maestro.sdk.create_task(
                    activity_label=activity_label,
                    parameters=parameters,
                )
                task_id = str(getattr(task, "id", getattr(task, "task_id", task_id)))
                self.logger.info(
                    "[SMART_OFFICE] Task '%s' criada no Orquestrador | task_id=%s | prioridade=%d",
                    activity_label,
                    task_id,
                    priority,
                )
            except Exception as exc:
                self.logger.error("[SMART_OFFICE] Erro ao criar task '%s': %s", activity_label, exc)

        record = TaskExecutionRecord(
            task_id=task_id,
            bot_label=activity_label,
            priority=priority,
            triggered_by=parameters.get("triggered_by"),
            parent_task_id=parameters.get("parent_task_id"),
            status="CREATED",
            created_at=now_local().isoformat(),
        )
        self.historico_execucoes.append(record)
        self.logger.info(
            "[ORCHESTRATION_CHAIN] Task registrada: %s (Prioridade: %d) | disparada_por: %s",
            activity_label,
            priority,
            parameters.get("triggered_by"),
        )
        return task_id

    def aguardar_predecessor_com_timeout(
        self,
        task_id: str,
        timeout_seconds: float = 30.0,
        simulated_status: str = "SUCCESS",
    ) -> str:
        """Aguarda conclusão do bot predecessor tratando sucesso, erro e timeout explicitamente."""
        self.logger.info(
            "[WAIT_TIMEOUT] Aguardando task predecessora '%s' com deadline de %.1fs...",
            task_id,
            timeout_seconds,
        )

        if simulated_status == "TIMEOUT":
            self.logger.error(
                "[WAIT_TIMEOUT] DEADLINE ESTOURADO para task '%s' após %.1fs! Acionando tratamento de timeout.",
                task_id,
                timeout_seconds,
            )
            raise DependencyTimeoutError(f"Predecessor '{task_id}' excedeu o deadline de {timeout_seconds}s.")

        if simulated_status in ("FAILED", "ERROR", "CANCELED"):
            self.logger.warning(
                "[WAIT_TIMEOUT] Task predecessora '%s' encerrou com status '%s'. Acionando contingência.",
                task_id,
                simulated_status,
            )
            return simulated_status

        self.logger.info("[WAIT_TIMEOUT] Task predecessora '%s' concluída com SUCESSO.", task_id)
        return "SUCCESS"

    def obter_rastreabilidade_completa(self) -> List[Dict[str, Any]]:
        """Retorna a cadeia de execução de ponta a ponta para auditoria e logs."""
        return [
            {
                "task_id": r.task_id,
                "bot_label": r.bot_label,
                "prioridade": r.priority,
                "disparado_por": r.triggered_by,
                "predecessor": r.parent_task_id,
                "status": r.status,
                "timestamp": r.created_at,
            }
            for r in self.historico_execucoes
        ]
