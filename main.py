"""Orquestrador do fluxo Playwright baseado em Page Object Model."""

from __future__ import annotations

import logging
import os
from collections.abc import Callable
from pathlib import Path
from typing import Any

from src.pages.form_page import FormPage
from src.pages.login_page import LoginPage
from src.services.evidence_service import EvidenceService


CAMPOS_OBRIGATORIOS = ("lote", "produto", "status", "screenshot")


def _validar_item(item: dict[str, str]) -> None:
    """Mantém a regra de entrada fora dos Page Objects."""
    ausentes = [campo for campo in CAMPOS_OBRIGATORIOS if not item.get(campo)]
    if ausentes:
        raise ValueError(
            f"Item do DataPool sem campo(s) obrigatório(s): {', '.join(ausentes)}"
        )


def executar_automacao_web(
    itens: list[dict[str, str]],
    *,
    url: str | None = None,
    headless: bool = True,
    evidencias_dir: Path = Path("evidencias"),
    logger: logging.Logger,
    sessao_navegador: Callable[..., Any],
) -> list[dict[str, Any]]:
    """Executa login, cadastro e geração de evidências por meio dos Page Objects."""
    logger.info(
        "AUTOMACAO_WEB_INICIADA url=%s quantidade_lotes=%d",
        url or "http://frontend:3000",
        len(itens),
    )
    resultados: list[dict[str, Any]] = []

    with sessao_navegador(url, headless=headless) as page:
        login_page = LoginPage(page)
        form_page = FormPage(page)
        evidence_service = EvidenceService(page, evidencias_dir)

        login_page.fazer_login(
            {
                "usuario": os.getenv("BOT_USUARIO", "automacao"),
                "senha": os.getenv("BOT_SENHA", "automacao"),
            }
        )
        logger.info("LOGIN_REALIZADO_COM_SUCESSO")

        for item in itens:
            lote = item.get("lote", "desconhecido")
            try:
                _validar_item(item)
                form_page.preencher_lote(item)
                if not form_page.is_sucesso(lote):
                    raise TimeoutError(f"Comprovante não exibido para {lote}.")

                evidencia = evidence_service.capturar_sucesso(
                    form_page.comprovante_sucesso(lote),
                    item["screenshot"],
                )
                logger.info(
                    "LOTE_PROCESSADO_COM_SUCESSO lote=%s evidencia=%s",
                    lote,
                    evidencia,
                )
                resultados.append(
                    {
                        **item,
                        "resultado": "sucesso",
                        "evidencia": str(evidencia),
                    }
                )
            except Exception as erro:
                erro_path = evidence_service.capturar_erro(lote)
                logger.exception("ITEM_FALHOU lote=%s erro=%s", lote, erro)
                resultados.append(
                    {
                        **item,
                        "resultado": "falha",
                        "erro": str(erro),
                        "evidencia": str(erro_path),
                    }
                )

    logger.info(
        "AUTOMACAO_WEB_FINALIZADA sucessos=%d falhas=%d",
        sum(item["resultado"] == "sucesso" for item in resultados),
        sum(item["resultado"] == "falha" for item in resultados),
    )
    return resultados
