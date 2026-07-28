"""Page Object do formulário de cadastro de lotes."""

from playwright.sync_api import (
    Locator,
    Page,
    TimeoutError as PlaywrightTimeoutError,
)


class FormPage:
    """Centraliza os locators, ações e estado visual do formulário."""

    def __init__(self, page: Page) -> None:
        self.page = page
        self.campo_numero_lote = page.locator("#numero")
        self.campo_produto = page.get_by_role("combobox")
        self.grupo_status = page.get_by_role("radiogroup")
        self.botao_enviar = page.get_by_role(
            "button", name="Processar lote", exact=True
        )
        self.mensagem_sucesso = page.get_by_role("status")

    @staticmethod
    def _nomes_compativeis(nome: str) -> list[str]:
        """Considera o texto original e uma variante de codificação legada."""
        nomes = [nome]
        try:
            variante = nome.encode("utf-8").decode("latin-1")
            if variante != nome:
                nomes.append(variante)
        except UnicodeError:
            pass
        return nomes

    def _opcao_produto(self, nome: str) -> Locator:
        return self.page.get_by_role("option", name=nome, exact=True)

    def _opcao_status(self, nome: str) -> Locator:
        return self.grupo_status.get_by_role("radio", name=nome, exact=True)

    def _clicar_opcao(self, tipo: str, nome: str) -> None:
        ultimo_erro: PlaywrightTimeoutError | None = None
        for candidato in self._nomes_compativeis(nome):
            locator = (
                self._opcao_produto(candidato)
                if tipo == "produto"
                else self._opcao_status(candidato)
            )
            try:
                locator.click(timeout=5_000)
                return
            except PlaywrightTimeoutError as erro:
                ultimo_erro = erro
        raise ValueError(f"Não foi encontrada a opção {nome!r} para {tipo}.") from ultimo_erro

    def preencher_lote(self, dados_lote: dict[str, str]) -> None:
        """Preenche e envia o formulário com os dados já validados."""
        self.campo_numero_lote.fill(dados_lote["lote"])
        self.campo_produto.click()
        self._clicar_opcao("produto", dados_lote["produto"])
        self._clicar_opcao("status", dados_lote["status"])
        self.botao_enviar.click()

    def preencher_formulario(self, dados_lote: dict[str, str]) -> None:
        """Nome alternativo solicitado para o preenchimento do formulário."""
        self.preencher_lote(dados_lote)

    def comprovante_sucesso(self, lote: str) -> Locator:
        """Retorna a mensagem final correspondente ao lote processado."""
        return self.mensagem_sucesso.filter(
            has_text=f"Lote {lote} processado com sucesso."
        )

    def is_sucesso(self, lote: str | None = None) -> bool:
        """Informa se a mensagem final está visível."""
        mensagem = self.comprovante_sucesso(lote) if lote else self.mensagem_sucesso
        try:
            mensagem.wait_for(state="visible", timeout=10_000)
            return True
        except PlaywrightTimeoutError:
            return False
