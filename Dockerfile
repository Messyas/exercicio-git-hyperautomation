# ---------------------------------------------------------------------------- #
#  Bot de Inspeção de Lotes Diários – imagem de produção
#  Base: python:3.11-slim (Debian Bookworm, sem camada gráfica)
# ---------------------------------------------------------------------------- #
FROM python:3.11-slim

# Metadados
LABEL maintainer="hyperautomation" \
      description="Bot BotCity de triagem e validação de planilha de inspeção de lotes"

# Evita prompts interativos durante o build
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Instala dependências do sistema em camada única (boa prática de camadas)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        gcc \
        libffi-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copia e instala dependências Python antes do código (melhor cache)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o código-fonte
COPY . .

# Cria os diretórios de saída e ajusta dono para o usuário sem privilégios
RUN mkdir -p data/output logs \
    && adduser --disabled-password --gecos '' appuser \
    && chown -R appuser:appuser /app

# Executa como usuário não-root (boa prática de segurança)
USER appuser

# Healthcheck: verifica se o bot consegue importar o módulo principal
HEALTHCHECK --interval=60s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import bot" || exit 1

# Comando padrão: executa o bot
CMD ["python", "bot.py"]
