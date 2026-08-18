from dataclasses import dataclass
import logging
import math
import threading
from typing import Optional, Protocol
import httpx

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class MLPrediction:
    lote_id: str
    classe: str
    probabilidade: float
    nivel_confianca: str
    acao: str
    modelo_versao: str

    def to_dict(self) -> dict[str, object]:
        return {
            "lote_id": self.lote_id,
            "classe": self.classe,
            "probabilidade": self.probabilidade,
            "nivel_confianca": self.nivel_confianca,
            "acao": self.acao,
            "modelo_versao": self.modelo_versao,
        }


class MLClassifier(Protocol):
    def classificar(
        self, *, lote_id: str, status_raw: str, turno: str, tem_obs: bool
    ) -> Optional[MLPrediction]: ...


class CircuitBreaker:
    """Implementação simples de Circuit Breaker com estados CLOSED e OPEN."""

    def __init__(self, failure_threshold: int = 5):
        self.failure_threshold = max(1, failure_threshold)
        self._consecutive_failures = 0
        self._is_open = False
        self._lock = threading.Lock()

    def allow_request(self) -> bool:
        with self._lock:
            return not self._is_open

    def record_success(self) -> None:
        with self._lock:
            self._consecutive_failures = 0
            self._is_open = False

    def record_failure(self) -> None:
        with self._lock:
            self._consecutive_failures += 1
            should_log = self._consecutive_failures >= self.failure_threshold and not self._is_open
            if should_log:
                self._is_open = True
            failures = self._consecutive_failures
        if should_log:
            logger.warning(
                f"CircuitBreaker aberto após {failures} falhas consecutivas."
            )

    def reset(self) -> None:
        with self._lock:
            self._consecutive_failures = 0
            self._is_open = False

    @property
    def is_open(self) -> bool:
        with self._lock:
            return self._is_open

    @property
    def consecutive_failures(self) -> int:
        with self._lock:
            return self._consecutive_failures


class MLClient:
    """Cliente HTTP para comunicação com a API de ML com resiliência por Circuit Breaker."""

    def __init__(
        self,
        base_url: str,
        timeout_ms: int = 1000,
        failure_threshold: int = 5,
        client: Optional[httpx.Client] = None,
        logger_instance: Optional[logging.Logger] = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout_sec = max(0.001, timeout_ms / 1000.0)
        self.logger = logger_instance or logger
        self.circuit_breaker = CircuitBreaker(failure_threshold=failure_threshold)

        if client is not None:
            self._client = client
            self._owns_client = False
        else:
            timeout_config = httpx.Timeout(timeout=self.timeout_sec, connect=min(0.20, self.timeout_sec))
            self._client = httpx.Client(base_url=self.base_url, timeout=timeout_config)
            self._owns_client = True

    def classificar(
        self, *, lote_id: str, status_raw: str, turno: str, tem_obs: bool
    ) -> Optional[MLPrediction]:
        """Classifica um lote ambíguo chamando POST /predict na API de ML.
        
        Caso o circuito esteja aberto ou a chamada falhe, retorna None sem propagar exceção.
        """
        if not self.circuit_breaker.allow_request():
            self.logger.warning(
                f"Circuito aberto. Chamada para o lote '{lote_id}' ignorada sem tentar rede."
            )
            return None

        payload = {
            "lote_id": lote_id,
            "status_raw": status_raw,
            "turno": turno,
            "tem_obs": bool(tem_obs),
        }

        try:
            response = self._client.post("/predict", json=payload)
            if response.status_code != 200:
                self.logger.warning(
                    f"API de ML retornou HTTP {response.status_code} para lote {lote_id}"
                )
                self.circuit_breaker.record_failure()
                return None

            data = response.json()
            if not isinstance(data, dict):
                raise ValueError("Resposta da API de ML não é um objeto JSON válido")

            prediction = self._validar_resposta(data, lote_id_esperado=lote_id)
            self.circuit_breaker.record_success()
            return prediction

        except (httpx.TimeoutException, httpx.NetworkError, httpx.TransportError) as net_err:
            self.logger.warning(f"Erro de rede na API de ML para lote {lote_id}: {net_err}")
            self.circuit_breaker.record_failure()
            return None
        except Exception as exc:
            self.logger.warning(f"Falha inesperada ao classificar lote {lote_id}: {exc}")
            self.circuit_breaker.record_failure()
            return None

    def reset_circuit(self) -> None:
        self.circuit_breaker.reset()

    @staticmethod
    def _validar_resposta(
        data: dict[str, object], *, lote_id_esperado: str
    ) -> MLPrediction:
        """Valida o contrato de resposta antes de o bot confiar na predição."""
        campos_esperados = {
            "lote_id",
            "classe",
            "probabilidade",
            "nivel_confianca",
            "acao",
            "modelo_versao",
        }
        if set(data) != campos_esperados:
            raise ValueError("Resposta da API de ML não corresponde ao contrato esperado")

        lote_id = data["lote_id"]
        probabilidade = data["probabilidade"]
        if not isinstance(lote_id, str) or lote_id != lote_id_esperado:
            raise ValueError("Resposta da API contém lote_id inesperado")
        if isinstance(probabilidade, bool) or not isinstance(probabilidade, (int, float)):
            raise ValueError("Resposta da API contém probabilidade inválida")
        probabilidade_float = float(probabilidade)
        if not math.isfinite(probabilidade_float) or not 0.0 <= probabilidade_float <= 1.0:
            raise ValueError("Resposta da API contém probabilidade fora do intervalo")

        campos_textuais = ("classe", "nivel_confianca", "acao", "modelo_versao")
        if not all(isinstance(data[campo], str) and data[campo] for campo in campos_textuais):
            raise ValueError("Resposta da API contém campos textuais inválidos")

        if data["classe"] not in {"valido_automatico", "revisar", "recusar_automatico"}:
            raise ValueError("Resposta da API contém classe desconhecida")
        if data["nivel_confianca"] not in {"alta", "media", "baixa"}:
            raise ValueError("Resposta da API contém nível de confiança desconhecido")
        if data["acao"] not in {
            "VALIDO_AUTOMATICO",
            "RECUSAR_AUTOMATICO",
            "REVISAR",
            "REVISAO_PRIORITARIA",
        }:
            raise ValueError("Resposta da API contém ação desconhecida")

        return MLPrediction(
            lote_id=lote_id,
            classe=data["classe"],
            probabilidade=probabilidade_float,
            nivel_confianca=data["nivel_confianca"],
            acao=data["acao"],
            modelo_versao=data["modelo_versao"],
        )

    def close(self) -> None:
        if self._owns_client:
            self._client.close()
