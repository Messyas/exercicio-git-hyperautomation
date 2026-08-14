"""Cenarios parametrizados e identificados das RN01-RN12."""

from __future__ import annotations

import pytest

from dashboard.servico_validacao import validar_registro


pytestmark = pytest.mark.unit


@pytest.mark.parametrize(
    ("alteracoes", "duplicado", "classificacao_esperada", "regra_esperada"),
    (
        pytest.param({}, False, "Válido", None, id="registro_valido"),
        pytest.param(
            {"lote_id": "LG-2026-99999"},
            False,
            "Divergência",
            "RN05",
            id="lote_fora_referencia_rn05",
        ),
        pytest.param(
            {"status": "EM AJUSTE"},
            False,
            "Ambíguo",
            "RN09",
            id="status_ambiguo_rn09",
        ),
        pytest.param(
            {"status": "REPROVADO", "observacao": ""},
            False,
            "Divergência",
            "RN10",
            id="reprovado_sem_observacao_rn10",
        ),
        pytest.param(
            {},
            True,
            "Divergência",
            "RN11",
            id="duplicado_no_dia_rn11",
        ),
        pytest.param(
            {"data": "2026-06-15"},
            False,
            "Erro de Entrada",
            "RN12",
            id="data_formato_invalido_rn12",
        ),
    ),
)
def test_validar_registro_em_cenarios_distintos(
    registro_valido: dict[str, str],
    lotes_referencia: set[str],
    alteracoes: dict[str, str],
    duplicado: bool,
    classificacao_esperada: str,
    regra_esperada: str | None,
) -> None:
    # Arrange
    dados = {**registro_valido, **alteracoes}

    # Act
    resultado = validar_registro(
        dados,
        lotes_referencia,
        duplicado_no_dia=duplicado,
    )

    # Assert
    assert resultado.classificacao == classificacao_esperada
    if regra_esperada is None:
        assert resultado.regras_aplicadas == []
    else:
        assert regra_esperada in resultado.regras_aplicadas
