"""Testes do handoff local e do consumidor RN01–RN07."""

from __future__ import annotations

import json
from types import SimpleNamespace

import pandas as pd
import pytest

from consumer import run_consumer
from src.datapool_gateway import (
    BotCityDatapoolPublisher,
    BotCityDatapoolConsumer,
    LocalDatapoolConsumer,
    LocalDatapoolPublisher,
)
from src.excel_source import load_excel_batch
from src.maestro_client import configure_local_logging
from src.resilience import close_logger


SAMPLE = "data/samples/inspecao_lotes_dia.xlsx"


def test_publisher_botcity_explica_datapool_ausente_no_preflight() -> None:
    class NotFoundError(Exception):
        response = SimpleNamespace(status_code=404)

    class Maestro:
        def get_datapool(self, label):
            assert label == "pool-mk7"
            raise NotFoundError("not found")

    publisher = BotCityDatapoolPublisher(
        Maestro(),
        datapool_label="pool-mk7",
        validator_activity_label="validador-mk7",
    )

    with pytest.raises(
        RuntimeError,
        match="label técnico 'pool-mk7'.*HTTP 404",
    ):
        publisher.check_ready()


def test_datapool_local_publica_consume_e_persiste_estados(tmp_path) -> None:
    records = [
        {
            "item_id": "hash:4",
            "batch_id": "batch-test",
            "source_file": "entrada.xlsx",
            "lote_id": "L1",
        },
        {
            "item_id": "hash:5",
            "batch_id": "batch-test",
            "source_file": "entrada.xlsx",
            "lote_id": "L2",
        },
    ]
    publisher = LocalDatapoolPublisher(tmp_path)
    destination = publisher.publish(
        batch_id="batch-test",
        records=records,
        reference_lote_ids={"L1"},
    )

    assert destination.endswith(".pending.json")
    consumer = LocalDatapoolConsumer(tmp_path)
    batch = consumer.consume()
    batch.items[0].report_done("ok")
    batch.items[1].report_business_error("RN03")
    result_path = consumer.persist_states(batch)

    assert result_path is not None and result_path.exists()
    assert not list(tmp_path.glob("*.pending.json"))
    payload = json.loads(result_path.read_text(encoding="utf-8"))
    assert [item["datapool_state"] for item in payload["items"]] == [
        "DONE",
        "ERROR",
    ]


def test_consumer_local_preserva_resultado_do_pdd(tmp_path, monkeypatch) -> None:
    batch = load_excel_batch(SAMPLE)
    records = [
        {
            **record,
            "cadastro_status": "SUCESSO",
            "cadastro_error": "",
            "evidence_name": "evidencia.png",
        }
        for record in batch.records()
    ]
    datapool_dir = tmp_path / "datapool"
    LocalDatapoolPublisher(datapool_dir).publish(
        batch_id=batch.batch_id,
        records=records,
        reference_lote_ids=batch.reference_lote_ids,
    )
    monkeypatch.setenv("MAESTRO_ENABLED", "false")
    monkeypatch.setenv("DATAPOOL_BACKEND", "local")
    monkeypatch.setenv("DATAPOOL_LOCAL_DIR", str(datapool_dir))
    monkeypatch.setenv("BOT_OUTPUT_DIR", str(tmp_path / "output"))
    monkeypatch.setenv("BOT_LOG_DIR", str(tmp_path / "logs"))
    monkeypatch.delenv("SHUTDOWN_FILE", raising=False)

    assert run_consumer() == 0

    summary = json.loads(
        (tmp_path / "logs/validador/resumo_execucao.json").read_text(
            encoding="utf-8"
        )
    )
    assert summary["status"] == "SUCCESS"
    assert summary["summary"]["total_registros"] == 25
    assert summary["summary"]["total_divergencias"] == 9
    assert summary["summary"]["total_lotes_validados"] == 16
    assert summary["summary"]["total_items"] == 25
    assert summary["summary"]["processed_items"] == 16
    assert summary["summary"]["failed_items"] == 9
    processed = json.loads(
        next(datapool_dir.glob("*.processed.json")).read_text(
            encoding="utf-8"
        )
    )
    assert sum(
        item["datapool_state"] == "ERROR"
        for item in processed["items"]
    ) == 9


def test_consumer_separa_rejeicao_e_falha_tecnica(tmp_path, monkeypatch) -> None:
    batch = load_excel_batch(SAMPLE)
    records = [
        {
            **record,
            "cadastro_status": "SUCESSO",
            "cadastro_error": "",
            "cadastro_error_type": "",
            "evidence_name": "evidencia.png",
        }
        for record in batch.records()
    ]
    records[0].update(
        {
            "cadastro_status": "REJEITADO_NEGOCIO",
            "cadastro_error": "Cadastro recusado.",
            "cadastro_error_type": "BUSINESS",
        }
    )
    records[1].update(
        {
            "cadastro_status": "FALHA_TECNICA",
            "cadastro_error": "Timeout do navegador.",
            "cadastro_error_type": "SYSTEM",
        }
    )
    datapool_dir = tmp_path / "datapool"
    LocalDatapoolPublisher(datapool_dir).publish(
        batch_id=batch.batch_id,
        records=records,
        reference_lote_ids=batch.reference_lote_ids,
    )
    monkeypatch.setenv("MAESTRO_ENABLED", "false")
    monkeypatch.setenv("DATAPOOL_BACKEND", "local")
    monkeypatch.setenv("DATAPOOL_LOCAL_DIR", str(datapool_dir))
    monkeypatch.setenv("BOT_OUTPUT_DIR", str(tmp_path / "output"))
    monkeypatch.setenv("BOT_LOG_DIR", str(tmp_path / "logs"))
    monkeypatch.delenv("SHUTDOWN_FILE", raising=False)

    assert run_consumer() == 0

    summary = json.loads(
        (tmp_path / "logs/validador/resumo_execucao.json").read_text(
            encoding="utf-8"
        )
    )
    assert summary["status"] == "PARTIALLY_COMPLETED"
    assert summary["summary"]["total_rejeicoes_cadastro"] == 1
    assert summary["summary"]["total_falhas_tecnicas"] == 1
    assert summary["summary"]["total_items"] == 25
    assert (
        summary["summary"]["processed_items"]
        + summary["summary"]["failed_items"]
        == 25
    )
    report = summary["summary"]["relatorio"]
    assert len(pd.read_excel(report, sheet_name="rejeicoes_cadastro")) == 1
    assert len(pd.read_excel(report, sheet_name="falhas_tecnicas")) == 1
    processed = json.loads(
        next(datapool_dir.glob("*.processed.json")).read_text(encoding="utf-8")
    )
    assert processed["items"][0]["error_type"] == "BUSINESS"
    assert processed["items"][1]["error_type"] == "SYSTEM"
    assert all(
        item["datapool_state"] != "PROCESSING"
        for item in processed["items"]
    )


def test_logger_injeta_ids_e_contexto_em_json(tmp_path) -> None:
    logger = configure_local_logging(
        tmp_path,
        execution_id="exec-123",
        bot_id="bot-abc",
        logger_name="test.contexto.estruturado",
    )
    logger.info(
        "EVENTO_TESTE",
        extra={
            "batch_id": "batch-1",
            "lote_id": "L1",
            "source_row": 4,
        },
    )
    close_logger(logger)

    payload = json.loads(
        (tmp_path / "execucao.log").read_text(encoding="utf-8").splitlines()[0]
    )
    assert payload["execution_id"] == "exec-123"
    assert payload["bot_id"] == "bot-abc"
    assert payload["batch_id"] == "batch-1"
    assert payload["lote_id"] == "L1"
    assert payload["source_row"] == 4


def test_consumer_botcity_nao_drena_lote_seguinte() -> None:
    class Entry:
        def __init__(self, values):
            self.values = values

        def report_error(self, **_kwargs):
            return None

    class Pool:
        def __init__(self):
            self.entries = [
                Entry({"batch_id": "A", "batch_total": "2"}),
                Entry({"batch_id": "A", "batch_total": "2"}),
                Entry({"batch_id": "B", "batch_total": "1"}),
            ]

        def has_next(self):
            return bool(self.entries)

        def next(self, task_id):
            assert task_id == "task-A"
            return self.entries.pop(0)

    pool = Pool()

    class Maestro:
        def get_datapool(self, _label):
            return pool

        def get_task(self, _task_id):
            return SimpleNamespace(
                parameters={"batch_id": "A", "batch_total": 2}
            )

    consumer = BotCityDatapoolConsumer(
        Maestro(), datapool_label="pool", task_id="task-A"
    )

    batch = consumer.consume()

    assert batch.batch_id == "A"
    assert len(batch.items) == 2
    assert len(pool.entries) == 1
    assert pool.entries[0].values["batch_id"] == "B"
