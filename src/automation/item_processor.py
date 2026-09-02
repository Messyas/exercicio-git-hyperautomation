from dataclasses import dataclass
from datetime import datetime, timezone
import logging
import time
from typing import Any, Iterable, Optional

from src.ml.ml_client import MLClassifier, MLPrediction


@dataclass(frozen=True)
class MLDecision:
    timestamp: str
    lote_id: str
    status_raw: str
    turno: str
    tem_obs: bool
    classe: Optional[str]
    probabilidade: Optional[float]
    nivel_confianca: str
    acao_final: str
    latencia_ms: float
    tentou_rede: bool
    circuit_open: bool
    modelo_versao: Optional[str]
    erro_tipo: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        """Formata os dados para o DataFrame/Excel da 9ª aba."""
        return {
            "Timestamp": self.timestamp,
            "Lote": self.lote_id,
            "Status original": self.status_raw,
            "Turno": self.turno,
            "Tem observação": "SIM" if self.tem_obs else "NÃO",
            "Classe predita": self.classe if self.classe is not None else "N/A",
            "Probabilidade": self.probabilidade if self.probabilidade is not None else "N/A",
            "Nível de confiança": self.nivel_confianca,
            "Ação final": self.acao_final,
            "Latência total (ms)": round(self.latencia_ms, 2),
            "Tentou rede": "SIM" if self.tentou_rede else "NÃO",
            "Circuit breaker aberto": "SIM" if self.circuit_open else "NÃO",
            "Versão do modelo": self.modelo_versao if self.modelo_versao is not None else "N/A",
            "Tipo de erro": self.erro_tipo if self.erro_tipo is not None else "Nenhum",
        }

    def to_log_dict(self) -> dict[str, Any]:
        """Formata os dados para o log estruturado JSON Lines (sem dados de observação sensíveis)."""
        return {
            "event": "ML_DECISION",
            "timestamp": self.timestamp,
            "lote_id": self.lote_id,
            "status_raw": self.status_raw,
            "turno": self.turno,
            "tem_obs": self.tem_obs,
            "classe": self.classe,
            "probabilidade": self.probabilidade,
            "nivel_confianca": self.nivel_confianca,
            "acao_final": self.acao_final,
            "latencia_ms": round(self.latencia_ms, 2),
            "tentou_rede": self.tentou_rede,
            "circuit_open": self.circuit_open,
            "modelo_versao": self.modelo_versao,
            "erro_tipo": self.erro_tipo,
        }


class ItemProcessor:
    """Processador de itens de lote que integra a camada de Machine Learning para registros ambíguos."""

    def __init__(self, ml_client: MLClassifier, logger: logging.Logger):
        self.ml_client = ml_client
        self.logger = logger

    def processar(self, registro: Any) -> Optional[MLDecision]:
        """Processa um registro. Se não for 'Ambíguo', ignora e retorna None.
        
        Se for 'Ambíguo', chama o modelo de ML via MLClient, mede a latência,
        emite log de auditoria e constrói um MLDecision.
        """
        classificacao = getattr(registro, "classificacao", None)
        if classificacao != "Ambíguo":
            return None

        lote_id = getattr(registro, "lote_id", "")
        status_raw = getattr(registro, "status_original", None) or getattr(registro, "status", "")
        turno = getattr(registro, "turno", "")
        obs = getattr(registro, "observacao", "") or ""
        tem_obs = bool(obs.strip())

        t0 = time.perf_counter()
        now_iso = datetime.now(timezone.utc).isoformat()

        # Verifica se o cliente possui circuit breaker
        circuit_open = False
        if hasattr(self.ml_client, "circuit_breaker") and getattr(self.ml_client.circuit_breaker, "is_open", False):
            circuit_open = True

        tentou_rede = not circuit_open

        try:
            pred: Optional[MLPrediction] = self.ml_client.classificar(
                lote_id=lote_id,
                status_raw=status_raw,
                turno=turno,
                tem_obs=tem_obs,
            )
        except Exception as exc:
            self.logger.error(f"Erro ao chamar ml_client.classificar para lote {lote_id}: {exc}")
            pred = None

        latencia_ms = (time.perf_counter() - t0) * 1000.0

        circuit_open_after_call = bool(
            hasattr(self.ml_client, "circuit_breaker")
            and getattr(self.ml_client.circuit_breaker, "is_open", False)
        )

        if pred is not None:
            decision = MLDecision(
                timestamp=now_iso,
                lote_id=lote_id,
                status_raw=status_raw,
                turno=turno,
                tem_obs=tem_obs,
                classe=pred.classe,
                probabilidade=pred.probabilidade,
                nivel_confianca=pred.nivel_confianca,
                acao_final=pred.acao,
                latencia_ms=latencia_ms,
                tentou_rede=True,
                circuit_open=False,
                modelo_versao=pred.modelo_versao,
                erro_tipo=None,
            )
        else:
            erro_tipo = "circuit_open" if circuit_open_after_call else "network_or_api_error"
            decision = MLDecision(
                timestamp=now_iso,
                lote_id=lote_id,
                status_raw=status_raw,
                turno=turno,
                tem_obs=tem_obs,
                classe=None,
                probabilidade=None,
                nivel_confianca="baixa",
                acao_final="REVISAO_ML_OFFLINE",
                latencia_ms=latencia_ms,
                tentou_rede=tentou_rede,
                circuit_open=circuit_open_after_call,
                modelo_versao=None,
                erro_tipo=erro_tipo,
            )

        # Emite log estruturado de auditoria
        self.logger.info("ML_DECISION", extra=decision.to_log_dict())
        return decision

    def processar_lote(self, registros: Iterable[Any]) -> list[MLDecision]:
        """Processa um iterável de registros validados e retorna todas as decisões de ML dos registros ambíguos."""
        decisoes: list[MLDecision] = []
        for reg in registros:
            try:
                dec = self.processar(reg)
                if dec is not None:
                    decisoes.append(dec)
            except Exception as exc:
                self.logger.error(f"Erro defensivo no processamento do item {getattr(reg, 'lote_id', 'desconhecido')}: {exc}")
        return decisoes
