"""Persistência das evidências visuais da automação."""

from pathlib import Path

from playwright.sync_api import Locator, Page


class EvidenceService:
    """Mantém filesystem e screenshots fora dos Page Objects."""

    def __init__(self, page: Page, evidencias_dir: Path) -> None:
        self.page = page
        self.evidencias_dir = evidencias_dir

    def capturar_sucesso(self, comprovante: Locator, nome_arquivo: str) -> Path:
        self.evidencias_dir.mkdir(parents=True, exist_ok=True)
        caminho = self.evidencias_dir / Path(nome_arquivo).name
        comprovante.screenshot(path=str(caminho))
        return caminho

    def capturar_erro(self, lote: str) -> Path:
        self.evidencias_dir.mkdir(parents=True, exist_ok=True)
        caminho = self.evidencias_dir / f"erro_{Path(lote).name}.png"
        self.page.screenshot(path=str(caminho), full_page=True)
        return caminho
