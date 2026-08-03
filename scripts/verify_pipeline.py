"""Valida por conteúdo os artefatos produzidos pelo E2E do Compose."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]


def _read_json(path: Path) -> dict:
    if not path.is_file():
        raise AssertionError(f"Arquivo não encontrado: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _execution_records(path: Path, started_at: str) -> list[dict]:
    # O resumo preserva microssegundos, enquanto o formatter JSON dos logs
    # registra somente segundos. Arredondar o início para baixo impede que
    # execuções rápidas percam todas as suas linhas no filtro.
    start = datetime.fromisoformat(started_at).replace(microsecond=0)
    records = [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    return [
        record
        for record in records
        if datetime.fromisoformat(record["timestamp"]) >= start
    ]


def main() -> int:
    producer = _read_json(ROOT / "logs/produtor/resumo_execucao.json")
    validator = _read_json(ROOT / "logs/validador/resumo_execucao.json")
    producer_summary = producer["summary"]
    validator_summary = validator["summary"]

    assert producer["status"] == "PARTIALLY_COMPLETED"
    assert producer_summary["total"] == 25
    assert producer_summary["cadastros_sucesso"] == 24
    assert producer_summary["cadastros_rejeitados"] == 1
    assert producer_summary["cadastros_falha_tecnica"] == 0
    assert validator["status"] == "SUCCESS"
    assert validator_summary["total_registros"] == 25
    assert validator_summary["total_divergencias"] == 9
    assert validator_summary["total_rejeicoes_cadastro"] == 1
    assert validator_summary["total_falhas_tecnicas"] == 0

    batch_id = producer_summary["batch_id"]
    datapool = _read_json(ROOT / f"data/datapool/{batch_id}.processed.json")
    assert datapool["total"] == 25
    assert sum(item["datapool_state"] == "DONE" for item in datapool["items"]) == 16
    assert sum(item["datapool_state"] == "ERROR" for item in datapool["items"]) == 9
    assert not any(
        item["datapool_state"] == "PROCESSING" for item in datapool["items"]
    )
    assert sum(item["error_type"] == "BUSINESS" for item in datapool["items"]) == 9
    assert not (ROOT / f"data/datapool/{batch_id}.pending.json").exists()

    evidence_dir = ROOT / "screenshots/local" / batch_id / "produtor"
    screenshots = list(evidence_dir.glob("*.png"))
    assert len(screenshots) == 25
    assert sum(path.name.startswith("comprovante_") for path in screenshots) == 24
    assert sum(path.name.startswith("rejeicao_") for path in screenshots) == 1
    assert all(item["evidence_name"] for item in datapool["items"])
    assert all(item["evidence_path"] for item in datapool["items"])

    report_name = Path(validator_summary["relatorio"]).name
    report = ROOT / "data/output" / report_name
    with pd.ExcelFile(report) as workbook:
        assert set(workbook.sheet_names) == {
            "resumo",
            "divergencias",
            "lotes_validados",
            "rejeicoes_cadastro",
            "falhas_tecnicas",
            "revisao_humana",
        }
    assert len(pd.read_excel(report, sheet_name="divergencias")) == 9
    assert len(pd.read_excel(report, sheet_name="lotes_validados")) == 16
    assert len(pd.read_excel(report, sheet_name="rejeicoes_cadastro")) == 1
    assert pd.read_excel(report, sheet_name="falhas_tecnicas").empty
    assert len(pd.read_excel(report, sheet_name="revisao_humana")) == 2

    for name, expected_bot_id, execution in (
        (
            "produtor",
            "bot-lotes-cadastro-playwright-mk7",
            producer,
        ),
        (
            "validador",
            "bot-lotes-validacao-mk7",
            validator,
        ),
    ):
        records = _execution_records(
            ROOT / f"logs/{name}/execucao.log",
            execution["started_at"],
        )
        assert records
        assert all(record["execution_id"] == "local" for record in records)
        assert all(record["bot_id"] == expected_bot_id for record in records)

    print(
        json.dumps(
            {
                "batch_id": batch_id,
                "cadastros_sucesso": 24,
                "cadastros_rejeitados": 1,
                "divergencias": 9,
                "lotes_validados": 16,
                "evidencias": 25,
                "relatorio": str(report),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
