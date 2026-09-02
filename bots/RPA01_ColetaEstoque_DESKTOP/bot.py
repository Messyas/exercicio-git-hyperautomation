"""Bot RPA01_ColetaEstoque_DESKTOP (Smart Office / The DX Way).

Responsabilidade:
- Conecta-se à sessão gráfica dedicada do Runner (Prioridade 1).
- Utiliza CoexistenceGuard para garantir exclusividade sobre o desktop.
- Automação de tela para extrair posições físicas de estoque no sistema interno legado.
- Persiste a extração de dados no DataPool para consumo pelo bot de consolidação.
"""

from __future__ import annotations

import json
import logging
import os
import sys
from pathlib import Path

# Ajusta path para importar módulos da raiz
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.coexistence_guard import CoexistenceGuard
from src.desktop_automation import DesktopAutomationClient
from src.time_utils import now_local

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("RPA01_ColetaEstoque_DESKTOP")


def main() -> int:
    logger.info("=== INICIANDO RPA01_ColetaEstoque_DESKTOP (Prioridade 1) ===")
    guard = CoexistenceGuard()

    # 1. Garantir exclusividade na sessão gráfica (evita conflito com BotCity legado)
    try:
        guard.acquire(orchestrator="SMART_OFFICE", bot_id="RPA01_ColetaEstoque_DESKTOP")
    except Exception as exc:
        logger.error("[RPA01_DESKTOP] Falha de sessão gráfica: %s", exc)
        return 1

    try:
        client = DesktopAutomationClient()
        client.conectar_sistema_desktop()

        # Lista de lotes a serem coletados no sistema desktop
        lotes_amostra = ["LOTE-001", "LOTE-002", "LOTE-003", "LOTE-004", "LOTE-005", "LOTE-006", "LOTE-007"]
        coletas = []

        for lote in lotes_amostra:
            resultado = client.consultar_lote(lote)
            coletas.append(resultado)

        # Salva dados coletados no DataPool
        output_dir = Path("data/datapool")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / "coleta_desktop_estoque.json"
        output_file.write_text(json.dumps(coletas, indent=2, ensure_ascii=False), encoding="utf-8")

        logger.info(
            "OK: %d posições de estoque extraídas do sistema desktop | salvo em '%s'",
            len(coletas),
            output_file,
        )
        return 0

    except Exception as exc:
        logger.exception("[RPA01_DESKTOP] Erro durante a automação desktop: %s", exc)
        return 1

    finally:
        guard.release()


if __name__ == "__main__":
    raise SystemExit(main())
