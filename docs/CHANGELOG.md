# CHANGELOG

Todas as alterações notáveis deste projeto serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
e este projeto adere ao [Semantic Versioning](https://semver.org/lang/pt-BR/).

## [1.1.0] — Exercício 24-A (ML + RPA) — 2026-08-18

### Adicionado
- Microserviço `api_ml` em FastAPI com endpoints `POST /predict` e `GET /health`.
- Pipeline de treino Random Forest com `CalibratedClassifierCV` em `scripts/train_model.py` e dataset sintético de 12.000 amostras.
- Cliente resiliente `MLClient` com `CircuitBreaker` (abertura após 5 falhas consecutivas) em `src/ml_client.py`.
- Módulo `src/item_processor.py` integrando ML para registros ambíguos sem interromper o fluxo do lote (`REVISAO_ML_OFFLINE`).
- 9ª aba `Decisões de ML` no relatório Excel consolidado `relatorio_conferencia_lotes.xlsx`.
- Script de demonstração `scripts/demo_torneio.py` para os 50 casos ambíguos.
- Suíte completa de testes unitários e de integração/sabotagem para ML (`test_api_ml.py`, `test_ml_client.py`, `test_item_processor_ml.py`, `test_sabotagem_ml.py`).

## [1.0.0] — Aula 24 — 2026-08-17

### Adicionado
- Módulo puro `src/operational_indicators.py` para cálculo centralizado e desacoplado dos 10 indicadores operacionais (`OperationalIndicators`, `RankedRule`, `_percentual()`, `CATALOGO_REGRAS`).
- Orquestrador principal `dashboard/main.py` e CLI oficial (`python -m dashboard.main`) para o Dashboard Executivo da Aula 24.
- Gerador do resumo executivo em Markdown `data/output/resumo_executivo.md` em linguagem de negócio e alinhado ao gabarito do Excel.
- Abas `Ranking de Regras` (aba 7) e `Dicionário` (aba 8) no relatório Excel `relatorio_conferencia_lotes.xlsx`.
- Suíte de testes unitários para a camada pura de indicadores em `tests/unit/test_operational_indicators.py`.
- Teste de integração consolidado em `tests/integration/test_relatorio_consolidado.py`.
- Checklist final de aceite da Aula 24 em `docs/CHECKLIST_ACEITE_AULA24.md`.

### Alterado
- Refatoração da validação em `dashboard/servico_validacao.py` adicionando `validar_registros_lista()` para preservar a lista de `RegistroValidado` sem conversões prematuras.
- Relatório Excel refatorado para 8 abas (`Resumo`, `Todos`, `Válidos`, `Divergências`, `Ambíguos`, `Erros de Entrada`, `Ranking de Regras`, `Dicionário`).
- Fachada `dashboard/gerar_relatorio.py` adaptada para delegar a execução ao novo orquestrador `dashboard/main.py`.
- `dashboard/docker-compose.yml` atualizado para executar a CLI oficial `python -m dashboard.main`.
- `.gitignore` ajustado para ignorar saídas geradas (`*.xlsx`, `*.pdf`, `resumo_executivo.md`, `*.log`, relatórios de cobertura).
- `.github/workflows/ci-cd.yml` atualizado para preservar XML, HTML, log do pytest e os artefatos gerados da Aula 24.
- Gráfico de rosca do Resumo corrigido para representar somente as quatro classificações, sem incluir o total processado.
- Referências da tabela Resumo ajustadas: classificações são informativas e as metas ficam restritas às taxas de negócio.

### Testes
- A suíte possui cobertura para a origem e os intervalos dos gráficos, além da consistência entre Excel e Markdown.
- A execução completa e a confirmação de cobertura devem ser registradas pelos artefatos do CI antes do aceite final.
- Validação de chamada única a `calcular_indicadores()` por execução.

### Documentação
- `README.md` e `dashboard/README.md` atualizados com instruções, comandos CLI, arquitetura de fonte única e gabarito.
- `PDD_Process_Design_Document.md` atualizado com a seção 20.1 detalhando a arquitetura da Aula 24, escopo de RN01–RN12 e rotulagem do ganho como estimativa didática.
