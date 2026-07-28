"""Orquestra DataPool, regras, logs e evidências fora dos Page Objects."""

from __future__ import annotations

import json
import logging
import os
import re
from collections.abc import Callable, Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, ContextManager, Protocol
from urllib.parse import urlsplit


DEFAULT_URL = "http://frontend:3000"
ALLOWED_HOSTS = {"frontend", "localhost", "127.0.0.1"}
REQUIRED_FIELDS = ("lote", "produto", "status", "screenshot")
VALID_PRODUCTS = {
    "Chapa de Aço 1020",
    "Perfil de Alumínio",
    "Tubo Galvanizado",
    "Bobina Laminada",
    "Barra Trefilada",
    "Fio de Cobre",
}
VALID_STATUSES = {"Pendente", "Em processamento", "Concluído"}


class WebAutomation(Protocol):
    """Contrato mínimo compartilhado pelas duas tecnologias."""

    def login(self, credentials: Mapping[str, str]) -> None: ...

    def process(self, item: Mapping[str, str]) -> None: ...

    def capture_success(self, lote: str, path: Path) -> None: ...

    def capture_error(self, path: Path) -> None: ...


AutomationFactory = Callable[
    [str, bool], ContextManager[WebAutomation]
]


def _as_bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "sim", "yes"}


def _safe_name(value: str) -> str:
    return re.sub(r"[^\w.-]+", "_", Path(value).name, flags=re.UNICODE)


def _validate_target(url: str) -> None:
    host = urlsplit(url).hostname
    if host not in ALLOWED_HOSTS:
        raise ValueError(
            f"Destino {host!r} não permitido. Use somente o ambiente local."
        )


def _validate_item(item: Mapping[str, Any], seen_lotes: set[str]) -> None:
    missing = [
        field
        for field in REQUIRED_FIELDS
        if not isinstance(item.get(field), str) or not item[field].strip()
    ]
    if missing:
        raise ValueError(
            "Campos obrigatórios ausentes ou inválidos: "
            + ", ".join(missing)
        )

    lote = str(item["lote"])
    if lote in seen_lotes:
        raise ValueError(f"Lote duplicado no DataPool: {lote}.")
    if item["produto"] not in VALID_PRODUCTS:
        raise ValueError(f"Produto inválido: {item['produto']}.")
    if item["status"] not in VALID_STATUSES:
        raise ValueError(f"Status inválido: {item['status']}.")
    if Path(str(item["screenshot"])).suffix.lower() != ".png":
        raise ValueError("O campo screenshot deve indicar um arquivo PNG.")

    seen_lotes.add(lote)


def load_datapool(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8") as file:
        data = json.load(file)
    if not isinstance(data, list) or not data:
        raise ValueError("O DataPool deve ser uma lista JSON não vazia.")
    if not all(isinstance(item, dict) for item in data):
        raise ValueError("Cada item do DataPool deve ser um objeto JSON.")
    return data


def configure_logger(framework: str, logs_root: Path) -> logging.Logger:
    log_dir = logs_root / framework
    log_dir.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger(f"bot_{framework}")
    logger.handlers.clear()
    logger.setLevel(logging.INFO)
    logger.propagate = False

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s"
    )
    console = logging.StreamHandler()
    console.setFormatter(formatter)
    file_handler = logging.FileHandler(
        log_dir / "execucao.log", mode="w", encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(console)
    logger.addHandler(file_handler)
    return logger


def _run_items(
    items: list[dict[str, str]],
    *,
    url: str,
    headless: bool,
    evidence_dir: Path,
    logger: logging.Logger,
    automation_factory: AutomationFactory,
) -> list[dict[str, Any]]:
    credentials = {
        "usuario": os.getenv("BOT_USUARIO", "automacao"),
        "senha": os.getenv("BOT_SENHA", "automacao"),
    }
    results: list[dict[str, Any]] = []
    seen_lotes: set[str] = set()

    with automation_factory(url, headless) as automation:
        automation.login(credentials)
        logger.info("LOGIN_REALIZADO_COM_SUCESSO")

        for index, item in enumerate(items, start=1):
            lote = str(item.get("lote", f"item-{index}"))
            logger.info(
                "INTERACAO_WEB_INICIADA indice=%d lote=%s",
                index,
                lote,
            )
            try:
                _validate_item(item, seen_lotes)
                automation.process(item)
                logger.info("FORMULARIO_ENVIADO lote=%s", lote)

                evidence_path = evidence_dir / _safe_name(
                    item["screenshot"]
                )
                automation.capture_success(lote, evidence_path)
                logger.info(
                    "MENSAGEM_VALIDADA_E_EVIDENCIA_GERADA "
                    "lote=%s evidencia=%s",
                    lote,
                    evidence_path,
                )
                results.append(
                    {
                        "indice": index,
                        **item,
                        "resultado": "SUCESSO",
                        "evidencia": str(evidence_path),
                    }
                )
            except Exception as error:
                error_path = evidence_dir / (
                    f"erro_{_safe_name(lote)}.png"
                )
                try:
                    automation.capture_error(error_path)
                except Exception:
                    logger.exception(
                        "FALHA_AO_GERAR_EVIDENCIA_DE_ERRO lote=%s",
                        lote,
                    )
                logger.exception(
                    "DIVERGENCIA_REGISTRADA lote=%s erro=%s "
                    "evidencia=%s",
                    lote,
                    error,
                    error_path,
                )
                results.append(
                    {
                        "indice": index,
                        **item,
                        "resultado": "FALHA",
                        "erro": str(error),
                        "evidencia": str(error_path),
                    }
                )

    return results


def run_bot(
    framework: str,
    datapool_path: Path,
    automation_factory: AutomationFactory,
) -> int:
    """Executa um bot, persiste seu resultado e devolve o código de saída."""
    framework_dir = framework.lower()
    url = os.getenv("BOT_URL", DEFAULT_URL)
    evidence_dir = (
        Path(os.getenv("EVIDENCIAS_ROOT", "evidencias")) / framework_dir
    )
    logs_root = Path(os.getenv("LOGS_ROOT", "logs"))
    logger = configure_logger(framework_dir, logs_root)
    evidence_dir.mkdir(parents=True, exist_ok=True)

    logger.info(
        "BOT_INICIADO ferramenta=%s url=%s datapool=%s",
        framework,
        url,
        datapool_path,
    )
    try:
        _validate_target(url)
        items = load_datapool(datapool_path)
        logger.info("DATAPOOL_CARREGADO total_itens=%d", len(items))
        results = _run_items(
            items,
            url=url,
            headless=_as_bool(os.getenv("BOT_HEADLESS", "true")),
            evidence_dir=evidence_dir,
            logger=logger,
            automation_factory=automation_factory,
        )
    except Exception as error:
        logger.exception("BOT_FALHOU erro=%s", error)
        return 1

    success_count = sum(
        result["resultado"] == "SUCESSO" for result in results
    )
    summary = {
        "ferramenta": framework,
        "executado_em": datetime.now(timezone.utc).isoformat(),
        "url": url,
        "total": len(results),
        "sucessos": success_count,
        "falhas": len(results) - success_count,
        "itens": results,
    }
    result_path = evidence_dir / "resultado.json"
    result_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    logger.info(
        "BOT_FINALIZADO sucessos=%d falhas=%d resultado=%s",
        summary["sucessos"],
        summary["falhas"],
        result_path,
    )
    return 0 if summary["falhas"] == 0 else 1
