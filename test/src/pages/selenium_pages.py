"""Page Objects da interface usados pela automação Selenium."""

from __future__ import annotations

from collections.abc import Mapping

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


TIMEOUT_SECONDS = 10


def _xpath_literal(value: str) -> str:
    if "'" not in value:
        return f"'{value}'"
    if '"' not in value:
        return f'"{value}"'
    parts = value.split("'")
    return "concat(" + ", \"'\", ".join(f"'{part}'" for part in parts) + ")"


class SeleniumLoginPage:
    """Centraliza locators e ações da tela de login."""

    USUARIO = (By.ID, "usuario")
    SENHA = (By.ID, "senha")
    ENTRAR = (By.XPATH, "//button[normalize-space()='Entrar']")
    TITULO_SISTEMA = (
        By.XPATH,
        "//h1[normalize-space()='Cadastro de Lotes']",
    )

    def __init__(self, driver: WebDriver) -> None:
        self._driver = driver
        self._wait = WebDriverWait(driver, TIMEOUT_SECONDS)

    def entrar(self, credenciais: Mapping[str, str]) -> None:
        usuario = self._wait.until(
            EC.visibility_of_element_located(self.USUARIO)
        )
        senha = self._wait.until(EC.visibility_of_element_located(self.SENHA))
        usuario.send_keys(credenciais["usuario"])
        senha.send_keys(credenciais["senha"])
        self._wait.until(EC.element_to_be_clickable(self.ENTRAR)).click()
        self._wait.until(
            EC.visibility_of_element_located(self.TITULO_SISTEMA)
        )


class SeleniumFormPage:
    """Centraliza locators e ações do cadastro de lotes."""

    NUMERO = (By.ID, "numero")
    PRODUTO = (By.CSS_SELECTOR, "[role='combobox']")
    STATUS_GROUP = (By.CSS_SELECTOR, "[role='radiogroup']")
    PROCESSAR = (
        By.XPATH,
        "//button[normalize-space()='Processar lote']",
    )

    def __init__(self, driver: WebDriver) -> None:
        self._driver = driver
        self._wait = WebDriverWait(driver, TIMEOUT_SECONDS)

    @staticmethod
    def _opcao_produto(nome: str) -> tuple[str, str]:
        return (
            By.XPATH,
            "//*[@role='option' and normalize-space()="
            f"{_xpath_literal(nome)}]",
        )

    @staticmethod
    def _opcao_status(nome: str) -> tuple[str, str]:
        return (
            By.XPATH,
            "//*[@role='radio' and normalize-space()="
            f"{_xpath_literal(nome)}]",
        )

    @staticmethod
    def _mensagem_sucesso(lote: str) -> tuple[str, str]:
        mensagem = f"Lote {lote} processado com sucesso."
        return (
            By.XPATH,
            "//*[@role='status' and contains(normalize-space(.), "
            f"{_xpath_literal(mensagem)})]",
        )

    def preencher_e_enviar(self, item: Mapping[str, str]) -> None:
        numero = self._wait.until(
            EC.visibility_of_element_located(self.NUMERO)
        )
        numero.clear()
        numero.send_keys(item["lote"])

        self._wait.until(EC.element_to_be_clickable(self.PRODUTO)).click()
        self._wait.until(
            EC.element_to_be_clickable(
                self._opcao_produto(item["produto"])
            )
        ).click()
        self._wait.until(
            EC.element_to_be_clickable(self._opcao_status(item["status"]))
        ).click()
        self._wait.until(EC.element_to_be_clickable(self.PROCESSAR)).click()

    def comprovante(self, lote: str) -> WebElement:
        return self._wait.until(
            EC.visibility_of_element_located(
                self._mensagem_sucesso(lote)
            )
        )
