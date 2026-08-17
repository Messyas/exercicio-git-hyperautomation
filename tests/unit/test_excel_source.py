"""Testes do contrato entre a planilha bruta e o produtor."""

import pytest

from src.excel_source import load_excel_batch


pytestmark = pytest.mark.unit


SAMPLE = "data/samples/inspecao_lotes_dia.xlsx"


def test_load_excel_batch_preserva_dados_brutos_e_metadados() -> None:
    batch = load_excel_batch(SAMPLE)
    records = batch.records()

    assert batch.batch_id.startswith("batch-")
    assert len(batch.source_hash) == 64
    assert batch.reference_date == "14/06/2026"
    assert len(batch.reference_lote_ids) == 23
    assert len(records) == 25
    assert records[0]["source_row"] == 4
    assert records[-1]["source_row"] == 28
    assert records[23]["lote_id"] == ""
    assert records[8]["responsavel"] == ""
    assert records[4]["status"] == "OK"
    assert records[6]["status"] == "NOK"


def test_item_id_e_deterministico_por_arquivo_e_linha() -> None:
    first = load_excel_batch(SAMPLE).records()
    second = load_excel_batch(SAMPLE).records()

    assert [item["item_id"] for item in first] == [
        item["item_id"] for item in second
    ]
    assert len({item["item_id"] for item in first}) == 25
