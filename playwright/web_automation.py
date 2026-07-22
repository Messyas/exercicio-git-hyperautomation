"""Automacao web do cadastro de lotes com Playwright."""

from __future__ import annotations

import logging
import random
from pathlib import Path
from typing import Any

from playwright.sync_api import (
    Page,
    TimeoutError as PlaywrightTimeoutError,
    sync_playwright,
)

from config import Settings, get_settings
from src.maestro_client import configure_local_logging


DEFAULT_URL = "https://lote-seven.vercel.app/"
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
    """Usa o mesmo logger estruturado do fluxo principal."""
    settings = get_settings()
    return configure_local_logging(
        settings.log_dir,
        execution_id=settings.execution_id,
        bot_id=settings.bot_id,
    )


def registrar_log(
    logger: logging.Logger,
    evento: str,
    detalhes: dict[str, Any] | None = None,
) -> None:
    """Registra o evento no logger que injeta execution_id e bot_id."""
    logger.info("%s | detalhes=%s", evento, detalhes or {})


def capturar_comprovante(
    page: Page,
    lote: str,
    logger: logging.Logger,
    artefatos_dir: Path,
) -> None:
    """Salva o alerta de sucesso como evidencia da execucao."""
    artefatos_dir.mkdir(parents=True, exist_ok=True)
    mensagem = f"Lote {lote} processado com sucesso."
    comprovante = page.get_by_role("status").filter(has_text=mensagem)

    try:
        comprovante.wait_for(state="visible", timeout=10_000)
        caminho = artefatos_dir / f"comprovante_{lote}.png"
        comprovante.screenshot(path=str(caminho))
        print(f"Evidencia salva: {caminho}")
        registrar_log(logger, "COMPROVANTE_SALVO", {
            "lote": lote,
            "arquivo": str(caminho),
        })
    except PlaywrightTimeoutError as erro:
        caminho_erro = artefatos_dir / f"erro_timeout_{lote}.png"
        page.screenshot(path=str(caminho_erro), full_page=True)
        registrar_log(logger, "TIMEOUT_AO_CARREGAR_COMPROVANTE", {
            "lote": lote,
            "erro": str(erro),
            "arquivo": str(caminho_erro),
        })
        raise


def selecionar_produto(page: Page, produto: str) -> None:
    """Seleciona o produto em um select nativo ou combobox customizado."""
    combobox = page.get_by_role("combobox")
    tag_name = combobox.evaluate("element => element.tagName")

    if tag_name == "SELECT":
        combobox.select_option(label=produto)
        return

    combobox.click()
    page.get_by_role("option", name=produto, exact=True).click()


def cadastrar(
    page: Page,
    numero: int,
    logger: logging.Logger,
    artefatos_dir: Path,
) -> None:
    lote = f"LT-2026-{numero:04d}"
    produto = PRODUTOS[(numero - 1) % len(PRODUTOS)]
    escolhido = random.choice(STATUS)

    page.get_by_label("Número do lote", exact=True).fill(lote)
    selecionar_produto(page, produto)
    page.get_by_role("radio", name=escolhido, exact=True).click()
    page.get_by_role("button", name="Processar lote", exact=True).click()

    capturar_comprovante(page, lote, logger, artefatos_dir)
    registrar_log(logger, "FORMULARIO_ENVIADO_COM_SUCESSO", {
        "lote": lote,
        "produto": produto,
        "status": escolhido,
    })


def executar_automacao_web(
    *,
    settings: Settings | None = None,
    logger: logging.Logger | None = None,
    url: str | None = None,
    quantidade: int | None = None,
    headless: bool | None = None,
    slow_mo: int | None = None,
) -> dict[str, Any]:
    """Executa o cadastro web e retorna um resumo serializavel."""
    settings = settings or get_settings()
    logger = logger or configurar_logger()
    url = url or settings.playwright_url or DEFAULT_URL
    quantidade = quantidade if quantidade is not None else settings.playwright_quantity
    headless = headless if headless is not None else settings.playwright_headless
    slow_mo = slow_mo if slow_mo is not None else settings.playwright_slow_mo

    registrar_log(logger, "AUTOMACAO_WEB_INICIADA", {
        "url": url,
        "quantidade_lotes": quantidade,
    })

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=headless,
            slow_mo=slow_mo,
        )
        try:
            page = browser.new_page()
            page.goto(url, wait_until="networkidle")

            for numero in range(1, quantidade + 1):
                cadastrar(
                    page,
                    numero,
                    logger,
                    settings.playwright_artifacts_dir,
                )

            registrar_log(logger, "AUTOMACAO_WEB_FINALIZADA", {
                "quantidade_lotes": quantidade,
            })
            print(f"{quantidade} registro(s) realizado(s) com Playwright.")
            return {
                "status_execucao": "SUCESSO",
                "url": url,
                "total_registros": quantidade,
            }
        except Exception as erro:
            registrar_log(logger, "AUTOMACAO_WEB_FALHOU", {
                "erro": str(erro),
            })
            raise
        finally:
            browser.close()


def main() -> None:
    executar_automacao_web()


if __name__ == "__main__":
    main()
