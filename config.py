"""Configuração central do bot.

As configurações de execução ficam no ``.env`` local e não devem ser
codificadas nos módulos de negócio. O arquivo ``.env.example`` documenta as
variáveis esperadas sem conter segredos reais.
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parent
load_dotenv(PROJECT_ROOT / ".env", override=False)


def _running_from_botcity() -> bool:
    """Reconhece os argumentos server/task/token injetados pelo BotRunner."""
    return len(sys.argv) >= 4 and str(sys.argv[1]).startswith(("http://", "https://"))


def _runner_task_id() -> str | None:
    return str(sys.argv[2]) if _running_from_botcity() else None


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


def _env_int(name: str, default: int, *, minimum: int = 0) -> int:
    """Lê um inteiro do ambiente e valida seu limite mínimo."""
    valor = os.getenv(name)
    if valor is None or not valor.strip():
        return default

    try:
        convertido = int(valor.strip())
    except ValueError as exc:
        raise ValueError(
            f"A variável {name} deve conter um inteiro (valor recebido: {valor!r})."
        ) from exc

    if convertido < minimum:
        raise ValueError(
            f"A variável {name} deve ser maior ou igual a {minimum}."
        )
    return convertido


def _env_float(name: str, default: float, *, minimum: float = 0.0, maximum: float = 1.0) -> float:
    """Lê um float do ambiente e valida seu intervalo."""
    valor = os.getenv(name)
    if valor is None or not valor.strip():
        return default

    try:
        convertido = float(valor.strip())
    except ValueError as exc:
        raise ValueError(
            f"A variável {name} deve conter um número decimal (valor recebido: {valor!r})."
        ) from exc

    if not (minimum <= convertido <= maximum):
        raise ValueError(
            f"A variável {name} deve estar entre {minimum} e {maximum} (valor recebido: {convertido})."
        )
    return convertido


@dataclass(frozen=True)
class Settings:
    """Configurações usadas pelas etapas atuais e futuras do bot."""

    project_root: Path
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
    execution_id: str
    bot_id: str
    playwright_enabled: bool
    playwright_url: str
    playwright_headless: bool
    playwright_slow_mo: int
    playwright_quantity: int
    playwright_artifacts_dir: Path
    playwright_timeout_ms: int
    web_username: str
    web_password: str
    datapool_backend: str
    datapool_label: str
    datapool_local_dir: Path
    validator_activity_label: str
    timezone: str
    ml_enabled: bool
    ml_api_url: str
    ml_timeout_ms: int
    ml_failure_threshold: int
    ml_model_path: Path
    ml_confianca_minima: float
    telegram_token: str | None
    telegram_chat_id: str | None
    whatsapp_enabled: bool
    twilio_account_sid: str | None
    twilio_auth_token: str | None
    whatsapp_to: str | None
    whatsapp_from: str | None
    email_enabled: bool
    smtp_server: str | None
    smtp_port: int
    email_from: str | None
    email_to: str | None
    dead_letter_file: Path



def get_settings() -> Settings:
    """Monta as configurações a partir das variáveis de ambiente."""
    return Settings(
        project_root=PROJECT_ROOT,
        output_dir=_env_path("BOT_OUTPUT_DIR", "data/output"),
        log_dir=_env_path("BOT_LOG_DIR", "logs"),
        default_input_file=_env_path(
            "BOT_INPUT_FILE", "data/samples/inspecao_lotes_dia.xlsx"
        ),
        maestro_enabled=_env_bool(
            "MAESTRO_ENABLED", default=_running_from_botcity()
        ),
        maestro_server=os.getenv("MAESTRO_SERVER") or None,
        maestro_login=os.getenv("MAESTRO_LOGIN") or None,
        maestro_key=os.getenv("MAESTRO_KEY") or None,
        maestro_task_id=(
            os.getenv("MAESTRO_TASK_ID") or _runner_task_id()
        ),
        maestro_activity_label=os.getenv(
            "MAESTRO_ACTIVITY_LABEL", "auditoria-acessos"
        ).strip(),
        execution_report_file=_env_path(
            "BOT_EXECUTION_REPORT_FILE", "logs/resumo_execucao.json"
        ),
        execution_id=(
            os.getenv("EXECUTION_ID")
            or os.getenv("MAESTRO_TASK_ID")
            or _runner_task_id()
            or "local"
        ).strip(),
        bot_id=(
            os.getenv("BOT_ID") or "bot-conferencia-lotes"
        ).strip(),
        playwright_enabled=_env_bool("PLAYWRIGHT_ENABLED"),
        playwright_url=os.getenv(
            "BOT_URL",
            os.getenv(
                "PLAYWRIGHT_URL",
                (PROJECT_ROOT / "web" / "lote-teste.html").as_uri(),
            ),
        ).strip(),
        playwright_headless=_env_bool(
            "BOT_HEADLESS",
            default=_env_bool("PLAYWRIGHT_HEADLESS", default=True),
        ),
        playwright_slow_mo=_env_int("PLAYWRIGHT_SLOW_MO", 300),
        playwright_quantity=_env_int("PLAYWRIGHT_QUANTITY", 10, minimum=1),
        playwright_artifacts_dir=_env_path(
            "PLAYWRIGHT_ARTIFACTS_DIR", "screenshots"
        ),
        playwright_timeout_ms=_env_int(
            "PLAYWRIGHT_TIMEOUT_MS", 10_000, minimum=1
        ),
        web_username=os.getenv("BOT_USUARIO", "automacao").strip(),
        web_password=os.getenv("BOT_SENHA", "automacao"),
        datapool_backend=os.getenv(
            "DATAPOOL_BACKEND",
            "botcity" if _running_from_botcity() else "local",
        ).strip().lower(),
        datapool_label=os.getenv(
            "DATAPOOL_LABEL", "lotes-inspecao-validacao-off-guilliman"
        ).strip(),
        datapool_local_dir=_env_path(
            "DATAPOOL_LOCAL_DIR", "data/datapool"
        ),
        validator_activity_label=os.getenv(
            "VALIDATOR_ACTIVITY_LABEL", "bot-lotes-validacao-mk7"
        ).strip(),
        timezone=os.getenv("APP_TIMEZONE", "America/Manaus").strip(),
        ml_enabled=_env_bool("ML_ENABLED", default=True),
        ml_api_url=os.getenv("ML_API_URL", "http://127.0.0.1:8000").strip(),
        ml_timeout_ms=_env_int("ML_TIMEOUT_MS", 1000, minimum=1),
        ml_failure_threshold=_env_int("ML_FAILURE_THRESHOLD", 5, minimum=1),
        ml_model_path=_env_path("ML_MODEL_PATH", "models/classificador_lotes.pkl"),
        ml_confianca_minima=_env_float("ML_CONFIANCA_MINIMA", 0.70, minimum=0.0, maximum=1.0),
        telegram_token=os.getenv("TELEGRAM_TOKEN") or None,
        telegram_chat_id=os.getenv("TELEGRAM_CHAT_ID") or None,
        whatsapp_enabled=_env_bool("WHATSAPP_ENABLED", default=False),
        twilio_account_sid=os.getenv("TWILIO_ACCOUNT_SID") or None,
        twilio_auth_token=os.getenv("TWILIO_AUTH_TOKEN") or None,
        whatsapp_to=os.getenv("WHATSAPP_TO") or None,
        whatsapp_from=os.getenv("WHATSAPP_FROM") or None,
        email_enabled=_env_bool("EMAIL_ENABLED", default=False),
        smtp_server=os.getenv("SMTP_SERVER") or None,
        smtp_port=_env_int("SMTP_PORT", 587),
        email_from=os.getenv("EMAIL_FROM") or None,
        email_to=os.getenv("EMAIL_TO") or None,
        dead_letter_file=_env_path("DEAD_LETTER_FILE", "data/output/dead_letter.jsonl"),
    )



settings = get_settings()

