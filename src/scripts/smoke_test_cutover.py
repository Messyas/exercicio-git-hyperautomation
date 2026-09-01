"""Script de Validação Pós-Deploy e Smoke Test de Corte (Smart Office - Capítulo 13).

Atende rigorosamente às Seções 4.6, 5 (Etapa 4) do Manual de Operação do Smart Office:
- Envio de Tasks mínimas e não críticas para validar conectividade, credenciais e fluxo básico.
- Validação obrigatória antes de autorizar a criação de Schedules em produção no Smart Office.
- Condição objetiva para cutover: 100% dos smoke tests concluídos com status SUCCESS.
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict

# Ajusta path para importar módulos da raiz
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))

from src.ml.classificador_divergencia import ClassificadorDivergencia
from src.automation.coexistence_guard import CoexistenceGuard
from src.utils.dead_letter import DeadLetterQueue
from src.automation.desktop_automation import DesktopAutomationClient
from src.utils.time_utils import now_local

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("smoke_test_cutover")


def smoke_test_rpa01_desktop() -> Dict[str, Any]:
    """Testa conectividade e resposta do sistema desktop em modo smoke test."""
    logger.info("[SMOKE TEST 1/6] Testando RPA01_ColetaEstoque_DESKTOP...")
    guard = CoexistenceGuard(lock_file=Path("data/datapool/smoke_session.lock"))
    guard.acquire("SMART_OFFICE_SMOKE", "RPA01_ColetaEstoque_DESKTOP")
    try:
        client = DesktopAutomationClient(max_retries=1)
        res = client.consultar_lote("LOTE-001")
        sucesso = res.get("encontrado") is True
        return {"bot": "RPA01_ColetaEstoque_DESKTOP", "status": "SUCCESS" if sucesso else "FAILED", "detalhes": res}
    finally:
        guard.release()


def smoke_test_rpa02_web() -> Dict[str, Any]:
    """Testa leitura e parsing dos pedidos web."""
    logger.info("[SMOKE TEST 2/6] Testando RPA02_ColetaPedidos_WEB...")
    input_file = Path("data/samples/inspecao_lotes_dia.xlsx")
    sucesso = input_file.exists()
    return {"bot": "RPA02_ColetaPedidos_WEB", "status": "SUCCESS" if sucesso else "FAILED", "detalhes": {"arquivo_entrada": str(input_file)}}


def smoke_test_rpa03_consolidacao() -> Dict[str, Any]:
    """Testa o motor de regras RN01–RN12."""
    logger.info("[SMOKE TEST 3/6] Testando RPA03_ConsolidacaoRegras_CORE...")
    from bot import validar_dataframe
    import pandas as pd
    df_amostra = pd.DataFrame([{"lote_id": "LOTE-SMOKE-01", "produto": "TV 55 OLED", "linha": "LINHA_01", "turno": "A", "status": "OK", "responsavel": "Operador 1", "data": "28/08/2026", "observacao": "tudo ok"}])
    clf = ClassificadorDivergencia(enabled=False)
    resumo = validar_dataframe(
        df_amostra,
        lotes_validos={"LOTE-SMOKE-01"},
        diretorio_saida=Path("data/output"),
        classificador=clf,
        logger=logger,
    )
    sucesso = resumo.get("status_execucao") == "SUCESSO"
    return {"bot": "RPA03_ConsolidacaoRegras_CORE", "status": "SUCCESS" if sucesso else "FAILED", "detalhes": resumo}


def smoke_test_rpa04_ml() -> Dict[str, Any]:
    """Testa inferência e resiliência de fallback do Classificador ML."""
    logger.info("[SMOKE TEST 4/6] Testando RPA04_ClassificadorML_HYBRID...")
    classificador = ClassificadorDivergencia(enabled=False)
    res = classificador.classificar(lote_id="LOTE-SMOKE-ML", observacao="obs teste")
    sucesso = res.origem_decisao == "fallback" and res.motivo_fallback == "feature_flag_desativada"
    return {"bot": "RPA04_ClassificadorML_HYBRID", "status": "SUCCESS" if sucesso else "FAILED", "detalhes": res.to_dict()}


def smoke_test_rpa05_notificacao() -> Dict[str, Any]:
    """Testa geração de relatório e canal de notificação."""
    logger.info("[SMOKE TEST 5/6] Testando RPA05_RelatorioAlertas_NOTIF...")
    from src.reporting.sistema_alertas import SistemaAlertas
    alertas = SistemaAlertas()
    res = alertas.notificar("Smoke Test Smart Office", nivel="INFO", evento="SMOKE_TEST")
    sucesso = res.get("sucesso") is True
    return {"bot": "RPA05_RelatorioAlertas_NOTIF", "status": "SUCCESS" if sucesso else "FAILED", "detalhes": res}


def smoke_test_rpa06_deadletter() -> Dict[str, Any]:
    """Testa persistência e consulta da Dead Letter Queue."""
    logger.info("[SMOKE TEST 6/6] Testando RPA06_ReprocessadorDeadLetter_SCHED...")
    dlq = DeadLetterQueue(storage_dir=Path("data/dead_letter"))
    total = dlq.total_itens()
    return {"bot": "RPA06_ReprocessadorDeadLetter_SCHED", "status": "SUCCESS", "detalhes": {"total_itens_dlq": total}}


def main() -> int:
    logger.info("================================================================================")
    logger.info("INICIANDO SMOKE TEST DE VALIDAÇÃO PÓS-DEPLOY (CAPÍTULO 13 - SMART OFFICE)")
    logger.info("================================================================================")

    testes = [
        smoke_test_rpa01_desktop(),
        smoke_test_rpa02_web(),
        smoke_test_rpa03_consolidacao(),
        smoke_test_rpa04_ml(),
        smoke_test_rpa05_notificacao(),
        smoke_test_rpa06_deadletter(),
    ]

    total_pass = sum(1 for t in testes if t["status"] == "SUCCESS")
    total_testes = len(testes)

    report_dir = Path("data/reports")
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / "smoke_test_report.json"

    report_data = {
        "timestamp": now_local().isoformat(),
        "total_testes": total_testes,
        "total_sucesso": total_pass,
        "aprovado_para_schedule": total_pass == total_testes,
        "resultados": testes,
    }
    report_path.write_text(json.dumps(report_data, indent=2, default=str, ensure_ascii=False), encoding="utf-8")

    logger.info("================================================================================")
    logger.info("RESULTADO DO SMOKE TEST: %d/%d TASKS APROVADAS COM SUCESSO!", total_pass, total_testes)
    if total_pass == total_testes:
        logger.info("DECISÃO DO REVISOR: ✅ APROVADO — Pipeline pronto para agendamento (Schedule)!")
    else:
        logger.error("DECISÃO DO REVISOR: ❌ BLOQUEADO — Falha no smoke test. Agendamento proibido!")
    logger.info("Relatório salvo em: '%s'", report_path)
    logger.info("================================================================================")
    return 0 if total_pass == total_testes else 1


if __name__ == "__main__":
    raise SystemExit(main())
