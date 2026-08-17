# Pipeline de Cadastro e Validação de Lotes

[![CI/CD](https://github.com/Messyas/exercicio-git-hyperautomation/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/Messyas/exercicio-git-hyperautomation/actions/workflows/ci-cd.yml)

O projeto contém dois bots independentes, encadeados por um DataPool:

1. **Produtor Playwright**: lê a planilha bruta, cadastra cada lote no sistema
   web local, salva evidências e publica no DataPool apenas os cadastros
   concluídos.
2. **Consumidor compatível com BotCity**: consome o DataPool local ou remoto,
   executa RN01-RN07, atualiza o estado individual dos itens e gera o relatório
   Excel.

O fuso operacional é sempre `America/Manaus`. Rejeições do formulário,
divergências de negócio e falhas técnicas são classificadas separadamente;
nenhuma divergência interrompe o processamento dos itens seguintes.

Rejeições e falhas de cadastro não entram no DataPool. O Bot 1 preserva esses
itens em um relatório próprio, com os dados de origem, o motivo e o caminho da
evidência. Assim, o Bot 2 recebe apenas itens que concluíram a etapa anterior.

## Fluxo

```text
data/samples/inspecao_lotes_dia.xlsx
  -> producer.py + Playwright
       |-> erros de cadastro -> relatório de erros do Bot 1
       `-> cadastros concluídos -> DataPool local ou BotCity
                                  -> consumer.py + RN01-RN07 + XLSX
```

## Entrada processada

Por padrão, o projeto usa `data/samples/inspecao_lotes_dia.xlsx`. A primeira
aba contém os 25 registros didáticos e a aba `Base_Referencia` fornece os IDs
válidos usados pela RN03. O arquivo possui os campos `lote_id`, `produto`,
`linha`, `turno`, `status`, `responsavel`, `data` e `observacao`.

Para usar outro arquivo dentro do projeto, defina no `.env`:

```env
BOT_INPUT_FILE=data/samples/minha_planilha.xlsx
```

Não há monitoramento de pasta nem agendamento automático nesta versão. O fluxo
é iniciado por comando local, Docker Compose, GitHub Actions ou BotRunner.

## Modelagem do processo

A imagem abaixo apresenta o **AS-IS** e o **TO-BE** do processo modelado de
inspeção de lotes. Os detalhes e limites da automação estão no
[PDD do processo](docs/pdd/PDD_Process_Design_Document.md).

![Modelagem BPMN do processo de inspeção de lotes: AS-IS e TO-BE](docs/print_inspecao_lotes_bpmn.png)

O frontend de demonstração fica em `frontend/`. Seus registros são mantidos no
`localStorage` do navegador; o contrato persistente entre os bots é o
DataPool.

## Frontend Next.js e equivalência ao `lote-teste.html`

O roteiro original do Exercício 19-X utiliza uma página estática em
`web/lote-teste.html`, aberta pelo Playwright por meio de um caminho `file://`.
Neste projeto, o mesmo papel é desempenhado pela aplicação Next.js em
`frontend/`, principalmente por `frontend/app/page.tsx`,
`frontend/components/login-form.tsx` e `frontend/components/lote-form.tsx`.

Como o frontend usa Next.js, os testes acessam a aplicação em execução por
`http://127.0.0.1:3000`. Por isso, a fixture `pagina_html` em
`tests/conftest.py` retorna uma URL em vez de um arquivo estático e faz o login
antes de criar o Page Object.

| Exemplo da aula | Implementação deste projeto |
| --- | --- |
| `web/lote-teste.html` | aplicação Next.js em `frontend/` |
| caminho local `file://` | `E2E_BASE_URL=http://127.0.0.1:3000` |
| formulário acessível diretamente | login de demonstração antes do formulário |
| radio button de status | campo de texto para preservar o valor original |
| status padrão `pendente` | status padrão `APROVADO` |
| opções como `TV-55` | códigos do domínio, como `TV55-4K-B` |
| `PlaywrightFormularioLotesPage` | fachada E2E que reutiliza os Page Objects de `src/pages/` |

Os oito testes E2E verificam título, lote, produto, status padrão, envio do
formulário, validações negativas e captura de screenshot no Chromium.

O formulário registra os oito campos da planilha: `lote_id`, `produto`,
`linha`, `turno`, `status`, `responsavel`, `data` e `observacao`. O status é
mantido como texto para que valores não normalizados também cheguem ao Bot 2,
responsável pela aplicação das regras RN01-RN07.

O frontend exige apenas lote e produto para concluir o cadastro demonstrativo.
As demais obrigatoriedades pertencem ao motor de regras do Bot 2. Por isso, um
responsável vazio chega ao DataPool para ser classificado pela RN02, enquanto
um lote sem ID é rejeitado pelo Bot 1 e registrado no relatório de erros do
produtor.

A inicialização do Chromium fica em `src/web_automation.py`.
`src/playwright_automation.py` controla o restante do ciclo de vida do browser.

## Execução com Docker

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

O perfil `avaliacao` executa produtor e consumidor em sequência:

```bash
docker compose --profile avaliacao build bot-conferencia
docker compose run --rm bot-conferencia
```

O serviço `bot-conferencia` atende ao comando previsto no exercício. Os serviços
`producer` e `consumer` continuam disponíveis para execução separada.

Execução individual: o produtor precisa do frontend, e o consumidor precisa de
um lote pendente criado pelo produtor.

```bash
docker compose run --rm producer
docker compose run --rm consumer
```

O `.env` é opcional. Copie `.env.example` somente quando precisar substituir
algum padrão:

```powershell
Copy-Item .env.example .env
```

## Saídas no host

```text
screenshots/local/<batch_id>/produtor/             screenshots de sucesso e erro
data/datapool/*.processed.json                      estado final do DataPool local
data/output/relatorio_erros_fluxo_produtor_*.xlsx  erros retidos pelo Bot 1
data/output/relatorio_divergencias_*.xlsx          resultado do Bot 2
logs/produtor/execucao.log                          log JSON Lines do produtor
logs/validador/execucao.log                         log JSON Lines do consumidor
logs/*/resumo_execucao.json                         resumo de cada bot
reports/                                             volume reservado
```

Cada item do DataPool preserva `evidence_name` para compatibilidade e também
registra `evidence_path`. No container, o caminho começa em `/app/screenshots`;
esse diretório corresponde a `./screenshots` no host. DataPools já existentes
no Maestro precisam receber a coluna textual `evidence_path` antes do deploy.

Na planilha didática atual, o resultado esperado é:

- 25 tentativas de cadastro pelo Bot 1;
- 24 cadastros web bem-sucedidos e publicados no DataPool;
- 1 rejeição por lote sem ID, retida no relatório de erros do Bot 1;
- 8 registros divergentes identificados pelo Bot 2;
- 9 violações de regras nesses 8 registros do Bot 2;
- 9 exceções no fluxo completo, somando a rejeição do Bot 1 e as 8
  divergências do Bot 2;
- 16 lotes validados;
- 2 itens para revisão humana.

O Bot 1 termina como `PARTIALLY_COMPLETED` porque preserva a rejeição sem
interromper o lote. O Bot 2 termina como `SUCCESS`; no DataPool local, 16 itens
ficam `DONE` e 8 ficam `ERROR` do tipo `BUSINESS`.

## Dashboard executivo da planilha de 10 dias — Aula 24

O dashboard é um fluxo independente do processo legado RN01–RN07. Ele aplica
RN01–RN12 à planilha de dez dias, preserva cada `RegistroValidado` e calcula os
indicadores uma única vez antes de gerar todos os artefatos.

```text
Planilha + Base de Referência
  -> validação RN01–RN12
  -> OperationalIndicators
  -> Excel (8 abas) + resumo executivo Markdown + PDF compatível + log
```

Execute o fluxo oficial com:

```bash
python -m dashboard.main \
  --entrada "data/samples/inspecao_lotes_10dias_sem gabarito.xlsx" \
  --saida data/output
```

Os dez indicadores incluem volume processado, classificações, regra mais
acionada, qualidade da entrada, revisão humana, retrabalho e ganho de tempo.
Para o conjunto didático, o resultado esperado é 250 registros: 150 válidos,
50 divergências, 20 ambíguos, 30 erros de entrada, RN06 como regra principal
(25 ocorrências) e 437,5 minutos de ganho estimado.

O ganho é uma **estimativa didática**, baseada em 2,00 minutos por registro no
processo manual e 0,25 minuto no automatizado; não representa uma medição de
produção. As taxas devem ser interpretadas com as limitações do conjunto de
dados didático e não substituem telemetria operacional contínua.

Os artefatos são gravados em `data/output/`: Excel com oito abas, resumo
executivo Markdown, PDF compatível e log. Para detalhes sobre as abas, o
dicionário, Docker e demonstração, consulte [dashboard/README.md](dashboard/README.md).

### Testes do dashboard

```bash
python -m pytest -m unit -v
python -m pytest -m integration -v
python -m pytest -m regression -v
python -m pytest -m "e2e and not browser" -v
python -m pytest -m "not browser" --cov=src --cov=dashboard \
  --cov-config=.coveragerc --cov-report=term-missing \
  --cov-report=xml:reports/coverage.xml \
  --cov-report=html:reports/coverage-html --cov-fail-under=80
```

## DataPool BotCity

> Não crie o DataPool antes de implantar os dois bots. O produtor só cria a
> tarefa do validador depois de publicar o lote completo.

Gere os dois pacotes independentes:

```bash
python scripts/build_botcity_packages.py
```

Os arquivos ficam em `dist/botcity/` e contêm `bot.py` e `requirements.txt`
na raiz, como esperado pelo Runner. O workflow manual `CD - Bots BotCity`
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

O produtor tenta cadastrar todas as entradas e só publica as que concluíram o
cadastro web. Depois de publicar esse lote filtrado, cria a tarefa do
consumidor. O campo `item_id`, formado pelo hash do arquivo e pela linha de
origem, fornece idempotência. Um `lote_id` vazio é retido pelo Bot 1; IDs
duplicados ou não encontrados na referência ainda chegam ao Bot 2 para a
aplicação das regras de negócio.

Itens válidos terminam como `DONE`. Divergências RN01-RN07 terminam como erro
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

Use Python 3.12. O ambiente virtual não é obrigatório, mas evita conflitos com
outros projetos.

### Preparar o ambiente no Windows PowerShell

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
```

Se não quiser ativar o ambiente, execute os comandos com
`.\.venv\Scripts\python.exe` no lugar de `python`.

No Linux ou macOS:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
```

O arquivo `requirements-dev.txt` instala as dependências da aplicação,
`pytest`, `pytest-cov` e `pytest-playwright`. Ele não instala Selenium.

### Suíte consolidada da Aula 23

A suíte é organizada estritamente em quatro pastas correspondentes às camadas de teste (`tests/unit/`, `tests/integration/`, `tests/regression/`, `tests/e2e/`). Os markers são declarados e validados com `--strict-markers` pelo `pytest.ini`:

- `unit`: funções isoladas e regras RN01–RN12;
- `integration`: colaboração entre leitura, validação, DataPool e relatório;
- `regression`: alarmes isolados para comportamentos corrigidos e salva-guardas de regras (RN05, RN07, RN10, RN11, RN12);
- `e2e`: fluxo completo sintético de dados até o relatório/dashboard executivo;
- `browser`: E2E opcional com Chromium e interface web;
- `slow`: testes de maior duração (pipeline de 10 dias e navegadores).

Executar a suíte completa sem browser ou serviço externo:

```bash
python -m pytest -m "not browser" -q -rsxX
```

Executar cada camada isoladamente:

```bash
python -m pytest -m unit -v
python -m pytest -m integration -v
python -m pytest -m regression -v
python -m pytest -m "e2e and not browser" -v
python -m pytest -m slow -v
```

O E2E local cria uma planilha sintética de 10 dias e 250 registros em
`tmp_path`, simula a `Base_Referencia` com `MagicMock`, fixa o relógio e confere
o gabarito de 150 válidos, 50 divergências, 20 ambíguos e 30 erros de entrada.
Ele não usa internet, credenciais ou arquivo preparado manualmente.
Os testes legados dos adaptadores Excel ainda usam apenas fixtures versionadas
em `data/samples`; a lógica de negócio e o E2E da Aula 23 usam dados sintéticos
e mocks, portanto não dependem de arquivos locais não versionados.

Os motivos de limitações conhecidas aparecem com:

```bash
python -m pytest -q -rsxX
```

Atualmente, a integração real com Maestro é `SKIPPED` por exigir credenciais de
homologação. A aceitação de datas impossíveis em nomes de aba é `XFAIL` estrito
e documenta um bug conhecido da RN12.

### Cobertura

A cobertura mínima obrigatória é 80%. O comando usado localmente e no CI é:

```bash
python -m pytest -m "not browser" -q \
  --cov=src --cov=dashboard --cov-config=.coveragerc \
  --cov-report=term-missing --cov-fail-under=80
```

A medição consolidada da implementação da Aula 23 atingiu 85,84%; a medição
literal de `src` atingiu 84,33%. A
configuração exclui apenas os Page Objects/Playwright e a interface Streamlit:
essas interfaces pertencem ao job de browser, enquanto
`dashboard/gerar_relatorio.py` e `dashboard/servico_validacao.py` continuam
obrigatoriamente cobertos. O CI anexa `reports/coverage.xml` como evidência.

### E2E opcional de browser

Instale o Chromium, inicie o frontend e habilite explicitamente os testes:

```powershell
python -m playwright install chromium
docker compose up -d --build --wait frontend
$env:RUN_BROWSER_E2E = "1"
$env:E2E_BASE_URL = "http://127.0.0.1:3000"
python -m pytest -m browser -v
docker compose down --volumes --remove-orphans
```

### Pipeline completo em Docker

Este caminho não usa o ambiente virtual local. As dependências e o Chromium são
instalados na imagem:

```bash
docker compose --profile avaliacao build bot-conferencia
docker compose run --rm bot-conferencia
docker compose run --rm --no-deps --entrypoint python bot-conferencia scripts/verify_pipeline.py
docker compose --profile avaliacao down --volumes --remove-orphans
```

O workflow `.github/workflows/ci-cd.yml` executa qualidade Python, testes
unitários, build do frontend, oito testes E2E, pipeline completo em container e
checagem de credenciais. Os jobs publicam screenshots, DataPool local, logs e
relatórios com `actions/upload-artifact@v4`.

## Escopo e limitações das automações web

Na branch `main`, a automação web usa Page Object Model com Playwright e está
integrada ao produtor, ao DataPool e ao Maestro.

O Selenium não faz parte desta branch nem do pipeline atual. A implementação
comparativa usada no passado está em `origin/feature/page-objects`. A branch
`main` mantém apenas o POM Playwright.

Outras limitações conhecidas: o frontend é demonstrativo, aceita qualquer par
não vazio de usuário e senha e persiste os lotes somente no `localStorage` do
navegador. O estado durável entre os bots é o DataPool, não o frontend.

Também não fazem parte desta versão: agendamento ou monitoramento de pasta,
autenticação de produção, integração com ERP/MES, correção automática dos casos
de revisão humana e reprocessamento automático após a decisão do analista.

## Estrutura principal

```text
producer.py                         entrypoint do bot produtor
consumer.py                         entrypoint do bot consumidor
pipeline.py                         execução conjunta para o perfil avaliacao
bot.py                              núcleo de validação RN01-RN07
src/excel_source.py                 adaptador da planilha bruta
src/datapool_gateway.py             DataPool local e BotCity
src/playwright_automation.py        ciclo do navegador
src/web_automation.py               lançamento do Chromium local/container
src/pages/playwright_pages.py       locators semânticos e waits
tests/unit/                         testes unitários isolados
tests/integration/                  testes de integração entre componentes
tests/regression/                   alarmes de regressão (RN05, RN07, RN10, RN11, RN12)
tests/e2e/                          testes end-to-end de pipeline e browser
src/maestro_client.py               Maestro, artefatos e logs JSON
frontend/                           aplicação Next.js de cadastro
```
