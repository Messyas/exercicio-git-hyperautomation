"""Automacao independente para cadastrar lotes usando Selenium."""

from __future__ import annotations

import argparse
import logging
import random
import time
from pathlib import Path
from typing import Any

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.ui import WebDriverWait


DEFAULT_URL = "https://lote-seven.vercel.app/"
DEFAULT_QUANTIDADE = 10
DEFAULT_SLOW_MO_MS = 300
DEFAULT_ARTIFACTS_DIR = Path(__file__).resolve().parent / "artefatos"
TIMEOUT_SECONDS = 10
PRODUTOS = [
    "Chapa de Aço 1020",
    "Perfil de Alumínio",
    "Tubo Galvanizado",
    "Bobina Laminada",
    "Barra Trefilada",
    "Fio de Cobre",
]
STATUS = ["Pendente", "Em processamento", "Concluído"]


def configurar_logger() -> logging.Logger:
    """Cria o logger local, sem depender de outro projeto ou bot."""
    logger = logging.getLogger("automacao_selenium")
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
        )
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False
    return logger


def registrar_log(
    logger: logging.Logger,
    evento: str,
    detalhes: dict[str, Any] | None = None,
) -> None:
    """Registra eventos da automação no console."""
    logger.info("%s | detalhes=%s", evento, detalhes or {})


def _xpath_literal(valor: str) -> str:
    """Retorna uma string segura para uso como literal em XPath."""
    if "'" not in valor:
        return f"'{valor}'"
    if '"' not in valor:
        return f'"{valor}"'
    partes = valor.split("'")
    return "concat(" + ", \"'\", ".join(f"'{parte}'" for parte in partes) + ")"


def _esperar_elemento(
    driver: webdriver.Chrome,
    locator: tuple[str, str],
) -> Any:
    return WebDriverWait(driver, TIMEOUT_SECONDS).until(
        EC.visibility_of_element_located(locator)
    )


def capturar_comprovante(
    driver: webdriver.Chrome,
    lote: str,
    logger: logging.Logger,
    artefatos_dir: Path,
) -> None:
    """Salva o alerta de sucesso como evidência da execução."""
    artefatos_dir.mkdir(parents=True, exist_ok=True)
    mensagem = f"Lote {lote} processado com sucesso."

    try:
        comprovante = _esperar_elemento(
            driver,
            (By.XPATH, f"//*[@role='status' and contains(., {_xpath_literal(mensagem)})]"),
        )
        caminho = artefatos_dir / f"comprovante_{lote}.png"
        comprovante.screenshot(str(caminho))
        print(f"Evidência salva: {caminho}")
        registrar_log(logger, "COMPROVANTE_SALVO", {
            "lote": lote,
            "arquivo": str(caminho),
        })
    except TimeoutException as erro:
        caminho_erro = artefatos_dir / f"erro_timeout_{lote}.png"
        driver.save_screenshot(str(caminho_erro))
        registrar_log(logger, "TIMEOUT_AO_CARREGAR_COMPROVANTE", {
            "lote": lote,
            "erro": str(erro),
            "arquivo": str(caminho_erro),
        })
        raise


def selecionar_produto(driver: webdriver.Chrome, produto: str) -> None:
    """Seleciona o produto em um select nativo ou combobox customizado."""
    combobox = _esperar_elemento(
        driver,
        (By.CSS_SELECTOR, "select, [role='combobox']"),
    )

    if combobox.tag_name.lower() == "select":
        Select(combobox).select_by_visible_text(produto)
        return

    combobox.click()
    opcao = _esperar_elemento(
        driver,
        (By.XPATH, f"//*[@role='option' and normalize-space()={_xpath_literal(produto)}]"),
    )
    opcao.click()


def cadastrar(
    driver: webdriver.Chrome,
    numero: int,
    logger: logging.Logger,
    artefatos_dir: Path,
) -> None:
    """Preenche e envia um lote."""
    lote = f"LT-2026-{numero:04d}"
    produto = PRODUTOS[(numero - 1) % len(PRODUTOS)]
    escolhido = random.choice(STATUS)

    campo_lote = _esperar_elemento(
        driver,
        (By.XPATH, "//label[normalize-space()='Número do lote']/following::input[1]"),
    )
    campo_lote.clear()
    campo_lote.send_keys(lote)
    selecionar_produto(driver, produto)

    status = _esperar_elemento(
        driver,
        (By.XPATH, f"//label[normalize-space()={_xpath_literal(escolhido)}]"),
    )
    status.click()
    botao = WebDriverWait(driver, TIMEOUT_SECONDS).until(
        EC.element_to_be_clickable(
            (By.XPATH, "//button[normalize-space()='Processar lote']")
        )
    )
    botao.click()

    capturar_comprovante(driver, lote, logger, artefatos_dir)
    registrar_log(logger, "FORMULARIO_ENVIADO_COM_SUCESSO", {
        "lote": lote,
        "produto": produto,
        "status": escolhido,
    })


def _criar_driver(*, headless: bool) -> webdriver.Chrome:
    """Cria um Chrome controlado pelo Selenium Manager."""
    options = Options()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--window-size=1440,1200")
    return webdriver.Chrome(options=options)


def executar_automacao_web(
    *,
    url: str = DEFAULT_URL,
    quantidade: int = DEFAULT_QUANTIDADE,
    headless: bool = False,
    slow_mo: int = DEFAULT_SLOW_MO_MS,
    artefatos_dir: Path | str = DEFAULT_ARTIFACTS_DIR,
    logger: logging.Logger | None = None,
) -> dict[str, Any]:
    """Executa o cadastro web e retorna um resumo serializável."""
    if quantidade < 1:
        raise ValueError("A quantidade de lotes deve ser maior que zero.")
    if slow_mo < 0:
        raise ValueError("O intervalo entre lotes não pode ser negativo.")

    logger = logger or configurar_logger()
    diretorio_artefatos = Path(artefatos_dir)
    registrar_log(logger, "AUTOMACAO_WEB_INICIADA", {
        "url": url,
        "quantidade_lotes": quantidade,
    })

    driver = _criar_driver(headless=headless)
    try:
        driver.get(url)
        WebDriverWait(driver, TIMEOUT_SECONDS).until(
            lambda navegador: navegador.execute_script("return document.readyState") == "complete"
        )

        for numero in range(1, quantidade + 1):
            cadastrar(driver, numero, logger, diretorio_artefatos)
            if slow_mo:
                time.sleep(slow_mo / 1000)

        registrar_log(logger, "AUTOMACAO_WEB_FINALIZADA", {
            "quantidade_lotes": quantidade,
        })
        print(f"{quantidade} registro(s) realizado(s) com Selenium.")
        return {
            "status_execucao": "SUCESSO",
            "url": url,
            "total_registros": quantidade,
        }
    except Exception as erro:
        registrar_log(logger, "AUTOMACAO_WEB_FALHOU", {"erro": str(erro)})
        raise
    finally:
        driver.quit()


def main() -> None:
    parser = argparse.ArgumentParser(description="Cadastro de lotes com Selenium.")
    parser.add_argument("--url", default=DEFAULT_URL)
    parser.add_argument("--quantidade", type=int, default=DEFAULT_QUANTIDADE)
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--slow-mo", type=int, default=DEFAULT_SLOW_MO_MS)
    parser.add_argument("--artefatos-dir", type=Path, default=DEFAULT_ARTIFACTS_DIR)
    argumentos = parser.parse_args()

    executar_automacao_web(
        url=argumentos.url,
        quantidade=argumentos.quantidade,
        headless=argumentos.headless,
        slow_mo=argumentos.slow_mo,
        artefatos_dir=argumentos.artefatos_dir,
    )


if __name__ == "__main__":
    main()
