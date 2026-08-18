FROM python:3.12-slim-bookworm AS runtime-base

LABEL maintainer="hyperautomation" \
      description="Pipeline de cadastro Playwright e validação BotCity"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    APP_TIMEZONE=America/Manaus

ENV ENVIRONMENT=container
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
ENV TZ=America/Manaus

WORKDIR /app

# Dependências de runtime do consumidor.
FROM runtime-base AS consumer-dependencies
COPY bots/validacao/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt


# Runtime dedicado ao classificador da Aula 24-A. Mantém o bot de ML
# independente das dependências do consumidor legado e da interface Streamlit.
FROM runtime-base AS ml-runner-dependencies
COPY dashboard/requirements-runner.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt


FROM runtime-base AS producer-dependencies
COPY bots/cadastro/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt


FROM producer-dependencies AS browser-dependencies

# Chromium usado pelo produtor.
RUN python -m playwright install-deps chromium
RUN python -m playwright install chromium \
    && chmod -R a+rX /ms-playwright \
    && rm -rf /var/lib/apt/lists/*


FROM consumer-dependencies AS consumer

RUN adduser --disabled-password --gecos "" appuser
COPY --chown=appuser:appuser . .
RUN mkdir -p /app/data/output /app/data/datapool /app/logs /app/reports \
    && chown -R appuser:appuser /app
USER appuser
CMD ["python", "consumer.py"]


FROM ml-runner-dependencies AS ml-runner

RUN adduser --disabled-password --gecos "" appuser
COPY --chown=appuser:appuser . .
RUN mkdir -p /app/data/output /app/logs \
    && chown -R appuser:appuser /app
USER appuser
CMD ["python", "dashboard/main.py"]


FROM browser-dependencies AS producer

RUN adduser --disabled-password --gecos "" appuser
COPY --chown=appuser:appuser . .
RUN mkdir -p /app/screenshots /app/data/output /app/data/datapool \
    /app/logs /app/reports \
    && chown -R appuser:appuser /app
USER appuser
CMD ["python", "producer.py"]
