import json
import logging
import os
import random
from datetime import datetime, timezone
from pathlib import Path

from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError, sync_playwright


URL = "https://lote-seven.vercel.app/"
ARTEFATOS_DIR = Path("artefatos")
LOGS_DIR = Path("logs")

PRODUTOS = ["Notebook", "Smartphone", "Monitor", "Teclado", "Mouse"]
STATUS = ["Pendente", "Em processamento", "Concluído"]


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "evento": getattr(record, "evento", record.getMessage()),
            "aplicacao": "automacao-lotes-web",
            "ambiente": os.getenv("ENVIRONMENT", "homologacao"),
            "usuario": getattr(record, "usuario", "teste_qa"),
            "detalhes": getattr(record, "detalhes", {}),
        }
        return json.dumps(log_data, ensure_ascii=False)


def configurar_logger() -> logging.Logger:
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("automacao_lotes")
    logger.setLevel(logging.INFO)
    logger.propagate = False

    if not logger.handlers:
        handler = logging.FileHandler(LOGS_DIR / "automacao.log", encoding="utf-8")
        handler.setFormatter(JsonFormatter())
        logger.addHandler(handler)

    return logger


logger = configurar_logger()


def registrar_log(evento: str, detalhes: dict | None = None, usuario: str = "teste_qa") -> None:
    logger.info(
        evento,
        extra={"evento": evento, "usuario": usuario, "detalhes": detalhes or {}},
    )


def capturar_comprovante(page: Page, lote: str) -> None:
    """Salva o alerta de sucesso, que é o comprovante disponível na página."""
    ARTEFATOS_DIR.mkdir(parents=True, exist_ok=True)
    mensagem = f"Lote {lote} processado com sucesso."
    comprovante = page.get_by_role("status").filter(has_text=mensagem)

    try:
        # A página não expõe .mensagem-sucesso/.comprovante; o alerta usa role=status.
        comprovante.wait_for(state="visible", timeout=10_000)
        caminho = ARTEFATOS_DIR / f"comprovante_{lote}.png"
        comprovante.screenshot(path=str(caminho))
        print(f"✓ Evidência salva: {caminho}")
        registrar_log("COMPROVANTE_SALVO", {"lote": lote, "arquivo": str(caminho)})
    except PlaywrightTimeoutError as erro:
        caminho_erro = ARTEFATOS_DIR / f"erro_timeout_{lote}.png"
        page.screenshot(path=str(caminho_erro), full_page=True)
        registrar_log(
            "TIMEOUT_AO_CARREGAR_COMPROVANTE",
            {"lote": lote, "erro": str(erro), "arquivo": str(caminho_erro)},
        )
        raise


def cadastrar(page: Page, numero: int) -> None:
    lote = f"LT-2026-{numero:04d}"
    produto = PRODUTOS[(numero - 1) % len(PRODUTOS)]
    escolhido = random.choice(STATUS)

    page.get_by_label("Número do lote").fill(lote)

    # O SelectTrigger possui id="produto": abre a lista, sem digitar o valor.
    page.locator("#produto").click()
    page.get_by_role("option", name=produto, exact=True).click()

    # Os status são botões com role="radio", então devem receber click().
    page.get_by_role("radio", name=escolhido, exact=True).click()
    page.get_by_role("button", name="Processar lote", exact=True).click()

    capturar_comprovante(page, lote)
    registrar_log(
        "FORMULARIO_ENVIADO_COM_SUCESSO",
        {"lote": lote, "produto": produto, "status": escolhido},
    )


def main() -> None:
    registrar_log("AUTOMACAO_INICIADA", {"url": URL, "quantidade_lotes": 10})

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=False, slow_mo=300)
        try:
            page = browser.new_page()
            page.goto(URL, wait_until="networkidle")

            for i in range(1, 11):
                cadastrar(page, i)

            print("10 registros realizados.")
            registrar_log("AUTOMACAO_FINALIZADA", {"quantidade_lotes": 10})
            page.wait_for_timeout(3000)
        except Exception as erro:
            registrar_log("AUTOMACAO_FALHOU", {"erro": str(erro)})
            raise
        finally:
            browser.close()


if __name__ == "__main__":
    main()
