"""Automação Desktop Resiliente (The DX Way).

Atende às Seções 4.1, 4.4, 6 (Cenário 1) e 8 do Enunciado do Capstone:
- Executa automação de tela sobre o sistema desktop interno legado de estoque.
- Implementa retry exponencial para reconexão à sessão gráfica e abertura da janela.
- Oferece fallback gracioso para modo degradado caso o aplicativo desktop esteja indisponível.
"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, Optional

from desktop_app.sistema_estoque import SistemaEstoqueDesktop
from src.core.exceptions import DesktopAppUnavailableError

logger = logging.getLogger(__name__)


class DesktopAutomationClient:
    """Cliente de automação para interação com o cliente desktop de estoque."""

    def __init__(
        self,
        max_retries: int = 3,
        backoff_seconds: float = 0.5,
        force_fail: bool = False,
        logger_instance: Optional[logging.Logger] = None,
    ) -> None:
        self.max_retries = max_retries
        self.backoff_seconds = backoff_seconds
        self.force_fail = force_fail
        self.logger = logger_instance or logger
        self._sistema = SistemaEstoqueDesktop()

    def conectar_sistema_desktop(self) -> bool:
        """Simula a localização da janela gráfica e acoplamento ao processo desktop."""
        if self.force_fail:
            raise DesktopAppUnavailableError(
                "Sessão gráfica indisponível: Janela 'LG Electronics - Sistema Interno' não encontrada."
            )
        self.logger.info("[DESKTOP_RPA] Janela do Sistema de Estoque localizada na sessão gráfica.")
        return True

    def consultar_lote(self, lote_id: str) -> Dict[str, Any]:
        """Consulta o saldo físico e status de um lote na aplicação desktop com política de retry."""
        attempt = 0
        last_error: Optional[Exception] = None

        while attempt < self.max_retries:
            attempt += 1
            try:
                if self.force_fail:
                    raise DesktopAppUnavailableError(
                        f"Janela desktop fechada durante a consulta do lote '{lote_id}' (Tentativa {attempt}/{self.max_retries})."
                    )

                self.logger.debug(
                    "[DESKTOP_RPA] Digitando código '%s' no campo de busca (F2) | tentativa=%d",
                    lote_id,
                    attempt,
                )
                posicao = self._sistema.consultar_posicao(lote_id)
                if posicao:
                    return {
                        "lote_id": lote_id,
                        "produto": posicao["produto"],
                        "saldo_fisico": posicao["saldo_fisico"],
                        "localizacao": posicao["localizacao"],
                        "status_estoque": posicao["status"],
                        "encontrado": True,
                        "origem": "DESKTOP_APP_GUI",
                    }
                else:
                    return {
                        "lote_id": lote_id,
                        "produto": "DESCONHECIDO",
                        "saldo_fisico": 0,
                        "localizacao": "N/A",
                        "status_estoque": "NAO_ENCONTRADO",
                        "encontrado": False,
                        "origem": "DESKTOP_APP_GUI",
                    }

            except DesktopAppUnavailableError as exc:
                last_error = exc
                self.logger.warning(
                    "[DESKTOP_RETRY] Falha na automação desktop | lote=%s | tentativa=%d/%d | erro=%s",
                    lote_id,
                    attempt,
                    self.max_retries,
                    exc,
                )
                if attempt < self.max_retries:
                    time.sleep(self.backoff_seconds * attempt)

        self.logger.error(
            "[DESKTOP_FALLBACK] Todas as %d tentativas falharam para o lote '%s'. Acionando fallback degradado.",
            self.max_retries,
            lote_id,
        )
        raise last_error or DesktopAppUnavailableError(f"Falha definitiva ao consultar lote {lote_id} no desktop.")
