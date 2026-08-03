FROM python:3.12-slim-bookworm AS runtime-base

LABEL maintainer="hyperautomation" \
      description="Pipeline de cadastro Playwright e validação BotCity"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright \
    TZ=America/Manaus \
    APP_TIMEZONE=America/Manaus

WORKDIR /app

# Cada bot recebe apenas suas dependências de runtime. Testes permanecem no
# requirements.txt da raiz e não aumentam as imagens de produção.
FROM runtime-base AS consumer-dependencies
COPY bots/validacao/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt


FROM runtime-base AS producer-dependencies
COPY bots/cadastro/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt


FROM producer-dependencies AS browser-dependencies

# Somente o produtor recebe Chromium e as bibliotecas do navegador.
RUN python -m playwright install --with-deps chromium \
    && chmod -R a+rX /ms-playwright \
    && rm -rf /var/lib/apt/lists/*


FROM consumer-dependencies AS consumer

RUN adduser --disabled-password --gecos "" appuser
COPY --chown=appuser:appuser . .
RUN mkdir -p /app/data/output /app/data/datapool /app/logs \
    && chown -R appuser:appuser /app
USER appuser
CMD ["python", "consumer.py"]


FROM browser-dependencies AS producer

RUN adduser --disabled-password --gecos "" appuser
COPY --chown=appuser:appuser . .
RUN mkdir -p /app/artefatos /app/data/datapool /app/logs \
    && chown -R appuser:appuser /app
USER appuser
CMD ["python", "producer.py"]
