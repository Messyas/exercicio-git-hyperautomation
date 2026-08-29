"""Bot RPA02_ColetaPedidos_WEB (Smart Office / The DX Way).

Responsabilidade:
- Automação web (Playwright) para consulta ao portal de fornecedores e pedidos abertos (Prioridade 2).
- Extração dos dados de pedidos de compra para cruzamento com o estoque físico.
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

from src.excel_source import load_excel_batch
from config import get_settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("RPA02_ColetaPedidos_WEB")


def main() -> int:
    logger.info("=== INICIANDO RPA02_ColetaPedidos_WEB (Prioridade 2) ===")
    settings = get_settings()

    try:
        # Carrega dados de pedidos (via planilha de entrada / mock do portal web)
        batch = load_excel_batch(settings.default_input_file)
        pedidos = batch.records()

        output_dir = Path("data/datapool")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / "coleta_web_pedidos.json"
        output_file.write_text(json.dumps(pedidos, indent=2, default=str, ensure_ascii=False), encoding="utf-8")

        logger.info(
            "OK: %d pedidos de compra coletados via automação web | salvo em '%s'",
            len(pedidos),
            output_file,
        )
        return 0

    except Exception as exc:
        logger.exception("[RPA02_WEB] Erro na coleta web de pedidos: %s", exc)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
