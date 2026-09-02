"""Módulo de Processos Executáveis dos Bots e Pipelines (The DX Way)."""

from src.runners.coletor import run_collector
from src.runners.consumer import run_consumer
from src.runners.pipeline import main as run_pipeline
from src.runners.producer import run_producer

__all__ = [
    "run_collector",
    "run_consumer",
    "run_pipeline",
    "run_producer",
]
