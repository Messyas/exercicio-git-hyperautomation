"""Testes da exportação do relatório de divergências."""

import re

import pandas as pd

from src.relatorio import (
    gerar_relatorio_divergencias,
    gerar_relatorio_erros_fluxo,
)


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


def test_relatorio_separa_rejeicoes_e_falhas_tecnicas(tmp_path) -> None:
    registro = {
        "item_id": "item-1",
        "source_row": 4,
        "lote_id": "L1",
        "cadastro_status": "REJEITADO_NEGOCIO",
        "cadastro_error": "Campo obrigatório vazio.",
        "evidence_name": "rejeicao.png",
        "evidence_path": "/app/screenshots/rejeicao.png",
    }
    falha = {
        **registro,
        "item_id": "item-2",
        "source_row": 5,
        "lote_id": "L2",
        "cadastro_status": "FALHA_TECNICA",
        "cadastro_error": "Timeout do navegador.",
        "evidence_name": "timeout.png",
        "evidence_path": "/app/screenshots/timeout.png",
    }

    caminho = gerar_relatorio_divergencias(
        [],
        tmp_path,
        rejeicoes_cadastro=[registro],
        falhas_tecnicas=[falha],
        resumo={"total_registros": 2},
    )

    with pd.ExcelFile(caminho) as arquivo:
        assert {
            "resumo",
            "divergencias",
            "lotes_validados",
            "rejeicoes_cadastro",
            "falhas_tecnicas",
            "revisao_humana",
        } == set(arquivo.sheet_names)
    rejeicoes = pd.read_excel(caminho, sheet_name="rejeicoes_cadastro")
    falhas = pd.read_excel(caminho, sheet_name="falhas_tecnicas")
    assert len(rejeicoes) == 1
    assert len(falhas) == 1
    assert rejeicoes.loc[0, "evidence_path"].endswith("rejeicao.png")
    assert falhas.loc[0, "evidence_path"].endswith("timeout.png")


def test_bot1_gera_relatorio_para_item_nao_publicado(tmp_path) -> None:
    erro = {
        "item_id": "item-27",
        "source_row": 27,
        "lote_id": "",
        "produto": "TV55-4K-B",
        "linha": "L1",
        "turno": "A",
        "status": "APROVADO",
        "responsavel": "Operador",
        "data": "14/06/2026",
        "observacao": "",
        "cadastro_status": "REJEITADO_NEGOCIO",
        "cadastro_error": "Informe o número do lote.",
        "cadastro_error_type": "BUSINESS",
        "evidence_name": "rejeicao.png",
        "evidence_path": "/app/screenshots/rejeicao.png",
    }

    caminho = gerar_relatorio_erros_fluxo([erro], tmp_path)

    with pd.ExcelFile(caminho) as arquivo:
        assert set(arquivo.sheet_names) == {"resumo", "erros_fluxo"}
    tabela = pd.read_excel(caminho, sheet_name="erros_fluxo")
    assert len(tabela) == 1
    assert tabela.loc[0, "source_row"] == 27
    assert tabela.loc[0, "cadastro_status"] == "REJEITADO_NEGOCIO"
    assert tabela.loc[0, "cadastro_error"] == "Informe o número do lote."
