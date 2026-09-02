"""Envio de alertas pelo Gmail API com OAuth 2.0.

O token de OAuth e o arquivo de credenciais ficam fora do repositório. A
autorização interativa ocorre somente pelo script ``scripts/autorizar_gmail.py``;
durante a execução do bot, a ausência ou invalidez do token é tratada pelo
``SistemaAlertas`` como falha de canal e nunca interrompe o pipeline.
"""

from __future__ import annotations

import base64
import mimetypes
from email.message import EmailMessage
from pathlib import Path
from typing import Any, Iterable


GMAIL_SEND_SCOPE = "https://www.googleapis.com/auth/gmail.send"


class GmailAuthorizationError(RuntimeError):
    """Indica que o Gmail ainda não está apto a enviar alertas."""


def _google_dependencies() -> tuple[Any, Any, Any, Any]:
    """Importa as bibliotecas Google somente quando o canal é utilizado."""
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build
    except ImportError as exc:  # pragma: no cover - protegido pela imagem Docker
        raise GmailAuthorizationError(
            "Dependências do Gmail ausentes. Instale os pacotes google-* previstos "
            "em requirements.txt."
        ) from exc
    return Request, Credentials, InstalledAppFlow, build


class GmailOAuthSender:
    """Cliente mínimo para enviar mensagens já autorizadas pelo Gmail API."""

    def __init__(
        self,
        *,
        credentials_file: str | Path | None,
        token_file: str | Path,
        email_from: str | None = None,
        service: Any | None = None,
    ) -> None:
        self.credentials_file = (
            Path(credentials_file) if credentials_file is not None else None
        )
        self.token_file = Path(token_file)
        self.email_from = email_from
        self._service = service

    def enviar(
        self,
        *,
        destinatario: str,
        assunto: str,
        corpo: str,
        anexos: Iterable[str | Path] = (),
    ) -> bool:
        """Envia uma mensagem MIME codificada como exige o endpoint Gmail."""
        if not destinatario.strip():
            raise GmailAuthorizationError("GMAIL_TO não foi configurado.")

        mensagem = EmailMessage()
        mensagem["To"] = destinatario
        mensagem["Subject"] = assunto
        if self.email_from:
            mensagem["From"] = self.email_from
        mensagem.set_content(corpo)

        for anexo in anexos:
            caminho = Path(anexo)
            if not caminho.is_file():
                raise FileNotFoundError(f"Anexo do alerta não encontrado: {caminho}")
            mime_type, _ = mimetypes.guess_type(caminho.name)
            main_type, sub_type = (mime_type or "application/octet-stream").split(
                "/", maxsplit=1
            )
            mensagem.add_attachment(
                caminho.read_bytes(),
                maintype=main_type,
                subtype=sub_type,
                filename=caminho.name,
            )

        raw = base64.urlsafe_b64encode(mensagem.as_bytes()).decode("ascii")
        service = self._service or self._build_service()
        resposta = (
            service.users()
            .messages()
            .send(userId="me", body={"raw": raw})
            .execute()
        )
        return bool(resposta.get("id"))

    def _build_service(self) -> Any:
        Request, Credentials, _, build = _google_dependencies()
        if not self.token_file.is_file():
            raise GmailAuthorizationError(
                "Token OAuth do Gmail não encontrado. Execute "
                "'python scripts/autorizar_gmail.py' na máquina local antes de "
                "habilitar GMAIL_ENABLED."
            )

        credentials = Credentials.from_authorized_user_file(
            str(self.token_file), [GMAIL_SEND_SCOPE]
        )
        if not credentials.valid:
            if credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())
            else:
                raise GmailAuthorizationError(
                    "Token OAuth do Gmail inválido ou sem refresh token. Execute "
                    "novamente 'python scripts/autorizar_gmail.py'."
                )
        return build("gmail", "v1", credentials=credentials, cache_discovery=False)


def autorizar_gmail(
    *,
    credentials_file: str | Path,
    token_file: str | Path,
    port: int = 0,
    bind_address: str | None = None,
    redirect_host: str = "localhost",
    open_browser: bool = True,
) -> Path:
    """Abre o consentimento OAuth local e guarda um token renovável com segurança."""
    _, _, InstalledAppFlow, _ = _google_dependencies()
    credentials_path = Path(credentials_file)
    token_path = Path(token_file)
    if not credentials_path.is_file():
        raise GmailAuthorizationError(
            f"Arquivo de credenciais OAuth não encontrado: {credentials_path}"
        )

    flow = InstalledAppFlow.from_client_secrets_file(
        str(credentials_path), [GMAIL_SEND_SCOPE]
    )
    credentials = flow.run_local_server(
        host=redirect_host,
        bind_addr=bind_address,
        port=port,
        open_browser=open_browser,
        access_type="offline",
        prompt="consent",
    )
    token_path.parent.mkdir(parents=True, exist_ok=True)
    token_path.write_text(credentials.to_json(), encoding="utf-8")
    return token_path
