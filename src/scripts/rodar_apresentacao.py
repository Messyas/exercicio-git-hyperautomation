"""Runner do lote incidente para a apresentação S10-B."""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from coletor import run_collector  # noqa: E402
from config import get_settings  # noqa: E402
from pipeline import main as run_pipeline  # noqa: E402
from src.utils.excel_source import load_excel_batch  # noqa: E402


def _score_path() -> Path:
    return ROOT / "data" / "reports" / "apresentacao" / "placar.json"


def _update_score(**values: object) -> None:
    path = _score_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {"grupos": {}}
    group = os.getenv("PRESENTATION_GROUP", "messyas").strip() or "messyas"
    current = payload.setdefault("grupos", {}).setdefault(group, {"eixos": {}})
    current.update(values)
    current["eixos"].setdefault("orquestracao", 0)
    current["eixos"].setdefault("hibrido", 0)
    current["eixos"].setdefault("resiliencia", 0)
    current["eixos"].setdefault("notificacao", 0)
    current["total"] = sum(current["eixos"].values())
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    settings = get_settings()
    try:
        batch = load_excel_batch(settings.default_input_file)
    except Exception as exc:
        _update_score(status="FALHOU_ENTRADA", detalhe=str(exc))
        print(f"Lote incidente inválido: {exc}")
        return 1

    if len(batch.records()) != 30:
        message = f"O lote incidente deve conter 30 casos; recebido: {len(batch.records())}."
        _update_score(status="FALHOU_QUANTIDADE", detalhe=message)
        print(message)
        return 1

    _update_score(
        status="AGUARDANDO_SABOTAGEM",
        lote=batch.batch_id,
        total_casos=30,
        detalhe="Aguardando início do pipeline; o instrutor pode derrubar api-ml.",
    )
    delay = max(0, int(os.getenv("PRESENTATION_START_DELAY_SECONDS", "15")))
    print(f"Lote de 30 casos validado. Início em {delay}s; sabotagem ML liberada.")
    time.sleep(delay)

    if run_collector() != 0:
        _update_score(status="FALHOU_COLETOR", detalhe="Coletor não concluiu.")
        return 1
    _update_score(status="COLETOR_OK", eixos={"orquestracao": 25, "hibrido": 0, "resiliencia": 0, "notificacao": 0})

    pipeline_status = run_pipeline()
    if pipeline_status != 0:
        _update_score(status="FALHOU_PIPELINE", detalhe="Pipeline encerrou com falha.")
        return pipeline_status

    _update_score(
        status="PIPELINE_CONCLUIDO",
        detalhe="Abra os logs e relatórios; pontuação de resiliência/notificação é confirmada pelo revisor.",
        eixos={"orquestracao": 25, "hibrido": 25, "resiliencia": 0, "notificacao": 0},
    )
    print(f"Apresentação concluída. Placar: {_score_path()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
