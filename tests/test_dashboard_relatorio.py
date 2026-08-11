from pathlib import Path

import openpyxl
import pandas as pd

from dashboard.gerar_relatorio import gerar_relatorio


ENTRADA = Path("data/samples/inspecao_lotes_10dias_sem gabarito.xlsx")


def test_relatorio_dashboard_tem_totais_e_abas_isoladas(tmp_path: Path) -> None:
    destino = gerar_relatorio(ENTRADA, tmp_path)

    with pd.ExcelFile(destino) as arquivo:
        assert arquivo.sheet_names == ["Resumo", "Todos", "Válidos", "Divergências", "Ambiguos", "Erros de Entrada"]
        todos = pd.read_excel(arquivo, sheet_name="Todos")
        assert len(todos) == 250
        assert todos["classificacao"].value_counts().to_dict() == {
            "Válido": 150,
            "Divergência": 50,
            "Erro de Entrada": 30,
            "Ambíguo": 20,
        }
        for aba, classificacao in (("Válidos", "Válido"), ("Divergências", "Divergência"), ("Ambiguos", "Ambíguo"), ("Erros de Entrada", "Erro de Entrada")):
            tabela = pd.read_excel(arquivo, sheet_name=aba)
            assert set(tabela["classificacao"]) <= {classificacao}

    workbook = openpyxl.load_workbook(destino)
    assert len(workbook["Resumo"]._charts) == 2
    assert (tmp_path / "execucao_dashboard.log").exists()
    assert (tmp_path / "resumo_conferencia_lotes.pdf").exists()
