"""Dead Letter Queue e Reprocessamento (The DX Way).

Atende às Seções 4.4, 6 (Cenário 6), 8 e 9 do Enunciado do Capstone:
- Coleta itens que falham repetidamente por erro de dados (`FalhaItemError`).
- Registra histórico de auditoria completo (item_id, motivo da falha, tentativas, timestamp).
- Permite reprocessamento agendado ou sob demanda sem interromper o pipeline principal.
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, List, Optional

from src.time_utils import now_local

logger = logging.getLogger(__name__)

DEFAULT_DEAD_LETTER_DIR = Path("data/dead_letter")


@dataclass
class DeadLetterItem:
    """Registro de um item encaminhado para a Dead Letter Queue."""

    item_id: str
    lote_id: str
    dados_originais: dict[str, Any]
    motivo_falha: str
    tentativas_realizadas: int
    origem_processo: str
    registrado_em: str
    status: str = "PENDENTE_REVISAO"  # PENDENTE_REVISAO, REPROCESSADO, DESCARTADO
    observacao_revisao: Optional[str] = None


class DeadLetterQueue:
    """Fila resiliente de itens não processáveis com persistência em JSON Lines."""

    def __init__(
        self,
        storage_dir: Optional[Path] = None,
        logger_instance: Optional[logging.Logger] = None,
    ) -> None:
        self.storage_dir = storage_dir or DEFAULT_DEAD_LETTER_DIR
        self.storage_file = self.storage_dir / "dead_letter_items.jsonl"
        self.logger = logger_instance or logger
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def registrar_falha(
        self,
        *,
        item_id: str,
        lote_id: str,
        dados_originais: dict[str, Any],
        motivo_falha: str,
        tentativas: int = 3,
        origem: str = "PIPELINE_CAPSTONE",
    ) -> DeadLetterItem:
        """Adiciona um item com falha irrecuperável à Dead Letter Queue."""
        item = DeadLetterItem(
            item_id=item_id,
            lote_id=lote_id,
            dados_originais=dados_originais,
            motivo_falha=motivo_falha,
            tentativas_realizadas=tentativas,
            origem_processo=origem,
            registrado_em=now_local().isoformat(),
        )

        with open(self.storage_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(item), ensure_ascii=False) + "\n")

        self.logger.warning(
            "[DEAD_LETTER] Item '%s' (Lote: %s) encaminhado para Dead Letter | Motivo: %s | Tentativas: %d",
            item_id,
            lote_id,
            motivo_falha,
            tentativas,
        )
        return item

    def listar_itens(self, status: Optional[str] = None) -> List[DeadLetterItem]:
        """Lê todos os itens persistidos na Dead Letter Queue."""
        if not self.storage_file.exists():
            return []

        itens = []
        with open(self.storage_file, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    data = json.loads(line)
                    if status is None or data.get("status") == status:
                        itens.append(DeadLetterItem(**data))
                except Exception as exc:
                    self.logger.error("[DEAD_LETTER] Erro ao decodificar item: %s", exc)
        return itens

    def total_itens(self) -> int:
        """Contabiliza o total de itens na Dead Letter Queue."""
        return len(self.listar_itens())

    def limpar(self) -> None:
        """Esvazia a Dead Letter Queue (usado em testes)."""
        if self.storage_file.exists():
            self.storage_file.unlink()
