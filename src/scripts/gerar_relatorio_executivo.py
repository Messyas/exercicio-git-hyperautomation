"""Script CLI para gerar o Relatório Executivo Consolidado e Indicadores Operacionais."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))

from src.reporting.relatorio_executivo import (
    ARQUIVO_ENTRADA_PADRAO,
    DIRETORIO_SAIDA_PADRAO,
    executar_pipeline_dashboard,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Gera o relatório executivo e indicadores de inspeção.")
    parser.add_argument("--entrada", type=Path, default=ARQUIVO_ENTRADA_PADRAO, help="Planilha Excel de entrada.")
    parser.add_argument("--saida", type=Path, default=DIRETORIO_SAIDA_PADRAO, help="Diretório de saída para os artefatos.")
    args = parser.parse_args()

    resultados = executar_pipeline_dashboard(args.entrada, args.saida)
    print(f"[OK] Excel 9 abas: {resultados['excel']}")
    print(f"[OK] Resumo Executivo Markdown: {resultados['markdown']}")
    print(f"[OK] PDF compatível: {resultados['pdf']}")
    print(f"[OK] Log de auditoria: {resultados['log']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
