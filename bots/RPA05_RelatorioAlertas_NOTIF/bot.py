"""Bot RPA05_RelatorioAlertas_NOTIF (Smart Office / The DX Way).

Responsabilidade:
- Geração do relatório consolidado (.xlsx de 9 abas) com a 9ª aba 'Decisões de ML' (Prioridade 5).
- Exposição das colunas obrigatórias `origem_decisao` e `confianca_ml`.
- Disparo de notificações multicanal resilientes: Telegram como canal principal, com fallback automático
  para Email/WhatsApp e registro em log de alta visibilidade.
- Alerta obrigatório quando operando em modo degradado de ML.
"""

from __future__ import annotations

import json
import logging
import os
import sys
from pathlib import Path

# Ajusta path para importar módulos da raiz
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
from config import get_settings
from src.relatorio import gerar_relatorio_divergencias
from src.sistema_alertas import SistemaAlertas

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("RPA05_RelatorioAlertas_NOTIF")


def main() -> int:
    logger.info("=== INICIANDO RPA05_RelatorioAlertas_NOTIF (Prioridade 5) ===")
    settings = get_settings()

    input_file = Path("data/datapool/lotes_enriquecidos_ml.json")
    if not input_file.exists():
        logger.error("[RPA05_NOTIF] Arquivo de lotes enriquecidos não encontrado: %s", input_file)
        return 1

    try:
        registros = json.loads(input_file.read_text(encoding="utf-8"))
        df_lotes = pd.DataFrame(registros)

        # 1. Gera o relatório consolidado de divergências em Excel
        output_dir = Path("data/output")
        output_dir.mkdir(parents=True, exist_ok=True)

        # Extrai divergências para o relatório oficial
        erros_list = []
        for reg in registros:
            if reg.get("status") != "APROVADO" or reg.get("origem_decisao") == "fallback":
                erros_list.append({
                    "lote_id": reg.get("lote_id"),
                    "regra_violada": reg.get("regra_violada", "RN05"),
                    "descricao_do_erro": reg.get("divergencia_rn05") or "Divergência de conferência de estoque",
                    "acao_recomendada": "Revisão manual na doca / conferência física",
                    "severidade": "AVISO" if reg.get("origem_decisao") == "ml" else "ERRO",
                    "origem_decisao": reg.get("origem_decisao", "fallback"),
                    "confianca_ml": reg.get("confianca_ml", 0.0),
                    "causa_provavel_ml": reg.get("causa_provavel_ml", "N/A"),
                    "motivo_fallback": reg.get("motivo_fallback", "Nenhum"),
                })

        relatorio_path = gerar_relatorio_divergencias(
            erros=erros_list,
            diretorio_saida=output_dir,
            lotes_validados=df_lotes,
        )
        logger.info("[RPA05_NOTIF] Relatório oficial gerado com SUCESSO: '%s'", relatorio_path)

        # 2. Inicializa o Sistema de Alertas Multicanal com Fallback
        alertas = SistemaAlertas(
            telegram_token=settings.telegram_token,
            telegram_chat_id=settings.telegram_chat_id,
            email_enabled=settings.email_enabled,
            email_to=settings.email_to,
            logger_instance=logger,
        )

        total_itens = len(registros)
        total_divergencias = len(erros_list)
        msg_sucesso = (
            f"Pipeline de Conferência Concluído com Sucesso!\n"
            f"• Itens Processados: {total_itens}\n"
            f"• Divergências Identificadas: {total_divergencias}\n"
            f"• Relatório Gerado: {relatorio_path.name}"
        )
        alertas.notificar(msg_sucesso, nivel="INFO", evento="FIM_PIPELINE", anexos=[relatorio_path])

        # Se houver operação 100% em modo degradado de ML, emite alerta de severidade AVISO
        fallbacks = sum(1 for r in registros if r.get("origem_decisao") == "fallback")
        if total_itens > 0 and fallbacks == total_itens:
            alertas.notificar(
                "ATENÇÃO: Pipeline operou 100% em modo degradado (Fallback Determinístico de ML).",
                nivel="AVISO",
                evento="ML_DEGRADADO",
            )

        logger.info("OK: Relatório e notificações multicanal concluídos com sucesso.")
        return 0

    except Exception as exc:
        logger.exception("[RPA05_NOTIF] Erro no bot de relatórios e alertas: %s", exc)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
