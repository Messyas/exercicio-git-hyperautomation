# Cadastro de Lotes — Playwright com Page Object Model

Aplicação Next.js com um bot Playwright executado pelo Docker Compose. O bot
realiza login, processa dez registros do DataPool e mantém screenshots e um
resumo JSON em `./evidencias/`.

## Executar

```bash
docker compose up --build --abort-on-container-exit --exit-code-from playwright-bot
```

O Compose:

1. constrói e inicia o front-end;
2. aguarda o healthcheck;
3. inicia o Chromium headless;
4. realiza o login de demonstração;
5. processa os lotes;
6. gera screenshots e `resultado.json`.

Credenciais não são validadas pelo front-end. Os valores usados pelo bot podem
ser alterados pelas variáveis `BOT_USUARIO` e `BOT_SENHA`. O endereço é
configurável por `BOT_URL`.

## Arquitetura POM

```text
playwright/bot.py                     # ponto de composição
  ├─ playwright/web_automation.py     # ciclo do navegador
  └─ main.py                          # fluxo e validação do DataPool
       ├─ src/pages/login_page.py     # locators e ações de login
       ├─ src/pages/form_page.py      # locators e ações do formulário
       └─ src/services/evidence_service.py
                                       # filesystem e screenshots
```

Os Page Objects conhecem somente a interface. Validação dos dados, logs,
tratamento por item e montagem dos resultados ficam no orquestrador. A gravação
das imagens fica no serviço de evidências. O entry-point injeta a sessão do
navegador no orquestrador, evitando dependência direta de Playwright no
`main.py`.

## DataPool

`playwright/datapool.json` contém dez itens com:

- `lote`;
- `produto`;
- `status`;
- `screenshot`.

## Evidências

O volume `./evidencias:/app/evidencias` preserva:

- uma imagem `evidencia_LT-2026-XXXX.png` por sucesso;
- `erro_LT-2026-XXXX.png` quando um item falha;
- `resultado.json` com totais e resultado individual.

`evidencias/`, caches Python e artefatos de execução estão no `.gitignore`.

## Tecnologias

- Next.js 16 e React 19;
- Python e Playwright 1.52;
- Chromium da imagem oficial Playwright;
- Docker Compose.
