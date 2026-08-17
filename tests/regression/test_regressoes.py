"""Alarmes contra regressao das regras criticas do PDD.

Cada teste nesta camada representa uma salvaguarda contra regressao de
comportamentos criticos de negocio ja corrigidos ou especificados no PDD.
"""

from __future__ import annotations

import pytest

from dashboard.servico_validacao import validar_registro
from src.regras_negocio import normalizar_status


@pytest.mark.regression(reason="RN05: Lote ausente da base de referencia deve ser classificado como Divergencia")
def test_rn05_lote_fora_da_base_referencia_gera_divergencia(
    registro_valido: dict[str, str], lotes_referencia: set[str]
) -> None:
    # Arrange
    dados = {**registro_valido, "lote_id": "LG-2026-99999"}

    # Act
    resultado = validar_registro(dados, lotes_referencia)

    # Assert
    assert resultado.classificacao == "Divergência"
    assert "RN05" in resultado.regras_aplicadas


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


@pytest.mark.regression(
    reason="RN11: Lote duplicado no mesmo dia deve ser classificado como Divergencia"
)
def test_rn11_duplicado_no_dia_continua_divergencia(
    registro_valido: dict[str, str], lotes_referencia: set[str]
) -> None:
    # Arrange & Act
    resultado = validar_registro(
        registro_valido, lotes_referencia, duplicado_no_dia=True
    )

    # Assert
    assert resultado.classificacao == "Divergência"
    assert "RN11" in resultado.regras_aplicadas


@pytest.mark.regression(
    reason="RN12: Data em formato invalido deve ser classificada como Erro de Entrada"
)
def test_rn12_data_formato_invalido_continua_erro_de_entrada(
    registro_valido: dict[str, str], lotes_referencia: set[str]
) -> None:
    # Arrange
    dados = {**registro_valido, "data": "2026-06-15"}

    # Act
    resultado = validar_registro(dados, lotes_referencia)

    # Assert
    assert resultado.classificacao == "Erro de Entrada"
    assert "RN12" in resultado.regras_aplicadas
