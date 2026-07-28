"""Ciclo do navegador Playwright e integração com seus Page Objects."""

from __future__ import annotations

import os
from collections.abc import Mapping
from pathlib import Path
from types import TracebackType

from playwright.sync_api import Browser, Page, Playwright, sync_playwright

from src.pages import PlaywrightFormPage, PlaywrightLoginPage


class PlaywrightAutomation:
    """Adapta o Playwright ao contrato compartilhado pelo orquestrador."""

    def __init__(self, url: str, headless: bool) -> None:
        self._url = url
        self._headless = headless
        self._playwright: Playwright | None = None
        self._browser: Browser | None = None
        self._page: Page | None = None
        self._login_page: PlaywrightLoginPage | None = None
        self._form_page: PlaywrightFormPage | None = None

    def __enter__(self) -> "PlaywrightAutomation":
        self._playwright = sync_playwright().start()
        executable = os.getenv("CHROMIUM_PATH")
        launch_options: dict[str, object] = {
            "headless": self._headless,
            "args": ["--no-sandbox", "--disable-dev-shm-usage"],
        }
        if executable:
            launch_options["executable_path"] = executable

        self._browser = self._playwright.chromium.launch(**launch_options)
        self._page = self._browser.new_page(
            viewport={"width": 1440, "height": 1200}
        )
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
        if self._browser:
            self._browser.close()
        if self._playwright:
            self._playwright.stop()

    def login(self, credentials: Mapping[str, str]) -> None:
        assert self._login_page is not None
        self._login_page.entrar(credentials)

    def process(self, item: Mapping[str, str]) -> None:
        assert self._form_page is not None
        self._form_page.preencher_e_enviar(item)

    def capture_success(self, lote: str, path: Path) -> None:
        assert self._form_page is not None
        path.parent.mkdir(parents=True, exist_ok=True)
        self._form_page.comprovante(lote).screenshot(path=str(path))

    def capture_error(self, path: Path) -> None:
        assert self._page is not None
        path.parent.mkdir(parents=True, exist_ok=True)
        self._page.screenshot(path=str(path), full_page=True)
