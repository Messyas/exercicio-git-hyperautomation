# Bot de Inspeção de Lotes Diários

## Sobre o projeto

Este projeto é uma automação desenvolvida em Python para realizar a triagem e
validação da planilha diária de inspeção de lotes do controle de qualidade.
O bot atua como um filtro de governança inicial: lê os dados de entrada,
aplica as regras de negócio RN01 a RN07, identifica divergências e gera um
relatório Excel para acompanhamento e revisão humana.

Além do processamento da planilha, o projeto oferece:

- logs estruturados em JSON com `execution_id` e `bot_id`;
- integração opcional com o BotCity Maestro;
- empacotamento e execução com Docker Compose;
- workflow de validação contínua com GitHub Actions;
- automação web opcional com Playwright.

### Fluxo do processo

O fluxo geral da automação está representado no diagrama BPMN abaixo:

![Diagrama BPMN do processo de inspeção de lotes](docs/print_inspecao_lotes_bpmn.png)

## Pré-requisitos
* Python 3.11+
* Gerenciador de pacotes `pip`

## Instalação e Configuração

1. **Acesse a pasta do projeto:**
   ```bash
   cd caminho/para/o/projeto
   ```

2. **Crie e ative um ambiente virtual:**

   No Windows:
   ```bash
   python -m venv .venv
   venv\Scripts\activate
   ```

   No Linux/Ubuntu:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Instale as dependências do projeto:** O projeto requer bibliotecas para manipulação de dados e testes (como pandas, openpyxl e pytest). Instale todas rodando:
   ```bash
   pip install -r requirements.txt
   ```

## Como Executar

Para iniciar o bot e processar a planilha de exemplo:

```bash
python main.py
```

O bot gera os artefatos em `data/output/`:

- `relatorio_divergencias_DDMMAAAA.xlsx`, com as abas `divergencias`,
  `lotes_validados` e `revisao_humana`;
- `log_execucao.json`, com o resultado e os totais da execução.

Para informar outro arquivo ou diretório de saída:

```bash
python bot.py caminho/para/arquivo.xlsx --saida caminho/para/saida
```

Para rodar a suíte de testes unitários e garantir que as validações (RN01-RN07) estão funcionando corretamente:

```bash
pytest
```

## Executando com Docker

Como alternativa ao ambiente Python local, o bot pode ser executado em um container Docker via **Docker Compose**.

### Pré-requisitos

* [Docker Desktop](https://www.docker.com/products/docker-desktop/) instalado e em execução

### Execução

O comando abaixo constrói a imagem (instalando todas as dependências do `requirements.txt`) e inicia o container:

```bash
docker compose up --build
```

> Use `--build` sempre que alterar dependências (`requirements.txt`) ou o `Dockerfile`.  
> Nas execuções seguintes, sem alterações, basta:
> ```bash
> docker compose up
> ```

### Artefatos gerados no host

Os volumes configurados no [`docker-compose.yml`](docker-compose.yml) persistem os arquivos diretamente na máquina host:

| Pasta no host | Pasta no container | Conteúdo |
|---|---|---|
| `./dados_entrada/` | `/app/dados_entrada/` | Planilhas `.xlsx` de entrada |
| `./data/output/` | `/app/data/output/` | Relatório de divergências |
| `./logs/` | `/app/logs/` | Log estruturado JSON (`execucao.log`) |

Após a execução, verifique os artefatos em `data/output/` e `logs/` — eles estarão disponíveis mesmo após o container encerrar.

## CI/CD

O projeto utiliza **GitHub Actions** para integração contínua. O pipeline está definido em [`.github/workflows/CI.yml`](.github/workflows/CI.yml).

### CI — Integração Contínua

Executado automaticamente em **todo push e pull request** para as branches `main`, `develop`, `feature/**`, `release/**` e `hotfix/**`:

| Etapa | O que faz |
|-------|-----------|
| **Lint (flake8)** | Verifica erros de sintaxe e nomes indefinidos (bloqueia merge) + avisos de estilo (não bloqueia) |
| **Testes (pytest)** | Executa a suíte de testes em `tests/` |
| **Segurança** | Verifica ausência de credenciais hardcodadas no código-fonte |

> **Importante:** As branches `main` e `develop` estão protegidas — o merge via PR só é permitido se o CI estiver verde.

### Secrets necessários no GitHub

Para que o **CD (deploy)** funcione, os seguintes secrets devem ser configurados em **Settings > Secrets and variables > Actions**:

| Secret | Descrição |
|--------|-----------|
| `MAESTRO_SERVER` | URL do servidor BotCity Maestro (ex: `https://developers.botcity.dev`) |
| `MAESTRO_LOGIN` | Login de acesso ao Maestro |
| `MAESTRO_KEY` | Chave/token de API do Maestro |
| `BOT_ID` | Identificador do bot no Maestro (ex: `bot-conferencia-lotes`) |

>  **Nunca** coloque credenciais diretamente no código ou no arquivo de workflow. Use apenas GitHub Secrets.

## Logs Estruturados

O bot gera logs em **JSON estruturado** (via `python-json-logger`) com os campos `execution_id` e `bot_id` injetados automaticamente em todas as mensagens:

```json
{
  "timestamp": "2026-07-22T10:15:00-0400",
  "level": "INFO",
  "name": "botcity.auditoria",
  "execution_id": "abc-123",
  "bot_id": "bot-conferencia-lotes",
  "message": "Iniciando auditoria de acessos | lote_id=N/A"
}
```

### Variáveis de ambiente para os IDs

| Variável | Descrição | Valor padrão |
|----------|-----------|--------------|
| `EXECUTION_ID` | ID único da execução (preenchido pelo Maestro em produção) | `local` |
| `BOT_ID` | Identificador do bot | `bot-conferencia-lotes` |

Configure no `.env` ou via variáveis de ambiente do orquestrador (BotCity Maestro).

## Automação Web com Playwright

O fluxo web é opcional e continua apontando para o ambiente Vercel atual até
que a página local seja disponibilizada.

### Deploy no BotCity

No deploy para o BotCity Maestro/Runner, mantenha o Playwright desativado:

```env
PLAYWRIGHT_ENABLED=false
```

Com essa configuração, o Runner executa somente o bot principal. O Playwright
não é iniciado e não é necessário instalar o navegador Chromium no ambiente
de deploy. O pacote Python pode permanecer no `requirements.txt`, pois ele
será apenas instalado e não executado.

### Execução local com Playwright

Para testar a automação web localmente, instale o navegador uma vez no
ambiente virtual:

```bash
python -m pip install -r requirements.txt
python -m playwright install chromium
```

Para executar a automação integrada ao `main.py`, habilite-a no ambiente:

```bash
PLAYWRIGHT_ENABLED=true PLAYWRIGHT_HEADLESS=false python main.py
```

No PowerShell:

```powershell
$env:PLAYWRIGHT_ENABLED="true"
$env:PLAYWRIGHT_HEADLESS="false"
venv\Scripts\python.exe main.py
```
