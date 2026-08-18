from unittest.mock import MagicMock
from fastapi.testclient import TestClient
import pytest

from api_ml.main import app, model_service
from api_ml.schemas import (
    AcaoML,
    ClasseML,
    LoteInput,
    NivelConfianca,
    PredictionOutput,
    determinar_acao,
)


@pytest.fixture
def client():
    return TestClient(app)


def test_limites_de_confianca_065_e_085():
    """Testa rigorosamente as fronteiras de probabilidade (0.65 e 0.85)."""
    # 0.85 e acima -> ALTA
    nivel, acao = determinar_acao(ClasseML.VALIDO_AUTOMATICO, 0.85)
    assert nivel == NivelConfianca.ALTA
    assert acao == AcaoML.VALIDO_AUTOMATICO

    nivel, acao = determinar_acao(ClasseML.RECUSAR_AUTOMATICO, 0.90)
    assert nivel == NivelConfianca.ALTA
    assert acao == AcaoML.RECUSAR_AUTOMATICO

    nivel, acao = determinar_acao(ClasseML.REVISAR, 0.88)
    assert nivel == NivelConfianca.ALTA
    assert acao == AcaoML.REVISAR

    # 0.849999 -> MEDIA (REVISAR)
    nivel, acao = determinar_acao(ClasseML.VALIDO_AUTOMATICO, 0.849999)
    assert nivel == NivelConfianca.MEDIA
    assert acao == AcaoML.REVISAR

    # 0.65 -> MEDIA (REVISAR)
    nivel, acao = determinar_acao(ClasseML.RECUSAR_AUTOMATICO, 0.65)
    assert nivel == NivelConfianca.MEDIA
    assert acao == AcaoML.REVISAR

    # 0.649999 -> BAIXA (REVISAO_PRIORITARIA)
    nivel, acao = determinar_acao(ClasseML.VALIDO_AUTOMATICO, 0.649999)
    assert nivel == NivelConfianca.BAIXA
    assert acao == AcaoML.REVISAO_PRIORITARIA

    nivel, acao = determinar_acao(ClasseML.REVISAR, 0.20)
    assert nivel == NivelConfianca.BAIXA
    assert acao == AcaoML.REVISAO_PRIORITARIA


def test_health_sem_modelo_retorna_503(client):
    """Quando o modelo não está carregado, /health deve retornar 503."""
    model_service._is_loaded = False
    model_service._model_version = None
    response = client.get("/health")
    assert response.status_code == 503
    data = response.json()
    assert data["status"] == "unavailable"
    assert data["model_loaded"] is False
    assert data["modelo_versao"] is None


def test_health_com_modelo_retorna_200(client):
    """Quando o modelo está carregado, /health deve retornar 200."""
    model_service._is_loaded = True
    model_service._model_version = "rf-lotes-1.0.0"
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["model_loaded"] is True
    assert data["modelo_versao"] == "rf-lotes-1.0.0"
    assert float(response.headers["X-Request-Latency-Ms"]) >= 0.0
    assert float(response.headers["X-Queue-Wait-Ms"]) == 0.0


def test_predict_sem_modelo_retorna_503(client):
    """POST /predict sem modelo deve retornar 503."""
    model_service._is_loaded = False
    payload = {
        "lote_id": "LOTE-123",
        "status_raw": "PENDENTE",
        "turno": "A",
        "tem_obs": True,
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 503
    assert "Modelo de ML indisponível" in response.json()["detail"]


def test_predict_turno_invalido_retorna_422(client):
    """POST /predict com turno inválido deve retornar 422 Unprocessable Entity."""
    payload = {
        "lote_id": "LOTE-123",
        "status_raw": "PENDENTE",
        "turno": "X",  # Inválido
        "tem_obs": True,
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 422


def test_predict_rejeita_campo_extra_e_booleano_coagido(client):
    """O contrato é estrito para impedir JSON inesperado de chegar ao modelo."""
    payload = {
        "lote_id": "LOTE-123",
        "status_raw": "PENDENTE",
        "turno": "A",
        "tem_obs": True,
    }
    assert client.post("/predict", json={**payload, "origem": "externa"}).status_code == 422
    assert client.post("/predict", json={**payload, "tem_obs": 1}).status_code == 422


def test_predict_payload_valido_retorna_contrato(client):
    """POST /predict com modelo mockado deve retornar contrato de PredictionOutput."""
    model_service._is_loaded = True
    model_service._model_version = "rf-lotes-1.0.0"
    
    mock_prediction = PredictionOutput(
        lote_id="LOTE-999",
        classe=ClasseML.VALIDO_AUTOMATICO,
        probabilidade=0.92,
        nivel_confianca=NivelConfianca.ALTA,
        acao=AcaoML.VALIDO_AUTOMATICO,
        modelo_versao="rf-lotes-1.0.0",
    )
    
    original_predict = model_service.predict
    model_service.predict = MagicMock(return_value=mock_prediction)
    try:
        payload = {
            "lote_id": "LOTE-999",
            "status_raw": "APROVADO PARCIAL",
            "turno": "B",
            "tem_obs": True,
        }
        response = client.post("/predict", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["lote_id"] == "LOTE-999"
        assert data["classe"] == "valido_automatico"
        assert data["probabilidade"] == 0.92
        assert data["nivel_confianca"] == "alta"
        assert data["acao"] == "VALIDO_AUTOMATICO"
        assert data["modelo_versao"] == "rf-lotes-1.0.0"
        assert float(response.headers["X-Inference-Latency-Ms"]) >= 0.0
        assert float(response.headers["X-Request-Latency-Ms"]) >= 0.0
        assert float(response.headers["X-Queue-Wait-Ms"]) >= 0.0
    finally:
        model_service.predict = original_predict
