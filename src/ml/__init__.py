"""Módulo de Inteligência Artificial e Classificação (The DX Way)."""

from src.ml.classificador_divergencia import (
    ClassificadorDivergencia,
    ResultadoClassificacao,
)
from src.ml.ml_client import (
    CircuitBreaker,
    MLClassifier,
    MLClient,
    MLPrediction,
)
from src.ml.ml_client_factory import get_ml_client

__all__ = [
    "ClassificadorDivergencia",
    "ResultadoClassificacao",
    "CircuitBreaker",
    "MLClassifier",
    "MLClient",
    "MLPrediction",
    "get_ml_client",
]
