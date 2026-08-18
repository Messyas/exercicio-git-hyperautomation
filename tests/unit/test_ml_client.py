import httpx
import pytest

from src.ml_client import MLClient, MLPrediction


def test_classificar_sucesso_retorna_prediction():
    """Deve converter resposta HTTP 200 em objeto MLPrediction e manter circuito fechado."""
    call_count = 0

    def mock_handler(request: httpx.Request) -> httpx.Response:
        nonlocal call_count
        call_count += 1
        assert request.url.path == "/predict"
        return httpx.Response(
            200,
            json={
                "lote_id": "LOTE-001",
                "classe": "valido_automatico",
                "probabilidade": 0.95,
                "nivel_confianca": "alta",
                "acao": "VALIDO_AUTOMATICO",
                "modelo_versao": "rf-lotes-1.0.0",
            },
        )

    transport = httpx.MockTransport(mock_handler)
    client = httpx.Client(base_url="http://test-ml:8000", transport=transport)
    ml_client = MLClient(base_url="http://test-ml:8000", client=client)

    res = ml_client.classificar(
        lote_id="LOTE-001", status_raw="PENDENTE", turno="A", tem_obs=True
    )
    assert call_count == 1
    assert isinstance(res, MLPrediction)
    assert res.lote_id == "LOTE-001"
    assert res.classe == "valido_automatico"
    assert res.probabilidade == 0.95
    assert not ml_client.circuit_breaker.is_open


def test_timeout_retorna_none_sem_propagar():
    """Timeout de rede deve ser capturado, retornar None e incrementar falhas."""

    def mock_handler(request: httpx.Request) -> httpx.Response:
        raise httpx.TimeoutException("Timeout simulado")

    transport = httpx.MockTransport(mock_handler)
    client = httpx.Client(base_url="http://test-ml:8000", transport=transport)
    ml_client = MLClient(base_url="http://test-ml:8000", client=client)

    res = ml_client.classificar(
        lote_id="LOTE-002", status_raw="PENDENTE", turno="B", tem_obs=False
    )
    assert res is None
    assert ml_client.circuit_breaker.consecutive_failures == 1
    assert not ml_client.circuit_breaker.is_open


def test_erro_http_retorna_none_sem_propagar():
    """HTTP 500 deve ser capturado, retornar None e incrementar falhas."""

    def mock_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, json={"error": "Internal Error"})

    transport = httpx.MockTransport(mock_handler)
    client = httpx.Client(base_url="http://test-ml:8000", transport=transport)
    ml_client = MLClient(base_url="http://test-ml:8000", client=client)

    res = ml_client.classificar(
        lote_id="LOTE-003", status_raw="PENDENTE", turno="C", tem_obs=True
    )
    assert res is None
    assert ml_client.circuit_breaker.consecutive_failures == 1


def test_json_invalido_retorna_none_sem_propagar():
    """Resposta JSON truncada ou inválida deve retornar None."""

    def mock_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="{invalid_json...")

    transport = httpx.MockTransport(mock_handler)
    client = httpx.Client(base_url="http://test-ml:8000", transport=transport)
    ml_client = MLClient(base_url="http://test-ml:8000", client=client)

    res = ml_client.classificar(
        lote_id="LOTE-004", status_raw="PENDENTE", turno="A", tem_obs=True
    )
    assert res is None
    assert ml_client.circuit_breaker.consecutive_failures == 1


def test_resposta_com_campo_inesperado_ou_lote_trocado_retorna_none():
    """O cliente não aceita resposta JSON fora do contrato ou de outro lote."""
    def mock_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "lote_id": "LOTE-DE-OUTRO-CLIENTE",
                "classe": "valido_automatico",
                "probabilidade": 0.95,
                "nivel_confianca": "alta",
                "acao": "VALIDO_AUTOMATICO",
                "modelo_versao": "rf-lotes-1.0.0",
                "campo_injetado": "não confiar",
            },
        )

    client = httpx.Client(base_url="http://test-ml:8000", transport=httpx.MockTransport(mock_handler))
    ml_client = MLClient(base_url="http://test-ml:8000", client=client)

    assert ml_client.classificar(lote_id="LOTE-005", status_raw="PENDENTE", turno="A", tem_obs=False) is None
    assert ml_client.circuit_breaker.consecutive_failures == 1


def test_cinco_falhas_abrem_circuito_e_sexta_chamada_nao_tenta_rede():
    """Após 5 falhas consecutivas, o circuito abre e a 6ª chamada não dispara requisição."""
    call_count = 0

    def mock_handler(request: httpx.Request) -> httpx.Response:
        nonlocal call_count
        call_count += 1
        return httpx.Response(503, json={"status": "unavailable"})

    transport = httpx.MockTransport(mock_handler)
    client = httpx.Client(base_url="http://test-ml:8000", transport=transport)
    ml_client = MLClient(base_url="http://test-ml:8000", failure_threshold=5, client=client)

    # 5 chamadas com falha
    for i in range(5):
        res = ml_client.classificar(
            lote_id=f"LOTE-FALHA-{i}", status_raw="EM ANÁLISE", turno="A", tem_obs=False
        )
        assert res is None

    assert call_count == 5
    assert ml_client.circuit_breaker.is_open

    # 6ª chamada: circuito já está aberto!
    res6 = ml_client.classificar(
        lote_id="LOTE-FALHA-6", status_raw="EM ANÁLISE", turno="A", tem_obs=False
    )
    assert res6 is None
    # Deve continuar 5 chamadas de rede!
    assert call_count == 5


def test_sucesso_zera_falhas_consecutivas():
    """Um sucesso interrupção da sequência reseta o contador de falhas."""
    should_fail = True

    def mock_handler(request: httpx.Request) -> httpx.Response:
        if should_fail:
            return httpx.Response(500)
        return httpx.Response(
            200,
            json={
                "lote_id": "LOTE-OK",
                "classe": "revisar",
                "probabilidade": 0.70,
                "nivel_confianca": "media",
                "acao": "REVISAR",
                "modelo_versao": "rf-lotes-1.0.0",
            },
        )

    transport = httpx.MockTransport(mock_handler)
    client = httpx.Client(base_url="http://test-ml:8000", transport=transport)
    ml_client = MLClient(base_url="http://test-ml:8000", failure_threshold=5, client=client)

    # 3 falhas
    for i in range(3):
        ml_client.classificar(lote_id=f"LOTE-{i}", status_raw="EM AJUSTE", turno="B", tem_obs=True)

    assert ml_client.circuit_breaker.consecutive_failures == 3

    # Sucesso na 4ª
    should_fail = False
    res = ml_client.classificar(lote_id="LOTE-OK", status_raw="EM AJUSTE", turno="B", tem_obs=True)
    assert res is not None
    assert ml_client.circuit_breaker.consecutive_failures == 0
    assert not ml_client.circuit_breaker.is_open


def test_reset_manual_fecha_circuito():
    """reset_circuit() deve fechar o circuito e permitir novas chamadas."""
    ml_client = MLClient(base_url="http://test-ml:8000", failure_threshold=2)
    ml_client.circuit_breaker.record_failure()
    ml_client.circuit_breaker.record_failure()
    assert ml_client.circuit_breaker.is_open

    ml_client.reset_circuit()
    assert not ml_client.circuit_breaker.is_open
    assert ml_client.circuit_breaker.consecutive_failures == 0
