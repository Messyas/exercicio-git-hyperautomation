"""Ponto de entrada do bot Playwright executado pelo Docker Compose."""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path

from main import executar_automacao_web
from web_automation import abrir_pagina


BASE_DIR = Path(__file__).resolve().parent
DATAPOOL_PATH = Path(os.getenv("DATAPOOL_PATH", BASE_DIR / "datapool.json"))
EVIDENCIAS_DIR = Path(os.getenv("EVIDENCIAS_DIR", "evidencias"))


def _booleano(valor: str) -> bool:
    return valor.strip().lower() in {"1", "true", "sim", "yes"}


def configurar_logger() -> logging.Logger:
    logger = logging.getLogger("playwright_bot")
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False
    return logger


def carregar_datapool(caminho: Path) -> list[dict[str, str]]:
    with caminho.open(encoding="utf-8") as arquivo:
        itens = json.load(arquivo)
    if not isinstance(itens, list):
        raise ValueError("O DataPool deve ser uma lista JSON de itens.")
    if not all(isinstance(item, dict) for item in itens):
        raise ValueError("Cada item do DataPool deve ser um objeto JSON.")
    return itens


def main() -> None:
    logger = configurar_logger()
    itens = carregar_datapool(DATAPOOL_PATH)
    resultados = executar_automacao_web(
        itens,
        url=os.getenv("BOT_URL"),
        headless=_booleano(os.getenv("BOT_HEADLESS", "true")),
        evidencias_dir=EVIDENCIAS_DIR,
        logger=logger,
        sessao_navegador=abrir_pagina,
    )
    sucesso = sum(item["resultado"] == "sucesso" for item in resultados)
    saida = {
        "executado_em": datetime.now(timezone.utc).isoformat(),
        "total": len(resultados),
        "sucesso": sucesso,
        "falha": len(resultados) - sucesso,
        "itens": resultados,
    }
    EVIDENCIAS_DIR.mkdir(parents=True, exist_ok=True)
    (EVIDENCIAS_DIR / "resultado.json").write_text(
        json.dumps(saida, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    logger.info("RESULTADO_SALVO arquivo=%s", EVIDENCIAS_DIR / "resultado.json")

    if sucesso != len(resultados):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
