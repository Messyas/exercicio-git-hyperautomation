"""Page Objects da interface usados pela automação Playwright."""

from __future__ import annotations

from collections.abc import Mapping

from playwright.sync_api import Locator, Page, expect


class PlaywrightLoginPage:
    """Centraliza locators e ações da tela de login."""

    def __init__(self, page: Page) -> None:
        self._page = page
        self._usuario = page.locator("#usuario")
        self._senha = page.locator("#senha")
        self._entrar = page.get_by_role("button", name="Entrar", exact=True)
        self._titulo_sistema = page.get_by_role(
            "heading", name="Cadastro de Lotes", exact=True
        )

    def entrar(self, credenciais: Mapping[str, str]) -> None:
        expect(self._usuario).to_be_visible()
        self._usuario.fill(credenciais["usuario"])
        self._senha.fill(credenciais["senha"])
        self._entrar.click()
        expect(self._titulo_sistema).to_be_visible()


class PlaywrightFormPage:
    """Centraliza locators e ações do cadastro de lotes."""

    def __init__(self, page: Page) -> None:
        self._page = page
        self._numero = page.locator("#numero")
        self._produto = page.get_by_role("combobox")
        self._status = page.get_by_role("radiogroup")
        self._processar = page.get_by_role(
            "button", name="Processar lote", exact=True
        )

    def preencher_e_enviar(self, item: Mapping[str, str]) -> None:
        self._numero.fill(item["lote"])
        self._produto.click()
        self._page.get_by_role(
            "option", name=item["produto"], exact=True
        ).click()
        self._status.get_by_role(
            "radio", name=item["status"], exact=True
        ).click()
        self._processar.click()

    def comprovante(self, lote: str) -> Locator:
        mensagem = f"Lote {lote} processado com sucesso."
        comprovante = self._page.get_by_role("status").filter(
            has_text=mensagem
        )
        expect(comprovante).to_be_visible(timeout=10_000)
        return comprovante
