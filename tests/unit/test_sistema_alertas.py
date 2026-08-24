"""Testes unitários para SistemaAlertas (Estudo de Caso S10-B)."""

from __future__ import annotations

from unittest.mock import MagicMock
import httpx
from src.sistema_alertas import SistemaAlertas


def test_telegram_com_sucesso():
    mock_client = MagicMock(spec=httpx.Client)
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_client.post.return_value = mock_response

    alertas = SistemaAlertas(
        telegram_token="TOKEN123", telegram_chat_id="CHAT123", client=mock_client
    )
    res = alertas.notificar("Teste de alerta Telegram", nivel="INFO", evento="TESTE")
    assert res["sucesso"] is True
    assert res["canal_utilizado"] == "Telegram"


def test_telegram_falha_fallback_para_log_local():
    mock_client = MagicMock(spec=httpx.Client)
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_client.post.return_value = mock_response

    alertas = SistemaAlertas(
        telegram_token="TOKEN123", telegram_chat_id="CHAT123", client=mock_client
    )
    res = alertas.notificar("Teste de falha no Telegram", nivel="ERRO", evento="SABOTAGEM")
    assert res["sucesso"] is True
    assert res["canal_utilizado"] == "LogLocal"
    assert len(res["tentativas_falhas"]) > 0


def test_notificar_pipeline_sem_ml():
    alertas = SistemaAlertas()
    res = alertas.notificar_pipeline_sem_ml(total_itens_fallback=5)
    assert res["evento"] == "PIPELINE_SEM_ML"
    assert res["nivel"] == "AVISO"
    assert "PIPELINE OPERANDO SEM ML" in res["mensagem"]
