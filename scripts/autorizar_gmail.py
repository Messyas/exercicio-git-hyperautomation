"""Autoriza localmente o Gmail API e cria o token usado pelos bots."""

from __future__ import annotations

import os
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from config import get_settings  # noqa: E402
from src.gmail_client import GmailAuthorizationError, autorizar_gmail  # noqa: E402


def main() -> int:
    settings = get_settings()
    try:
        port = int(os.getenv("GMAIL_OAUTH_PORT", "0"))
    except ValueError:
        print("GMAIL_OAUTH_PORT deve ser um número inteiro.")
        return 1

    abrir_navegador = os.getenv("GMAIL_OAUTH_OPEN_BROWSER", "true").strip().lower()
    try:
        token_path = autorizar_gmail(
            credentials_file=settings.gmail_credentials_file,
            token_file=settings.gmail_token_file,
            port=port,
            bind_address=os.getenv("GMAIL_OAUTH_BIND_ADDRESS") or None,
            redirect_host=os.getenv("GMAIL_OAUTH_REDIRECT_HOST", "localhost"),
            open_browser=abrir_navegador in {"1", "true", "yes", "sim", "on"},
        )
    except GmailAuthorizationError as exc:
        print(f"Não foi possível autorizar o Gmail: {exc}")
        return 1

    print(f"Token OAuth do Gmail criado em: {token_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
