"""Ensaio de carga, contrato JSON e sabotagem controlada da API de ML.

O script usa uma fila limitada para exercer a API sem criar uma explosão de
requisições. A sabotagem do container só ocorre com ``--sabotage-docker``.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json
import logging
import math
from pathlib import Path
import queue
import subprocess
import sys
import threading
import time
from typing import Any, Iterable

import httpx

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import settings
from src.ml_client import MLClient


LOGGER = logging.getLogger("ensaio_torneio_ml")
STATUS_AMBIGUOS = (
    "PENDENTE",
    "EM ANÁLISE",
    "EM AJUSTE",
    "ESPECIFICAÇÃO EM REVISÃO",
    "AGUARDANDO REINSPEÇÃO",
    "APROVADO PARCIAL",
    "CANCELADO",
)
TURNOS = ("A", "B", "C")


@dataclass(frozen=True)
class ResultadoRequisicao:
    sequencia: int
    lote_id: str
    sucesso: bool
    fallback_offline: bool
    circuit_open: bool
    latencia_ms: float
    erro: str | None


def construir_payloads(total: int) -> list[dict[str, object]]:
    """Gera cargas determinísticas e válidas, sem dados pessoais ou identificadores reais."""
    if total < 1:
        raise ValueError("total deve ser maior que zero")

    payloads: list[dict[str, object]] = []
    for indice in range(total):
        payloads.append(
            {
                "lote_id": f"TORNEIO-{indice + 1:05d}",
                "status_raw": STATUS_AMBIGUOS[indice % len(STATUS_AMBIGUOS)],
                "turno": TURNOS[indice % len(TURNOS)],
                "tem_obs": bool(indice % 2),
            }
        )
    return payloads


def validar_payload_local(payload: dict[str, object]) -> None:
    """Espelha o contrato estrito do endpoint antes de transmitir o JSON."""
    campos = {"lote_id", "status_raw", "turno", "tem_obs"}
    if set(payload) != campos:
        raise ValueError("Payload possui campos ausentes ou não permitidos")
    if not isinstance(payload["lote_id"], str) or not 1 <= len(payload["lote_id"]) <= 80:
        raise ValueError("lote_id inválido")
    if not isinstance(payload["status_raw"], str) or not 1 <= len(payload["status_raw"]) <= 100:
        raise ValueError("status_raw inválido")
    if payload["turno"] not in TURNOS:
        raise ValueError("turno inválido")
    if not isinstance(payload["tem_obs"], bool):
        raise ValueError("tem_obs deve ser booleano")


def validar_rejeicoes_da_api(api_url: str, timeout_ms: int) -> list[dict[str, object]]:
    """Confirma que JSONs malformados não chegam ao modelo."""
    base = construir_payloads(1)[0]
    casos_invalidos = {
        "turno_invalido": {**base, "turno": "X"},
        "campo_extra": {**base, "origem_nao_confiavel": "tentativa"},
        "booleano_coagido": {**base, "tem_obs": 1},
    }
    resultados: list[dict[str, object]] = []
    timeout = httpx.Timeout(max(timeout_ms / 1000.0, 0.1))
    with httpx.Client(base_url=api_url.rstrip("/"), timeout=timeout) as client:
        for nome, payload in casos_invalidos.items():
            response = client.post("/predict", json=payload)
            resultado = {"caso": nome, "status_code": response.status_code}
            resultados.append(resultado)
            if response.status_code != 422:
                raise RuntimeError(f"API aceitou JSON inválido no caso {nome}: HTTP {response.status_code}")
    return resultados


def executar_fila(
    payloads: Iterable[dict[str, object]],
    *,
    ml_client: MLClient,
    workers: int,
    tamanho_fila: int,
    inicio_sequencia: int = 1,
) -> list[ResultadoRequisicao]:
    """Executa payloads com backpressure: no máximo ``tamanho_fila`` pendentes."""
    tarefas = list(payloads)
    fila: queue.Queue[tuple[int, dict[str, object]] | None] = queue.Queue(maxsize=tamanho_fila)
    resultados: list[ResultadoRequisicao] = []
    lock_resultados = threading.Lock()

    def worker() -> None:
        while True:
            tarefa = fila.get()
            try:
                if tarefa is None:
                    return
                sequencia, payload = tarefa
                validar_payload_local(payload)
                inicio = time.perf_counter()
                circuit_open_antes = ml_client.circuit_breaker.is_open
                predicao = ml_client.classificar(
                    lote_id=str(payload["lote_id"]),
                    status_raw=str(payload["status_raw"]),
                    turno=str(payload["turno"]),
                    tem_obs=bool(payload["tem_obs"]),
                )
                latencia_ms = (time.perf_counter() - inicio) * 1000.0
                resultado = ResultadoRequisicao(
                    sequencia=sequencia,
                    lote_id=str(payload["lote_id"]),
                    sucesso=predicao is not None,
                    fallback_offline=predicao is None,
                    circuit_open=circuit_open_antes or ml_client.circuit_breaker.is_open,
                    latencia_ms=round(latencia_ms, 2),
                    erro=None if predicao is not None else "network_or_api_error",
                )
            except Exception as exc:  # defesa do ensaio: uma tarefa não interrompe a fila
                resultado = ResultadoRequisicao(
                    sequencia=tarefa[0] if tarefa is not None else -1,
                    lote_id=str(tarefa[1].get("lote_id", "desconhecido")) if tarefa else "desconhecido",
                    sucesso=False,
                    fallback_offline=True,
                    circuit_open=ml_client.circuit_breaker.is_open,
                    latencia_ms=0.0,
                    erro=type(exc).__name__,
                )
            finally:
                fila.task_done()
            with lock_resultados:
                resultados.append(resultado)

    threads = [threading.Thread(target=worker, name=f"ml-worker-{indice + 1}") for indice in range(workers)]
    for thread in threads:
        thread.start()
    for indice, payload in enumerate(tarefas, start=inicio_sequencia):
        fila.put((indice, payload))
    for _ in threads:
        fila.put(None)
    fila.join()
    for thread in threads:
        thread.join()
    return sorted(resultados, key=lambda resultado: resultado.sequencia)


def derrubar_api_docker(
    *, compose_file: Path | None = None, compose_project: str | None = None
) -> None:
    """Derruba deliberadamente a API em um Compose; uso somente em demonstração.

    ``compose_file`` permite isolar o ensaio de carga do Compose principal. Sem
    ele, preserva o comportamento histórico de usar o perfil ``ml`` do Compose
    da raiz do repositório.
    """
    comando = ["docker", "compose"]
    if compose_file is not None:
        comando.extend(["-f", str(compose_file.resolve())])
    else:
        comando.extend(["--profile", "ml"])
    if compose_project:
        comando.extend(["-p", compose_project])
    comando.extend(["kill", "api-ml"])
    resultado = subprocess.run(comando, cwd=ROOT, check=False, capture_output=True, text=True, timeout=30)
    if resultado.returncode != 0:
        detalhe = resultado.stderr.strip() or resultado.stdout.strip()
        raise RuntimeError(f"Não foi possível sabotar api-ml: {detalhe}")
    LOGGER.warning("SABOTAGEM_EXECUTADA: container api-ml derrubado deliberadamente")


def verificar_completude(resultados: list[ResultadoRequisicao], total_esperado: int) -> None:
    sequencias = [resultado.sequencia for resultado in resultados]
    if len(resultados) != total_esperado or set(sequencias) != set(range(1, total_esperado + 1)):
        raise RuntimeError("Fila perdeu, duplicou ou deixou tarefas sem processar")


def montar_resumo(
    resultados: list[ResultadoRequisicao],
    *,
    total: int,
    workers: int,
    tamanho_fila: int,
    validacoes_json: list[dict[str, object]],
    sabotagem: bool,
) -> dict[str, Any]:
    latencias = sorted(resultado.latencia_ms for resultado in resultados)
    indice_p95 = max(0, math.ceil(len(latencias) * 0.95) - 1) if latencias else 0
    return {
        "total_solicitado": total,
        "total_processado": len(resultados),
        "sucessos": sum(resultado.sucesso for resultado in resultados),
        "fallbacks_offline": sum(resultado.fallback_offline for resultado in resultados),
        "circuito_aberto_em": sum(resultado.circuit_open for resultado in resultados),
        "workers": workers,
        "tamanho_maximo_fila": tamanho_fila,
        "sabotagem_docker": sabotagem,
        "validacoes_json": validacoes_json,
        "latencia_ms": {
            "p50": latencias[len(latencias) // 2] if latencias else 0.0,
            "p95": latencias[indice_p95] if latencias else 0.0,
            "media": round(sum(latencias) / len(latencias), 2) if latencias else 0.0,
            "max": max(latencias, default=0.0),
        },
        "resultados": [asdict(resultado) for resultado in resultados],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ensaio de carga e sabotagem da API de ML.")
    parser.add_argument("--total", type=int, default=50, help="Quantidade de JSONs válidos a processar (padrão: 50).")
    parser.add_argument("--workers", type=int, default=5, help="Quantidade máxima de requisições concorrentes.")
    parser.add_argument("--queue-size", type=int, default=20, help="Máximo de tarefas pendentes na fila.")
    parser.add_argument("--api-url", default=settings.ml_api_url, help="URL base da API de ML.")
    parser.add_argument("--timeout-ms", type=int, default=settings.ml_timeout_ms, help="Timeout por requisição.")
    parser.add_argument("--sabotage-docker", action="store_true", help="Derruba api-ml entre as duas fases do ensaio.")
    parser.add_argument("--sabotage-after", type=int, default=10, help="Quantidade processada antes da sabotagem.")
    parser.add_argument(
        "--compose-file",
        type=Path,
        help="Arquivo Compose usado para derrubar api-ml; permite usar o ambiente isolado de sabotagem.",
    )
    parser.add_argument(
        "--compose-project",
        help="Nome do projeto Compose usado na sabotagem (ex.: sabotagem-ml).",
    )
    parser.add_argument("--output", type=Path, default=Path("data/output/ensaio_torneio_ml.json"), help="Relatório JSON de saída.")
    args = parser.parse_args()
    if args.total < 1 or args.workers < 1 or args.queue_size < 1 or args.timeout_ms < 1:
        parser.error("total, workers, queue-size e timeout-ms devem ser positivos")
    if args.sabotage_docker and not 0 < args.sabotage_after < args.total:
        parser.error("sabotage-after deve estar entre 1 e total - 1 quando a sabotagem estiver ativa")
    return args


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)
    args = parse_args()
    payloads = construir_payloads(args.total)
    validacoes_json = validar_rejeicoes_da_api(args.api_url, args.timeout_ms)
    LOGGER.info("Validações de JSON rejeitadas corretamente: %s", validacoes_json)

    ml_client = MLClient(
        base_url=args.api_url,
        timeout_ms=args.timeout_ms,
        failure_threshold=settings.ml_failure_threshold,
        logger_instance=LOGGER,
    )
    try:
        if args.sabotage_docker:
            primeira_fase = executar_fila(
                payloads[:args.sabotage_after],
                ml_client=ml_client,
                workers=args.workers,
                tamanho_fila=args.queue_size,
            )
            derrubar_api_docker(
                compose_file=args.compose_file,
                compose_project=args.compose_project,
            )
            segunda_fase = executar_fila(
                payloads[args.sabotage_after:],
                ml_client=ml_client,
                workers=args.workers,
                tamanho_fila=args.queue_size,
                inicio_sequencia=args.sabotage_after + 1,
            )
            resultados = primeira_fase + segunda_fase
        else:
            resultados = executar_fila(
                payloads,
                ml_client=ml_client,
                workers=args.workers,
                tamanho_fila=args.queue_size,
            )
    finally:
        ml_client.close()

    resultados.sort(key=lambda resultado: resultado.sequencia)
    verificar_completude(resultados, args.total)
    resumo = montar_resumo(
        resultados,
        total=args.total,
        workers=args.workers,
        tamanho_fila=args.queue_size,
        validacoes_json=validacoes_json,
        sabotagem=args.sabotage_docker,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(resumo, ensure_ascii=False, indent=2), encoding="utf-8")

    LOGGER.info(
        "Ensaio concluído: processados=%s sucessos=%s fallbacks=%s circuito_aberto=%s relatório=%s",
        resumo["total_processado"], resumo["sucessos"], resumo["fallbacks_offline"], resumo["circuito_aberto_em"], args.output,
    )
    if not resumo["sucessos"] or (args.sabotage_docker and not resumo["fallbacks_offline"]):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
