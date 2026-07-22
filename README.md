# Bot de Inspeção de Lotes Diários

![CI/CD Pipeline](https://github.com/Messyas/exercicio-git-hyperautomation/actions/workflows/ci.yml/badge.svg)

## Resumo do Projeto
Este projeto é uma automação desenvolvida em Python para realizar a triagem e validação da planilha de inspeção diária do controle de qualidade. O bot atua como um filtro de governança inicial, aplicando regras de negócio (RN01 a RN07) para automatizar o trabalho braçal. 

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

O projeto utiliza **GitHub Actions** para integração contínua. O pipeline está definido em [`.github/workflows/ci.yml`](.github/workflows/ci.yml).

### CI — Integração Contínua

Executado automaticamente em **todo push e pull request** para as branches `main`, `develop`, `feature/**`, `release/**` e `hotfix/**`:

| Etapa | O que faz |
|-------|-----------|
| **Lint (flake8)** | Verifica erros de sintaxe e nomes indefinidos (bloqueia merge) + avisos de estilo (não bloqueia) |
| **Testes (pytest)** | Executa a suíte de testes em `tests/` |
| **Segurança** | Verifica ausência de credenciais hardcodadas no código-fonte |

> **Importante:** As branches `main` e `develop` estão protegidas — o merge via PR só é permitido se o CI estiver verde (badge ✅).

### Secrets necessários no GitHub

Para que o **CD (deploy)** funcione, os seguintes secrets devem ser configurados em **Settings → Secrets and variables → Actions**:

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
