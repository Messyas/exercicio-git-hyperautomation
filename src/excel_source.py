"""Leitura da planilha bruta e criação do contrato do lote de execução."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from src.base_referencia import carregar_base_referencia
from src.validacao import carregar_planilha, valida_estrutura


@dataclass(frozen=True)
class ExcelBatch:
    """Dados necessários ao cadastro web e à publicação no DataPool."""

    batch_id: str
    source_file: Path
    source_hash: str
    reference_date: str
    reference_lote_ids: set[str]
    dataframe: pd.DataFrame

    def records(self) -> list[dict[str, str | int]]:
        records: list[dict[str, str | int]] = []
        for index, row in self.dataframe.iterrows():
            source_row = int(index) + 4
            record = {
                column: _serializable_value(row.get(column))
                for column in self.dataframe.columns
            }
            record.update(
                {
                    "item_id": f"{self.source_hash}:{source_row}",
                    "batch_id": self.batch_id,
                    "source_file": self.source_file.name,
                    "source_hash": self.source_hash,
                    "source_row": source_row,
                    "reference_date": self.reference_date,
                }
            )
            records.append(record)
        return records


def _serializable_value(value: Any) -> str:
    if pd.isna(value):
        return ""
    if isinstance(value, pd.Timestamp):
        return value.strftime("%d/%m/%Y")
    return str(value).strip()


def _reference_date(path: Path) -> str:
    with pd.ExcelFile(path) as workbook:
        first_sheet = workbook.sheet_names[0]
    match = re.search(r"(\d{2})_(\d{2})_(\d{4})", first_sheet)
    if match:
        return "/".join(match.groups())
    return ""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_excel_batch(path: str | Path) -> ExcelBatch:
    """Carrega a entrada sem aplicar RN02–RN07, preservando os dados brutos."""
    source_file = Path(path)
    if not source_file.is_file():
        raise FileNotFoundError(f"Planilha de entrada não encontrada: {source_file}")

    dataframe = carregar_planilha(str(source_file))
    valida_estrutura(dataframe)
    source_hash = _sha256(source_file)
    return ExcelBatch(
        batch_id=f"batch-{source_hash[:16]}",
        source_file=source_file,
        source_hash=source_hash,
        reference_date=_reference_date(source_file),
        reference_lote_ids=carregar_base_referencia(str(source_file)),
        dataframe=dataframe,
    )
