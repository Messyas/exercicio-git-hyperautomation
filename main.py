"""Ponto de entrada do bot corporativo.

Nesta etapa, o launcher delega o fluxo legado para ``bot.py``. A separação
permite adicionar as integrações BotCity nas próximas issues sem quebrar as
regras de negócio e os testes existentes.
"""

from __future__ import annotations

from bot import main as run_bot


def main(argumentos: list[str] | None = None) -> int:
    """Executa o bot usando a interface de linha de comando existente."""
    return run_bot(argumentos)


if __name__ == "__main__":
    raise SystemExit(main())

