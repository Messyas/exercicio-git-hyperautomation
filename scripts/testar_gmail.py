"""Dispara um único alerta Gmail de demonstração, sem chamar o Telegram real."""

from __future__ import annotations

import sys
from pathlib import Path

import httpx


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from config import get_settings  # noqa: E402
from src.sistema_alertas import SistemaAlertas  # noqa: E402


def main() -> int:
    settings = get_settings()
    if not settings.gmail_enabled or not settings.gmail_to:
        print("Defina GMAIL_ENABLED=true e GMAIL_TO no .env antes do teste.")
        return 1
    if not settings.gmail_token_file.is_file():
        print(f"Token Gmail não encontrado: {settings.gmail_token_file}")
        return 1

    evidencia = PROJECT_ROOT / "reports" / "teste_gmail" / "alerta_teste_gmail.txt"
    evidencia.parent.mkdir(parents=True, exist_ok=True)
    evidencia.write_text(
        "Alerta de demonstração do pipeline S10-B.\n"
        "Telegram foi simulado como indisponível; Gmail foi o fallback.\n",
        encoding="utf-8",
    )

    # O transporte simulado impede qualquer chamada para a API Telegram.
    client = httpx.Client(
        transport=httpx.MockTransport(lambda request: httpx.Response(503))
    )
    mock_tkn = "telegram-simulacao-indisponivel"
    try:
        alertas = SistemaAlertas(
            telegram_token=mock_tkn,
            telegram_chat_id="chat-simulacao",
            whatsapp_enabled=False,
            email_enabled=False,
            gmail_enabled=settings.gmail_enabled,
            gmail_credentials_file=settings.gmail_credentials_file,
            gmail_token_file=settings.gmail_token_file,
            gmail_from=settings.gmail_from,
            gmail_to=settings.gmail_to,
            client=client,
        )
        resultado = alertas.notificar(
            mensagem=(
                "Teste controlado: falha simulada do Telegram para demonstrar "
                "o fallback Gmail."
            ),
            nivel="ERRO",
            evento="TESTE_GMAIL_DEMONSTRACAO",
            anexos=[evidencia],
        )
    finally:
        client.close()

    print(
        "Teste Gmail concluído | "
        f"canal={resultado['canal_utilizado']} | sucesso={resultado['sucesso']}"
    )
    return 0 if resultado["canal_utilizado"] == "Gmail" else 1


if __name__ == "__main__":
    raise SystemExit(main())
