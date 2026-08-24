"""Módulo de espera por tarefa predecessora no Maestro (Estudo de Caso S10-B).

Reaproveitado da Aula 26: um bot que depende de outro aguarda a conclusão da
tarefa predecessora antes de iniciar o seu processamento. A espera usa polling
com backoff linear e timeout configurável.
"""

from __future__ import annotations

import logging
import time
from typing import Optional

logger = logging.getLogger(__name__)

# Configurações padrão de espera
DEFAULT_POLL_INTERVAL_SECONDS = 5.0
DEFAULT_MAX_WAIT_SECONDS = 300.0
TASK_STATUS_COMPLETED = ("SUCCESS", "PARTIALLY_COMPLETED", "COMPLETED")
TASK_STATUS_FAILED = ("FAILED", "ERROR", "CANCELED")


def wait_for_predecessor(
    maestro_sdk,
    task_id: str,
    *,
    poll_interval: float = DEFAULT_POLL_INTERVAL_SECONDS,
    max_wait: float = DEFAULT_MAX_WAIT_SECONDS,
    logger_instance: Optional[logging.Logger] = None,
) -> str:
    """Aguarda a tarefa predecessora concluir no Maestro via polling.

    Retorna o status final da tarefa predecessora. Lança TimeoutError se o
    tempo máximo de espera for excedido.

    Parameters
    ----------
    maestro_sdk:
        Instância autenticada do SDK do BotCity Maestro.
    task_id:
        ID da tarefa predecessora a ser monitorada.
    poll_interval:
        Intervalo base entre consultas (em segundos). Cresce linearmente.
    max_wait:
        Tempo máximo de espera antes de lançar TimeoutError.
    logger_instance:
        Logger opcional; usa o logger do módulo se não fornecido.
    """
    log = logger_instance or logger
    elapsed = 0.0
    attempt = 0

    log.info(
        f"[WAIT_PREDECESSOR] Aguardando tarefa predecessora '{task_id}' "
        f"(poll={poll_interval}s, max_wait={max_wait}s)..."
    )

    while elapsed < max_wait:
        attempt += 1
        try:
            task = maestro_sdk.get_task(task_id)
            status = str(getattr(task, "status", getattr(task, "state", "UNKNOWN"))).upper()
        except Exception as exc:
            log.warning(
                f"[WAIT_PREDECESSOR] Falha ao consultar tarefa '{task_id}' "
                f"(tentativa {attempt}): {exc}"
            )
            status = "UNKNOWN"

        if status in TASK_STATUS_COMPLETED:
            log.info(
                f"[WAIT_PREDECESSOR] Tarefa '{task_id}' concluída com status '{status}' "
                f"após {elapsed:.1f}s ({attempt} consultas)."
            )
            return status

        if status in TASK_STATUS_FAILED:
            log.error(
                f"[WAIT_PREDECESSOR] Tarefa '{task_id}' falhou com status '{status}' "
                f"após {elapsed:.1f}s."
            )
            return status

        # Backoff linear: intervalo cresce a cada tentativa
        sleep_time = min(poll_interval * attempt, max_wait - elapsed)
        if sleep_time <= 0:
            break

        log.debug(
            f"[WAIT_PREDECESSOR] Tarefa '{task_id}' em '{status}'. "
            f"Próxima consulta em {sleep_time:.1f}s (tentativa {attempt})."
        )
        time.sleep(sleep_time)
        elapsed += sleep_time

    raise TimeoutError(
        f"Tarefa predecessora '{task_id}' não concluiu em {max_wait}s "
        f"({attempt} consultas realizadas)."
    )
