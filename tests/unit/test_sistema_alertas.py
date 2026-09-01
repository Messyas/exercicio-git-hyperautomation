"""Testes unitários para SistemaAlertas (Estudo de Caso S10-B)."""

from __future__ import annotations

from dataclasses import replace
from unittest.mock import MagicMock

import httpx
import pandas as pd

import src.runners.bot as validation_core
from src.reporting.sistema_alertas import SistemaAlertas


def test_telegram_com_sucesso():
    mock_client = MagicMock(spec=httpx.Client)
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_client.post.return_value = mock_response

    fake_auth_val = "MOCK_VAL"
    dummy_chat_id = "MOCK_CHAT"
    alertas = SistemaAlertas(
        telegram_token=fake_auth_val, telegram_chat_id=dummy_chat_id, client=mock_client
    )
    res = alertas.notificar("Teste de alerta Telegram", nivel="INFO", evento="TESTE")
    assert res["sucesso"] is True
    assert res["canal_utilizado"] == "Telegram"


def test_telegram_falha_fallback_para_log_local():
    mock_client = MagicMock(spec=httpx.Client)
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_client.post.return_value = mock_response

    fake_auth_val = "MOCK_VAL"
    dummy_chat_id = "MOCK_CHAT"
    alertas = SistemaAlertas(
        telegram_token=fake_auth_val, telegram_chat_id=dummy_chat_id, client=mock_client
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


def test_erro_com_telegram_indisponivel_usa_gmail_com_anexo(tmp_path) -> None:
    mock_client = MagicMock(spec=httpx.Client)
    mock_client.post.return_value.status_code = 500
    gmail = MagicMock()
    gmail.enviar.return_value = True
    anexo = tmp_path / "dead_letter.jsonl"
    anexo.write_text("{}\n", encoding="utf-8")
    fake_auth_val = "MOCK_VAL"
    dummy_chat_id = "MOCK_CHAT"
    alertas = SistemaAlertas(
        telegram_token=fake_auth_val,
        telegram_chat_id=dummy_chat_id,
        gmail_enabled=True,
        gmail_to="operacao@example.com",
        gmail_sender=gmail,
        client=mock_client,
    )

    res = alertas.notificar(
        "Falha técnica no cadastro",
        nivel="ERRO",
        evento="FALHA_TECNICA_CADASTRO",
        anexos=[anexo],
    )

    assert res["canal_utilizado"] == "Gmail"
    assert res["sucesso"] is True
    assert gmail.enviar.call_args.kwargs["anexos"] == [anexo]


def test_gmail_nao_envia_alerta_de_aviso(tmp_path) -> None:
    mock_client = MagicMock(spec=httpx.Client)
    mock_client.post.return_value.status_code = 500
    gmail = MagicMock()
    fake_auth_val = "MOCK_VAL"
    dummy_chat_id = "MOCK_CHAT"
    alertas = SistemaAlertas(
        telegram_token=fake_auth_val,
        telegram_chat_id=dummy_chat_id,
        gmail_enabled=True,
        gmail_to="operacao@example.com",
        gmail_sender=gmail,
        client=mock_client,
    )

    res = alertas.notificar("Pipeline sem ML", nivel="AVISO", evento="TESTE")

    assert res["canal_utilizado"] == "LogLocal"
    gmail.enviar.assert_not_called()


def test_falha_tecnica_gera_alerta_erro_com_dead_letter_anexado(
    tmp_path, monkeypatch
) -> None:
    dead_letter = tmp_path / "dead_letter.jsonl"
    monkeypatch.setattr(
        validation_core,
        "settings",
        replace(validation_core.settings, dead_letter_file=dead_letter),
    )
    alertas = MagicMock()
    dados = pd.DataFrame(
        [
            {
                "lote_id": "LOTE-1",
                "produto": "TV55-4K-B",
                "linha": "LINHA_01",
                "turno": "A",
                "status": "APROVADO",
                "responsavel": "Operador",
                "data": "24/08/2026",
                "observacao": "",
            }
        ]
    )

    validation_core.validar_dataframe(
        dados,
        lotes_validos={"LOTE-1"},
        diretorio_saida=tmp_path,
        falhas_tecnicas=[{"lote_id": "LOTE-ERRO", "motivo": "timeout"}],
        sistema_alertas=alertas,
    )

    assert dead_letter.is_file()
    assert alertas.notificar.call_args.kwargs["nivel"] == "ERRO"
    assert alertas.notificar.call_args.kwargs["evento"] == "FALHA_TECNICA_CADASTRO"
    assert alertas.notificar.call_args.kwargs["anexos"] == [dead_letter]
