"""Módulo de Relatórios, Notificações e Observabilidade (The DX Way)."""

from src.reporting.gmail_client import (
    GMAIL_SEND_SCOPE,
    GmailAuthorizationError,
    GmailOAuthSender,
    autorizar_gmail,
)
from src.reporting.operational_indicators import (
    CATALOGO_REGRAS,
    CLASSIFICACOES_VALIDAS,
    OperationalIndicators,
    RankedRule,
    calcular_indicadores,
)
from src.reporting.relatorio import (
    COLUNAS_RELATORIO as COLUNAS_RELATORIO_LEGADO,
    gerar_relatorio_divergencias,
    gerar_relatorio_erros_fluxo,
)
from src.reporting.relatorio_executivo import (
    COLUNAS_RELATORIO,
    carregar_inspecoes,
    executar_pipeline_dashboard,
    gerar_excel_consolidado,
    gerar_pdf_compativel,
    gerar_relatorio,
    gerar_resumo_executivo_md,
    preparar_dados_relatorio,
    registrar_log_execucao,
    validar_registros_lista,
)
from src.reporting.sistema_alertas import SistemaAlertas

__all__ = [
    "GMAIL_SEND_SCOPE",
    "GmailAuthorizationError",
    "GmailOAuthSender",
    "autorizar_gmail",
    "CATALOGO_REGRAS",
    "CLASSIFICACOES_VALIDAS",
    "OperationalIndicators",
    "RankedRule",
    "calcular_indicadores",
    "COLUNAS_RELATORIO_LEGADO",
    "gerar_relatorio_divergencias",
    "gerar_relatorio_erros_fluxo",
    "COLUNAS_RELATORIO",
    "carregar_inspecoes",
    "executar_pipeline_dashboard",
    "gerar_excel_consolidado",
    "gerar_pdf_compativel",
    "gerar_relatorio",
    "gerar_resumo_executivo_md",
    "preparar_dados_relatorio",
    "registrar_log_execucao",
    "validar_registros_lista",
    "SistemaAlertas",
]
