"""SistemaAlertas: Notificação multicanal com resiliência e fallback.

Este módulo atende às Seções 3.4, 6 (Cenário 5) e 8 do Estudo de Caso S10-B:
- Telegram como canal principal.
- WhatsApp (Twilio) ou Email (SMTP) como canais secundários de fallback.
- Se o canal principal falhar (ex.: token Telegram inválido), a notificação é
  enviada pelo canal secundário ou registrada com destaque nos logs locais.
- Alerta obrigatório de severidade AVISO quando 100% dos itens caírem em fallback de ML.
- NUNCA lança exceção para a aplicação em caso de falha de envio de alertas.
"""

from __future__ import annotations

import logging
import smtplib
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any, Iterable, Optional

import httpx

from src.gmail_client import GmailOAuthSender

logger = logging.getLogger(__name__)


class SistemaAlertas:
    """Gerenciador resiliente de notificações multicanal."""

    def __init__(
        self,
        telegram_token: Optional[str] = None,
        telegram_chat_id: Optional[str] = None,
        whatsapp_enabled: bool = False,
        twilio_account_sid: Optional[str] = None,
        twilio_auth_token: Optional[str] = None,
        whatsapp_to: Optional[str] = None,
        whatsapp_from: Optional[str] = None,
        email_enabled: bool = False,
        smtp_server: Optional[str] = None,
        smtp_port: int = 587,
        email_from: Optional[str] = None,
        email_to: Optional[str] = None,
        gmail_enabled: bool = False,
        gmail_credentials_file: Optional[str | Path] = None,
        gmail_token_file: Optional[str | Path] = None,
        gmail_from: Optional[str] = None,
        gmail_to: Optional[str] = None,
        gmail_sender: Optional[GmailOAuthSender] = None,
        client: Optional[httpx.Client] = None,
        logger_instance: Optional[logging.Logger] = None,
    ):
        self.telegram_token = telegram_token
        self.telegram_chat_id = telegram_chat_id
        self.whatsapp_enabled = whatsapp_enabled
        self.twilio_account_sid = twilio_account_sid
        self.twilio_auth_token = twilio_auth_token
        self.whatsapp_to = whatsapp_to
        self.whatsapp_from = whatsapp_from
        self.email_enabled = email_enabled
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.email_from = email_from
        self.email_to = email_to
        self.gmail_enabled = gmail_enabled
        self.gmail_credentials_file = gmail_credentials_file
        self.gmail_token_file = gmail_token_file
        self.gmail_from = gmail_from
        self.gmail_to = gmail_to
        self._gmail_sender = gmail_sender
        self.logger = logger_instance or logger

        if client is not None:
            self._client = client
            self._owns_client = False
        else:
            self._client = httpx.Client(timeout=5.0)
            self._owns_client = True

    def notificar(
        self,
        mensagem: str,
        *,
        nivel: str = "INFO",
        evento: str = "GERAL",
        anexos: Iterable[str | Path] = (),
    ) -> dict[str, Any]:
        """Dispara uma notificação com fallback de canal de envio."""
        texto_formatado = f"[{nivel}][{evento}] {mensagem}"
        resultado = {
            "evento": evento,
            "nivel": nivel,
            "mensagem": mensagem,
            "canal_utilizado": None,
            "sucesso": False,
            "tentativas_falhas": [],
        }

        # 1. Tenta canal principal (Telegram)
        if self.telegram_token and self.telegram_chat_id:
            try:
                if self._enviar_telegram(texto_formatado):
                    resultado["canal_utilizado"] = "Telegram"
                    resultado["sucesso"] = True
                    self.logger.info(f"[ALERTA_ENVIADO] Canal: Telegram | Evento: {evento}")
                    return resultado
                else:
                    resultado["tentativas_falhas"].append("Telegram (HTTP erro)")
            except Exception as exc:
                self.logger.warning(f"[ALERTA_FALHA_CANAL] Telegram falhou: {exc}")
                resultado["tentativas_falhas"].append(f"Telegram ({exc})")

        # 2. Fallback para WhatsApp
        if self.whatsapp_enabled and self.twilio_account_sid and self.twilio_auth_token:
            try:
                if self._enviar_whatsapp(texto_formatado):
                    resultado["canal_utilizado"] = "WhatsApp"
                    resultado["sucesso"] = True
                    self.logger.warning(
                        f"[ALERTA_FALLBACK_CANAL] Alerta enviado via WhatsApp | Evento: {evento}"
                    )
                    return resultado
                else:
                    resultado["tentativas_falhas"].append("WhatsApp (HTTP erro)")
            except Exception as exc:
                self.logger.warning(f"[ALERTA_FALHA_CANAL] WhatsApp falhou: {exc}")
                resultado["tentativas_falhas"].append(f"WhatsApp ({exc})")

        # 3. Fallback Gmail para erros que exigem canal secundário e evidências.
        if self._gmail_aplicavel(nivel):
            try:
                if self._enviar_gmail(
                    assunto=f"Alerta Pipeline: {evento}",
                    corpo=texto_formatado,
                    anexos=anexos,
                ):
                    resultado["canal_utilizado"] = "Gmail"
                    resultado["sucesso"] = True
                    self.logger.warning(
                        f"[ALERTA_FALLBACK_CANAL] Alerta enviado via Gmail | Evento: {evento}"
                    )
                    return resultado
                resultado["tentativas_falhas"].append("Gmail (API erro)")
            except Exception as exc:
                self.logger.warning(f"[ALERTA_FALHA_CANAL] Gmail falhou: {exc}")
                resultado["tentativas_falhas"].append(f"Gmail ({exc})")

        # 4. Fallback para Email SMTP legado.
        if self.email_enabled and self.smtp_server and self.email_to:
            try:
                if self._enviar_email(f"Alerta Pipeline: {evento}", texto_formatado):
                    resultado["canal_utilizado"] = "Email"
                    resultado["sucesso"] = True
                    self.logger.warning(
                        f"[ALERTA_FALLBACK_CANAL] Alerta enviado via Email | Evento: {evento}"
                    )
                    return resultado
                else:
                    resultado["tentativas_falhas"].append("Email (SMTP erro)")
            except Exception as exc:
                self.logger.warning(f"[ALERTA_FALHA_CANAL] Email falhou: {exc}")
                resultado["tentativas_falhas"].append(f"Email ({exc})")

        # 5. Fallback final: Log de Emergência Destacado
        resultado["canal_utilizado"] = "LogLocal"
        resultado["sucesso"] = True
        self.logger.error(
            f"**************************************************\n"
            f"[ALERTA_EMERGENCIA_LOG] Falha em todos os canais remotos!\n"
            f"Evento: {evento} | Nível: {nivel}\n"
            f"Mensagem: {mensagem}\n"
            f"Canais com falha: {resultado['tentativas_falhas']}\n"
            f"**************************************************"
        )
        return resultado

    def notificar_pipeline_sem_ml(self, total_itens_fallback: int) -> dict[str, Any]:
        """Dispara o alerta obrigatório de severidade AVISO indicando pipeline operando 100% sem ML."""
        mensagem = (
            f"⚠️ PIPELINE OPERANDO SEM ML: Todos os {total_itens_fallback} itens com divergência "
            f"caíram em modo de fallback nesta execução."
        )
        return self.notificar(
            mensagem=mensagem,
            nivel="AVISO",
            evento="PIPELINE_SEM_ML",
        )

    def _enviar_telegram(self, texto: str) -> bool:
        url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
        payload = {
            "chat_id": self.telegram_chat_id,
            "text": texto,
            "parse_mode": "Markdown",
        }
        res = self._client.post(url, json=payload)
        return res.status_code == 200

    def _enviar_whatsapp(self, texto: str) -> bool:
        url = f"https://api.twilio.com/2010-04-01/Accounts/{self.twilio_account_sid}/Messages.json"
        data = {
            "To": self.whatsapp_to,
            "From": self.whatsapp_from,
            "Body": texto,
        }
        auth = (self.twilio_account_sid, self.twilio_auth_token or "")
        res = self._client.post(url, data=data, auth=auth)
        return res.status_code in (200, 201)

    def _enviar_email(self, assunto: str, corpo: str) -> bool:
        msg = MIMEText(corpo, "plain", "utf-8")
        msg["Subject"] = assunto
        msg["From"] = self.email_from or "bot@hyperautomation.com"
        msg["To"] = self.email_to or "operacao@hyperautomation.com"

        with smtplib.SMTP(self.smtp_server or "localhost", self.smtp_port, timeout=5.0) as server:
            server.send_message(msg)
        return True

    def _gmail_aplicavel(self, nivel: str) -> bool:
        """Gmail é o canal adicional do enunciado apenas para ERRO/CRÍTICO."""
        nivel_normalizado = nivel.strip().upper()
        return (
            self.gmail_enabled
            and bool(self.gmail_to)
            and nivel_normalizado in {"ERRO", "CRITICO", "CRÍTICO"}
        )

    def _enviar_gmail(
        self,
        *,
        assunto: str,
        corpo: str,
        anexos: Iterable[str | Path],
    ) -> bool:
        if self._gmail_sender is None:
            if not self.gmail_token_file:
                raise ValueError(
                    "GMAIL_TOKEN_FILE é obrigatório quando GMAIL_ENABLED=true."
                )
            self._gmail_sender = GmailOAuthSender(
                credentials_file=self.gmail_credentials_file,
                token_file=self.gmail_token_file,
                email_from=self.gmail_from,
            )
        return self._gmail_sender.enviar(
            destinatario=self.gmail_to or "",
            assunto=assunto,
            corpo=corpo,
            anexos=anexos,
        )

    def close(self) -> None:
        if self._owns_client:
            self._client.close()
