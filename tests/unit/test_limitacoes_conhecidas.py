"""Limitacoes mantidas visiveis no relatorio do pytest."""

from __future__ import annotations

import pytest

from dashboard.servico_validacao import data_da_aba


pytestmark = pytest.mark.unit


@pytest.mark.xfail(
    strict=True,
    reason=(
        "Bug conhecido RN12: data_da_aba aceita uma data impossivel; "
        "a validacao de calendario ainda sera adicionada"
    ),
)
def test_rn12_nome_de_aba_rejeita_data_impossivel() -> None:
    with pytest.raises(ValueError, match="data"):
        data_da_aba("Insp_31_02_2026")
