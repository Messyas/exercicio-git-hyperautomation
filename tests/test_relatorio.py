"""Testes da exportação do relatório de divergências."""

import re

import pandas as pd

from src.relatorio import gerar_relatorio_divergencias


def test_gera_xlsx_com_colunas_obrigatorias(tmp_path) -> None:
    """A lista de erros deve gerar um arquivo legível pelo Analista."""
    erros = [
        {
            "lote_id": "LG-2026-00109",
            "regra_violada": "RN02",
            "descricao_do_erro": "Campo responsavel vazio.",
            "acao_recomendada": "Preencher o responsável.",
        },
        {
            "lote_id": "LG-2026-00112",
            "divergencias": [
                {
                    "regra_violada": "RN06",
                    "descricao": "Status ambíguo.",
                    "acao_recomendada": "Enviar para revisão humana.",
                }
            ],
        },
    ]

    caminho = gerar_relatorio_divergencias(erros, tmp_path)

    assert caminho.exists()
    assert caminho.suffix == ".xlsx"
    assert re.search(r"relatorio_divergencias_\d{8}(?:_\d+)?\.xlsx$", caminho.name)

    tabela = pd.read_excel(caminho, sheet_name="divergencias")
    assert {"lote_id", "regra_violada", "descricao_do_erro"}.issubset(
        tabela.columns
    )
    assert len(tabela) == 2
    assert tabela["regra_violada"].tolist() == ["RN02", "RN06"]


def test_relatorio_vazio_mantem_modelo_de_colunas(tmp_path) -> None:
    """Mesmo sem falhas, o arquivo deve respeitar o modelo de saída."""
    caminho = gerar_relatorio_divergencias([], tmp_path)

    tabela = pd.read_excel(caminho, sheet_name="divergencias")

    assert tabela.empty
    assert "lote_id" in tabela.columns
    assert "regra_violada" in tabela.columns
    assert "descricao_do_erro" in tabela.columns


def test_nao_sobrescreve_relatorios_do_mesmo_dia(tmp_path) -> None:
    """Uma segunda execução deve gerar outro nome no mesmo diretório."""
    primeiro = gerar_relatorio_divergencias([], tmp_path)
    segundo = gerar_relatorio_divergencias([], tmp_path)

    assert primeiro != segundo
    assert primeiro.exists()
    assert segundo.exists()
