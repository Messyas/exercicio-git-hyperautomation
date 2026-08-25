"""Componente isolado de classificação de divergências via ML.

Este módulo atende a todas as especificações das Seções 3.2, 7 e 8 do Estudo de Caso S10-B:
- Isolamento total por abstração (`ClassificadorDivergencia`).
- Controle estrito por feature flag (`ML_ENABLED`). Quando desativado, nenhuma chamada de rede é feita.
- Limiar de confiança mínima configurável (`ML_CONFIANCA_MINIMA`).
- Resiliência total: NUNCA lança exceção para o bot, tratando indisponibilidade, timeout,
  erros HTTP ou baixa confiança como fallbacks seguros e auditáveis.
"""

from __future__ import annotations

from dataclasses import dataclass
import logging
import math
import time
from typing import Any, Optional

import httpx

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ResultadoClassificacao:
    """Resultado da sugestão de causa provável com auditoria de origem."""

    lote_id: str
    causa_provavel_ml: str
    confianca_ml: float
    origem_decisao: str  # "ml" ou "fallback"
    motivo_fallback: str | None = None  # "feature_flag_desativada", "indisponibilidade", "timeout", "baixa_confianca", "resposta_invalida"
    latencia_ms: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "lote_id": self.lote_id,
            "causa_provavel_ml": self.causa_provavel_ml,
            "confianca_ml": self.confianca_ml,
            "origem_decisao": self.origem_decisao,
            "motivo_fallback": self.motivo_fallback or "Nenhum",
            "latencia_ms": round(self.latencia_ms, 2),
        }


class ClassificadorDivergencia:
    """Classificador híbrido RPA+ML para enriquecimento de divergências."""

    def __init__(
        self,
        api_url: str = "http://127.0.0.1:8000",
        enabled: bool = True,
        timeout_ms: int = 1000,
        confianca_minima: float = 0.70,
        simulated_delay_ms: int = 0,
        client: Optional[httpx.Client] = None,
        logger_instance: Optional[logging.Logger] = None,
    ):
        self.api_url = api_url.rstrip("/")
        self.enabled = enabled
        self.timeout_sec = max(0.001, timeout_ms / 1000.0)
        self.confianca_minima = confianca_minima
        self.simulated_delay_ms = max(0, simulated_delay_ms)
        self.logger = logger_instance or logger

        self._stats_total = 0
        self._stats_fallback = 0

        if client is not None:
            self._client = client
            self._owns_client = False
        else:
            timeout_config = httpx.Timeout(
                timeout=self.timeout_sec, connect=min(0.20, self.timeout_sec)
            )
            self._client = httpx.Client(base_url=self.api_url, timeout=timeout_config)
            self._owns_client = True

    def classificar(
        self,
        *,
        lote_id: str,
        observacao: str = "",
        status_raw: str = "",
        turno: str = "",
    ) -> ResultadoClassificacao:
        """Classifica a causa provável de uma divergência a partir do texto livre.

        Garantia de contrato S10-B: NUNCA propaga exceção ao chamador.
        """
        self._stats_total += 1
        t0 = time.perf_counter()

        # 1. Feature Flag Check (sem chamadas de rede se False)
        if not self.enabled:
            self._stats_fallback += 1
            latencia = (time.perf_counter() - t0) * 1000.0
            self.logger.info(
                f"[ML_FALLBACK] Lote '{lote_id}' em fallback | Motivo: feature_flag_desativada"
            )
            return ResultadoClassificacao(
                lote_id=lote_id,
                causa_provavel_ml="nao_classificado",
                confianca_ml=0.0,
                origem_decisao="fallback",
                motivo_fallback="feature_flag_desativada",
                latencia_ms=latencia,
            )

        payload: dict[str, Any] = {
            "lote_id": lote_id,
            "observacao": observacao,
        }
        if self.simulated_delay_ms:
            payload["simular_atraso_ms"] = self.simulated_delay_ms

        try:
            response = self._client.post("/classify-divergence", json=payload)
            latencia = (time.perf_counter() - t0) * 1000.0

            if response.status_code != 200:
                self._stats_fallback += 1
                self.logger.warning(
                    f"[ML_FALLBACK] HTTP {response.status_code} na API de ML para lote '{lote_id}'"
                )
                return ResultadoClassificacao(
                    lote_id=lote_id,
                    causa_provavel_ml="nao_classificado",
                    confianca_ml=0.0,
                    origem_decisao="fallback",
                    motivo_fallback="indisponibilidade",
                    latencia_ms=latencia,
                )

            data = response.json()
            if not isinstance(data, dict):
                raise ValueError("Resposta da API ML não é um objeto JSON")

            # Extração defensiva dos dados
            confianca_raw = data.get("probabilidade", data.get("confianca", 0.0))
            if isinstance(confianca_raw, (int, float)) and math.isfinite(confianca_raw):
                confianca = float(confianca_raw)
            else:
                confianca = 0.0

            sugestao = str(
                data.get("causa_provavel", data.get("classe", "duplicidade_digitacao"))
            )

            # 2. Check de Limiar de Confiança Mínima
            if confianca < self.confianca_minima:
                self._stats_fallback += 1
                self.logger.info(
                    f"[ML_FALLBACK] Lote '{lote_id}' abaixo da confiança mínima ({confianca:.2f} < {self.confianca_minima:.2f})"
                )
                return ResultadoClassificacao(
                    lote_id=lote_id,
                    causa_provavel_ml="nao_classificado",
                    confianca_ml=confianca,
                    origem_decisao="fallback",
                    motivo_fallback="baixa_confianca",
                    latencia_ms=latencia,
                )

            # Predição válida via ML
            self.logger.info(
                f"[ML_SUCESSO] Lote '{lote_id}' classificado como '{sugestao}' com confiança {confianca:.2f}"
            )
            return ResultadoClassificacao(
                lote_id=lote_id,
                causa_provavel_ml=sugestao,
                confianca_ml=confianca,
                origem_decisao="ml",
                motivo_fallback=None,
                latencia_ms=latencia,
            )

        except httpx.TimeoutException:
            latencia = (time.perf_counter() - t0) * 1000.0
            self._stats_fallback += 1
            self.logger.warning(
                f"[ML_FALLBACK] Timeout ({self.timeout_sec * 1000:.0f}ms) ao chamar API ML para lote '{lote_id}'"
            )
            return ResultadoClassificacao(
                lote_id=lote_id,
                causa_provavel_ml="nao_classificado",
                confianca_ml=0.0,
                origem_decisao="fallback",
                motivo_fallback="timeout",
                latencia_ms=latencia,
            )
        except (httpx.NetworkError, httpx.TransportError, Exception) as exc:
            latencia = (time.perf_counter() - t0) * 1000.0
            self._stats_fallback += 1
            self.logger.warning(
                f"[ML_FALLBACK] Falha de comunicação/API de ML para lote '{lote_id}': {exc}"
            )
            return ResultadoClassificacao(
                lote_id=lote_id,
                causa_provavel_ml="nao_classificado",
                confianca_ml=0.0,
                origem_decisao="fallback",
                motivo_fallback="indisponibilidade",
                latencia_ms=latencia,
            )

    @property
    def operando_100_percent_fallback(self) -> bool:
        """Indica se 100% dos itens processados nesta instância caíram em fallback."""
        return self._stats_total > 0 and self._stats_fallback == self._stats_total

    def reset_stats(self) -> None:
        self._stats_total = 0
        self._stats_fallback = 0

    def close(self) -> None:
        if self._owns_client:
            self._client.close()
