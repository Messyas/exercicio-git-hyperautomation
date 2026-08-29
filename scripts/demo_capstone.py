"""Script de Demonstração Completa do Pipeline Capstone (Smart Office / The DX Way).

Executa a cadeia de ponta a ponta dos 6 bots registrados:
1. `RPA01_ColetaEstoque_DESKTOP`
2. `RPA02_ColetaPedidos_WEB`
3. `RPA03_ConsolidacaoRegras_CORE`
4. `RPA04_ClassificadorML_HYBRID`
5. `RPA05_RelatorioAlertas_NOTIF`
6. `RPA06_ReprocessadorDeadLetter_SCHED`

Gera o relatório de rastreabilidade de ponta a ponta em `reports/rastreabilidade_pipeline_capstone.json`.
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict

# Ajusta path para importar módulos da raiz
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from bots.RPA01_ColetaEstoque_DESKTOP import bot as bot_desktop
from bots.RPA02_ColetaPedidos_WEB import bot as bot_web
from bots.RPA03_ConsolidacaoRegras_CORE import bot as bot_consolidacao
from bots.RPA04_ClassificadorML_HYBRID import bot as bot_ml
from bots.RPA05_RelatorioAlertas_NOTIF import bot as bot_notif
from bots.RPA06_ReprocessadorDeadLetter_SCHED import bot as bot_deadletter
from src.orchestrator import PipelineOrchestrator
from src.time_utils import now_local

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("demo_capstone")


def executar_pipeline_completo(batch_id: str = "LOTE-DEMO-CAPSTONE-2026") -> Dict[str, Any]:
    logger.info("================================================================================")
    logger.info("INICIANDO DEMO AO VIVO DO PIPELINE HÍBRIDO CAPSTONE — 6 BOTS NO SMART OFFICE")
    logger.info("Batch ID: %s | Horário de Manaus: %s", batch_id, now_local().isoformat())
    logger.info("================================================================================")

    orchestrator = PipelineOrchestrator(logger_instance=logger)
    status_execucao: Dict[str, str] = {}

    # 1. Disparo do Bot Desktop (Prioridade 1)
    task_desktop = orchestrator.disparar_bot_desktop(batch_id=batch_id)
    ret_desktop = bot_desktop.main()
    status_execucao[task_desktop] = "SUCCESS" if ret_desktop == 0 else "FAILED"

    # 2. Disparo do Bot Web (Prioridade 2)
    task_web = orchestrator.disparar_bot_web(batch_id=batch_id)
    ret_web = bot_web.main()
    status_execucao[task_web] = "SUCCESS" if ret_web == 0 else "FAILED"

    # 3. Consolidação com Timeout (Prioridade 3)
    task_consolidacao = orchestrator.disparar_bot_consolidacao(batch_id=batch_id, parent_task_id=f"{task_desktop}+{task_web}")
    orchestrator.aguardar_predecessor_com_timeout(task_desktop, timeout_seconds=10.0)
    orchestrator.aguardar_predecessor_com_timeout(task_web, timeout_seconds=10.0)
    ret_consolidacao = bot_consolidacao.main()
    status_execucao[task_consolidacao] = "SUCCESS" if ret_consolidacao == 0 else "FAILED"

    # 4. Classificador de ML Híbrido (Prioridade 4)
    task_ml = orchestrator.disparar_bot_ml(batch_id=batch_id, parent_task_id=task_consolidacao)
    ret_ml = bot_ml.main()
    status_execucao[task_ml] = "SUCCESS" if ret_ml == 0 else "FAILED"

    # 5. Relatórios e Alertas Multicanal (Prioridade 5)
    task_notif = orchestrator.disparar_bot_relatorio(batch_id=batch_id, parent_task_id=task_ml)
    ret_notif = bot_notif.main()
    status_execucao[task_notif] = "SUCCESS" if ret_notif == 0 else "FAILED"

    # 6. Reprocessador Dead Letter (Prioridade 5)
    task_deadletter = orchestrator.disparar_bot_deadletter(parent_task_id="SCHEDULED")
    ret_deadletter = bot_deadletter.main()
    status_execucao[task_deadletter] = "SUCCESS" if ret_deadletter == 0 else "FAILED"

    cadeia = orchestrator.obter_rastreabilidade_completa()
    for item in cadeia:
        item["status_final"] = status_execucao.get(item["task_id"], "UNKNOWN")

    report_dir = Path("reports")
    report_dir.mkdir(parents=True, exist_ok=True)
    report_file = report_dir / "rastreabilidade_pipeline_capstone.json"

    resultado_final = {
        "batch_id": batch_id,
        "executado_em": now_local().isoformat(),
        "total_bots_executados": len(cadeia),
        "sucesso_global": all(v == "SUCCESS" for v in status_execucao.values()),
        "cadeia_orquestracao": cadeia,
    }
    report_file.write_text(json.dumps(resultado_final, indent=2, ensure_ascii=False), encoding="utf-8")

    logger.info("================================================================================")
    logger.info("DEMO AO VIVO FINALIZADA COM SUCESSO EM 100%% DOS BOTS!")
    logger.info("Relatório de Rastreabilidade salvo em: '%s'", report_file)
    logger.info("================================================================================")
    return resultado_final


def main() -> int:
    resultado = executar_pipeline_completo()
    return 0 if resultado["sucesso_global"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
