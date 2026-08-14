"""Alarmes contra regressao das regras criticas do PDD."""

from __future__ import annotations

import pytest

from dashboard.servico_validacao import validar_registro
from src.regras_negocio import normalizar_status


pytestmark = pytest.mark.unit


@pytest.mark.regression(reason="RN07: NOK deve continuar normalizado para REPROVADO")
def test_rn07_nok_continua_normalizado_para_reprovado() -> None:
    # Arrange
    registro = {"status": "NOK"}

    # Act
    resultado = normalizar_status(registro)

    # Assert
    assert resultado["status"] == "REPROVADO"
    assert resultado["status_original"] == "NOK"


@pytest.mark.regression(
    reason="RN10: REPROVADO sem observacao deve continuar como divergencia"
)
def test_rn10_reprovado_sem_observacao_continua_divergencia(
    registro_valido: dict[str, str], lotes_referencia: set[str]
) -> None:
    # Arrange
    dados = {**registro_valido, "status": "REPROVADO", "observacao": ""}

    # Act
    resultado = validar_registro(dados, lotes_referencia)

    # Assert
    assert resultado.classificacao == "Divergência"
    assert "RN10" in resultado.regras_aplicadas
