"""Gera o relatório executivo da conferência dos lotes de inspeção.

O arquivo de entrada possui duas linhas de apresentação; por isso os cabeçalhos
estão na linha 3 e os dados começam na linha 4. Cada aba diária declara a
quantidade de registros no texto de apresentação, evitando que o rodapé da
planilha seja interpretado como dado.
"""

from __future__ import annotations

import argparse
import logging
import re
import sys
import unicodedata
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
from openpyxl.chart import DoughnutChart, LineChart, Reference
from openpyxl.chart.label import DataLabelList
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.table import Table, TableStyleInfo

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.base_referencia import carregar_base_referencia
from dashboard.servico_validacao import (
    ABAS_DIARIAS,
    CLASSIFICACOES,
    data_da_aba,
    texto,
    validar_registro,
)
from src.validacao import valida_estrutura


ARQUIVO_ENTRADA_PADRAO = ROOT / "data" / "samples" / "inspecao_lotes_10dias_sem gabarito.xlsx"
DIRETORIO_SAIDA_PADRAO = ROOT / "data" / "output"
COLUNAS_RELATORIO = {
    "lote_id": "Lote",
    "produto": "Produto",
    "linha": "Linha",
    "turno": "Turno",
    "status_normalizado": "Status",
    "responsavel": "Responsável",
    "data": "Data da inspeção",
    "data_referencia": "Data de referência",
    "observacao": "Observação",
    "descricao_validacao": "Orientação",
    "classificacao": "Classificação",
}
FUSO_MANAUS = timezone(timedelta(hours=-4), name="America/Manaus")


def _agora_manaus() -> datetime:
    """Retorna um instante com fuso explícito, inclusive dentro do Docker."""
    return datetime.now(FUSO_MANAUS)


def carregar_inspecoes(caminho: str | Path) -> pd.DataFrame:
    """Lê as dez abas diárias, respeitando a linha 3 como cabeçalho."""
    caminho = Path(caminho)
    frames: list[pd.DataFrame] = []
    with pd.ExcelFile(caminho) as arquivo:
        abas = [aba for aba in arquivo.sheet_names if ABAS_DIARIAS.match(aba)]
        if len(abas) != 10:
            raise ValueError(f"Esperadas 10 abas de inspeção; encontradas {len(abas)}.")
        for aba in abas:
            apresentacao = pd.read_excel(arquivo, sheet_name=aba, header=None, nrows=2)
            texto_apresentacao = " ".join(apresentacao.fillna("").astype(str).to_numpy().ravel())
            encontrado = re.search(r"Registros:\s*(\d+)", texto_apresentacao, flags=re.I)
            if not encontrado:
                raise ValueError(f"Quantidade de registros não encontrada na aba {aba}.")
            quantidade = int(encontrado.group(1))
            diario = pd.read_excel(arquivo, sheet_name=aba, skiprows=2, nrows=quantidade)
            valida_estrutura(diario)
            diario["aba_origem"] = aba
            diario["linha_origem"] = range(4, 4 + len(diario))
            diario["data_referencia"] = data_da_aba(aba)
            frames.append(diario)
    consolidado = pd.concat(frames, ignore_index=True)
    if len(consolidado) != 250:
        raise ValueError(f"Foram lidos {len(consolidado)} registros; o esperado é 250.")
    return consolidado


def validar_registros(df: pd.DataFrame, lotes_referencia: set[str]) -> pd.DataFrame:
    """Deduplica por dia e chama o Serviço de Validação para cada linha."""
    repetidos: set[int] = set()
    for _, diario in df.groupby("aba_origem", sort=False):
        ids = [texto(valor) for valor in diario["lote_id"]]
        contador = Counter(lote_id for lote_id in ids if lote_id)
        vistos: Counter[str] = Counter()
        for indice, lote_id in zip(diario.index, ids):
            vistos[lote_id] += 1
            if lote_id and contador[lote_id] > 1 and vistos[lote_id] > 1:
                repetidos.add(indice)

    registros: list[dict[str, object]] = []
    for indice, linha in df.iterrows():
        registro = validar_registro(
            linha.to_dict(),
            lotes_referencia,
            duplicado_no_dia=indice in repetidos,
        )
        registros.append(registro.to_dict())
    resultado = pd.DataFrame(registros)
    if len(resultado) != len(df) or not resultado["classificacao"].isin(CLASSIFICACOES).all():
        raise RuntimeError("Falha ao classificar os registros do relatório.")
    return resultado


def preparar_dados_relatorio(resultado: pd.DataFrame) -> pd.DataFrame:
    """Expõe no Excel somente campos compreensíveis ao público de negócio."""
    return resultado.loc[:, list(COLUNAS_RELATORIO)].rename(
        columns=COLUNAS_RELATORIO
    )





def gerar_relatorio(
    caminho_entrada: str | Path = ARQUIVO_ENTRADA_PADRAO,
    diretorio_saida: str | Path = DIRETORIO_SAIDA_PADRAO,
) -> Path:
    """Fachada compatível que delega a execução ao orquestrador principal."""
    from dashboard.main import executar_pipeline_dashboard

    resultados = executar_pipeline_dashboard(caminho_entrada, diretorio_saida)
    return resultados["excel"]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Gera o relatório executivo de conferência de lotes."
    )
    parser.add_argument("--entrada", type=Path, default=ARQUIVO_ENTRADA_PADRAO)
    parser.add_argument("--saida", type=Path, default=DIRETORIO_SAIDA_PADRAO)
    args = parser.parse_args()
    print(gerar_relatorio(args.entrada, args.saida))


if __name__ == "__main__":
    main()
