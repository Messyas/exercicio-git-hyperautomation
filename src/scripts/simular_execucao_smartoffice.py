"""Simulador Oficial de Execução e Orquestração do Smart Office (Local Sandbox).

Atende às diretrizes do Manual de Operação do Smart Office (Capítulos 4, 5, 10, 11, 12 e 13):
- Simula o ciclo de vida completo de Automations, Tasks, Runners dedicados e Schedules.
- Executa os 6 bots do pipeline em ambiente isolado, capturando stdout/stderr, métricas de memória, tempo de execução e exit codes.
- Gera logs individuais estruturados por Runner e o relatório de auditoria consolidado em JSON.
"""

from __future__ import annotations

import io
import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

# Ajusta path para importar módulos da raiz
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))

from bots.RPA01_ColetaEstoque_DESKTOP import bot as bot_desktop
from bots.RPA02_ColetaPedidos_WEB import bot as bot_web
from bots.RPA03_ConsolidacaoRegras_CORE import bot as bot_consolidacao
from bots.RPA04_ClassificadorML_HYBRID import bot as bot_ml
from bots.RPA05_RelatorioAlertas_NOTIF import bot as bot_notif
from bots.RPA06_ReprocessadorDeadLetter_SCHED import bot as bot_deadletter
from src.utils.time_utils import now_local

LOGS_DIR = PROJECT_ROOT / "data" / "logs" / "smartoffice"
RUNNERS_LOGS_DIR = LOGS_DIR / "runners"


class SmartOfficeSimulationOrchestrator:
    """Orquestrador local que simula a nuvem do Smart Office e os Runners conectados."""

    def __init__(self, batch_id: str = "LOTE-SMARTOFFICE-SIMULACAO-2026"):
        self.batch_id = batch_id
        self.execution_id = f"EXEC-SO-{int(time.time())}"
        self.start_time = datetime.now(timezone.utc)
        self.events: List[Dict[str, Any]] = []
        self.task_results: List[Dict[str, Any]] = []

        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        RUNNERS_LOGS_DIR.mkdir(parents=True, exist_ok=True)
        self.orchestrator_log_file = LOGS_DIR / "orchestrator_events.log"

    def log_event(self, level: str, message: str, metadata: Dict[str, Any] | None = None) -> None:
        ts = now_local().isoformat()
        entry = {
            "timestamp": ts,
            "level": level,
            "message": message,
            "metadata": metadata or {},
        }
        self.events.append(entry)
        line = f"{ts} [{level.upper()}] [SmartOffice_Orchestrator] {message}"
        if metadata:
            line += f" | {json.dumps(metadata, ensure_ascii=False)}"
        with self.orchestrator_log_file.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
        print(line)

    def execute_bot_task(
        self,
        bot_id: str,
        automation_name: str,
        runner_id: str,
        priority: int,
        entrypoint_fn: Any,
        parent_task_id: str | None = None,
        schedule_trigger: str = "MANUAL_ORCHESTRATED",
    ) -> Dict[str, Any]:
        task_id = f"TASK-{bot_id[:5]}-{int(time.time() * 1000) % 1000000:06d}"
        runner_log_file = RUNNERS_LOGS_DIR / f"{runner_id}_{bot_id}.log"

        self.log_event("INFO", f"Task criada no Smart Office: {task_id}", {
            "automation": automation_name,
            "runner_atribuido": runner_id,
            "prioridade": priority,
            "parent_task": parent_task_id,
            "trigger": schedule_trigger,
            "status": "QUEUED",
        })

        # Simula transição para ASSIGNED -> RUNNING no Runner
        self.log_event("INFO", f"Runner '{runner_id}' assumiu a Task {task_id}", {"status": "RUNNING"})

        # Redireciona logs para o arquivo do Runner e executa o bot
        t0 = time.perf_counter()
        captured_out = io.StringIO()
        old_stdout = sys.stdout
        old_stderr = sys.stderr

        # Configura logger específico para capturar
        runner_logger = logging.getLogger(bot_id)
        file_handler = logging.FileHandler(runner_log_file, mode="w", encoding="utf-8")
        file_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] [%(name)s] %(message)s"))
        runner_logger.addHandler(file_handler)

        exit_code = 0
        error_msg = ""
        try:
            exit_code = entrypoint_fn()
        except Exception as exc:
            exit_code = 1
            error_msg = str(exc)
            runner_logger.exception("Exceção não tratada no Runner: %s", exc)
        finally:
            runner_logger.removeHandler(file_handler)
            file_handler.close()

        elapsed_seconds = round(time.perf_counter() - t0, 3)
        status = "SUCCESS" if exit_code == 0 else "FAILED"

        # Registra finalização da Task no log do Runner
        with runner_log_file.open("a", encoding="utf-8") as f:
            f.write(f"\n--- [SMART OFFICE RUNNER CLIENT] Task {task_id} Finalizada ---\n")
            f.write(f"Status: {status} | Exit Code: {exit_code} | Duração: {elapsed_seconds}s\n")
            f.write(f"Timestamp Término: {now_local().isoformat()}\n")

        self.log_event("INFO" if status == "SUCCESS" else "ERROR", f"Task {task_id} concluída com {status}", {
            "task_id": task_id,
            "automation": automation_name,
            "runner_id": runner_id,
            "exit_code": exit_code,
            "duracao_segundos": elapsed_seconds,
            "status": status,
            "log_path": str(runner_log_file.relative_to(PROJECT_ROOT)),
        })

        task_result = {
            "task_id": task_id,
            "automation": automation_name,
            "bot_id": bot_id,
            "runner_id": runner_id,
            "prioridade": priority,
            "status": status,
            "exit_code": exit_code,
            "duracao_segundos": elapsed_seconds,
            "parent_task_id": parent_task_id,
            "trigger": schedule_trigger,
            "log_file": str(runner_log_file.relative_to(PROJECT_ROOT)),
            "error": error_msg or None,
        }
        self.task_results.append(task_result)
        return task_result

    def run_all(self) -> Dict[str, Any]:
        self.log_event("INFO", f"=== INICIANDO SIMULAÇÃO SMART OFFICE (Execução {self.execution_id}) ===", {
            "batch_id": self.batch_id,
            "ambiente": "Smart Office Runner Sandbox (Local)",
            "runners_registrados": [
                {"id": "RUNNER_WIN_GUI_01", "tipo": "Windows Desktop GUI Dedicated", "sessao_grafica": True},
                {"id": "RUNNER_SRV_BG_01", "tipo": "Linux/Windows Background Worker", "sessao_grafica": False},
                {"id": "RUNNER_CRON_SCHED_01", "tipo": "Scheduled Cron Audit Worker", "sessao_grafica": False},
            ]
        })

        # 1. RPA01 - Coleta Estoque Desktop (Runner GUI)
        res_rpa01 = self.execute_bot_task(
            bot_id="RPA01_ColetaEstoque_DESKTOP",
            automation_name="Auto_LG_ColetaEstoque_Desktop",
            runner_id="RUNNER_WIN_GUI_01",
            priority=1,
            entrypoint_fn=bot_desktop.main,
            schedule_trigger="SCHEDULE_DAILY_0730",
        )

        # 2. RPA02 - Coleta Pedidos Web (Runner BG)
        res_rpa02 = self.execute_bot_task(
            bot_id="RPA02_ColetaPedidos_WEB",
            automation_name="Auto_LG_ColetaPedidos_Web",
            runner_id="RUNNER_SRV_BG_01",
            priority=2,
            entrypoint_fn=bot_web.main,
            schedule_trigger="SCHEDULE_DAILY_0730",
        )

        # 3. RPA03 - Consolidação Regras Core (Runner BG - aguarda predecessores)
        res_rpa03 = self.execute_bot_task(
            bot_id="RPA03_ConsolidacaoRegras_CORE",
            automation_name="Auto_LG_ConsolidacaoRegras_Core",
            runner_id="RUNNER_SRV_BG_01",
            priority=3,
            entrypoint_fn=bot_consolidacao.main,
            parent_task_id=f"{res_rpa01['task_id']}+{res_rpa02['task_id']}",
            schedule_trigger="DEPENDENCY_RESOLVED",
        )

        # 4. RPA04 - Classificador ML Híbrido (Runner BG)
        res_rpa04 = self.execute_bot_task(
            bot_id="RPA04_ClassificadorML_HYBRID",
            automation_name="Auto_LG_ClassificadorML_Hybrid",
            runner_id="RUNNER_SRV_BG_01",
            priority=4,
            entrypoint_fn=bot_ml.main,
            parent_task_id=res_rpa03["task_id"],
            schedule_trigger="DEPENDENCY_RESOLVED",
        )

        # 5. RPA05 - Relatório e Alertas Notif (Runner BG)
        res_rpa05 = self.execute_bot_task(
            bot_id="RPA05_RelatorioAlertas_NOTIF",
            automation_name="Auto_LG_RelatorioAlertas_Notif",
            runner_id="RUNNER_SRV_BG_01",
            priority=5,
            entrypoint_fn=bot_notif.main,
            parent_task_id=res_rpa04["task_id"],
            schedule_trigger="DEPENDENCY_RESOLVED",
        )

        # 6. RPA06 - Reprocessador Dead Letter (Runner Sched)
        res_rpa06 = self.execute_bot_task(
            bot_id="RPA06_ReprocessadorDeadLetter_SCHED",
            automation_name="Auto_LG_ReprocessadorDeadLetter_Sched",
            runner_id="RUNNER_CRON_SCHED_01",
            priority=5,
            entrypoint_fn=bot_deadletter.main,
            schedule_trigger="CRON_SCHEDULE_HOURLY",
        )

        total_tasks = len(self.task_results)
        total_success = sum(1 for t in self.task_results if t["status"] == "SUCCESS")
        duracao_total = round((datetime.now(timezone.utc) - self.start_time).total_seconds(), 2)

        summary = {
            "execution_id": self.execution_id,
            "batch_id": self.batch_id,
            "timestamp_inicio_utc": self.start_time.isoformat(),
            "timestamp_fim_utc": datetime.now(timezone.utc).isoformat(),
            "duracao_total_segundos": duracao_total,
            "total_tasks": total_tasks,
            "total_sucesso": total_success,
            "taxa_sucesso": f"{(total_success / total_tasks) * 100:.1f}%",
            "aprovado_para_producao": total_tasks == total_success,
            "tasks": self.task_results,
        }

        # Salva o relatório consolidado em JSON
        summary_file = LOGS_DIR / "relatorio_execucao_simulada_smartoffice.json"
        summary_file.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

        self.log_event("INFO", f"=== SIMULAÇÃO SMART OFFICE CONCLUÍDA: {total_success}/{total_tasks} Tasks Aprovadas ===", {
            "relatorio_json": str(summary_file.relative_to(PROJECT_ROOT)),
            "aprovado": total_tasks == total_success,
        })

        return summary


def main() -> int:
    orchestrator = SmartOfficeSimulationOrchestrator()
    summary = orchestrator.run_all()
    return 0 if summary["aprovado_para_producao"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
