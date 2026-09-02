"""Testes da camada de rastreabilidade da Issue 2."""

import json
import logging
from datetime import datetime

import pytest
from requests.exceptions import ConnectionError as RequestsConnectionError

from main import main
from config import get_settings
from src.maestro_client import (
    ExecutionResult,
    MaestroClient,
    write_execution_report,
)
from src.resilience import call_with_network_retry
from src.time_utils import now_local


pytestmark = pytest.mark.integration


def test_execution_result_gera_relatorio_json(tmp_path) -> None:
    inicio = datetime.now().astimezone()
    resultado = ExecutionResult.success(
        started_at=inicio,
        finished_at=datetime.now().astimezone(),
        summary={"total": 2},
    )

    arquivo = write_execution_report(resultado, tmp_path / "resumo.json")

    payload = json.loads(arquivo.read_text(encoding="utf-8"))
    assert payload["status"] == "SUCCESS"
    assert payload["summary"] == {"total": 2}
    assert payload["report_path"] == str(arquivo)


def test_resultado_parcial_e_conclusao_controlada() -> None:
    inicio = now_local()
    resultado = ExecutionResult.partial(
        started_at=inicio,
        finished_at=now_local(),
        summary={"total": 2, "cadastros_falha_tecnica": 1},
    )

    assert resultado.status == "PARTIALLY_COMPLETED"
    assert resultado.completed
    assert not resultado.succeeded


def test_finish_reporta_indicadores_de_itens_ao_maestro(
    monkeypatch,
) -> None:
    monkeypatch.setenv("MAESTRO_ENABLED", "true")
    monkeypatch.setenv("MAESTRO_TASK_ID", "321")
    settings = get_settings()
    captured = {}

    class FakeMaestro:
        def finish_task(self, **kwargs):
            captured.update(kwargs)

    client = MaestroClient(settings, logging.getLogger("test.finish.items"))
    client.sdk = FakeMaestro()
    result = ExecutionResult.success(
        started_at=now_local(),
        finished_at=now_local(),
        summary={},
    )

    client.finish(
        result,
        total_items=25,
        processed_items=16,
        failed_items=9,
    )

    assert captured["task_id"] == 321
    assert captured["total_items"] == 25
    assert captured["processed_items"] == 16
    assert captured["failed_items"] == 9


def test_runner_define_contexto_e_defaults_botcity(monkeypatch) -> None:
    for variable in (
        "MAESTRO_ENABLED",
        "MAESTRO_TASK_ID",
        "EXECUTION_ID",
        "DATAPOOL_BACKEND",
        "BOT_URL",
        "PLAYWRIGHT_URL",
    ):
        monkeypatch.delenv(variable, raising=False)
    monkeypatch.setattr(
        "sys.argv",
        ["bot.py", "https://example.invalid", "task-123", "token", "org"],
    )

    settings = get_settings()

    assert settings.maestro_enabled
    assert settings.maestro_task_id == "task-123"
    assert settings.execution_id == "task-123"
    assert settings.datapool_backend == "botcity"
    assert "index.html" in settings.playwright_url


def test_relogio_operacional_usa_fuso_manaus(monkeypatch) -> None:
    monkeypatch.setenv("APP_TIMEZONE", "America/Manaus")
    timestamp = now_local()

    assert timestamp.tzinfo is not None
    assert timestamp.utcoffset().total_seconds() == -4 * 60 * 60


def test_main_falha_imediatamente_quando_arquivo_de_entrada_nao_existe(
    tmp_path, monkeypatch
) -> None:
    entrada_ausente = tmp_path / "entrada_ausente.xlsx"
    relatorio = tmp_path / "resumo.json"
    monkeypatch.setenv("MAESTRO_ENABLED", "false")
    monkeypatch.setenv("BOT_INPUT_FILE", str(entrada_ausente))
    monkeypatch.setenv("BOT_EXECUTION_REPORT_FILE", str(relatorio))
    monkeypatch.setenv("BOT_LOG_DIR", str(tmp_path / "logs"))

    codigo = main([])

    assert codigo == 1
    payload = json.loads(relatorio.read_text(encoding="utf-8"))
    assert payload["status"] == "FAILED"
    assert payload["error"] == "INPUT_FILE_NOT_FOUND"
    log = (tmp_path / "logs" / "execucao.log").read_text(encoding="utf-8")
    assert "ERROR" in log
    assert "Arquivo de entrada" in log


def test_retry_tenta_tres_vezes_apenas_para_falha_de_rede() -> None:
    logger = logging.getLogger("test.retry")
    tentativas = 0

    def operacao():
        nonlocal tentativas
        tentativas += 1
        if tentativas < 3:
            raise RequestsConnectionError("rede indisponível")
        return "ok"

    resultado = call_with_network_retry(
        operacao,
        logger=logger,
        context="teste | lote_id=L1",
        delay_seconds=0,
    )

    assert resultado == "ok"
    assert tentativas == 3


def test_retry_repropaga_falha_de_rede_apos_tres_tentativas() -> None:
    logger = logging.getLogger("test.retry.final")
    tentativas = 0

    def operacao():
        nonlocal tentativas
        tentativas += 1
        raise RequestsConnectionError("rede indisponível")

    with pytest.raises(RequestsConnectionError):
        call_with_network_retry(
            operacao,
            logger=logger,
            context="teste | lote_id=L2",
            delay_seconds=0,
        )

    assert tentativas == 3
