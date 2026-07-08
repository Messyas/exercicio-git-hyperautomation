import pytest
from src.validacao import validar_observacao_reprovado

def teste_reprovado_sem_observacao():
    registro = {
        "lote_id": "LG-2026-00102",
        "status": "REPROVADO",
        "observacao": ""
    }

    resultado = validar_observacao_reprovado(registro)

    # Verifica se a chave 'divergencias' existe e se tem pelo menos 1 erro dentro dela
    assert "divergencias" in resultado
    assert len(resultado["divergencias"]) > 0
    # Verifica se o erro registrado foi a RN07
    assert resultado["divergencias"][0]["regra_violada"] == "RN07"


def teste_aprovado_sem_observacao():
    registro = {
        "lote_id": "LG-2026-00103",
        "status": "APROVADO",
        "observacao": ""
    }

    resultado = validar_observacao_reprovado(registro)

    # Se a chave existir, ela deve estar vazia (nenhum erro adicionado)
    if "divergencias" in resultado:
        assert len(resultado["divergencias"]) == 0