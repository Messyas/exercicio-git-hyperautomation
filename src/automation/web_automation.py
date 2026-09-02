"""Inicialização do Chromium em ambiente local ou container."""

from __future__ import annotations

import os

from playwright.sync_api import Browser, Playwright


EM_CONTAINER = os.getenv("ENVIRONMENT", "local") != "local"


def iniciar_browser(
    playwright: Playwright,
    *,
    headless: bool = True,
    slow_mo: int = 0,
) -> Browser:
    """Inicia o Chromium com as opções do ambiente atual."""
    args: list[str] = []
    if EM_CONTAINER:
        args = [
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--disable-gpu",
        ]

    launch_options: dict[str, object] = {
        "headless": headless,
        "slow_mo": slow_mo,
        "args": args,
    }
    executable = os.getenv("CHROMIUM_PATH")
    if executable:
        launch_options["executable_path"] = executable
    return playwright.chromium.launch(**launch_options)
