from __future__ import annotations

import os
from pathlib import Path

import pytest

from src.pages import PlaywrightFormularioLotesPage


@pytest.fixture
def pagina_web() -> str:
    """Retorna a URL usada nos testes E2E."""
    return os.getenv("E2E_BASE_URL", "http://127.0.0.1:3000")


@pytest.fixture
def pagina_html() -> str:
    """Mantém o nome de fixture usado no exercício 19-X."""
    return (Path(__file__).parents[1] / "web" / "lote-teste.html").as_uri()


@pytest.fixture
def formulario_page(page, pagina_html: str) -> PlaywrightFormularioLotesPage:
    po = PlaywrightFormularioLotesPage(
        page=page,
        pagina_html=pagina_html,
        credenciais={"usuario": "automacao", "senha": "automacao"},
    )
    po.abrir()
    return po


@pytest.fixture
def e2e_screenshot_dir() -> Path:
    path = Path(__file__).parent / "e2e" / "screenshots"
    path.mkdir(parents=True, exist_ok=True)
    return path
