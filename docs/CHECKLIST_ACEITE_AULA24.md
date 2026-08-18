# Checklist de Aceite — Aula 24

**Projeto:** Exercício Git / Hyperautomation — Aula 24<br>
**Branch de trabalho:** `feature/indicadores-operacionais`<br>
**Alvo de PR:** `Developer`<br>
**Data de revisão:** 17/08/2026<br>
**Status:** Validado localmente — CI remoto e PR ainda pendentes.

## Critérios e evidências

| Item | Critério de aceite | Estado | Evidência verificável |
|---:|---|:---:|---|
| 1 | RN01–RN12 e a precedência de classificação são preservadas. | `[x]` | [serviço de validação](../dashboard/servico_validacao.py) e testes de regressão. |
| 2 | A deduplicação permanece limitada ao mesmo dia. | `[x]` | `validar_registros_lista()` em [serviço de validação](../dashboard/servico_validacao.py). |
| 3 | A camada de indicadores é pura e não depende de apresentação. | `[x]` | [operational_indicators.py](../src/operational_indicators.py). |
| 4 | `_percentual()` protege divisão por zero e centraliza os percentuais do dashboard. | `[x]` | [_percentual()](../src/operational_indicators.py) é reutilizada também no PDF compatível. |
| 5 | Os dez indicadores conferem com o gabarito de 250 registros. | `[x]` | Testes unitários e [teste de integração](../tests/integration/test_relatorio_consolidado.py). |
| 6 | Os indicadores são calculados uma única vez por execução. | `[x]` | `executar_pipeline_dashboard()` em [main.py](../dashboard/main.py), monitorado no teste de integração. |
| 7 | O Excel possui exatamente oito abas, na ordem definida. | `[x]` | [teste de integração](../tests/integration/test_relatorio_consolidado.py). |
| 8 | O Resumo contém os dez indicadores e dois gráficos nativos; a rosca usa somente as quatro classificações. | `[x]` | [main.py](../dashboard/main.py) e validação dos intervalos XML no teste de integração. |
| 9 | Ranking e regra principal vêm da mesma consolidação de regras. | `[x]` | `ranking_regras` em [operational_indicators.py](../src/operational_indicators.py). |
| 10 | O Dicionário explica colunas, classificações, regras, taxas e premissas. | `[x]` | Geração da aba em [main.py](../dashboard/main.py). |
| 11 | Excel e Markdown expõem os mesmos valores do cenário de referência. | `[x]` | [teste de integração](../tests/integration/test_relatorio_consolidado.py). |
| 12 | O ganho apresenta fórmula, 2,00 min manual, 0,25 min automatizado e aviso de estimativa didática. | `[x]` | [gerador do resumo](../dashboard/main.py) e [README](../README.md). |
| 13 | Os testes novos usam os markers `unit` e `integration`. | `[x]` | [testes unitários](../tests/unit/test_operational_indicators.py) e [teste de integração](../tests/integration/test_relatorio_consolidado.py). |
| 14 | A suíte completa passa e a cobertura total e do novo módulo é pelo menos 80%. | `[x]` | Execução local: 113 aprovados, 1 ignorado, 1 xfail conhecido; cobertura total 87,57% e `operational_indicators.py` 99%. Relatórios em `reports/`. |
| 15 | README, PDD e CHANGELOG documentam a Aula 24, premissas e limitações. | `[x]` | [README principal](../README.md), [README do dashboard](../dashboard/README.md), [PDD](pdd/PDD_Process_Design_Document.md) e [CHANGELOG](CHANGELOG.md). |
| 16 | Artefatos gerados não são versionados e não há caminhos absolutos ou credenciais na documentação. | `[x]` | `git ls-files data/output` lista somente `.gitkeep`; a documentação foi verificada sem links `file:///` ou caminhos locais absolutos. |
| 17 | PR contra `Developer` possui evidências, checklist preenchido e reviewers sem conflito. | `[ ]` | Criar PR somente após os checks verdes e substituir este item por links remotos verificáveis. |

## Comandos para conclusão

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

Anexar ao PR o log do pytest, `coverage.xml`, o relatório HTML e os quatro
artefatos do dashboard. Só então marcar o item 17 como concluído.
