"""Testes da montagem de mensagens Gmail sem acessar rede ou conta externa."""

from __future__ import annotations

import base64
from email import message_from_bytes
from email.header import decode_header, make_header
from pathlib import Path
from unittest.mock import MagicMock

from src.gmail_client import GmailOAuthSender, autorizar_gmail


def test_gmail_sender_codifica_mensagem_com_anexo(tmp_path: Path) -> None:
    anexo = tmp_path / "dead_letter.jsonl"
    anexo.write_text('{"lote_id":"L-1"}\n', encoding="utf-8")
    service = MagicMock()
    service.users().messages().send().execute.return_value = {"id": "gmail-123"}
    sender = GmailOAuthSender(
        credentials_file=tmp_path / "credentials.json",
        token_file=tmp_path / "token.json",
        email_from="bot@example.com",
        service=service,
    )

    enviado = sender.enviar(
        destinatario="operacao@example.com",
        assunto="Falha técnica",
        corpo="Há uma falha para análise.",
        anexos=[anexo],
    )

    assert enviado is True
    payload = service.users().messages().send.call_args.kwargs["body"]
    mensagem = message_from_bytes(base64.urlsafe_b64decode(payload["raw"]))
    assert mensagem["To"] == "operacao@example.com"
    assert str(make_header(decode_header(mensagem["Subject"]))) == "Falha técnica"
    assert "dead_letter.jsonl" in [
        parte.get_filename() for parte in mensagem.walk()
    ]


def test_autorizacao_oauth_no_container_escuta_todas_as_interfaces(
    tmp_path: Path, monkeypatch
) -> None:
    credentials_file = tmp_path / "credentials.json"
    credentials_file.write_text("{}", encoding="utf-8")
    token_file = tmp_path / "token.json"
    flow = MagicMock()
    flow.run_local_server.return_value.to_json.return_value = '{"token":"ok"}'
    flow_factory = MagicMock()
    flow_factory.from_client_secrets_file.return_value = flow
    monkeypatch.setattr(
        "src.gmail_client._google_dependencies",
        lambda: (None, None, flow_factory, None),
    )

    resultado = autorizar_gmail(
        credentials_file=credentials_file,
        token_file=token_file,
        port=8080,
        bind_address="0.0.0.0",
        redirect_host="localhost",
        open_browser=False,
    )

    assert resultado == token_file
    assert token_file.read_text(encoding="utf-8") == '{"token":"ok"}'
    assert flow.run_local_server.call_args.kwargs == {
        "host": "localhost",
        "bind_addr": "0.0.0.0",
        "port": 8080,
        "open_browser": False,
        "access_type": "offline",
        "prompt": "consent",
    }
