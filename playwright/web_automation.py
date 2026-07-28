"""Infraestrutura de criação e encerramento da sessão Playwright."""

from collections.abc import Iterator
from contextlib import contextmanager

from playwright.sync_api import Page, sync_playwright


DEFAULT_URL = "http://frontend:3000"


@contextmanager
def abrir_pagina(url: str | None = None, *, headless: bool = True) -> Iterator[Page]:
    """Abre uma página pronta para uso e encerra o navegador ao final."""
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=headless)
        try:
            page = browser.new_page()
            page.goto(url or DEFAULT_URL, wait_until="networkidle", timeout=30_000)
            yield page
        finally:
            browser.close()
