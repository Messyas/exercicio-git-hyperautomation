# Automação de cadastro de lotes

Aplicação didática local em Next.js com automações sequenciais em Playwright e
Selenium. As duas usam DataPool, Page Object Model, waits explícitos, logs por
item e evidências visuais separadas.

## Execução completa

Pré-requisito: Docker com Docker Compose.

```bash
docker compose up --build
```

Esse único comando:

1. constrói e inicia o front-end em `http://localhost:3000`;
2. aguarda o healthcheck da aplicação;
3. executa os dez itens do DataPool com Playwright;
4. executa os dez itens do DataPool com Selenium, mesmo se o Playwright falhar;
5. grava screenshots, resultados JSON e logs em pastas separadas;
6. sinaliza o encerramento e para também o front-end.

Ao final não fica nenhum container em execução. Para remover os containers e a
rede já encerrados, quando desejado, use `docker compose down`.

## Saídas

Os arquivos são recriados a cada execução:

```text
test/
├── evidencias/
│   ├── playwright/
│   │   ├── evidencia_LT-2026-0001.png
│   │   ├── ...
│   │   └── resultado.json
│   └── selenium/
│       ├── evidencia_LT-2026-0001.png
│       ├── ...
│       └── resultado.json
└── logs/
    ├── playwright/execucao.log
    └── selenium/execucao.log
```

Cada item do resultado mantém o campo `screenshot` recebido do DataPool e o
caminho efetivo em `evidencia`. Em caso de divergência, o bot registra a
exceção, tira `erro_<lote>.png`, continua os itens seguintes e termina com
código diferente de zero.

Screenshots, JSON de resultado, logs, ambientes virtuais, `__pycache__` e
arquivos `.pyc` estão fora do Git. Somente os `.gitkeep` das quatro pastas de
saída são versionados.

## Arquitetura

```text
docker-compose.yml
├── frontend/
│   ├── Dockerfile
│   └── start-and-wait.sh
└── test/
    ├── Dockerfile
    ├── main.py                         # Playwright → Selenium → shutdown
    ├── requirements.txt
    ├── playwright/
    │   ├── bot.py
    │   ├── datapool.json
    │   └── web_automation.py
    ├── selenium/
    │   ├── bot.py
    │   ├── datapool.json
    │   └── selenium_automation.py
    └── src/
        ├── runner.py                   # regras, DataPool, logs e resultados
        └── pages/
            ├── playwright_pages.py     # locators Playwright
            └── selenium_pages.py       # locators e waits Selenium
```

Os Page Objects conhecem somente elementos, espera de estado visual e ações da
interface. Validação de campos, produtos, status, duplicidade, destino local,
tratamento por item e persistência do resultado ficam em `test/src/runner.py`.
Assim, a regra de negócio é compartilhada sem misturar APIs dos navegadores.

Os bots permanecem pontos de entrada independentes e podem ser auditados com:

```bash
python test/playwright/bot.py
python test/selenium/bot.py
```

Na execução direta, o front deve estar ativo, as dependências e navegadores
devem existir na máquina, e `BOT_URL` deve apontar para
`http://localhost:3000`. O fluxo Docker é a forma reproduzível recomendada.

## DataPool

Cada ferramenta mantém seu DataPool para permitir revisão e execução
independentes:

- `test/playwright/datapool.json`;
- `test/selenium/datapool.json`.

Cada item possui `lote`, `produto`, `status` e `screenshot`. Os dez itens são
processados com dados reais do próprio objeto, sem geração aleatória e sem
`time.sleep()`.

## Configuração

Os padrões ficam em `test/.env.example`. Para sobrescrever localmente, copie o
arquivo para `test/.env`; esse arquivo é ignorado:

```bash
cp test/.env.example test/.env
```

Variáveis disponíveis:

- `BOT_URL`: somente `frontend`, `localhost` ou `127.0.0.1`;
- `BOT_HEADLESS`: execução sem interface gráfica;
- `BOT_USUARIO` e `BOT_SENHA`: credenciais fictícias da demonstração;
- `EVIDENCIAS_ROOT` e `LOGS_ROOT`: destinos internos dos artefatos;
- `CHROMIUM_PATH` e `CHROMEDRIVER_PATH`: binários instalados na imagem.

Não existe `.env` na raiz.

## Playwright e Selenium

Playwright oferece locators semânticos e espera automática nas ações, deixando
o fluxo mais compacto. Selenium usa `WebDriverWait` e condições esperadas de
forma explícita, o que evidencia a sincronização e mantém compatibilidade com o
ecossistema WebDriver. Ambos usam o mesmo Chromium da imagem para tornar a
comparação previsível.

O ambiente acessado é exclusivamente a aplicação local criada para a aula;
nenhuma credencial real é validada ou registrada.

Mais detalhes técnicos estão no [PDD](docs/PDD.md) e o checklist executado está
em [Revisão técnica](docs/REVISAO_TECNICA.md).
