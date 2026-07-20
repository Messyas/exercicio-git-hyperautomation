"""Configuração central do bot.

As configurações de execução ficam no ``.env`` local e não devem ser
codificadas nos módulos de negócio. O arquivo ``.env.example`` documenta as
variáveis esperadas sem conter segredos reais.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parent
load_dotenv(PROJECT_ROOT / ".env", override=False)


def _env_path(name: str, default: str) -> Path:
    """Lê um caminho do ambiente e resolve caminhos relativos no projeto."""
    valor = os.getenv(name, default).strip()
    caminho = Path(valor).expanduser()
    return caminho if caminho.is_absolute() else PROJECT_ROOT / caminho


def _env_bool(name: str, default: bool = False) -> bool:
    """Converte uma flag do ambiente para booleano de forma explícita."""
    valor = os.getenv(name)
    if valor is None or not valor.strip():
        return default

    normalizado = valor.strip().lower()
    if normalizado in {"1", "true", "yes", "sim", "on"}:
        return True
    if normalizado in {"0", "false", "no", "nao", "não", "off"}:
        return False
    raise ValueError(
        f"A variável {name} deve conter true/false (valor recebido: {valor!r})."
    )


@dataclass(frozen=True)
class Settings:
    """Configurações usadas pelas etapas atuais e futuras do bot."""

    project_root: Path
    input_dir: Path
    output_dir: Path
    log_dir: Path
    default_input_file: Path
    maestro_enabled: bool
    maestro_server: str | None
    maestro_login: str | None
    maestro_key: str | None
    maestro_task_id: str | None
    maestro_activity_label: str
    execution_report_file: Path


def get_settings() -> Settings:
    """Monta as configurações a partir das variáveis de ambiente."""
    return Settings(
        project_root=PROJECT_ROOT,
        input_dir=_env_path("BOT_INPUT_DIR", "dados_entrada"),
        output_dir=_env_path("BOT_OUTPUT_DIR", "data/output"),
        log_dir=_env_path("BOT_LOG_DIR", "logs"),
        default_input_file=_env_path(
            "BOT_INPUT_FILE", "data/samples/inspecao_lotes_dia.xlsx"
        ),
        maestro_enabled=_env_bool("MAESTRO_ENABLED"),
        maestro_server=os.getenv("MAESTRO_SERVER") or None,
        maestro_login=os.getenv("MAESTRO_LOGIN") or None,
        maestro_key=os.getenv("MAESTRO_KEY") or None,
        maestro_task_id=os.getenv("MAESTRO_TASK_ID") or None,
        maestro_activity_label=os.getenv(
            "MAESTRO_ACTIVITY_LABEL", "auditoria-acessos"
        ).strip(),
        execution_report_file=_env_path(
            "BOT_EXECUTION_REPORT_FILE", "logs/resumo_execucao.json"
        ),
    )


settings = get_settings()
