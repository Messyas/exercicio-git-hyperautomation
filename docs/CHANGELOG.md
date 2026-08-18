# CHANGELOG

Todas as alterações notáveis deste projeto serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
e este projeto adere ao [Semantic Versioning](https://semver.org/lang/pt-BR/).

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
