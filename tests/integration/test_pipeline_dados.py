"""Integracao entre leitura, validacao e preparacao do relatorio."""

from __future__ import annotations

import pytest

from src.relatorio_executivo import (
    carregar_inspecoes,
    preparar_dados_relatorio,
    validar_registros,
)


pytestmark = pytest.mark.integration


def test_planilha_sintetica_colabora_com_validacao_e_relatorio(
    planilha_10_dias_factory,
) -> None:
    # Arrange
    caminho, referencias, _ = planilha_10_dias_factory()

    # Act
    inspecoes = carregar_inspecoes(caminho)
    validados = validar_registros(inspecoes, referencias)
    relatorio = preparar_dados_relatorio(validados)

    # Assert
    assert len(inspecoes) == 250
    assert relatorio["Classificação"].value_counts().to_dict() == {
        "Válido": 150,
        "Divergência": 50,
        "Erro de Entrada": 30,
        "Ambíguo": 20,
    }
    assert not relatorio["Status"].isin(["OK", "NOK"]).any()


@pytest.mark.skip(
    reason=(
        "Maestro real exige credenciais e ambiente de homologacao indisponiveis; "
        "o contrato local e coberto por doubles de teste"
    )
)
def test_publicacao_real_no_maestro_em_homologacao() -> None:
    """Documenta a verificacao externa futura sem acessar rede na suite local."""
    raise AssertionError("Este corpo so deve executar no ambiente de homologacao.")
