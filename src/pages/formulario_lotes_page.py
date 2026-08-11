"""Page Object do formulário Next.js usado nos testes E2E."""

from __future__ import annotations

from collections.abc import Mapping

from playwright.sync_api import Page

from src.pages.playwright_pages import PlaywrightFormPage, PlaywrightLoginPage


class PlaywrightFormularioLotesPage(PlaywrightFormPage):
    """Abre a aplicação e autentica o usuário."""

    def __init__(
        self,
        page: Page,
        pagina_html: str,
        credenciais: Mapping[str, str],
        *,
        timeout_ms: int = 10_000,
    ) -> None:
        super().__init__(page)
        self._pagina_html = pagina_html
        self._credenciais = credenciais
        self._timeout_ms = timeout_ms
        self._login_page = PlaywrightLoginPage(page)

    def abrir(self) -> None:
        self.page.goto(
            self._pagina_html,
            wait_until="domcontentloaded",
            timeout=30_000,
        )
        self._login_page.entrar(
            self._credenciais,
            timeout_ms=self._timeout_ms,
        )

    def preencher_lote(self, valor: str) -> None:
        """Preenche o numero do lote no formulario de cadastro."""
        super().preencher_lote(valor)

    def selecionar_status(self, valor: str) -> None:
        """Seleciona o status pelo radio button do formulario."""
        super().selecionar_status(valor)
