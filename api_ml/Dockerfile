FROM python:3.11-slim

WORKDIR /service

# Evita geração de pyc e buffering de logs
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/service

# Instala dependências do sistema se necessário
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copia e instala dependências Python
COPY api_ml/requirements.txt /service/api_ml/requirements.txt
RUN pip install --no-cache-dir -r /service/api_ml/requirements.txt

# Copia o código da API e os modelos
COPY api_ml /service/api_ml
COPY models /service/models

# Cria usuário não-root
RUN useradd -m appuser && chown -R appuser:appuser /service
USER appuser

EXPOSE 8000

CMD ["uvicorn", "api_ml.main:app", "--host", "0.0.0.0", "--port", "8000"]
