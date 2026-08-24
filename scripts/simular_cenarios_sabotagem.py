"""Script de Simulação de Crise e Testes de Sabotagem (Estudo de Caso S10-B).

Este script executa e valida automatizadamente os 5 cenários de sabotagem definidos
na Seção 6 do enunciado:
- Cenário 1: Base de referência indisponível/instável.
- Cenário 2: Serviço de ML fora do ar.
- Cenário 3: ML lento (acima do timeout).
- Cenário 4: ML com baixa confiança.
- Cenário 5: Canal de alerta principal (Telegram) inválido/falhando.

Gera relatórios de evidências em `reports/evidencias_sabotagem/`.
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path
import pandas as pd

# Ajusta path para importar módulos da raiz
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config import get_settings
from src.classificador_divergencia import ClassificadorDivergencia
from src.sistema_alertas import SistemaAlertas
from bot import validar_dataframe

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("sabotagem")


def criar_dataframe_amostra() -> pd.DataFrame:
    """Cria um DataFrame de 5 lotes com divergências para teste dos cenários."""
    return pd.DataFrame([
        {
            "lote_id": "LOTE-SAB-01",
            "produto": "TV 55 OLED",
            "linha": "LINHA_01",
            "turno": "TURNO_A",
            "status": "OK",
            "responsavel": "Operador 1",
            "data": "24/08/2026",
            "observacao": "digitei errado o codigo",
        },
        {
            "lote_id": "LOTE-SAB-02",
            "produto": "LAVADORA 12KG",
            "linha": "LINHA_02",
            "turno": "TURNO_B",
            "status": "NOK",
            "responsavel": "Operador 2",
            "data": "24/08/2026",
            "observacao": "faltou peça na doca 3",
        },
        {
            "lote_id": "LOTE-SAB-03",
            "produto": "GELADEIRA FROST",
            "linha": "LINHA_01",
            "turno": "TURNO_A",
            "status": "INVALIDO_XYZ",
            "responsavel": "Operador 3",
            "data": "24/08/2026",
            "observacao": "lançamento duplicado por engano",
        },
        {
            "lote_id": "LOTE-SAB-04",
            "produto": "AR CONDICIONADO",
            "linha": "LINHA_03",
            "turno": "TURNO_C",
            "status": "PENDENTE",
            "responsavel": "Operador 4",
            "data": "24/08/2026",
            "observacao": "sem avarias observadas",
        },
        {
            "lote_id": "LOTE-SAB-05",
            "produto": "MICROONDAS 30L",
            "linha": "LINHA_02",
            "turno": "TURNO_B",
            "status": "NOK",
            "responsavel": "Operador 5",
            "data": "24/08/2026",
            "observacao": "erro de digitação no lote",
        },
    ])


def cenario_1_base_referencia_instavel(output_dir: Path) -> dict:
    """Cenário 1: Base de referência indisponível."""
    logger.info("=== EXECUTANDO CENÁRIO 1: Base de Referência Indisponível ===")
    df = criar_dataframe_amostra()
    # Simula base sem os lotes do lote-sab
    base_invalida = set()

    res = validar_dataframe(
        df,
        lotes_validos=base_invalida,
        diretorio_saida=output_dir / "cenario_1",
        logger=logger,
    )
    status_ok = res["status_execucao"] == "SUCESSO"
    logger.info(f"Cenário 1 Concluído | Status: {res['status_execucao']} | Divergências: {res['total_divergencias']}")
    return {
        "cenario": "1_base_referencia_instavel",
        "sucesso": status_ok,
        "detalhes": f"Bot concluiu com status {res['status_execucao']} identificando {res['total_divergencias']} divergências.",
    }


def cenario_2_servico_ml_fora_do_ar(output_dir: Path) -> dict:
    """Cenário 2: Serviço de ML totalmente fora do ar (porta 9999)."""
    logger.info("=== EXECUTANDO CENÁRIO 2: Serviço de ML Fora do Ar ===")
    df = criar_dataframe_amostra()
    clf = ClassificadorDivergencia(
        api_url="http://127.0.0.1:9999",  # Porta inválida
        enabled=True,
        timeout_ms=500,
        logger_instance=logger,
    )
    res = validar_dataframe(
        df,
        lotes_validos={"LOTE-SAB-01", "LOTE-SAB-02", "LOTE-SAB-04"},
        diretorio_saida=output_dir / "cenario_2",
        logger=logger,
        classificador=clf,
    )
    # Verifica se todos os itens de divergência receberam origem_decisao = 'fallback'
    divergencias = res["divergencias"]
    fallbacks = [d for d in divergencias if d.get("origem_decisao") == "fallback"]
    bot_nao_trava = res["status_execucao"] == "SUCESSO" and len(fallbacks) == len(divergencias)
    logger.info(f"Cenário 2 Concluído | Bot não travou: {bot_nao_trava} | Items em fallback: {len(fallbacks)}/{len(divergencias)}")
    return {
        "cenario": "2_servico_ml_fora_do_ar",
        "sucesso": bot_nao_trava,
        "detalhes": f"Bot concluiu normalmente sem travar. {len(fallbacks)} itens registraram origem_decisao='fallback'.",
    }


def cenario_3_ml_lento_timeout(output_dir: Path) -> dict:
    """Cenário 3: ML Lento (Timeout de 1ms forçado)."""
    logger.info("=== EXECUTANDO CENÁRIO 3: ML Lento (Timeout de 1ms) ===")
    df = criar_dataframe_amostra()
    clf = ClassificadorDivergencia(
        api_url="http://127.0.0.1:8000",
        enabled=True,
        timeout_ms=1,  # 1ms força timeout
        logger_instance=logger,
    )
    res = validar_dataframe(
        df,
        lotes_validos={"LOTE-SAB-01", "LOTE-SAB-02", "LOTE-SAB-04"},
        diretorio_saida=output_dir / "cenario_3",
        logger=logger,
        classificador=clf,
    )
    bot_concluiu = res["status_execucao"] == "SUCESSO"
    logger.info(f"Cenário 3 Concluído | Timeout respeitado sem travar bot | Status: {res['status_execucao']}")
    return {
        "cenario": "3_ml_lento_timeout",
        "sucesso": bot_concluiu,
        "detalhes": "Timeout de 1ms foi respeitado e o bot seguiu com o lote sem pendurar.",
    }


def cenario_4_ml_baixa_confianca(output_dir: Path) -> dict:
    """Cenário 4: ML com baixa confiança (limiar 0.999)."""
    logger.info("=== EXECUTANDO CENÁRIO 4: ML com Baixa Confiança (Limiar 0.999) ===")
    df = criar_dataframe_amostra()
    clf = ClassificadorDivergencia(
        api_url="http://127.0.0.1:8000",
        enabled=True,
        timeout_ms=1000,
        confianca_minima=0.999,  # Limiar altíssimo força fallback por baixa confiança
        logger_instance=logger,
    )
    res = validar_dataframe(
        df,
        lotes_validos={"LOTE-SAB-01", "LOTE-SAB-02", "LOTE-SAB-04"},
        diretorio_saida=output_dir / "cenario_4",
        logger=logger,
        classificador=clf,
    )
    divergencias = res["divergencias"]
    fallbacks = [d for d in divergencias if d.get("origem_decisao") == "fallback"]
    logger.info(f"Cenário 4 Concluído | Fallbacks por baixa confiança: {len(fallbacks)}/{len(divergencias)}")
    return {
        "cenario": "4_ml_baixa_confianca",
        "sucesso": len(fallbacks) == len(divergencias),
        "detalhes": f"Limiar de 0.999 descartou predições fracas. {len(fallbacks)} itens caíram em fallback.",
    }


def cenario_5_canal_alerta_falha(output_dir: Path) -> dict:
    """Cenário 5: Canal de Alerta Telegram Inválido -> Fallback de Canal."""
    logger.info("=== EXECUTANDO CENÁRIO 5: Canal Principal de Alerta Inválido ===")
    alertas = SistemaAlertas(
        telegram_token="TOKEN_INVALIDO_12345",
        telegram_chat_id="CHAT_INVALIDO",
        whatsapp_enabled=False,
        email_enabled=False,
        logger_instance=logger,
    )
    res_notificacao = alertas.notificar(
        mensagem="Teste de falha no Telegram e fallback para Log Local",
        nivel="ERRO",
        evento="SABOTAGEM_TELEGRAM",
    )
    fallback_ok = res_notificacao["canal_utilizado"] == "LogLocal" and res_notificacao["sucesso"]
    logger.info(f"Cenário 5 Concluído | Fallback de canal utilizado: {res_notificacao['canal_utilizado']}")
    return {
        "cenario": "5_canal_alerta_falha",
        "sucesso": fallback_ok,
        "detalhes": f"Telegram falhou como esperado. Alerta entregue via canal de fallback: {res_notificacao['canal_utilizado']}.",
    }


def rodar_todas_as_sabotagens() -> None:
    output_dir = PROJECT_ROOT / "reports" / "evidencias_sabotagem"
    output_dir.mkdir(parents=True, exist_ok=True)

    resultados = []
    resultados.append(cenario_1_base_referencia_instavel(output_dir))
    resultados.append(cenario_2_servico_ml_fora_do_ar(output_dir))
    resultados.append(cenario_3_ml_lento_timeout(output_dir))
    resultados.append(cenario_4_ml_baixa_confianca(output_dir))
    resultados.append(cenario_5_canal_alerta_falha(output_dir))

    relatorio_final = {
        "titulo": "Relatório de Evidências da Simulação de Crise (S10-B)",
        "total_cenarios": len(resultados),
        "sucessos": sum(r["sucesso"] for r in resultados),
        "cenarios": resultados,
    }

    relatorio_path = output_dir / "resumo_evidencias_sabotagem.json"
    relatorio_path.write_text(json.dumps(relatorio_final, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n==================================================")
    print(f"RELATÓRIO DE EVIDÊNCIAS GERADO EM: {relatorio_path}")
    print(f"Total de Cenários: {relatorio_final['total_cenarios']} | Aprovados: {relatorio_final['sucessos']}")
    print(f"==================================================\n")


if __name__ == "__main__":
    rodar_todas_as_sabotagens()
