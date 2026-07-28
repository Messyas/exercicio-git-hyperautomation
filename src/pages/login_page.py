"""Page Object da tela de login."""

from collections.abc import Mapping

from playwright.sync_api import Page


class LoginPage:
    """Centraliza os locators e as ações disponíveis no login."""

    def __init__(self, page: Page) -> None:
        self.page = page
        self.campo_usuario = page.locator("#usuario")
        self.campo_senha = page.locator("#senha")
        self.botao_login = page.get_by_role("button", name="Entrar", exact=True)

    def fazer_login(self, usuario_senha: Mapping[str, str]) -> None:
        """Preenche as credenciais e envia o formulário de login."""
        self.campo_usuario.fill(usuario_senha["usuario"])
        self.campo_senha.fill(usuario_senha["senha"])
        self.botao_login.click()
