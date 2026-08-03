"""Page Objects semânticos para o sistema local de cadastro de lotes."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from playwright.sync_api import Locator, Page


class RegistrationRejectedError(ValueError):
    """O formulário recusou os dados antes de efetivar o cadastro."""


class PlaywrightLoginPage:
    """Ações e locators da tela de login."""

    def __init__(self, page: Page) -> None:
        self._usuario = page.get_by_label("Usuário", exact=True)
        self._senha = page.get_by_label("Senha", exact=True)
        self._entrar = page.get_by_role("button", name="Entrar", exact=True)
        self._titulo = page.get_by_role(
            "heading", name="Cadastro de Lotes", exact=True
        )

    def entrar(
        self,
        credenciais: Mapping[str, str],
        *,
        timeout_ms: int,
    ) -> None:
        self._usuario.fill(credenciais["usuario"])
        self._senha.fill(credenciais["senha"])
        self._entrar.click()
        self._titulo.wait_for(state="visible", timeout=timeout_ms)


class PlaywrightFormPage:
    """Ações e locators semânticos do cadastro de lotes."""

    def __init__(self, page: Page) -> None:
        self._page = page
        self._numero = page.get_by_label("Número do lote", exact=True)
        self._produto = page.get_by_label("Produto", exact=True)
        self._status = page.get_by_label("Status", exact=True)
        self._processar = page.get_by_role(
            "button", name="Processar lote", exact=True
        )
        self._formulario = page.get_by_role(
            "form", name="Formulário de cadastro de lote", exact=True
        )
        self._rejeicoes = page.get_by_role("alert")

    @property
    def page(self) -> Page:
        return self._page

    @property
    def campo_lote(self) -> Locator:
        return self._numero

    @property
    def campo_produto(self) -> Locator:
        return self._produto

    def preencher_lote(self, valor: str) -> None:
        self._numero.fill(valor)

    def selecionar_produto(self, valor: str) -> None:
        self._produto.select_option(valor)

    def selecionar_status(self, valor: str) -> None:
        self._status.select_option(valor)

    def obter_status_selecionado(self) -> str:
        return self._status.input_value()

    def submeter(self) -> None:
        self._processar.click()

    def mensagem_sucesso_visivel(self) -> bool:
        return self._page.get_by_role("status").is_visible()

    def capturar_evidencia(self, caminho: str | Path) -> None:
        path = Path(caminho)
        path.parent.mkdir(parents=True, exist_ok=True)
        self._page.screenshot(path=str(path), full_page=True)

    def preencher_e_enviar(self, item: Mapping[str, str]) -> None:
        self.preencher_lote(item["lote_id"])
        self.selecionar_produto(item["produto"])
        self.selecionar_status(item["status"])
        self.submeter()
        mensagens = [
            texto.strip()
            for texto in self._rejeicoes.all_inner_texts()
            if texto.strip()
        ]
        if mensagens:
            raise RegistrationRejectedError(" | ".join(mensagens))

    def comprovante(self, lote_id: str) -> Locator:
        mensagem = f"Lote {lote_id} processado com sucesso."
        return self._page.get_by_role("status").filter(has_text=mensagem)

    def capturar_comprovante(
        self,
        lote_id: str,
        path: Path,
        *,
        timeout_ms: int,
    ) -> None:
        comprovante = self.comprovante(lote_id)
        comprovante.wait_for(state="visible", timeout=timeout_ms)
        path.parent.mkdir(parents=True, exist_ok=True)
        comprovante.screenshot(path=str(path))

    def capturar_erro(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self._page.screenshot(path=str(path), full_page=True)

    def capturar_rejeicao(self, path: Path) -> None:
        """Registra somente o formulário e suas mensagens de validação."""
        path.parent.mkdir(parents=True, exist_ok=True)
        self._formulario.screenshot(path=str(path))
