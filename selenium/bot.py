"""Entry-point para a automação — executa com `python bot.py`.

Carrega o DataPool (datapool.json), processa cada item via Selenium
e grava resultado.json com o resumo + caminho de cada screenshot.
"""

from __future__ import annotations

import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from web_automation_selenium import (
    cadastrar_item,
    capturar_comprovante,
    configurar_logger,
    registrar_log,
    criar_driver,
)

DATAPOOL_PATH = Path(__file__).resolve().parent / "datapool.json"
EVIDENCIAS_DIR = Path(
    os.environ.get("BOT_EVIDENCIAS_DIR", "/app/evidencias")
)


def carregar_datapool(caminho: Path) -> list[dict]:
    """Lê o DataPool JSON e retorna a lista de itens."""
    with open(caminho, encoding="utf-8") as f:
        dados = json.load(f)
    if not isinstance(dados, list) or len(dados) == 0:
        raise ValueError("DataPool vazio ou formato inválido.")
    return dados


def main() -> None:
    logger = configurar_logger()
    url = os.environ.get("BOT_URL", "http://frontend:3000")
    headless = os.environ.get("BOT_HEADLESS", "true").lower() == "true"

    registrar_log(logger, "BOT_INICIADO", {
        "url": url,
        "datapool": str(DATAPOOL_PATH),
        "evidencias_dir": str(EVIDENCIAS_DIR),
    })

    # ── Carregar DataPool ───────────────────────────────────
    datapool = carregar_datapool(DATAPOOL_PATH)
    registrar_log(logger, "DATAPOOL_CARREGADO", {
        "total_itens": len(datapool),
    })

    EVIDENCIAS_DIR.mkdir(parents=True, exist_ok=True)
    resultados: list[dict] = []

    # ── Iniciar driver ──────────────────────────────────────
    driver = criar_driver(headless=headless)

    try:
        driver.get(url)
        from selenium.webdriver.support.ui import WebDriverWait
        WebDriverWait(driver, 30).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        registrar_log(logger, "PAGINA_CARREGADA", {"url": url})

        # ── Processar cada item do DataPool ─────────────────
        for i, item in enumerate(datapool, start=1):
            lote = item["lote"]
            produto = item["produto"]
            status = item["status"]
            screenshot_nome = item["screenshot"]
            screenshot_path = EVIDENCIAS_DIR / screenshot_nome

            registrar_log(logger, "PROCESSANDO_ITEM", {
                "indice": i,
                "lote": lote,
                "produto": produto,
                "status": status,
            })

            try:
                # Preenche e envia o formulário
                cadastrar_item(driver, lote, produto, status, logger)

                # Captura evidência visual do comprovante
                capturar_comprovante(
                    driver, lote, logger, EVIDENCIAS_DIR, screenshot_nome
                )

                registrar_log(logger, "ITEM_PROCESSADO_COM_SUCESSO", {
                    "lote": lote,
                    "screenshot": str(screenshot_path),
                })

                resultados.append({
                    "indice": i,
                    "lote": lote,
                    "produto": produto,
                    "status": status,
                    "resultado": "SUCESSO",
                    "screenshot": str(screenshot_path),
                })

            except Exception as erro:
                # Screenshot de fallback para divergência
                erro_path = EVIDENCIAS_DIR / f"erro_{lote}.png"
                try:
                    driver.save_screenshot(str(erro_path))
                except Exception:
                    pass

                registrar_log(logger, "ITEM_FALHOU", {
                    "lote": lote,
                    "erro": str(erro),
                    "screenshot_erro": str(erro_path),
                })

                resultados.append({
                    "indice": i,
                    "lote": lote,
                    "produto": produto,
                    "status": status,
                    "resultado": "FALHA",
                    "erro": str(erro),
                    "screenshot_erro": str(erro_path),
                })

    finally:
        driver.quit()

    # ── Salvar resultado.json ───────────────────────────────
    resultado_final = {
        "data_execucao": datetime.now(timezone.utc).isoformat(),
        "url": url,
        "total_itens": len(datapool),
        "sucessos": sum(1 for r in resultados if r["resultado"] == "SUCESSO"),
        "falhas": sum(1 for r in resultados if r["resultado"] == "FALHA"),
        "itens": resultados,
    }

    resultado_path = EVIDENCIAS_DIR / "resultado.json"
    with open(resultado_path, "w", encoding="utf-8") as f:
        json.dump(resultado_final, f, ensure_ascii=False, indent=2)

    registrar_log(logger, "BOT_FINALIZADO", {
        "total": len(datapool),
        "sucessos": resultado_final["sucessos"],
        "falhas": resultado_final["falhas"],
        "resultado_arquivo": str(resultado_path),
    })

    print(f"\n{'='*60}")
    print(f"  Automação finalizada: {resultado_final['sucessos']}/{len(datapool)} itens com sucesso")
    print(f"  Resultado salvo em: {resultado_path}")
    print(f"  Evidências em: {EVIDENCIAS_DIR}")
    print(f"{'='*60}\n")

    # Sair com código 1 se houve falhas
    if resultado_final["falhas"] > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
