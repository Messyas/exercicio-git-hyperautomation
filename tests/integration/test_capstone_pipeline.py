"""Testes de integração do pipeline Capstone e dos 6 cenários de sabotagem."""

import pytest

from src.scripts.demo_capstone import executar_pipeline_completo
from src.scripts.simular_cenarios_sabotagem import (
    executar_cenario_1_desktop_indisponivel,
    executar_cenario_2_timeout_dependencia,
    executar_cenario_3_ml_fora_do_ar,
    executar_cenario_4_alerta_principal_falha,
    executar_cenario_5_coexistencia_orquestradores,
    executar_cenario_6_item_dado_irrecuperavel,
)


@pytest.mark.integration
def test_pipeline_capstone_demo_completo():
    resultado = executar_pipeline_completo(batch_id="TESTE-INTEGRACAO-CAPSTONE")
    assert resultado["sucesso_global"] is True
    assert resultado["total_bots_executados"] == 6


@pytest.mark.integration
def test_seis_cenarios_sabotagem():
    c1 = executar_cenario_1_desktop_indisponivel()
    assert c1["sucesso"] is True

    c2 = executar_cenario_2_timeout_dependencia()
    assert c2["sucesso"] is True

    c3 = executar_cenario_3_ml_fora_do_ar()
    assert c3["sucesso"] is True

    c4 = executar_cenario_4_alerta_principal_falha()
    assert c4["sucesso"] is True

    c5 = executar_cenario_5_coexistencia_orquestradores()
    assert c5["sucesso"] is True

    c6 = executar_cenario_6_item_dado_irrecuperavel()
    assert c6["sucesso"] is True
