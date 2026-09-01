from pathlib import Path
import json

import openpyxl
import pandas as pd
import pytest
from openpyxl.chart import DoughnutChart, LineChart

from src.relatorio_executivo import gerar_relatorio, validar_registros
from src.servico_validacao import RegistroValidado, validar_registro


pytestmark = pytest.mark.integration


ENTRADA = Path("data/samples/inspecao_lotes_10dias_sem gabarito.xlsx")


def test_relatorio_dashboard_tem_totais_e_abas_isoladas(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    instante_fixo_manaus,
) -> None:
    monkeypatch.setattr(
        "src.relatorio_executivo._agora_manaus",
        lambda: instante_fixo_manaus,
    )
    destino = gerar_relatorio(ENTRADA, tmp_path)

    with pd.ExcelFile(destino) as arquivo:
        assert arquivo.sheet_names == [
            "Resumo",
            "Todos",
            "Válidos",
            "Divergências",
            "Ambíguos",
            "Erros de Entrada",
            "Ranking de Regras",
            "Dicionário",
            "Decisões de ML",
        ]

        todos = pd.read_excel(arquivo, sheet_name="Todos")
        assert len(todos) == 250
        assert todos.columns.tolist() == [
            "Lote", "Produto", "Linha", "Turno", "Status", "Responsável",
            "Data da inspeção", "Data de referência", "Observação", "Orientação",
            "Classificação",
        ]
        assert todos["Classificação"].value_counts().to_dict() == {
            "Válido": 150,
            "Divergência": 50,
            "Erro de Entrada": 30,
            "Ambíguo": 20,
        }
        assert not todos["Status"].isin(["OK", "NOK"]).any()
        for aba, classificacao in (
            ("Válidos", "Válido"),
            ("Divergências", "Divergência"),
            ("Ambíguos", "Ambíguo"),
            ("Erros de Entrada", "Erro de Entrada"),
        ):
            tabela = pd.read_excel(arquivo, sheet_name=aba)
            assert set(tabela["Classificação"]) <= {classificacao}

    workbook = openpyxl.load_workbook(destino)
    resumo = workbook["Resumo"]
    assert resumo["B3"].value == 250
    assert len(resumo._charts) == 2
    assert isinstance(resumo._charts[0], DoughnutChart)
    assert isinstance(resumo._charts[1], LineChart)
    assert resumo._charts[1].title.tx.rich.p[0].r[0].t == (
        "Evolução dos registros"
    )
    assert [resumo.cell(linha, 1).value for linha in range(20, 30)] == [
        "15/06/2026",
        "16/06/2026",
        "17/06/2026",
        "18/06/2026",
        "19/06/2026",
        "22/06/2026",
        "23/06/2026",
        "24/06/2026",
        "25/06/2026",
        "26/06/2026",
    ]

    eventos = [
        json.loads(linha)
        for linha in (tmp_path / "execucao_dashboard.log").read_text(encoding="utf-8").splitlines()
    ]
    resumo_log = next(
        evento
        for evento in eventos
        if evento.get("event") == "DASHBOARD_EXECUTION_COMPLETED"
    )
    assert "Executado em 30/06/2026 08:15:00 -0400" in resumo_log["message"]
    assert resumo_log["summary"] == {
        "total": 250,
        "Válido": 150,
        "Divergência": 50,
        "Ambíguo": 20,
        "Erro de Entrada": 30,
    }

    resumo_pdf = tmp_path / "resumo_conferencia_lotes.pdf"
    assert resumo_pdf.exists()
    assert resumo_pdf.read_bytes().startswith(b"%PDF")


def test_servico_expoe_data_referencia_e_to_dict() -> None:
    registro = validar_registro(
        {
            "lote_id": "LG-2026-00001",
            "produto": "TV",
            "linha": "L1",
            "turno": "A",
            "status": "OK",
            "responsavel": "Ana",
            "data": "15/06/2026",
            "observacao": "",
            "data_referencia": "15/06/2026",
        },
        {"LG-2026-00001"},
    )

    assert isinstance(registro, RegistroValidado)
    assert registro.data_referencia == "15/06/2026"
    assert registro.to_dict()["status_normalizado"] == "APROVADO"
    assert registro.to_dict()["classificacao"] == "Válido"


def _registro_valido() -> dict[str, str]:
    return {
        "lote_id": "LG-2026-00001",
        "produto": "TV",
        "linha": "L1",
        "turno": "A",
        "status": "APROVADO",
        "responsavel": "Ana",
        "data": "15/06/2026",
        "observacao": "",
        "data_referencia": "15/06/2026",
    }


@pytest.mark.parametrize(
    ("campo", "regra"),
    (("lote_id", "RN01"), ("produto", "RN02"), ("linha", "RN03"), ("status", "RN04")),
)
def test_rn01_a_rn04_classificam_campos_vazios(
    campo: str, regra: str
) -> None:
    dados = _registro_valido()
    dados[campo] = ""

    resultado = validar_registro(dados, {"LG-2026-00001"})

    assert resultado.classificacao == "Erro de Entrada"
    assert regra in resultado.regras_aplicadas


def test_rn05_lote_fora_da_referencia_e_divergencia() -> None:
    resultado = validar_registro(_registro_valido(), set())

    assert resultado.classificacao == "Divergência"
    assert "RN05" in resultado.regras_aplicadas


@pytest.mark.parametrize(
    ("entrada", "normalizado", "regra"),
    (("OK", "APROVADO", "RN06"), ("NOK", "REPROVADO", "RN07")),
)
def test_rn06_rn07_normalizam_sem_gerar_divergencia(
    entrada: str, normalizado: str, regra: str
) -> None:
    dados = _registro_valido()
    dados["status"] = entrada
    dados["observacao"] = "Motivo informado"

    resultado = validar_registro(dados, {"LG-2026-00001"})

    assert resultado.status == normalizado
    assert resultado.classificacao == "Válido"
    assert regra in resultado.regras_aplicadas


@pytest.mark.parametrize("status", ("APROVADO", "REPROVADO", "PENDENTE"))
def test_rn08_aceita_status_canonicos(status: str) -> None:
    dados = _registro_valido()
    dados["status"] = status
    dados["observacao"] = "Motivo informado"

    resultado = validar_registro(dados, {"LG-2026-00001"})

    assert resultado.classificacao == "Válido"


def test_rn09_status_desconhecido_e_ambiguo() -> None:
    dados = _registro_valido()
    dados["status"] = "EM AJUSTE"

    resultado = validar_registro(dados, {"LG-2026-00001"})

    assert resultado.classificacao == "Ambíguo"
    assert "RN09" in resultado.regras_aplicadas


def test_rn10_reprovado_sem_observacao_e_divergencia() -> None:
    dados = _registro_valido()
    dados["status"] = "REPROVADO"

    resultado = validar_registro(dados, {"LG-2026-00001"})

    assert resultado.classificacao == "Divergência"
    assert "RN10" in resultado.regras_aplicadas


@pytest.mark.parametrize("data", ("", "2026-06-15", "31/02/2026", "16/06/2026"))
def test_rn12_rejeita_data_ausente_invalida_ou_fora_do_dia(data: str) -> None:
    dados = _registro_valido()
    dados["data"] = data

    resultado = validar_registro(dados, {"LG-2026-00001"})

    assert resultado.classificacao == "Erro de Entrada"
    assert "RN12" in resultado.regras_aplicadas


def test_rn11_nao_considera_repeticao_entre_dias() -> None:
    colunas = {
        "lote_id": "LG-2026-00001",
        "produto": "TV",
        "linha": "L1",
        "turno": "A",
        "status": "APROVADO",
        "responsavel": "Ana",
        "observacao": "",
    }
    registros = pd.DataFrame(
        [
            {
                **colunas,
                "data": "15/06/2026",
                "data_referencia": "15/06/2026",
                "aba_origem": "Insp_15_06_2026",
                "linha_origem": 4,
            },
            {
                **colunas,
                "data": "16/06/2026",
                "data_referencia": "16/06/2026",
                "aba_origem": "Insp_16_06_2026",
                "linha_origem": 4,
            },
        ]
    )

    resultado = validar_registros(registros, {"LG-2026-00001"})

    assert resultado["classificacao"].tolist() == ["Válido", "Válido"]
    assert not resultado["regras_aplicadas"].str.contains("RN11").any()


def test_rn11_marca_apenas_segunda_ocorrencia_do_mesmo_dia() -> None:
    registro = {
        "lote_id": "LG-2026-00001",
        "produto": "TV",
        "linha": "L1",
        "turno": "A",
        "status": "APROVADO",
        "responsavel": "Ana",
        "data": "15/06/2026",
        "observacao": "",
        "data_referencia": "15/06/2026",
        "aba_origem": "Insp_15_06_2026",
    }
    registros = pd.DataFrame(
        [
            {**registro, "linha_origem": 4},
            {**registro, "linha_origem": 5},
        ]
    )

    resultado = validar_registros(registros, {"LG-2026-00001"})

    assert resultado["classificacao"].tolist() == ["Válido", "Divergência"]
    assert resultado["regras_aplicadas"].tolist() == ["", "RN11"]
