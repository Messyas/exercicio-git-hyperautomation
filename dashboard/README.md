# Dashboard executivo de lotes (Aula 24)

Este diretório reúne o orquestrador principal (`main.py`), o gerador de relatórios e a interface de demonstração da conferência de lotes de 10 dias. A entrada é a planilha em `data/samples/inspecao_lotes_10dias_sem gabarito.xlsx`.

## CLI Oficial da Aula 24

Para processar a planilha de 10 dias e gerar todos os artefatos consolidados a partir da camada pura de indicadores (`src/operational_indicators.py`):

```bash
python -m dashboard.main \
  --entrada "data/samples/inspecao_lotes_10dias_sem gabarito.xlsx" \
  --saida data/output
```

## Executar com Docker

Na raiz do repositório, execute:

```bash
docker compose -f dashboard/docker-compose.yml up --build
```

O serviço executa `python -m dashboard.main` antes de iniciar a interface visual. Quando a inicialização terminar, abra `http://localhost:8501`.

Para encerrar o serviço:

```bash
docker compose -f dashboard/docker-compose.yml down
```

## Executar localmente (Streamlit)

Instale as dependências e inicie a interface:

```bash
python -m pip install -r dashboard/requirements.txt
python -m dashboard.main
streamlit run dashboard/app.py
```

## Arquivos gerados

O orquestrador grava os quatro artefatos em `data/output/`:

- `relatorio_conferencia_lotes.xlsx`: relatório consolidado oficial com exatamente **8 abas**;
- `resumo_executivo.md`: resumo executivo em linguagem de negócio;
- `resumo_conferencia_lotes.pdf`: exportação PDF (compatibilidade);
- `execucao_dashboard.log`: log de execução com timestamp e resumo por classificação.

### Estrutura das 8 Abas do Excel

1. `Resumo`: visão executiva com os 10 indicadores, nota de premissas, tabela diária de alertas e 2 gráficos nativos (Rosca e Evolução);
2. `Todos`: os 250 registros com dados normalizados e orientações;
3. `Válidos`: 150 registros totalmente conformes (60%);
4. `Divergências`: 50 registros com inconsistências de negócio (20%);
5. `Ambíguos`: 20 registros para revisão humana (8%);
6. `Erros de Entrada`: 30 registros com falhas de preenchimento ou data (12%);
7. `Ranking de Regras`: regras acionadas ordenadas por ocorrência (regra principal: **RN06** com 25 ocorrências / 10%);
8. `Dicionário`: documentação de termos, colunas, classificações, RN01–RN12, taxas e premissas.

## O que o dashboard mostra

- 10 indicadores operacionais calculados por uma fonte única de verdade;
- Gabarito oficial: 250 registros (150 válidos, 50 divergências, 20 ambíguos, 30 erros de entrada);
- Taxa de qualidade da entrada: 88,0% (meta > 80%);
- Taxa de revisão humana: 8,0% (meta < 15%);
- Taxa de retrabalho: 20,0% (meta < 6%);
- Regra principal: RN06 (Normalização de OK para APROVADO, 25 ocorrências);
- Ganho estimado de tempo: 437,5 minutos (7h17min30s) — *estimativa didática* (premissas: 2,00 min manual vs 0,25 min automatizado por registro).

## Estrutura de Código

- `main.py`: orquestrador da Aula 24 e CLI oficial (`executar_pipeline_dashboard()`);
- `servico_validacao.py`: classe auditável `RegistroValidado` e motor de regras RN01–RN12 (`validar_registro()` e `validar_registros_lista()`);
- `gerar_relatorio.py`: fachada de compatibilidade delegando ao orquestrador;
- `app.py`: interface Streamlit de demonstração;
- `docker-compose.yml`: automação Docker usando a CLI oficial da Aula 24.
