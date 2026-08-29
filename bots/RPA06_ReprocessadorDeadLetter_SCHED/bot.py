"""Bot RPA06_ReprocessadorDeadLetter_SCHED (Smart Office / The DX Way).

Responsabilidade:
- Bot agendado (Prioridade 5 / Sched) para auditoria e reprocessamento da Dead Letter Queue.
- Avalia itens com falha de dados acumulados em `data/dead_letter/`.
- Permite saneamento de base e emissão de alertas operacionais para itens retidos.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

# Ajusta path para importar módulos da raiz
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.dead_letter import DeadLetterQueue
from src.sistema_alertas import SistemaAlertas
from config import get_settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("RPA06_ReprocessadorDeadLetter_SCHED")


def main() -> int:
    logger.info("=== INICIANDO RPA06_ReprocessadorDeadLetter_SCHED (Prioridade 5) ===")
    settings = get_settings()
    dlq = DeadLetterQueue()

    try:
        itens_pendentes = dlq.listar_itens(status="PENDENTE_REVISAO")
        total = len(itens_pendentes)

        logger.info("[RPA06_DEADLETTER] Total de itens retidos para revisão: %d", total)

        if total > 0:
            alertas = SistemaAlertas(
                telegram_token=settings.telegram_token,
                telegram_chat_id=settings.telegram_chat_id,
                email_enabled=settings.email_enabled,
                email_to=settings.email_to,
                logger_instance=logger,
            )
            alertas.notificar(
                f"Auditoria Dead Letter: {total} itens retidos aguardam intervenção humana de dados.",
                nivel="AVISO",
                evento="DEAD_LETTER_AUDIT",
            )

        logger.info("OK: Auditoria da Dead Letter Queue finalizada com sucesso.")
        return 0

    except Exception as exc:
        logger.exception("[RPA06_DEADLETTER] Erro na auditoria de Dead Letter: %s", exc)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
