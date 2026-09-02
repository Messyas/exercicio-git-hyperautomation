import json
from pathlib import Path
import joblib
import pytest

from api_ml.features import FEATURE_ORDER
from api_ml.model_service import ModelService
from api_ml.schemas import LoteInput


def test_modelo_salvo_recarrega_e_prediz():
    """Testa se o modelo salvo em .pkl pode ser recarregado pelo ModelService e realiza predição."""
    model_path = Path("models/classificador_lotes.pkl")
    assert model_path.exists(), "O arquivo models/classificador_lotes.pkl deve existir."

    service = ModelService(model_path)
    service.load()
    assert service.is_loaded
    assert service.model_version == "rf-lotes-1.0.0"

    # Testa inferência para um lote de teste
    lote = LoteInput(
        lote_id="LOTE-TEST-001",
        status_raw="APROVADO PARCIAL",
        turno="A",
        tem_obs=True,
    )
    res = service.predict(lote)
    assert res.lote_id == "LOTE-TEST-001"
    assert res.probabilidade >= 0.0 and res.probabilidade <= 1.0
    assert res.modelo_versao == "rf-lotes-1.0.0"


def test_metricas_e_sha_no_manifesto_e_bundle():
    """Valida se o bundle .pkl e o arquivo .metrics.json possuem os metadados exigidos."""
    model_path = Path("models/classificador_lotes.pkl")
    metrics_path = Path("models/classificador_lotes.metrics.json")

    assert metrics_path.exists()
    with open(metrics_path, "r", encoding="utf-8") as f:
        metrics = json.load(f)

    assert "accuracy" in metrics
    assert "macro_f1" in metrics
    assert "latencia_ms" in metrics
    assert metrics["macro_f1"] >= 0.80

    bundle = joblib.load(model_path)
    assert bundle["feature_order"] == list(FEATURE_ORDER)
    assert "dataset_sha256" in bundle
    assert "trained_at" in bundle
