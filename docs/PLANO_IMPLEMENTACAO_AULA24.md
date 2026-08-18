# Plano de Implementação — Aula 24

## Dashboard Executivo, Relatório Consolidado, Testes e Checklist Final

> **Status deste documento:** planejamento. Nenhuma alteração técnica descrita aqui deve ser considerada implementada, testada ou aprovada sem a evidência correspondente.
>
> **Fontes normativas:** `Enunciado_Exercicio_Dashboard_Testes_Checklist_Aula24.docx` e `Formulario_Avaliacao_Pares_Aula24.pdf`. As instruções desses documentos são requisitos da futura implementação; a solicitação que originou este arquivo foi somente produzir o plano detalhado em Markdown.

## 1. Objetivo e definição de sucesso

Evoluir o dashboard de conferência de lotes da Aula 23 para a entrega completa da Aula 24, sem alterar o comportamento do motor RN01–RN12. A solução deverá possuir uma única fonte de verdade para os indicadores, gerar um Excel com oito abas, produzir um resumo executivo em Markdown, preservar os gráficos nativos, ampliar a suíte automatizada e entregar documentação e evidências suficientes para obter a classificação **Excelente** em todos os sete critérios da avaliação por pares.

A implementação estará concluída somente quando:

- os dez indicadores forem calculados por uma camada pura e dedicada;
- Excel, Markdown, PDF de compatibilidade e log consumirem o mesmo objeto de indicadores;
- a planilha tiver exatamente as oito abas exigidas, na ordem e com os nomes definidos neste plano;
- o relatório e o resumo executivo apresentarem os mesmos números;
- a suíte anterior continuar verde, os testes novos passarem e a cobertura comprovada for de pelo menos 80%;
- README, PDD, CHANGELOG e checklist final estiverem atualizados e coerentes com a entrega;
- arquivos gerados, logs, credenciais e caminhos locais não forem versionados;
- o Pull Request contra `Developer` estiver com checks verdes, evidências anexadas e revisão sem conflito de interesse.

## 2. Diagnóstico do estado atual

### 2.1 O que já pode ser reaproveitado

- `dashboard/servico_validacao.py` já contém `RegistroValidado`, `validar_registro()` e o campo `regras_aplicadas`.
- `regras_aplicadas` já fornece a rastreabilidade necessária para a regra mais acionada e para o Ranking de Regras; não é necessário alterar a lógica de RN01–RN12.
- A deduplicação por dia já é feita antes de `validar_registro()`, mediante contadores isolados por aba diária.
- `dashboard/gerar_relatorio.py` já consolida as dez abas, produz as seis abas da Aula 22 e cria um gráfico de rosca e um gráfico de evolução como objetos nativos do Excel.
- A suíte da Aula 23 já está separada em `unit`, `integration`, `regression` e `e2e`, com markers declarados no `pytest.ini`.
- O dataset efetivamente existente no projeto e equivalente ao nome usado no enunciado é `data/samples/inspecao_lotes_10dias_sem gabarito.xlsx`.

### 2.2 Lacunas encontradas

- Não existe `src/operational_indicators.py`.
- A aba `Resumo` ainda mostra apenas totais básicos, e não os dez indicadores completos.
- O Excel possui seis abas; faltam `Ranking de Regras` e `Dicionário`.
- Não existe `data/output/resumo_executivo.md`.
- Totais e percentuais são recalculados dentro do gerador do Excel e do PDF, criando múltiplas fontes de verdade.
- Não existem os testes específicos pedidos para a camada de indicadores e para o relatório consolidado de oito abas.
- `docs/CHANGELOG.md` está vazio.
- O PDD mantém descrições do fluxo legado de um dia/RN01–RN07 ao lado do dashboard de dez dias/RN01–RN12, sem uma separação explícita entre os dois contextos.
- `.gitignore` abre exceções para Excel, PDF e log gerados, embora o checklist da Aula 24 determine que saídas e logs não sejam versionados.
- A evidência de cobertura do CI ainda está identificada como Aula 23.
- O `main.py` da raiz pertence ao fluxo corporativo já existente; usá-lo diretamente para a Aula 24 aumentaria o risco de regressão.

### 2.3 Gabarito verificável do dataset

Os valores abaixo devem ser usados como oráculo de integração e E2E. Eles não devem ser codificados diretamente na lógica de produção.

| Indicador | Resultado esperado |
|---|---:|
| Total de registros | 250 |
| Registros válidos | 150 / 60% |
| Divergências | 50 / 20% |
| Ambíguos | 20 / 8% |
| Erros de Entrada | 30 / 12% |
| Regra mais acionada | RN06, 25 ocorrências / 10% |
| Taxa de qualidade da entrada | 88% / ✓ |
| Taxa de revisão humana | 8% / ✓ |
| Taxa de retrabalho | 20% / ⚠ |
| Ganho estimado de tempo | 437,5 min / 7h17min30s |

A distribuição de regras esperada para a planilha atual é: RN06=25, RN10=21, RN09=20, RN11=20, RN12=20, RN05=10, RN07=10, RN04=4, RN01=2, RN02=2 e RN03=2. A RN08 representa a aceitação de um status canônico e, no desenho atual, não gera ocorrência registrada.

## 3. Arquitetura-alvo e contratos públicos

### 3.1 Camada pura de indicadores

Criar `src/operational_indicators.py`. Esse módulo poderá importar apenas biblioteca-padrão e tipos necessários para anotação; não poderá importar pandas, openpyxl, ReportLab, Markdown, pytest nem componentes de interface.

Interfaces previstas:

```python
from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True)
class RankedRule:
    codigo: str
    nome: str
    ocorrencias: int
    percentual_total: float


@dataclass(frozen=True)
class OperationalIndicators:
    total_registros: int
    registros_validos: int
    percentual_validos: float
    divergencias: int
    percentual_divergencias: float
    ambiguos: int
    percentual_ambiguos: float
    erros_entrada: int
    percentual_erros_entrada: float
    regra_mais_acionada: RankedRule | None
    taxa_qualidade_entrada: float
    taxa_revisao_humana: float
    taxa_retrabalho: float
    tempo_manual_minutos: float
    tempo_automatizado_minutos: float
    ganho_estimado_minutos: float
    ranking_regras: tuple[RankedRule, ...]


def _percentual(parte: int, total: int) -> float:
    ...


def calcular_indicadores(
    registros: Sequence[RegistroValidado],
    *,
    tempo_manual_minutos: float = 2.0,
    tempo_automatizado_minutos: float = 0.25,
) -> OperationalIndicators:
    ...
```

### 3.2 Regras de cálculo

1. Materializar a sequência de registros uma única vez para impedir resultados diferentes ao receber iteradores.
2. Validar que toda `classificacao` pertença a `Válido`, `Divergência`, `Ambíguo` ou `Erro de Entrada`; valor desconhecido deve gerar `ValueError` com a classificação problemática.
3. Validar as premissas: ambos os tempos devem ser não negativos e o tempo manual deve ser maior ou igual ao automatizado.
4. Contar as quatro classificações com um único `Counter`.
5. Achatar `regras_aplicadas` e criar um único `Counter` de regras.
6. Gerar `ranking_regras` por `Counter.most_common()`. Em empate, preservar a ordem da primeira ocorrência na lista validada.
7. Definir `regra_mais_acionada` como o primeiro item do ranking ou `None` quando nenhuma regra tiver sido acionada.
8. Usar `_percentual()` para todos os percentuais, inclusive as participações do ranking.
9. Armazenar percentuais como pontos percentuais entre 0 e 100; os exportadores apenas convertem a apresentação, sem refazer o cálculo.
10. Calcular o ganho como `total_registros × (tempo_manual_minutos − tempo_automatizado_minutos)`.

`_percentual(parte, total)` deverá implementar exatamente `(parte / total) × 100`, retornando `0.0` quando `total == 0`. Uma lista vazia deve produzir totais, taxas e ganho iguais a zero, ranking vazio e `regra_mais_acionada=None`.

### 3.3 Catálogo central de regras

Manter no módulo um catálogo imutável com código e nome acessível de RN01–RN12. O mesmo catálogo alimentará Ranking de Regras e Dicionário. A descrição deverá refletir `dashboard/servico_validacao.py`, que continua sendo a autoridade do comportamento:

| Regra | Nome acessível |
|---|---|
| RN01 | Lote obrigatório |
| RN02 | Produto obrigatório |
| RN03 | Linha obrigatória |
| RN04 | Campos operacionais obrigatórios |
| RN05 | Lote ausente da Base de Referência |
| RN06 | Normalização de OK para APROVADO |
| RN07 | Normalização de NOK para REPROVADO |
| RN08 | Status canônico aceito, sem ocorrência registrada |
| RN09 | Status desconhecido encaminhado à revisão humana |
| RN10 | Reprovado sem observação |
| RN11 | Lote duplicado no mesmo dia |
| RN12 | Data inválida ou diferente da referência diária |

## 4. Fluxo principal da Aula 24

### 4.1 Orquestração

Criar `dashboard/main.py` para isolar o fluxo de dez dias e preservar o `main.py` corporativo da raiz.

Fluxo obrigatório:

1. Receber os caminhos de entrada e saída.
2. Carregar as dez abas de inspeção e a Base de Referência.
3. Aplicar a deduplicação por dia.
4. Validar cada linha exatamente uma vez e preservar uma lista de `RegistroValidado`.
5. Chamar `calcular_indicadores()` exatamente uma vez.
6. Converter a lista validada para DataFrame apenas na fronteira de apresentação.
7. Entregar o mesmo objeto `OperationalIndicators` aos geradores de Excel, Markdown, PDF de compatibilidade e log.
8. Retornar os caminhos dos artefatos gerados, permitindo testes sem depender de saída do terminal.

CLI oficial:

```bash
python -m dashboard.main \
  --entrada "data/samples/inspecao_lotes_10dias_sem gabarito.xlsx" \
  --saida data/output
```

Atualizar `dashboard/docker-compose.yml` para usar essa CLI. O `dashboard/Dockerfile` já copia `dashboard/` e `src/`, portanto não deve depender do `main.py` da raiz.

### 4.2 Compatibilidade

Manter `dashboard.gerar_relatorio.gerar_relatorio()` como fachada compatível. Ela deverá delegar ao orquestrador e continuar retornando o caminho de `relatorio_conferencia_lotes.xlsx`. Nenhum chamador existente deverá validar a mesma entrada uma segunda vez.

Separar no gerador as responsabilidades de:

- converter os objetos validados para dados tabulares;
- escrever o workbook usando indicadores já calculados;
- gerar o resumo executivo usando indicadores já calculados;
- gerar o PDF compatível usando indicadores já calculados;
- registrar o log final usando indicadores já calculados.

## 5. Relatório Excel com oito abas

### 5.1 Ordem e nomes obrigatórios

O workbook deverá conter exatamente:

1. `Resumo`
2. `Todos`
3. `Válidos`
4. `Divergências`
5. `Ambíguos`
6. `Erros de Entrada`
7. `Ranking de Regras`
8. `Dicionário`

As cinco abas de detalhe devem conservar as colunas e o comportamento atual. Cada aba classificada deverá conter somente registros da classificação indicada pelo nome.

### 5.2 Aba Resumo

Usar uma tabela com dez linhas e as colunas:

- `Indicador`;
- `Quantidade/Valor`;
- `Percentual`;
- `Referência`;
- `Sinal/Detalhe`.

As linhas devem aparecer nesta ordem:

1. Total de registros;
2. Registros válidos;
3. Divergências;
4. Ambíguos;
5. Erros de Entrada;
6. Regra mais acionada;
7. Taxa de qualidade da entrada;
8. Taxa de revisão humana;
9. Taxa de retrabalho;
10. Ganho estimado de tempo.

Requisitos de apresentação:

- gravar valores constantes oriundos de `OperationalIndicators`, sem fórmulas soltas;
- exibir quantidades e percentuais juntos nos indicadores 2–5;
- mostrar código, nome e ocorrências da regra principal;
- usar as referências `> 80%`, `< 15%` e `< 6%` apenas como sinal visual, nunca como aprovação do exercício;
- exibir `✓` para qualidade e revisão humana no gabarito atual e `⚠` para retrabalho;
- exibir o ganho em minutos e formato legível de horas;
- mostrar junto ao ganho: `Premissas: 2,00 min manual e 0,25 min automatizado por registro — estimativa didática`;
- manter timestamp com fuso `America/Manaus`;
- aplicar formatação numérica consistente, congelamento adequado e larguras que não cortem conteúdo.

O gráfico de rosca deve continuar usando as quatro contagens de classificação e ser um `DoughnutChart` nativo. O gráfico de evolução deve continuar como `LineChart` nativo, com os dez dias e a série `Divergências + Ambíguos`. A tabela diária ficará em área separada dos dez indicadores, sem sobreposição com os gráficos.

### 5.3 Aba Ranking de Regras

Colunas obrigatórias:

| Posição | Regra | Nome | Ocorrências | % do total |
|---:|---|---|---:|---:|

Regras:

- escrever somente regras acionadas;
- reutilizar `OperationalIndicators.ranking_regras` sem executar outro `Counter`;
- preservar a ordem de `most_common()`;
- garantir que a primeira linha seja idêntica ao indicador 6 da aba Resumo;
- formatar `% do total` a partir do percentual já calculado;
- incluir nota visível informando que um registro pode acionar mais de uma regra e, portanto, os percentuais não precisam somar 100%.

### 5.4 Aba Dicionário

Colunas obrigatórias:

| Termo | Definição | Fórmula/Regra | Interpretação |
|---|---|---|---|

Cobertura mínima:

- todas as colunas expostas nas abas de detalhe;
- as quatro classificações;
- RN01–RN12;
- total de registros, regra mais acionada e ranking;
- taxa de qualidade, revisão humana e retrabalho;
- ganho estimado, tempo manual e tempo automatizado;
- Base de Referência, data de referência e deduplicação por dia.

As definições devem ser compreensíveis para um leitor não técnico. RN08 deverá ser explicada mesmo sem aparecer no ranking.

## 6. Resumo executivo em Markdown

Gerar `data/output/resumo_executivo.md` em UTF-8 com esta estrutura fixa:

```text
# Resumo Executivo — Conferência de Lotes
## Visão Geral
## Indicadores Principais
## Destaque
## Ganho Estimado de Tempo
## Observação
```

Regras editoriais:

- escrever em linguagem de negócio;
- não mencionar nomes de função, classe, método ou coluna interna;
- apresentar total, quatro classificações, três taxas, regra principal e ganho;
- manter os mesmos valores e arredondamentos do Excel;
- explicar RN06 como volume de registros recebidos com `OK` e normalizados para `APROVADO`;
- declarar `2,00 min manual versus 0,25 min automatizado por registro`;
- rotular o ganho como **estimativa didática**, não como medição real de produção;
- explicar que transformar o ganho em métrica real exigiria telemetria de produção e medição de tempos observados;
- manter o texto sintético o suficiente para leitura em voz alta ou colagem em um e-mail executivo.

O Markdown nunca recalculará valores. Ele apenas formatará `OperationalIndicators`.

## 7. PDF e dashboard Streamlit de compatibilidade

O arquivo `resumo_conferencia_lotes.pdf` poderá continuar sendo gerado para não quebrar os testes e o uso anterior, mas deverá receber `OperationalIndicators` e deixar de recalcular totais e percentuais.

O Streamlit permanecerá como superfície adicional, fora dos entregáveis obrigatórios. Para evitar uma fonte paralela de indicadores, deverá ler os valores consolidados do workbook ou receber dados derivados do mesmo objeto; a evolução diária pode continuar usando os registros validados porque não faz parte dos dez indicadores oficiais.

## 8. Estratégia de testes

### 8.1 Linha de base

Antes de alterar código, registrar a execução da suíte da Aula 23. A implementação não deve começar sobre uma suíte instável. `skip` e `xfail(strict=True)` já documentados não contam como falha, mas seus motivos devem permanecer visíveis.

### 8.2 Testes unitários novos

Criar `tests/unit/test_operational_indicators.py`, marcado com `pytest.mark.unit`, cobrindo:

1. `_percentual(25, 100) == 25.0`;
2. `_percentual(1, 0) == 0.0` e `_percentual(0, 0) == 0.0`;
3. cenário parametrizado com registros conhecidos e expectativas para os dez indicadores;
4. lista vazia;
5. cada uma das quatro classificações;
6. classificação desconhecida gerando `ValueError`;
7. ranking em ordem decrescente;
8. regra principal idêntica ao primeiro item do ranking;
9. empate preservando a primeira ocorrência;
10. um registro acionando várias regras;
11. percentuais do ranking calculados sobre o total de registros;
12. ganho com 2,00 e 0,25 minutos;
13. tempo negativo e tempo automatizado superior ao manual gerando erro.

O teste parametrizado deverá criar `RegistroValidado` reais ou objetos de contrato equivalentes, sem ler Excel.

### 8.3 Teste de integração novo

Criar `tests/integration/test_relatorio_consolidado.py`, marcado com `pytest.mark.integration`, que execute o fluxo em `tmp_path` e confirme:

- criação física do Excel e do Markdown;
- oito abas na ordem exata;
- 250 registros em `Todos`;
- totais 150/50/20/30;
- ausência de mistura entre classificações;
- presença dos dez rótulos na aba Resumo;
- valores das células iguais ao objeto de indicadores;
- células dos indicadores sem fórmulas;
- dois gráficos nativos e séries válidas;
- Ranking ordenado, RN06 no topo com 25 ocorrências e consistência com Resumo;
- Dicionário com RN01–RN12, classificações, taxas e premissas;
- resumo Markdown com todos os números do Excel;
- presença das premissas e do rótulo `estimativa didática`;
- ausência de `_percentual`, `OperationalIndicators` e outros identificadores técnicos no texto executivo;
- chamada única a `calcular_indicadores()`, comprovada com spy/monkeypatch.

### 8.4 Regressão e E2E

Atualizar os testes existentes que esperam seis abas para esperar oito. Acrescentar ao E2E:

- `resumo_executivo.md` presente;
- gabarito completo dos dez indicadores;
- RN06 como regra principal;
- valores do Markdown iguais aos valores do workbook;
- PDF e log de compatibilidade ainda presentes;
- nenhuma dependência de internet, Maestro real ou credenciais.

Não remover nem enfraquecer testes da Aula 23 para elevar cobertura.

### 8.5 Comandos obrigatórios

```bash
python -m pytest -m unit -v
python -m pytest -m integration -v
python -m pytest -m regression -v
python -m pytest -m "e2e and not browser" -v
python -m pytest -m "not browser" \
  --cov=src --cov=dashboard --cov-config=.coveragerc \
  --cov-report=term-missing \
  --cov-report=xml:reports/coverage.xml \
  --cov-report=html:reports/coverage-html \
  --cov-fail-under=80
```

Critério de aceite: todos os testes executados passam, a cobertura consolidada é de pelo menos 80% e `src/operational_indicators.py` aparece no relatório.

## 9. Documentação

### 9.1 README principal

Atualizar com:

- visão geral da Aula 24;
- arquitetura de fonte única;
- dez indicadores e fórmulas;
- comando oficial do dashboard;
- oito abas e artefatos;
- premissas do ganho;
- execução da suíte e cobertura;
- limitações: estimativa didática, base local, ausência de ERP/MES e necessidade de revisão humana.

### 9.2 `dashboard/README.md`

Substituir referências a seis abas por oito, explicar `dashboard/main.py`, listar o Markdown novo e esclarecer que o PDF é compatibilidade. Documentar o gabarito atual e a regra principal RN06.

### 9.3 PDD

Adicionar uma seção específica da Aula 24 com:

```text
RegistroValidado
  → OperationalIndicators (uma chamada)
      ├─ Excel de 8 abas
      ├─ resumo_executivo.md
      ├─ PDF compatível
      └─ log/evidências
```

Declarar explicitamente que:

- o fluxo legado de um dia continua usando sua nomenclatura RN01–RN07;
- o dashboard de dez dias usa o contrato RN01–RN12 de `dashboard/servico_validacao.py`;
- não houve mudança de comportamento nas regras;
- as taxas e o ganho são derivados da lista já validada;
- o ganho é estimado e não observado em produção.

### 9.4 CHANGELOG

Criar a entrada `1.0.0 — Aula 24`, datada de `2026-08-17`, com grupos `Adicionado`, `Alterado`, `Testes` e `Documentação`. Não declarar o lançamento como concluído antes de todos os testes e evidências existirem; durante o desenvolvimento, identificar a entrada como planejada ou não lançada.

## 10. Segurança, Git e evidências

### 10.1 Branch

Neste repositório, `Developer` é a equivalente local de `develop`.

Procedimento:

1. Executar `git status` e preservar todas as alterações locais existentes.
2. Atualizar `Developer` sem usar comandos destrutivos.
3. Executar e registrar a suíte de linha de base.
4. Criar `feature/indicadores-operacionais` a partir de `Developer` atualizada.
5. Fazer commits pequenos por camada: indicadores, relatórios, testes, documentação e CI.
6. Abrir Pull Request contra `Developer`.

### 10.2 Arquivos gerados

Ajustar `.gitignore` para ignorar:

- `data/output/*.xlsx`;
- `data/output/*.pdf`;
- `data/output/resumo_executivo.md`;
- `data/output/*.log`;
- JSONs de execução gerados;
- ambientes locais, caches, relatórios de cobertura e credenciais.

Os artefatos já rastreados deverão ser removidos apenas do índice com `git rm --cached`, sem apagar as cópias locais. A exclusão deverá ocorrer somente depois de confirmar os caminhos exatos.

### 10.3 CI e pacote de evidências

Atualizar `.github/workflows/ci-cd.yml` para:

- manter `--cov=src --cov=dashboard` e o limite de 80%;
- gerar `reports/coverage.xml` e `reports/coverage-html/`;
- registrar a saída completa do pytest em `reports/pytest-aula24.log`, preservando o código de saída do pytest;
- renomear o artefato de cobertura para `cobertura-aula24-*`;
- anexar Excel, resumo Markdown, PDF compatível, JSONs, logs e cobertura;
- manter a verificação de credenciais e caminhos sensíveis.

O pacote final deve conter, sem ser commitado:

- `relatorio_conferencia_lotes.xlsx`;
- `resumo_executivo.md`;
- `resumo_conferencia_lotes.pdf`, como compatibilidade;
- JSONs já produzidos pelo pipeline, no formato existente;
- logs da rodada final e do pytest;
- cobertura XML e HTML;
- checklist final preenchido.

### 10.4 Checklist e Pull Request

Criar `docs/CHECKLIST_ACEITE_AULA24.md` copiando todos os itens da Seção 8 do enunciado. Cada item só poderá ser marcado após indicar a evidência correspondente: arquivo, teste, log, relatório ou check do CI.

O corpo do PR deve incluir:

- resumo técnico e impacto de negócio;
- confirmação de que RN01–RN12 não mudaram;
- comandos e resultados dos testes;
- cobertura total;
- gabarito dos dez indicadores;
- premissas e limitação do ganho estimado;
- links dos artefatos de CI;
- referência ao checklist preenchido;
- reviewers sem conflito de interesse.

## 11. Ordem recomendada de implementação

1. Registrar status da branch e suíte de linha de base.
2. Criar testes unitários de indicadores inicialmente falhando.
3. Implementar `src/operational_indicators.py` até os testes unitários passarem.
4. Separar a validação em lista de `RegistroValidado` e conversão para DataFrame, sem mudar RN01–RN12.
5. Criar `dashboard/main.py` e garantir a chamada única dos indicadores.
6. Refatorar o Excel para receber `OperationalIndicators` e criar as oito abas.
7. Criar o resumo executivo Markdown.
8. Adaptar PDF, log e Streamlit para não recalcularem os indicadores oficiais.
9. Criar o teste de integração consolidado.
10. Atualizar integração e E2E existentes.
11. Rodar unitários, integração, regressão, E2E e cobertura.
12. Atualizar README, PDD e CHANGELOG com resultados comprovados.
13. Ajustar `.gitignore` e CI.
14. Gerar o pacote final em ambiente limpo.
15. Preencher o checklist com evidências reais.
16. Abrir o PR contra `Developer`, anexar evidências e aguardar todos os checks.

## 12. Critérios de aceite técnicos

- [ ] RN01–RN12 e a precedência de classificação permanecem inalteradas.
- [ ] Deduplicação continua restrita ao mesmo dia.
- [ ] `src/operational_indicators.py` não possui dependências de apresentação.
- [ ] `_percentual()` protege divisão por zero e é a única função de percentual.
- [ ] Os dez indicadores fecham com o gabarito de 250 registros.
- [ ] Indicadores são calculados uma única vez por execução.
- [ ] Excel contém exatamente oito abas na ordem definida.
- [ ] Resumo contém os dez indicadores e dois gráficos nativos.
- [ ] Ranking reutiliza o mesmo `Counter` consolidado e começa por RN06/25.
- [ ] Dicionário é compreensível sem leitura do código.
- [ ] Markdown e Excel apresentam todos os mesmos valores.
- [ ] Ganho exibe fórmula, premissas e o rótulo de estimativa didática.
- [ ] Testes novos possuem markers corretos.
- [ ] Suíte anterior continua verde.
- [ ] Cobertura total e do novo módulo é de pelo menos 80%.
- [ ] README, PDD e CHANGELOG refletem o comportamento entregue.
- [ ] Evidências geradas não são commitadas.
- [ ] Checklist final está preenchido com referências verificáveis.
- [ ] PR contra `Developer` possui reviewers e checks verdes.

## 13. Preparação para as perguntas da banca

- **Se `regras_aplicadas` for removido, o que quebra?** O indicador de regra mais acionada e a aba Ranking de Regras quebram juntos, pois ambos derivam do mesmo ranking consolidado.
- **Por que o ganho não é métrica de produção?** Porque usa tempos assumidos, não telemetria observada. Para virar métrica real, seria necessário medir início/fim do processo manual e automatizado em produção, definir amostra e período e controlar exceções.
- **Como provar que Excel e Markdown usam os mesmos números?** Mostrar a chamada única de `calcular_indicadores()`, o objeto compartilhado e o teste de integração que compara os artefatos.
- **O que ocorre quando o total é zero?** `_percentual()` retorna zero, todas as taxas e o ganho ficam em zero, e não existe regra principal.
- **Por que Ranking e Dicionário são abas separadas?** Porque atendem tarefas distintas: análise de frequência e compreensão sem código, mantendo o Resumo executivo e legível.
- **Como adicionar RN13?** Implementar a regra no motor, adicionar seu nome ao catálogo e seus testes. O ranking e a regra principal passam a incluí-la automaticamente, sem novos cálculos nos exportadores.

## 14. Matriz para nota máxima

| Critério | Peso | Evidência de nível Excelente |
|---|---:|---|
| Indicadores | 20% | Módulo puro, dataclasses, `_percentual()`, chamada única e dez valores corretos |
| Relatório consolidado | 15% | Oito abas exatas, isolamento, ranking, dicionário e gráficos nativos |
| Resumo executivo | 15% | Linguagem de negócio e consistência integral com o Excel |
| Ganho estimado | 10% | Fórmula, valores 2,00/0,25 e rótulo de estimativa didática |
| Testes | 20% | Unitário, integração, suíte verde e cobertura comprovada ≥ 80% |
| Documentação | 10% | README, PDD e CHANGELOG atualizados e coerentes |
| Prontidão Demo Day | 10% | Checklist, evidências e respostas rastreáveis às perguntas da banca |

## 15. Validação deste plano

Antes de considerar este documento pronto para uso:

- conferir cada seção contra o enunciado e os sete critérios da rubrica;
- validar nomes e caminhos contra o repositório;
- confirmar os números do gabarito e as premissas de tempo;
- verificar se nenhuma atividade planejada foi apresentada como já executada;
- revisar ortografia, links, tabelas e blocos de código;
- manter claro que este arquivo orienta a implementação futura e não substitui testes, evidências, checklist ou aprovação do Pull Request.
