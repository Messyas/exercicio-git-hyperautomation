# Pipeline de Cadastro e Validação de Lotes

O projeto contém dois bots independentes:

1. **Produtor Playwright**: lê a planilha bruta, cadastra cada lote no sistema
   web local, salva evidências e publica todos os registros no DataPool.
2. **Consumidor BotCity**: consome o DataPool, executa RN01–RN07, atualiza o
   estado individual dos itens e gera o relatório Excel.

O fuso operacional é sempre `America/Manaus`. Rejeições do formulário,
divergências de negócio e falhas técnicas são classificadas separadamente;
nenhuma divergência interrompe o processamento dos itens seguintes.

Os dados inválidos também são enviados ao consumidor. Assim, uma rejeição do
formulário web não elimina justamente o registro que precisa ser auditado.

## Fluxo

```text
data/samples/inspecao_lotes_dia.xlsx
              │
              ▼
     producer.py + Playwright
       │ cadastro + PNG
       ▼
 DataPool local ou BotCity
              │
              ▼
         consumer.py
       RN01–RN07 + XLSX
```

O frontend de demonstração fica em `frontend/`. Seus registros são mantidos no
`localStorage` do navegador; o contrato persistente entre os bots é o
DataPool.

## Execução completa com Docker

Pré-requisito: Docker com Docker Compose.

```bash
docker compose config --quiet
docker compose build
docker compose up --abort-on-container-failure
```

O Compose:

- inicia e aguarda o healthcheck do frontend;
- executa o produtor;
- inicia o consumidor somente se o produtor concluir;
- encerra o frontend ao final;
- mantém todas as saídas na máquina host.

Para reconstruir e executar em um único comando:

```bash
docker compose up --build --abort-on-container-failure
```

Execução individual, quando o frontend já estiver disponível:

```bash
docker compose run --rm producer
docker compose run --rm consumer
```

O `.env` é opcional. Copie `.env.example` somente quando precisar substituir
algum padrão:

```powershell
Copy-Item .env.example .env
```

Para processar uma planilha colocada em `dados_entrada/`, configure no `.env`:

```env
BOT_INPUT_FILE=/app/dados_entrada/minha_planilha.xlsx
```

## Saídas no host

```text
artefatos/produtor/                 screenshots de sucesso e erro
data/datapool/*.processed.json      estado final do DataPool local
data/output/*.xlsx                  relatório de divergências
logs/produtor/execucao.log          log JSON do produtor
logs/validador/execucao.log         log JSON do consumidor
logs/*/resumo_execucao.json         resumo de cada bot
```

Na planilha didática atual, o resultado esperado é:

- 25 itens publicados;
- 24 cadastros web bem-sucedidos e 1 falha de formulário por lote vazio;
- 9 registros divergentes;
- 10 violações de regras;
- 16 lotes validados;
- 2 itens para revisão humana.

## DataPool BotCity

> Não crie o DataPool antes de implantar os dois bots. O produtor só cria a
> tarefa do validador depois de publicar o lote completo.

Gere os dois pacotes independentes:

```bash
python scripts/build_botcity_packages.py
```

Os arquivos ficam em `dist/botcity/` e contêm `bot.py` e `requirements.txt`
na raiz, como esperado pelo Runner. O workflow manual `CD — Bots BotCity`
permite `deploy`, `update` e `release`; configure no GitHub os secrets
`BOTCITY_SERVER`, `BOTCITY_LOGIN` e `BOTCITY_KEY` antes de executá-lo.

No Runner Windows, mantenha o frontend acessível em `http://localhost:3000`:

```bash
docker compose up -d frontend
```

Após a primeira instalação do ambiente virtual do bot produtor, instale o
Chromium com o Python daquele ambiente:

```powershell
python -m playwright install chromium
```

O entrypoint reconhece automaticamente os argumentos `server/task/token`
injetados pelo BotRunner; credenciais de desenvolvimento não precisam ficar
em `.env` no pacote.

O modo local é usado por padrão:

```env
DATAPOOL_BACKEND=local
```

No BotCity Orchestrator:

1. configure as credenciais de desenvolvimento ou execute pelo Runner;
2. defina `MAESTRO_ENABLED=true` e `DATAPOOL_BACKEND=botcity`;
3. crie o schema uma única vez:

   ```bash
   python -m scripts.create_datapool
   ```

4. registre a automação consumidora com o label definido em
   `VALIDATOR_ACTIVITY_LABEL`;
5. execute o produtor.

O produtor adiciona todas as entradas e só depois cria a tarefa do consumidor.
O campo `item_id`, formado pelo hash do arquivo e pela linha de origem, fornece
idempotência. `lote_id` não é único porque valores vazios e duplicados também
precisam chegar à validação.

Itens válidos terminam como `DONE`. Divergências RN01–RN07 terminam como erro
`BUSINESS`, sem acionar retentativa de sistema. Falhas técnicas usam erro
`SYSTEM`.

Ao finalizar a tarefa, o validador reporta ao Maestro `total_items`,
`processed_items` e `failed_items`. Itens `DONE` contam como processados com
sucesso; divergências de negócio e falhas técnicas contam como falhas.

## Logs estruturados

Todas as linhas contêm:

- `execution_id`;
- `bot_id`;
- `batch_id`;
- `lote_id`;
- `source_row`;
- timestamp, nível, logger e mensagem.

No Compose, os IDs dos bots são:

- `bot-lotes-cadastro-playwright-mk7`;
- `bot-lotes-validacao-mk7`.

## Desenvolvimento e testes

```bash
python -m pip install -r requirements.txt
pytest tests/ -v
```

Para executar o produtor fora do Docker, instale o Chromium do Playwright:

```bash
python -m playwright install chromium
```

O workflow `.github/workflows/ci.yml` executa lint, testes Python, build do
frontend e o pipeline completo em Docker, verificando screenshots, logs,
DataPool processado e relatório Excel.

## Estrutura principal

```text
producer.py                         entrypoint do bot produtor
consumer.py                         entrypoint do bot consumidor
bot.py                              núcleo de validação RN01–RN07
src/excel_source.py                 adaptador da planilha bruta
src/datapool_gateway.py             DataPool local e BotCity
src/playwright_automation.py        ciclo do navegador
src/pages/playwright_pages.py       locators semânticos e waits
src/maestro_client.py               Maestro, artefatos e logs JSON
frontend/                           página local de cadastro
```
