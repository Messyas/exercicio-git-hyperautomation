"""Relógio central do projeto no fuso operacional de Manaus."""

from __future__ import annotations

import os
from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


DEFAULT_TIMEZONE = "America/Manaus"


def operational_timezone() -> ZoneInfo:
    """Retorna o fuso configurado, usando Manaus como padrão do processo."""
    name = os.getenv("APP_TIMEZONE", DEFAULT_TIMEZONE).strip()
    try:
        return ZoneInfo(name)
    except ZoneInfoNotFoundError as exc:
        raise ValueError(f"Fuso horário inválido em APP_TIMEZONE: {name!r}.") from exc


def now_local() -> datetime:
    """Obtém um timestamp consciente do fuso operacional."""
    return datetime.now(operational_timezone())
