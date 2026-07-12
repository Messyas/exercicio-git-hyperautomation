"""Testes unitários das regras RN04 e RN05 para a coluna status."""

import pandas as pd
import pytest

from src.regras_negocio import normalizar_status, validar_dominio_status


def test_normaliza_ok_e_nok_e_registra_divergencia() -> None:
    """RN05 deve converter os dois valores conhecidos e deixar rastreabilidade."""
    entrada = pd.DataFrame({"lote_id": ["L1", "L2"], "status": ["OK", "NOK"]})

    resultado = normalizar_status(entrada)

    assert resultado["status"].tolist() == ["APROVADO", "REPROVADO"]
    assert resultado["status_original"].tolist() == ["OK", "NOK"]
    assert resultado["divergencia_rn05"].notna().all()
    assert entrada["status"].tolist() == ["OK", "NOK"]


def test_status_normalizado_e_valido_no_dominio() -> None:
    """RN04 não deve acusar divergência depois da normalização."""
    entrada = pd.DataFrame({"status": ["OK", "NOK", "PENDENTE"]})

    resultado = validar_dominio_status(normalizar_status(entrada))

    assert resultado.empty


def test_captura_status_ambiguo_para_revisao_humana() -> None:
    """RN04/RN06 deve separar ``APROVADO PARCIAL`` sem decidir por ele."""
    entrada = pd.DataFrame({"lote_id": ["L1"], "status": ["APROVADO PARCIAL"]})

    resultado = validar_dominio_status(normalizar_status(entrada))

    assert len(resultado) == 1
    assert resultado.loc[0, "status"] == "APROVADO PARCIAL"
    assert bool(resultado.loc[0, "status_ambiguo"])
    assert resultado.loc[0, "fila_destino"] == "revisao_humana"
    assert "RN04" in resultado.loc[0, "divergencia_rn04"]


def test_funcoes_rejeitam_dataframe_sem_status() -> None:
    """A coluna status é pré-requisito das RN04 e RN05."""
    entrada = pd.DataFrame({"lote_id": ["L1"]})

    with pytest.raises(ValueError, match="RN05"):
        normalizar_status(entrada)
    with pytest.raises(ValueError, match="RN04"):
        validar_dominio_status(entrada)
