import json
from pathlib import Path
import subprocess

import httpx

from scripts.demo_torneio import (
    construir_payloads,
    derrubar_api_docker,
    executar_fila,
    montar_resumo,
    verificar_completude,
)
from src.ml_client import MLClient


def test_ensaio_processa_50_tarefas_com_fila_limitada_sem_perdas():
    """A fila limitada preserva todas as 50 tarefas mesmo com múltiplos workers."""
    def mock_handler(request: httpx.Request) -> httpx.Response:
        lote_id = json.loads(request.content)["lote_id"]
        return httpx.Response(
            200,
            json={
                "lote_id": lote_id,
                "classe": "revisar",
                "probabilidade": 0.70,
                "nivel_confianca": "media",
                "acao": "REVISAR",
                "modelo_versao": "rf-lotes-1.0.0",
            },
        )

    client = httpx.Client(base_url="http://test-ml:8000", transport=httpx.MockTransport(mock_handler))
    ml_client = MLClient(base_url="http://test-ml:8000", client=client)
    resultados = executar_fila(construir_payloads(50), ml_client=ml_client, workers=4, tamanho_fila=7)

    verificar_completude(resultados, 50)
    assert len(resultados) == 50
    assert all(resultado.sucesso for resultado in resultados)
    assert len({resultado.lote_id for resultado in resultados}) == 50

    resumo = montar_resumo(
        resultados,
        total=50,
        workers=4,
        tamanho_fila=7,
        validacoes_json=[],
        sabotagem=False,
    )
    assert {"p50", "p95", "media", "max"} <= set(resumo["latencia_ms"])


def test_sabotagem_usa_compose_isolado_quando_informado(monkeypatch, tmp_path: Path):
    """O ensaio pode derrubar a API do Compose de sabotagem, sem tocar o principal."""
    compose_file = tmp_path / "docker-compose.sabotagem.yml"
    compose_file.touch()
    comandos: list[list[str]] = []

    def fake_run(comando, **_kwargs):
        comandos.append(comando)
        return subprocess.CompletedProcess(comando, returncode=0)

    monkeypatch.setattr("scripts.demo_torneio.subprocess.run", fake_run)

    derrubar_api_docker(
        compose_file=compose_file,
        compose_project="sabotagem-ml",
    )

    assert comandos == [
        [
            "docker",
            "compose",
            "-f",
            str(compose_file.resolve()),
            "-p",
            "sabotagem-ml",
            "kill",
            "api-ml",
        ]
    ]
