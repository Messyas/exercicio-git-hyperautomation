"""Gera um lote demonstrativo de 30 incidentes para a apresentação S10-B."""

from __future__ import annotations

from pathlib import Path

from openpyxl import Workbook


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "data" / "incident" / "lote_incidente.xlsx"
COLUMNS = [
    "lote_id",
    "produto",
    "linha",
    "turno",
    "status",
    "responsavel",
    "data",
    "observacao",
]


def _record(number: int, **changes: str) -> dict[str, str]:
    record = {
        "lote_id": f"INC-2026-{number:03d}",
        "produto": "Módulo de controle",
        "linha": f"L{(number % 3) + 1}",
        "turno": "ABC"[number % 3],
        "status": "APROVADO",
        "responsavel": "Equipe Inspeção",
        "data": "14/06/2026",
        "observacao": "",
    }
    record.update(changes)
    return record


def build_records() -> tuple[list[dict[str, str]], set[str]]:
    records: list[dict[str, str]] = []
    reference_ids: set[str] = set()

    # RN03: lote não cadastrado na referência (10 ocorrências).
    for number in range(1, 11):
        records.append(
            _record(
                number,
                observacao="Etiqueta confere visualmente, porém não localizada no ERP.",
            )
        )

    # RN07: reprovado sem justificativa (7 ocorrências).
    for number in range(11, 18):
        records.append(_record(number, status="REPROVADO"))
        reference_ids.add(f"INC-2026-{number:03d}")

    # Casos ambíguos, com texto livre, para a classificação híbrida (6 ocorrências).
    observations = [
        "Peça com tonalidade diferente; aguarda contraprova do laboratório.",
        "Leitura oscilou no sensor final, repetir medição antes da liberação.",
        "Lacre íntegro, mas o peso ficou próximo ao limite superior.",
        "Operador relata ruído intermitente após o teste funcional.",
        "Foto anexada indica risco superficial, sem decisão conclusiva.",
        "Amostra separada para análise de engenharia no próximo turno.",
    ]
    for number, observation in zip(range(18, 24), observations, strict=True):
        records.append(_record(number, status="EM AJUSTE", observacao=observation))
        reference_ids.add(f"INC-2026-{number:03d}")

    # RN01: data fora da referência (4 ocorrências).
    for number in range(24, 28):
        records.append(
            _record(
                number,
                data="13/06/2026",
                observacao="Registro lançado após o fechamento do turno.",
            )
        )
        reference_ids.add(f"INC-2026-{number:03d}")

    # RN02: campo obrigatório ausente (3 ocorrências).
    for number, field in zip(range(28, 31), ("produto", "responsavel", "linha"), strict=True):
        records.append(
            _record(
                number,
                **{
                    field: "",
                    "observacao": "Cadastro incompleto identificado na conferência.",
                },
            )
        )
        reference_ids.add(f"INC-2026-{number:03d}")

    return records, reference_ids


def main() -> None:
    records, reference_ids = build_records()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    workbook = Workbook()
    incident = workbook.active
    incident.title = "Incidente_14_06_2026"
    incident.append(["Lote de incidente para demonstração", "Registros: 30"])
    incident.append([])
    incident.append(COLUMNS)
    for record in records:
        incident.append([record[column] for column in COLUMNS])

    reference = workbook.create_sheet("Base_Referencia")
    reference.append(["Base de referência", f"Registros: {len(reference_ids)}"])
    reference.append(["lote_id"])
    for lote_id in sorted(reference_ids):
        reference.append([lote_id])

    for sheet in workbook.worksheets:
        for column in sheet.columns:
            letter = column[0].column_letter
            sheet.column_dimensions[letter].width = min(
                70, max(len(str(cell.value or "")) for cell in column) + 2
            )
    workbook.save(OUTPUT)
    print(f"Lote criado: {OUTPUT} ({len(records)} casos).")


if __name__ == "__main__":
    main()
