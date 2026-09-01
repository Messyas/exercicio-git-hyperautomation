# Pipeline Híbrido de Conferência de Estoque e Pedidos (Capstone de Hyperautomation)

[![CI/CD](https://github.com/Messyas/exercicio-git-hyperautomation/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/Messyas/exercicio-git-hyperautomation/actions/workflows/ci-cd.yml)

**Projeto Final de Conclusão de Curso** · *Técnicas de Hyperautomation (240h)*  
**Parceria:** LG Electronics do Brasil · AX Academy / IFAM / Polo de Inovação (INOVA)  
**Ambiente Operacional:** Smart Office Orchestrator & Governança The DX Way  

---

## Guia Rápido de Instalação (Setup em Outra Máquina)

Siga este procedimento para clonar, instalar e executar a solução completa em uma nova máquina do zero.

### Pré-requisitos
* **Python 3.12** (ou superior)
* **Git**
* **Navegador Chromium** (instalado automaticamente via Playwright)
* **Docker & Docker Compose** *(opcional, necessário apenas para execução em containers)*

---

### Passo a Passo de Instalação Local

#### 1. Clonar o repositório
```bash
git clone https://github.com/Messyas/exercicio-git-hyperautomation.git
cd exercicio-git-hyperautomation
```

#### 2. Criar e ativar o ambiente virtual (venv)
* **No Windows (PowerShell):**
  ```powershell
  python -m venv .venv
  .\.venv\Scripts\Activate.ps1
  ```
* **No Linux / macOS (Bash):**
  ```bash
  python3 -m venv .venv
  source .venv/bin/activate
  ```

#### 3. Instalar as dependências do projeto
```bash
python -m pip install --upgrade pip
pip install -r requirements-dev.txt -r api_ml/requirements.txt
```

#### 4. Instalar os navegadores do Playwright (Chromium)
```bash
playwright install chromium --with-deps
```

#### 5. Configurar o arquivo de variáveis de ambiente
Copie o modelo de configuração padrão:
* **No Windows (PowerShell):**
  ```powershell
  Copy-Item .env.example .env
  ```
* **No Linux / macOS:**
  ```bash
  cp .env.example .env
  ```
*(O arquivo `.env.example` já vem pré-configurado com valores padrão para execução local e em container).*

---

## Comandos Principais de Execução

Com o ambiente virtual ativado, execute as operações desejadas:

### 1. Iniciar o Portal Web & Control Tower (Apresentação Visual Interativa)
Inicia o servidor web integrado com a interface de apresentação em 7 etapas guiadas, dashboard executivo e cadastro de lotes:
```bash
python web/server.py 8080
```
> Abra no navegador: **`http://localhost:8080`**

---

### 2. Executar a Demonstração Completa da Esteira (6 Bots)
Executa a cadeia integrada dos 6 robôs em cascata, gerando o relatório de rastreabilidade ponta a ponta:
```bash
python src/scripts/demo_capstone.py
```
*(Artefato gerado: `data/reports/rastreabilidade_pipeline_capstone.json`)*

---

### 3. Executar o Pipeline Sequencial de Lotes (Produtor + Validador)
Executa o cadastro automatizado via Playwright e a validação determinística de regras:
```bash
python pipeline.py
```

---

### 4. Executar a Matriz de Resiliência sob Crise (6 Ensaios de Sabotagem)
Valida os 6 cenários de sabotagem com Circuit Breaker, fallback degradado, Dead Letter Queue e retenção de concorrência:
```bash
python src/scripts/simular_cenarios_sabotagem.py
```
*(Artefato gerado: `data/reports/evidencias_sabotagem/resumo_evidencias_capstone.json`)*

---

### 5. Executar o Smoke Test de Corte (Validação Pós-Deploy)
Valida a prontidão dos 6 bots e o guard de coexistência gráfica antes do agendamento oficial:
```bash
python src/scripts/smoke_test_cutover.py
```
*(Artefato gerado: `data/reports/smoke_test_report.json`)*

---

### 6. Gerar o Relatório Executivo Consolidado e Indicadores
Processa a base consolidada e gera os artefatos finais de auditoria:
```bash
python src/scripts/gerar_relatorio_executivo.py
```
*(Artefatos gerados em `data/output/`: planilha Excel de 9 abas, resumo executivo em Markdown, PDF consolidado e log de auditoria).*

---

### 7. Gerar Pacotes de Deploy `.zip` para o Smart Office / BotCity
Gera os arquivos `.zip` independentes de cada bot com `bot.py` e `requirements.txt` na raiz:
```bash
python src/scripts/build_smartoffice_packages.py
```
*(Arquivos gerados em: `dist/smartoffice/`)*

---

## Execução dos Testes Automatizados

O repositório possui suíte de testes com cobertura superior a 85%:

```bash
# 1. Executar testes unitários, integração e regressão (sem abrir browser)
python -m pytest tests/ -m "not browser" -v

# 2. Executar testes E2E com navegador Chromium real (Playwright)
# Windows (PowerShell):
$env:RUN_BROWSER_E2E="1"; python -m pytest tests/e2e/ -v

# Linux/macOS:
RUN_BROWSER_E2E=1 python -m pytest tests/e2e/ -v

# 3. Validar cobertura de código com limite mínimo de 80%
python -m pytest tests/ -m "not browser" --cov=src --cov-config=.coveragerc --cov-report=term-missing --cov-fail-under=80
```

---

## Execução com Docker Compose (Opcional)

Caso prefira executar a solução isolada em containers Docker:

```bash
# 1. Subir o Portal Web & Control Tower na porta 8080
docker compose up -d

# 2. Executar o classificador de Machine Learning em container
docker compose --profile ml up --build --abort-on-container-exit --exit-code-from bot-classificador api-ml bot-classificador

# 3. Executar o bot de conferência completo em container
docker compose --profile avaliacao run --rm bot-conferencia

# 4. Validar evidências geradas pelo container
docker compose --profile avaliacao run --rm --no-deps --entrypoint python bot-conferencia src/scripts/verify_pipeline.py

# 5. Encerrar todos os serviços e volumes
docker compose --profile avaliacao --profile ml down --volumes --remove-orphans
```

---

## Arquitetura da Solução Capstone (6 Bots)

A solução orquestra 6 robôs modulares com prioridades estritas e tratamento de exceções:

```
                  CADEIA DE ORQUESTRAÇÃO DE 6 BOTS (SMART OFFICE)
   ┌────────────────────────────────┐                 ┌───────────────────────────────┐
   │ RPA01_ColetaEstoque_DESKTOP    │                 │ RPA02_ColetaPedidos_WEB       │
   │ • Automação Windows Desktop    │                 │ • Automação Web (Playwright)  │
   │ • Prioridade: 1 (Alta/GUI Lock)│                 │ • Prioridade: 2 (Média)       │
   └───────────────┬────────────────┘                 └───────────────┬───────────────┘
                   │ [datapool/coleta_desktop.json]                   │ [datapool/coleta_web.json]
                   └────────────────────────┬─────────────────────────┘
                                            ▼
                          ┌───────────────────────────────────┐
                          │ RPA03_ConsolidacaoRegras_CORE     │
                          │ • Cruzamento Físico x Pedidos     │
                          │ • Motor Determinístico RN01-RN12  │
                          │ • Prioridade: 3 (Timeout Control) │
                          │ • Falhas de Dado -> Dead Letter Q │
                          └─────────────────┬─────────────────┘
                                            │ [datapool/lotes_consolidados.json]
                                            ▼
                          ┌───────────────────────────────────┐
                          │ RPA04_ClassificadorML_HYBRID      │
                          │ • Triagem de Causa Provável por ML│
                          │ • Feature Flag & Circuit Breaker  │
                          │ • Prioridade: 4 (Não Crítico)     │
                          │ • orig_decisao / confianca_ml     │
                          └─────────────────┬─────────────────┘
                                            │ [datapool/lotes_enriquecidos_ml.json]
                                            ▼
                          ┌───────────────────────────────────┐
                          │ RPA05_RelatorioAlertas_NOTIF      │
                          │ • Relatório Excel de 9 Abas       │
                          │ • Alertas Multicanal com Fallback │
                          │ • Prioridade: 5 (Notificação)     │
                          └───────────────────────────────────┘

                          ┌───────────────────────────────────┐
                          │ RPA06_ReprocessadorDeadLetter_SCHED│
                          │ • Auditoria Periódica da DLQ      │
                          │ • Saneamento e Alertas de Base    │
                          │ • Prioridade: 5 (Schedule Cron)   │
                          └───────────────────────────────────┘
```

### Destaques de Engenharia e Governança The DX Way
1. **Decisão Híbrida RPA + ML (Nunca Crítica):** O status do lote é decidido 100% pelo motor determinístico RN01–RN12. O modelo supervisionado atua exclusivamente recomendando a causa provável em itens divergentes, isolado por Circuit Breaker (abre após 5 falhas) e feature flag.
2. **Dead Letter Queue (`data/dead_letter/`):** Registros corrompidos ou irrecuperáveis são apartados sem interromper o processamento do restante do lote.
3. **CoexistenceGuard:** Prevenção de concorrência em sessão gráfica de runner entre orquestradores distintos.
4. **Notificação Multicanal:** Prioridade Telegram com fallback degradado automático para Log Local / Email.

---

## Documentação e Entregáveis Oficiais

* **[Process Design Document (PDD v2.0)](docs/pdd/PDD_Process_Design_Document.md)**: Mapeamento AS-IS/TO-BE, matriz de regras RN01–RN12 e Seção 21 do Capstone.
* **[Plano de Migração e Coexistência](docs/PLANO_MIGRACAO_COEXISTENCIA.md)**: Janela de coexistência (Shadow Mode), critérios de cutover e plano de Rollback (RTO < 15 min).
* **[Guia de Boas Práticas e Governança](docs/GUIA_AULA_DOCUMENTACAO_E_BOAS_PRATICAS.md)**: Governança, esteira Smart Office, idempotência e integridade de pacotes.
* **[Relatório de Auditoria de Conformidade](docs/RELATORIO_AUDITORIA_CONFORMIDADE_E_ENTREGAVEIS.md)**: Matriz de conformidade contra o guia de aula e checklist prático dos entregáveis.
* **[Evidências de Conformidade e Sabotagem](docs/evidencias/EVIDENCIAS_CAPSTONE.md)**: Rastreabilidade dos 7 eixos da rubrica e auditoria dos 6 ensaios de crise.
* **[Roteiro de Pitch e Defesa Técnica](docs/PITCH_APRESENTACAO_CAPSTONE.md)**: Estrutura da apresentação executiva de 10 min.

---

## Estrutura do Repositório

```text
├── api_ml/                     # Microserviço FastAPI e modelo de Machine Learning
│   ├── main.py                 # Endpoints /health e /predict
│   ├── model_service.py        # Serviço de predição e regras de confiança
│   ├── Dockerfile              # Imagem do serviço de inferência
│   └── requirements.txt        # Dependências da API de ML
├── bots/                       # Implementação dos 6 robôs Smart Office
│   ├── RPA01_ColetaEstoque_DESKTOP/
│   ├── RPA02_ColetaPedidos_WEB/
│   ├── RPA03_ConsolidacaoRegras_CORE/
│   ├── RPA04_ClassificadorML_HYBRID/
│   ├── RPA05_RelatorioAlertas_NOTIF/
│   └── RPA06_ReprocessadorDeadLetter_SCHED/
├── data/                       # Datapool local, amostras, outputs e dead letter
│   ├── datapool/               # Filas de comunicação desacopladas entre bots
│   ├── dead_letter/            # Fila de itens retidos para auditoria
│   ├── output/                 # Relatórios gerados (.xlsx, .pdf, .md, .log)
│   └── samples/                # Planilhas de inspeção de entrada
├── docs/                       # PDD, planos de migração, governança e evidências
├── models/                     # Modelo serializado (.pkl) e métricas de treino
├── src/                        # Código-fonte compartilhado da solução
│   ├── automation/             # Orquestrador, gateways de datapool e guards
│   ├── core/                   # Motor de regras determinísticas (RN01-RN12)
│   ├── ml/                     # Cliente HTTP resiliente e circuit breaker
│   ├── reporting/              # Geradores de relatórios e indicadores operacionais
│   └── scripts/                # Scripts utilitários, demos, treinos e sabotagens
├── tests/                      # Suíte de testes (unit, integration, regression, e2e)
├── web/                        # Portal Web & Control Tower (HTML5, CSS3, JS, server.py)
├── docker-compose.yml          # Definição multi-profile de containers (portal, ml, avaliacao)
├── Dockerfile                  # Multi-stage build para bots e runners
├── pipeline.py                 # Ponto de entrada sequencial (Produtor + Consumidor)
├── requirements.txt            # Dependências de produção
└── requirements-dev.txt        # Dependências de desenvolvimento e testes
```
