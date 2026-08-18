from contextlib import asynccontextmanager
import asyncio
import logging
import os
from pathlib import Path
import time
from typing import AsyncGenerator

from fastapi import FastAPI, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse

from api_ml.model_service import ModelService, ModelUnavailableError
from api_ml.schemas import HealthOutput, LoteInput, PredictionOutput

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("api_ml")

MODEL_PATH = Path(os.getenv("ML_MODEL_PATH", "models/classificador_lotes.pkl"))
MAX_CONCURRENCY = max(1, int(os.getenv("ML_MAX_CONCURRENCY", "1")))
model_service = ModelService(MODEL_PATH)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Lifespan context manager para inicializar e descarregar recursos."""
    logger.info("Inicializando serviço de ML e carregando artefato...")
    try:
        model_service.load()
    except Exception as exc:
        logger.warning(f"Não foi possível carregar o modelo na inicialização: {exc}")
    yield
    logger.info("Encerrando serviço de ML.")


app = FastAPI(
    title="API de Classificação de Lotes Ambíguos (ML)",
    version="1.0.0",
    lifespan=lifespan,
)
app.state.inference_semaphore = asyncio.Semaphore(MAX_CONCURRENCY)


@app.middleware("http")
async def controlar_concorrencia_e_medir_latencia(request: Request, call_next):
    """Limita inferências CPU-bound e registra latência total e tempo de fila."""
    inicio = time.perf_counter()
    espera_fila_ms = 0.0
    if request.url.path == "/predict":
        entrou_fila = time.perf_counter()
        async with app.state.inference_semaphore:
            espera_fila_ms = (time.perf_counter() - entrou_fila) * 1000.0
            response = await call_next(request)
    else:
        response = await call_next(request)

    latencia_total_ms = (time.perf_counter() - inicio) * 1000.0
    response.headers["X-Request-Latency-Ms"] = f"{latencia_total_ms:.2f}"
    response.headers["X-Queue-Wait-Ms"] = f"{espera_fila_ms:.2f}"
    logger.info(
        "API_REQUEST path=%s status=%s latency_ms=%.2f queue_wait_ms=%.2f",
        request.url.path,
        response.status_code,
        latencia_total_ms,
        espera_fila_ms,
    )
    return response


@app.get("/health", response_model=HealthOutput, status_code=status.HTTP_200_OK)
def health_check() -> JSONResponse:
    """Verifica a saúde do serviço e se o modelo está pronto para inferência."""
    if model_service.is_loaded:
        content = HealthOutput(
            status="ok",
            model_loaded=True,
            modelo_versao=model_service.model_version,
        ).model_dump()
        return JSONResponse(status_code=status.HTTP_200_OK, content=content)
    else:
        content = HealthOutput(
            status="unavailable",
            model_loaded=False,
            modelo_versao=None,
        ).model_dump()
        return JSONResponse(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, content=content)


@app.post("/predict", response_model=PredictionOutput, status_code=status.HTTP_200_OK)
def predict(lote: LoteInput, response: Response) -> PredictionOutput:
    """Endpoint de inferência para lotes ambíguos."""
    if not model_service.is_loaded:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Modelo de ML indisponível ou não carregado.",
        )
    try:
        inicio_inferencia = time.perf_counter()
        prediction = model_service.predict(lote)
        latencia_inferencia_ms = (time.perf_counter() - inicio_inferencia) * 1000.0
        response.headers["X-Inference-Latency-Ms"] = f"{latencia_inferencia_ms:.2f}"
        logger.info(
            "ML_INFERENCE lote_id=%s latency_ms=%.2f", lote.lote_id, latencia_inferencia_ms
        )
        return prediction
    except ModelUnavailableError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        )
    except Exception as exc:
        logger.error(f"Erro inesperado durante predicao: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao processar a requisição de classificação.",
        )
