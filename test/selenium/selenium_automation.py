"""Ciclo do navegador Selenium e integração com seus Page Objects."""

from __future__ import annotations

import os
from collections.abc import Mapping
from pathlib import Path
from types import TracebackType

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait

from src.pages import SeleniumFormPage, SeleniumLoginPage


class SeleniumAutomation:
    """Adapta o Selenium ao contrato compartilhado pelo orquestrador."""

    def __init__(self, url: str, headless: bool) -> None:
        self._url = url
        self._headless = headless
        self._driver: WebDriver | None = None
        self._login_page: SeleniumLoginPage | None = None
        self._form_page: SeleniumFormPage | None = None

    def __enter__(self) -> "SeleniumAutomation":
        options = Options()
        executable = os.getenv("CHROMIUM_PATH")
        if executable:
            options.binary_location = executable
        if self._headless:
            options.add_argument("--headless=new")
        options.add_argument("--window-size=1440,1200")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")

        driver_path = os.getenv("CHROMEDRIVER_PATH")
        service = Service(executable_path=driver_path) if driver_path else Service()
        self._driver = webdriver.Chrome(service=service, options=options)
        self._driver.get(self._url)
        WebDriverWait(self._driver, 30).until(
            lambda driver: driver.execute_script(
                "return document.readyState"
            )
            == "complete"
        )
        self._login_page = SeleniumLoginPage(self._driver)
        self._form_page = SeleniumFormPage(self._driver)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        if self._driver:
            self._driver.quit()

    def login(self, credentials: Mapping[str, str]) -> None:
        assert self._login_page is not None
        self._login_page.entrar(credentials)

    def process(self, item: Mapping[str, str]) -> None:
        assert self._form_page is not None
        self._form_page.preencher_e_enviar(item)

    def capture_success(self, lote: str, path: Path) -> None:
        assert self._form_page is not None
        assert self._driver is not None
        path.parent.mkdir(parents=True, exist_ok=True)
        comprovante = self._form_page.comprovante(lote)
        self._driver.execute_script(
            "arguments[0].scrollIntoView({block: 'center', inline: 'center'});",
            comprovante,
        )
        comprovante.screenshot(str(path))

    def capture_error(self, path: Path) -> None:
        assert self._driver is not None
        path.parent.mkdir(parents=True, exist_ok=True)
        self._driver.save_screenshot(str(path))
