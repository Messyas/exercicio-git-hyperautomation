import logging
import httpx
import pytest

from dashboard.servico_validacao import RegistroValidado
from src.item_processor import ItemProcessor
from src.ml_client import MLClient


@pytest.mark.integration
def test_sabotagem_falha_parcial_e_circuit_breaker():
    """Ensaio de Sabotagem:
    Simula um lote com 10 itens ambíguos.
    - As 3 primeiras chamadas respondem 200 (sucesso).
    - As 5 chamadas seguintes falham (HTTP 500).
    - A 5ª falha abre o circuit breaker.
    - As chamadas 9 e 10 entram em fallback sem disparar requisição HTTP.
    - O lote inteiro é processado até o fim e todas as 10 decisões ficam auditadas.
    """
    chamadas_rede = 0

    def mock_handler(request: httpx.Request) -> httpx.Response:
        nonlocal chamadas_rede
        chamadas_rede += 1

        if chamadas_rede <= 3:
            return httpx.Response(
                200,
                json={
                    "lote_id": f"LOTE-AMB-{chamadas_rede}",
                    "classe": "valido_automatico",
                    "probabilidade": 0.90,
                    "nivel_confianca": "alta",
                    "acao": "VALIDO_AUTOMATICO",
                    "modelo_versao": "rf-lotes-1.0.0",
                },
            )
        else:
            return httpx.Response(500, json={"error": "Simulação de sabotagem/queda de serviço"})

    transport = httpx.MockTransport(mock_handler)
    httpx_client = httpx.Client(base_url="http://sabotagem-ml:8000", transport=transport)
    ml_client = MLClient(
        base_url="http://sabotagem-ml:8000",
        failure_threshold=5,
        client=httpx_client,
    )

    registros_ambiguos = [
        RegistroValidado(
            lote_id=f"LOTE-AMB-{i}",
            produto="Prod Sabotagem",
            linha="Linha 1",
            turno="A",
            status="PENDENTE",
            responsavel="Op 1",
            data="01/01/2026",
            observacao="Obs",
            data_referencia="01/01/2026",
            classificacao="Ambíguo",
        )
        for i in range(1, 11)
    ]

    logger = logging.getLogger("test_sabotagem")
    processor = ItemProcessor(ml_client, logger)

    decisoes = processor.processar_lote(registros_ambiguos)

    # 1. Processamento chega ao último item (10 decisões)
    assert len(decisoes) == 10

    # 2. As 3 primeiras obtêm resposta válida do modelo
    for i in range(3):
        assert decisoes[i].acao_final == "VALIDO_AUTOMATICO"
        assert decisoes[i].tentou_rede is True
        assert decisoes[i].circuit_open is False

    # 3. As cinco falhas seguintes retornam REVISAO_ML_OFFLINE. A quinta
    # registra exatamente o instante em que o breaker passou a OPEN.
    for i in range(3, 7):
        assert decisoes[i].acao_final == "REVISAO_ML_OFFLINE"
        assert decisoes[i].tentou_rede is True
        assert decisoes[i].circuit_open is False

    assert decisoes[7].acao_final == "REVISAO_ML_OFFLINE"
    assert decisoes[7].tentou_rede is True
    assert decisoes[7].circuit_open is True
    assert decisoes[7].erro_tipo == "circuit_open"

    # 4. A 5ª falha (índice 7) abriu o breaker.
    assert ml_client.circuit_breaker.is_open

    # 5. Os itens 9 e 10 (índices 8 e 9) entram em fallback SEM disparar rede
    for i in range(8, 10):
        assert decisoes[i].acao_final == "REVISAO_ML_OFFLINE"
        assert decisoes[i].tentou_rede is False
        assert decisoes[i].circuit_open is True

    # Total de chamadas de rede no transport == exatamente 8 (3 sucessos + 5 falhas)
    assert chamadas_rede == 8
