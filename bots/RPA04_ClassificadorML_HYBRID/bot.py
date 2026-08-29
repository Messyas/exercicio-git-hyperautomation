"""Bot RPA04_ClassificadorML_HYBRID (Smart Office / The DX Way).

Responsabilidade:
- Enriquecimento inteligente de divergências com causa provável via Machine Learning (Prioridade 4).
- Isolamento total: controlado por feature flag (`ML_ENABLED`), limiar de confiança (0.70) e circuit breaker.
- NUNCA crítico: se a API falhar, houver timeout ou baixa confiança, o item segue por fallback determinístico.
- Registra `origem_decisao` e `confianca_ml` para 100% dos itens processados.
"""

from __future__ import annotations

import json
import logging
import os
import sys
from pathlib import Path

# Ajusta path para importar módulos da raiz
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import get_settings
from src.classificador_divergencia import ClassificadorDivergencia

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("RPA04_ClassificadorML_HYBRID")


def main() -> int:
    logger.info("=== INICIANDO RPA04_ClassificadorML_HYBRID (Prioridade 4) ===")
    settings = get_settings()

    input_file = Path("data/datapool/lotes_consolidados.json")
    if not input_file.exists():
        logger.error("[RPA04_ML] Arquivo de lotes consolidados não encontrado: %s", input_file)
        return 1

    try:
        registros = json.loads(input_file.read_text(encoding="utf-8"))
        classificador = ClassificadorDivergencia(
            api_url=os.getenv("ML_API_URL", "http://127.0.0.1:8000"),
            enabled=settings.ml_enabled,
            timeout_ms=settings.ml_timeout_ms,
            confianca_minima=0.70,
            logger_instance=logger,
        )

        lotes_enriquecidos = []
        total_ml = 0
        total_fallback = 0

        for reg in registros:
            lote_id = reg.get("lote_id", "SEM_ID")
            obs = reg.get("observacao", "") or ""
            status_raw = reg.get("status", "") or ""
            turno = reg.get("turno", "A") or "A"

            # Executa a classificação (NUNCA propaga exceção ao chamador)
            resultado = classificador.classificar(
                lote_id=lote_id,
                observacao=obs,
                status_raw=status_raw,
                turno=turno,
            )

            # Enriquece o registro com a decisão e auditoria de origem
            reg_enriquecido = dict(reg)
            reg_enriquecido["causa_provavel_ml"] = resultado.causa_provavel_ml
            reg_enriquecido["confianca_ml"] = resultado.confianca_ml
            reg_enriquecido["origem_decisao"] = resultado.origem_decisao
            reg_enriquecido["motivo_fallback"] = resultado.motivo_fallback or "Nenhum"
            reg_enriquecido["latencia_ms"] = resultado.latencia_ms

            if resultado.origem_decisao == "ml":
                total_ml += 1
            else:
                total_fallback += 1

            lotes_enriquecidos.append(reg_enriquecido)

        output_dir = Path("data/datapool")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / "lotes_enriquecidos_ml.json"
        output_file.write_text(json.dumps(lotes_enriquecidos, indent=2, default=str, ensure_ascii=False), encoding="utf-8")

        logger.info(
            "OK: %d itens processados pelo Bot ML | %d via modelo ML | %d via fallback | salvo em '%s'",
            len(lotes_enriquecidos),
            total_ml,
            total_fallback,
            output_file,
        )
        return 0

    except Exception as exc:
        logger.exception("[RPA04_ML] Erro inesperado na orquestração de ML: %s", exc)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
