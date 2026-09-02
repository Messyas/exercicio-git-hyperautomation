"""Testes unitários para ClassificadorDivergencia (Estudo de Caso S10-B)."""

from __future__ import annotations

from unittest.mock import MagicMock
import httpx
import pytest
from src.classificador_divergencia import ClassificadorDivergencia


def test_feature_flag_desativada():
    """Quando ML_ENABLED=False, retorna fallback sem realizar chamada HTTP."""
    clf = ClassificadorDivergencia(enabled=False)
    res = clf.classificar(lote_id="LOTE-001", observacao="digitei errado")
    assert res.origem_decisao == "fallback"
    assert res.motivo_fallback == "feature_flag_desativada"
    assert res.confianca_ml == 0.0
    assert res.causa_provavel_ml == "nao_classificado"


def test_falha_de_rede_retorna_fallback_seguro():
    """Serviço fora do ar retorna fallback de indisponibilidade sem lançar exceção."""
    clf = ClassificadorDivergencia(api_url="http://127.0.0.1:9999", enabled=True, timeout_ms=200)
    res = clf.classificar(lote_id="LOTE-002", observacao="erro de digitacao")
    assert res.origem_decisao == "fallback"
    assert res.motivo_fallback in ("indisponibilidade", "timeout")
    assert res.causa_provavel_ml == "nao_classificado"


def test_limiar_confianca_minima_descarta_predicao_fraca():
    """Predição abaixo de ML_CONFIANCA_MINIMA é descartada como fallback por baixa confiança."""
    mock_client = MagicMock(spec=httpx.Client)
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "lote_id": "LOTE-003",
        "probabilidade": 0.50,
        "classe": "duplicidade_digitacao",
    }
    mock_client.post.return_value = mock_response

    clf = ClassificadorDivergencia(
        api_url="http://127.0.0.1:8000",
        enabled=True,
        confianca_minima=0.70,
        client=mock_client,
    )
    res = clf.classificar(lote_id="LOTE-003", observacao="lote duplicado")
    assert res.origem_decisao == "fallback"
    assert res.motivo_fallback == "baixa_confianca"
    assert res.confianca_ml == 0.50


def test_predicao_valida_com_alta_confianca():
    """Predição acima da confiança mínima retorna origem_decisao='ml'."""
    mock_client = MagicMock(spec=httpx.Client)
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "lote_id": "LOTE-004",
        "probabilidade": 0.92,
        "causa_provavel": "erro_digitacao_codigo",
    }
    mock_client.post.return_value = mock_response

    clf = ClassificadorDivergencia(
        api_url="http://127.0.0.1:8000",
        enabled=True,
        confianca_minima=0.70,
        client=mock_client,
    )
    res = clf.classificar(lote_id="LOTE-004", observacao="codigo incorreto")
    assert res.origem_decisao == "ml"
    assert res.motivo_fallback is None
    assert res.confianca_ml == 0.92
    assert res.causa_provavel_ml == "erro_digitacao_codigo"
