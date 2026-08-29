"""Testes unitários do CoexistenceGuard (Prevenção de conflito de Runners)."""

import pytest
from pathlib import Path

from src.coexistence_guard import CoexistenceGuard
from src.exceptions import CoexistenceConflictError


def test_coexistence_guard_fluxo_basico(tmp_path: Path):
    lock_file = tmp_path / "test_session.lock"
    guard = CoexistenceGuard(lock_file=lock_file, timeout_seconds=0.5)

    assert not guard.is_locked()
    assert guard.acquire(orchestrator="SMART_OFFICE", bot_id="RPA01_DESKTOP") is True
    assert guard.is_locked()

    info = guard.get_lock_info()
    assert info is not None
    assert info["orchestrator"] == "SMART_OFFICE"
    assert info["bot_id"] == "RPA01_DESKTOP"

    guard.release()
    assert not guard.is_locked()


def test_coexistence_guard_bloqueia_concorrencia(tmp_path: Path):
    lock_file = tmp_path / "test_session_conflict.lock"
    guard1 = CoexistenceGuard(lock_file=lock_file, timeout_seconds=0.2)
    guard2 = CoexistenceGuard(lock_file=lock_file, timeout_seconds=0.2)

    # 1. Primeiro orquestrador adquire
    assert guard1.acquire(orchestrator="BOTCITY_LEGACY", bot_id="bot-conferencia-v1") is True

    # 2. Segundo orquestrador tenta adquirir o mesmo lock -> deve falhar
    with pytest.raises(CoexistenceConflictError) as exc_info:
        guard2.acquire(orchestrator="SMART_OFFICE", bot_id="RPA01_DESKTOP", blocking=False)

    assert "Runner ocupado por BOTCITY_LEGACY" in str(exc_info.value)

    guard1.release()
