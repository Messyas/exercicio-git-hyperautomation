"""Ciclo de vida do navegador usado pelo bot produtor."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from types import TracebackType
from urllib.parse import urlsplit

from playwright.sync_api import Browser, Page, Playwright, sync_playwright

from src.pages import PlaywrightFormPage, PlaywrightLoginPage
from src.web_automation import iniciar_browser


ALLOWED_HOSTS = {"frontend", "localhost", "127.0.0.1"}


class PlaywrightAutomation:
    """Adapta o Playwright ao fluxo de cadastro em lote."""

    def __init__(
        self,
        url: str,
        *,
        headless: bool,
        slow_mo: int,
        timeout_ms: int,
    ) -> None:
        host = urlsplit(url).hostname
        if host not in ALLOWED_HOSTS:
            raise ValueError(
                f"Destino {host!r} não permitido para a automação local."
            )
        self._url = url
        self._headless = headless
        self._slow_mo = slow_mo
        self._timeout_ms = timeout_ms
        self._playwright: Playwright | None = None
        self._browser: Browser | None = None
        self._page: Page | None = None
        self._login_page: PlaywrightLoginPage | None = None
        self._form_page: PlaywrightFormPage | None = None

    def __enter__(self) -> "PlaywrightAutomation":
        self._playwright = sync_playwright().start()
        self._browser = iniciar_browser(
            self._playwright,
            headless=self._headless,
            slow_mo=self._slow_mo,
        )
        self._page = self._browser.new_page(
            viewport={"width": 1440, "height": 1200}
        )
        self._page.set_default_timeout(self._timeout_ms)
        self._page.goto(
            self._url,
            wait_until="domcontentloaded",
            timeout=30_000,
        )
        self._login_page = PlaywrightLoginPage(self._page)
        self._form_page = PlaywrightFormPage(self._page)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        if self._browser is not None:
            self._browser.close()
        if self._playwright is not None:
            self._playwright.stop()

    def login(self, credentials: Mapping[str, str]) -> None:
        if self._login_page is None:
            raise RuntimeError("Navegador ainda não foi iniciado.")
        self._login_page.entrar(credentials, timeout_ms=self._timeout_ms)

    def register(
        self,
        item: Mapping[str, str],
        evidence_path: Path,
    ) -> None:
        if self._form_page is None:
            raise RuntimeError("Navegador ainda não foi iniciado.")
        self._form_page.preencher_e_enviar(item)
        self._form_page.capturar_comprovante(
            item["lote_id"],
            evidence_path,
            timeout_ms=self._timeout_ms,
        )

    def capture_error(self, path: Path) -> None:
        if self._form_page is None:
            raise RuntimeError("Navegador ainda não foi iniciado.")
        self._form_page.capturar_erro(path)

    def capture_rejection(self, path: Path) -> None:
        if self._form_page is None:
            raise RuntimeError("Navegador ainda não foi iniciado.")
        self._form_page.capturar_rejeicao(path)
