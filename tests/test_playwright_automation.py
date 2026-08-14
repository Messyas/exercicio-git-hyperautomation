from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

import src.web_automation as browser_module
from producer import _evidence_fields


pytestmark = pytest.mark.unit


class FakeChromium:
    def __init__(self) -> None:
        self.options: dict[str, object] | None = None

    def launch(self, **options):
        self.options = options
        return "browser"


def test_iniciar_browser_local_sem_flags(monkeypatch) -> None:
    chromium = FakeChromium()
    monkeypatch.setattr(browser_module, "EM_CONTAINER", False)
    monkeypatch.delenv("CHROMIUM_PATH", raising=False)

    browser = browser_module.iniciar_browser(
        SimpleNamespace(chromium=chromium),
        headless=False,
        slow_mo=25,
    )

    assert browser == "browser"
    assert chromium.options == {
        "headless": False,
        "slow_mo": 25,
        "args": [],
    }


def test_iniciar_browser_container_com_flags(monkeypatch) -> None:
    chromium = FakeChromium()
    monkeypatch.setattr(browser_module, "EM_CONTAINER", True)
    monkeypatch.setenv("CHROMIUM_PATH", "/usr/bin/chromium")

    browser_module.iniciar_browser(SimpleNamespace(chromium=chromium))

    assert chromium.options == {
        "headless": True,
        "slow_mo": 0,
        "args": [
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--disable-gpu",
        ],
        "executable_path": "/usr/bin/chromium",
    }


def test_evidence_fields_inclui_nome_e_caminho_completo(tmp_path: Path) -> None:
    path = tmp_path / "screenshots" / "evidencia.png"

    fields = _evidence_fields(path)

    assert fields["evidence_name"] == "evidencia.png"
    assert fields["evidence_path"] == path.resolve().as_posix()
