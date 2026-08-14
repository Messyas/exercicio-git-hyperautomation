"""Testes do verificador de evidências do E2E."""

import json

import pytest

from scripts.verify_pipeline import _execution_records


pytestmark = pytest.mark.unit


def test_logs_do_mesmo_segundo_do_inicio_sao_considerados(tmp_path) -> None:
    log_path = tmp_path / "execucao.log"
    log_path.write_text(
        json.dumps(
            {
                "timestamp": "2026-08-02T21:52:35-0400",
                "bot_id": "bot-lotes-validacao-mk7",
            }
        )
        + "\n",
        encoding="utf-8",
    )

    records = _execution_records(
        log_path,
        "2026-08-02T21:52:35.956434-04:00",
    )

    assert len(records) == 1
    assert records[0]["bot_id"] == "bot-lotes-validacao-mk7"
