# Bot de Inspeção de Lotes Diários

![CI/CD Pipeline](https://github.com/Messyas/exercicio-git-hyperautomation/actions/workflows/CI.yml/badge.svg)

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

## CI/CD

O projeto utiliza **GitHub Actions** para integração e entrega contínuas. O pipeline está definido em [`.github/workflows/CI.yml`](.github/workflows/CI.yml).

### CI — Integração Contínua

Executado automaticamente em **todo push e pull request** para as branches `main`, `develop`, `feature/**`, `release/**` e `hotfix/**`:

| Etapa | O que faz |
|-------|-----------|
| **Lint (flake8)** | Verifica erros de sintaxe e nomes indefinidos (bloqueia merge) + avisos de estilo (não bloqueia) |
| **Testes (pytest)** | Executa a suíte de testes em `tests/` com relatório de cobertura via `pytest-cov` |
| **Segurança** | Verifica ausência de credenciais hardcodadas no código-fonte |

> **Importante:** As branches `main` e `develop` estão protegidas — o merge via PR só é permitido se o CI estiver verde (badge ✅).

### CD — Deploy para BotCity Maestro

Executado automaticamente quando uma **tag de release** (`v*.*.*`) é criada:

1. Empacota o bot em `.zip` (exclui testes, `.env`, cache, etc.)
2. Faz upload do pacote para o **BotCity Maestro** via SDK

### Secrets necessários no GitHub

Para que o **CD (deploy)** funcione, os seguintes secrets devem ser configurados em **Settings → Secrets and variables → Actions**:

| Secret | Descrição |
|--------|-----------|
| `MAESTRO_SERVER` | URL do servidor BotCity Maestro (ex: `https://developers.botcity.dev`) |
| `MAESTRO_LOGIN` | Login de acesso ao Maestro |
| `MAESTRO_KEY` | Chave/token de API do Maestro |
| `BOT_ID` | Identificador do bot no Maestro (ex: `bot-conferencia-lotes`) |

> ⚠️ **Nunca** coloque credenciais diretamente no código ou no arquivo de workflow. Use apenas GitHub Secrets.

