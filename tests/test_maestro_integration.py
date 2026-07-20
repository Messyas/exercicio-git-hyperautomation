"""Testes da camada de rastreabilidade da Issue 2."""

import json
import logging
from datetime import datetime

import pytest
from requests.exceptions import ConnectionError as RequestsConnectionError

from main import main
from src.maestro_client import (
    ExecutionResult,
    write_execution_report,
)
from src.resilience import call_with_network_retry


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


def test_main_falha_imediatamente_quando_pasta_de_entrada_nao_existe(
    tmp_path, monkeypatch
) -> None:
    entrada_ausente = tmp_path / "dados_entrada_ausente"
    relatorio = tmp_path / "resumo.json"
    monkeypatch.setenv("MAESTRO_ENABLED", "false")
    monkeypatch.setenv("BOT_INPUT_DIR", str(entrada_ausente))
    monkeypatch.setenv("BOT_EXECUTION_REPORT_FILE", str(relatorio))
    monkeypatch.setenv("BOT_LOG_DIR", str(tmp_path / "logs"))

    codigo = main([])

    assert codigo == 1
    payload = json.loads(relatorio.read_text(encoding="utf-8"))
    assert payload["status"] == "FAILED"
    assert payload["error"] == "INPUT_DIRECTORY_NOT_FOUND"
    log = (tmp_path / "logs" / "execucao.log").read_text(encoding="utf-8")
    assert "ERROR" in log
    assert "Pasta de entrada" in log


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
