# Cadastro de Lotes — Automação Web com Selenium

Sistema de cadastro de lotes de produção com automação web via Selenium, orquestrado por Docker Compose.

## Visão Geral

O projeto contém dois componentes:

1. **Front-end** — Aplicação Next.js com formulário de cadastro de lotes (produto, número, status).
2. **Bot Selenium** — Automação que preenche o formulário automaticamente, alimentada por um DataPool (`datapool.json`), gerando evidências visuais (screenshots) de cada item processado.

## Pré-requisitos

- [Docker](https://docs.docker.com/get-docker/) e [Docker Compose](https://docs.docker.com/compose/install/) instalados.

## Como Executar

```bash
docker compose up --build
```

O que acontece:

1. O **front-end Next.js** sobe na porta `3000` e fica disponível em `http://localhost:3000`.
2. Quando o front estiver saudável (healthcheck), o **bot Selenium** inicia automaticamente.
3. O bot processa cada item do `datapool.json`, preenchendo o formulário e capturando screenshots.
4. As evidências são salvas na pasta `./evidencias/` (montada via volume Docker).

## Evidências de Execução

Após a execução, a pasta `evidencias/` conterá:

| Arquivo | Descrição |
|---------|-----------|
| `evidencia_LT-2026-XXXX.png` | Screenshot do comprovante de cada lote processado |
| `erro_LT-2026-XXXX.png` | Screenshot de fallback em caso de falha |
| `resultado.json` | Resumo completo da execução com status de cada item |

## Estrutura do Projeto

```
├── app/                    # Código-fonte do front-end Next.js
├── components/             # Componentes React (formulário, lista, badges)
├── lib/                    # Utilitários e tipos TypeScript
├── selenium/
│   ├── bot.py              # Entry-point da automação (python bot.py)
│   ├── web_automation_selenium.py  # Lógica de automação Selenium
│   ├── datapool.json       # Dados de entrada para a automação
│   └── requirements.txt    # Dependências Python
├── Dockerfile.frontend     # Build do front-end
├── Dockerfile.selenium     # Build do bot Selenium + Chrome
├── docker-compose.yml      # Orquestração dos serviços
├── PDD.md                  # Process Definition Document
└── README.md               # Este arquivo
```

## Variáveis de Ambiente

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `BOT_URL` | `http://frontend:3000` | URL do front-end |
| `BOT_HEADLESS` | `true` | Executa Chrome em modo headless |
| `BOT_QUANTIDADE` | `10` | Quantidade de itens a processar |

## DataPool

O arquivo `selenium/datapool.json` contém os dados de entrada da automação. Cada item possui:

- `lote` — Número identificador do lote
- `produto` — Produto a ser selecionado
- `status` — Status do lote (Pendente, Em processamento, Concluído)
- `screenshot` — Nome do arquivo de evidência visual

## Tecnologias

- **Front-end**: Next.js 16, React 19, Tailwind CSS, shadcn/ui
- **Automação**: Python 3.11, Selenium 4
- **Infraestrutura**: Docker, Docker Compose
