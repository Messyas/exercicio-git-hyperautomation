"""Gateways local e BotCity para o handoff entre produtor e consumidor."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

from botcity.maestro import BotMaestroSDK, DataPoolEntry, ErrorType


DATAPOOL_FIELDS = (
    "item_id",
    "batch_id",
    "batch_total",
    "producer_execution_id",
    "source_file",
    "source_hash",
    "source_row",
    "reference_date",
    "lote_id",
    "produto",
    "linha",
    "turno",
    "status",
    "responsavel",
    "data",
    "observacao",
    "cadastro_status",
    "cadastro_error",
    "cadastro_error_type",
    "evidence_name",
    "evidence_path",
    "reference_lotes_json",
)


@dataclass
class QueueItem:
    """Item consumido, com callbacks para atualizar seu estado na fila."""

    values: dict[str, Any]
    raw_entry: Any = None
    state: str = "PROCESSING"
    finish_message: str = ""
    error_type: str = ""

    def report_done(self, message: str) -> None:
        if self.raw_entry is not None:
            self.raw_entry.report_done(finish_message=message)
        self.state = "DONE"
        self.finish_message = message
        self.error_type = ""

    def report_business_error(self, message: str) -> None:
        if self.raw_entry is not None:
            self.raw_entry.report_error(
                error_type=ErrorType.BUSINESS,
                finish_message=message,
            )
        self.state = "ERROR"
        self.finish_message = message
        self.error_type = "BUSINESS"

    def report_system_error(self, message: str) -> None:
        if self.raw_entry is not None:
            self.raw_entry.report_error(
                error_type=ErrorType.SYSTEM,
                finish_message=message,
            )
        self.state = "ERROR"
        self.finish_message = message
        self.error_type = "SYSTEM"


@dataclass
class ConsumedBatch:
    batch_id: str
    items: list[QueueItem]
    reference_lote_ids: set[str]
    source_file: str
    local_pending_path: Path | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class DatapoolPublisher(Protocol):
    def check_ready(self) -> None: ...

    def publish(
        self,
        *,
        batch_id: str,
        records: list[dict[str, Any]],
        reference_lote_ids: set[str],
    ) -> str: ...


class DatapoolConsumer(Protocol):
    def consume(self) -> ConsumedBatch: ...

    def persist_states(self, batch: ConsumedBatch) -> Path | None: ...


class LocalDatapoolPublisher:
    """Persiste o lote de forma atômica para Compose, testes e CI."""

    def __init__(self, directory: Path) -> None:
        self.directory = directory

    def check_ready(self) -> None:
        """Falha cedo quando o diretório de handoff não pode ser criado."""
        self.directory.mkdir(parents=True, exist_ok=True)

    def publish(
        self,
        *,
        batch_id: str,
        records: list[dict[str, Any]],
        reference_lote_ids: set[str],
    ) -> str:
        self.directory.mkdir(parents=True, exist_ok=True)
        pending_path = self.directory / f"{batch_id}.pending.json"
        temporary_path = self.directory / f".{batch_id}.{os.getpid()}.tmp"
        payload = {
            "batch_id": batch_id,
            "reference_lote_ids": sorted(reference_lote_ids),
            "total": len(records),
            "items": records,
        }
        temporary_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        temporary_path.replace(pending_path)
        return str(pending_path)


class LocalDatapoolConsumer:
    def __init__(self, directory: Path) -> None:
        self.directory = directory

    def consume(self) -> ConsumedBatch:
        candidates = sorted(
            self.directory.glob("*.pending.json"),
            key=lambda path: path.stat().st_mtime_ns,
        )
        if not candidates:
            raise FileNotFoundError(
                f"Nenhum lote pendente em {self.directory}."
            )
        pending_path = candidates[-1]
        payload = json.loads(pending_path.read_text(encoding="utf-8"))
        items = [QueueItem(dict(values)) for values in payload["items"]]
        return ConsumedBatch(
            batch_id=str(payload["batch_id"]),
            items=items,
            reference_lote_ids=set(payload["reference_lote_ids"]),
            source_file=str(items[0].values.get("source_file", "datapool")),
            local_pending_path=pending_path,
        )

    def persist_states(self, batch: ConsumedBatch) -> Path | None:
        if batch.local_pending_path is None:
            return None
        processed_path = batch.local_pending_path.with_name(
            batch.local_pending_path.name.replace(
                ".pending.json", ".processed.json"
            )
        )
        payload = {
            "batch_id": batch.batch_id,
            "reference_lote_ids": sorted(batch.reference_lote_ids),
            "total": len(batch.items),
            "items": [
                {
                    **item.values,
                    "datapool_state": item.state,
                    "finish_message": item.finish_message,
                    "error_type": item.error_type,
                }
                for item in batch.items
            ],
        }
        processed_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        batch.local_pending_path.unlink()
        return processed_path


class BotCityDatapoolPublisher:
    def __init__(
        self,
        maestro: BotMaestroSDK,
        *,
        datapool_label: str,
        validator_activity_label: str,
    ) -> None:
        self.maestro = maestro
        self.datapool_label = datapool_label
        self.validator_activity_label = validator_activity_label

    def _get_datapool(self) -> Any:
        try:
            return self.maestro.get_datapool(self.datapool_label)
        except Exception as error:
            response = getattr(error, "response", None)
            status_code = getattr(response, "status_code", None)
            if status_code == 404:
                detail = "não encontrado no workspace atual (HTTP 404)"
            elif status_code:
                detail = f"indisponível (HTTP {status_code})"
            else:
                detail = f"indisponível ({type(error).__name__})"
            raise RuntimeError(
                f"DataPool com label técnico {self.datapool_label!r} {detail}. "
                "Confira o campo Label no Maestro e o workspace do Runner."
            ) from error

    def check_ready(self) -> None:
        """Valida o DataPool antes que o produtor altere o sistema web."""
        self._get_datapool()

    def publish(
        self,
        *,
        batch_id: str,
        records: list[dict[str, Any]],
        reference_lote_ids: set[str],
    ) -> str:
        datapool = self._get_datapool()
        reference_json = json.dumps(
            sorted(reference_lote_ids), ensure_ascii=False
        )
        for record in records:
            values = {
                field_name: record.get(field_name, "")
                for field_name in DATAPOOL_FIELDS
            }
            values["reference_lotes_json"] = reference_json
            datapool.create_entry(DataPoolEntry(values=values))

        self.maestro.create_task(
            self.validator_activity_label,
            parameters={
                "batch_id": batch_id,
                "batch_total": len(records),
            },
        )
        return self.datapool_label


class BotCityDatapoolConsumer:
    def __init__(
        self,
        maestro: BotMaestroSDK,
        *,
        datapool_label: str,
        task_id: str | None,
    ) -> None:
        self.maestro = maestro
        self.datapool_label = datapool_label
        self.task_id = task_id

    def consume(self) -> ConsumedBatch:
        datapool = self.maestro.get_datapool(self.datapool_label)
        expected_batch_id = ""
        expected_total = 0
        if self.task_id:
            task = self.maestro.get_task(self.task_id)
            parameters = task.parameters or {}
            expected_batch_id = str(parameters.get("batch_id", ""))
            expected_total = int(parameters.get("batch_total", 0) or 0)

        items: list[QueueItem] = []
        while datapool.has_next() and (
            expected_total <= 0 or len(items) < expected_total
        ):
            entry = datapool.next(task_id=self.task_id)
            if entry is None:
                break
            item = QueueItem(dict(entry.values), raw_entry=entry)
            item_batch_id = str(item.values.get("batch_id", ""))
            target_batch_id = expected_batch_id or (
                str(items[0].values.get("batch_id", "")) if items else item_batch_id
            )
            if item_batch_id != target_batch_id:
                message = (
                    f"Item do lote {item_batch_id!r} recebido durante o lote "
                    f"{target_batch_id!r}."
                )
                item.report_system_error(message)
                for acquired in items:
                    acquired.report_system_error(message)
                raise RuntimeError(message)
            items.append(item)

            if expected_total <= 0:
                expected_total = int(item.values.get("batch_total", 0) or 0)

        if not items:
            raise LookupError(
                f"DataPool {self.datapool_label!r} sem itens pendentes."
            )

        if expected_total and len(items) != expected_total:
            message = (
                f"Lote incompleto: esperados {expected_total}, "
                f"recebidos {len(items)}."
            )
            for item in items:
                item.report_system_error(message)
            raise RuntimeError(message)

        batch_ids = {str(item.values.get("batch_id", "")) for item in items}
        if len(batch_ids) != 1:
            message = f"Foram consumidos lotes mistos: {sorted(batch_ids)}"
            for item in items:
                item.report_system_error(message)
            raise RuntimeError(message)

        first = items[0].values
        reference_lote_ids = set(
            json.loads(str(first.get("reference_lotes_json", "[]")))
        )
        return ConsumedBatch(
            batch_id=batch_ids.pop(),
            items=items,
            reference_lote_ids=reference_lote_ids,
            source_file=str(first.get("source_file", "datapool")),
        )

    def persist_states(self, batch: ConsumedBatch) -> Path | None:
        return None
