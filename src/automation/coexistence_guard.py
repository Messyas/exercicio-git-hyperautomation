"""Guarda de Coexistência de Sessão Gráfica e Runner (BotCity vs Smart Office).

Atende às Seções 4.6, 6 (Cenário 5), 8 e 9 do Enunciado do Capstone:
- Garante que o bot legado (BotCity) e o novo bot (Smart Office) não disputem a mesma sessão gráfica.
- Utiliza mecanismo de Mutex por trava de arquivo e verificação de proprietário de sessão.
- Permite simular e auditar a retenção preventiva de execução em caso de concorrência.
"""

from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from src.core.exceptions import CoexistenceConflictError
from src.utils.time_utils import now_local

logger = logging.getLogger(__name__)

DEFAULT_LOCK_FILE = Path("data/datapool/runner_session.lock")


@dataclass
class LockInfo:
    orchestrator: str
    bot_id: str
    acquired_at: str
    pid: int

    def to_dict(self) -> dict[str, str | int]:
        return {
            "orchestrator": self.orchestrator,
            "bot_id": self.bot_id,
            "acquired_at": self.acquired_at,
            "pid": self.pid,
        }


class CoexistenceGuard:
    """Controlador de acesso exclusivo à sessão gráfica do Runner."""

    def __init__(
        self,
        lock_file: Optional[Path] = None,
        timeout_seconds: float = 5.0,
        logger_instance: Optional[logging.Logger] = None,
    ) -> None:
        self.lock_file = lock_file or DEFAULT_LOCK_FILE
        self.timeout_seconds = timeout_seconds
        self.logger = logger_instance or logger
        self._acquired = False
        self._current_orchestrator: Optional[str] = None
        self._current_bot_id: Optional[str] = None

    def acquire(
        self,
        orchestrator: str,
        bot_id: str,
        blocking: bool = True,
    ) -> bool:
        """Tenta obter o bloqueio da sessão gráfica para o orquestrador informado.

        Parameters
        ----------
        orchestrator : str
            Identificador do orquestrador ('SMART_OFFICE' ou 'BOTCITY_LEGACY').
        bot_id : str
            Nome ou identificador do robô.
        blocking : bool
            Se True, aguarda até timeout_seconds antes de falhar.
        """
        self.lock_file.parent.mkdir(parents=True, exist_ok=True)
        start_time = time.time()

        while True:
            if not self.lock_file.exists():
                try:
                    info = LockInfo(
                        orchestrator=orchestrator,
                        bot_id=bot_id,
                        acquired_at=now_local().isoformat(),
                        pid=os.getpid(),
                    )
                    self.lock_file.write_text(json.dumps(info.to_dict()), encoding="utf-8")
                    self._acquired = True
                    self._current_orchestrator = orchestrator
                    self._current_bot_id = bot_id
                    self.logger.info(
                        "[COEXISTENCE_GUARD] Sessão gráfica OBTIDA com sucesso | "
                        "orquestrador=%s | bot=%s | pid=%d",
                        orchestrator,
                        bot_id,
                        os.getpid(),
                    )
                    return True
                except OSError as exc:
                    self.logger.warning(
                        "[COEXISTENCE_GUARD] Falha de concorrência ao criar lock: %s", exc
                    )

            # Lock existente: ler informações do orquestrador proprietário
            try:
                content = json.loads(self.lock_file.read_text(encoding="utf-8"))
                owner_orch = content.get("orchestrator", "DESCONHECIDO")
                owner_bot = content.get("bot_id", "DESCONHECIDO")
            except Exception:
                owner_orch, owner_bot = "DESCONHECIDO", "DESCONHECIDO"

            if not blocking or (time.time() - start_time) >= self.timeout_seconds:
                self.logger.error(
                    "[COEXISTENCE_GUARD] CONFLITO DE RUNNER! Sessão gráfica bloqueada por '%s' (%s). "
                    "A execução de '%s' (%s) foi retida para evitar concorrência gráfica.",
                    owner_orch,
                    owner_bot,
                    orchestrator,
                    bot_id,
                )
                raise CoexistenceConflictError(
                    f"Runner ocupado por {owner_orch} ({owner_bot}). Execução de {orchestrator} bloqueada."
                )

            time.sleep(0.5)

    def release(self) -> None:
        """Libera o bloqueio da sessão gráfica."""
        if self._acquired and self.lock_file.exists():
            try:
                self.lock_file.unlink(missing_ok=True)
                self.logger.info(
                    "[COEXISTENCE_GUARD] Sessão gráfica LIBERADA | orquestrador=%s | bot=%s",
                    self._current_orchestrator,
                    self._current_bot_id,
                )
            except OSError as exc:
                self.logger.warning("[COEXISTENCE_GUARD] Erro ao remover lock file: %s", exc)
            finally:
                self._acquired = False

    def is_locked(self) -> bool:
        """Informa se a sessão gráfica está atualmente bloqueada."""
        return self.lock_file.exists()

    def get_lock_info(self) -> Optional[dict[str, Any]]:
        """Retorna os dados do lock atual se existir."""
        if not self.lock_file.exists():
            return None
        try:
            return json.loads(self.lock_file.read_text(encoding="utf-8"))
        except Exception:
            return None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()
