# Roteiro de apresentação — 5 minutos

## 1. Contexto e objetivo (30 segundos)

Foram consolidadas 10 execuções diárias de inspeção do Polo Industrial de
Manaus. A automação lê 250 registros a partir da terceira linha de cada aba,
aplica as regras RN01 a RN12 e disponibiliza uma visão executiva em Excel e
Streamlit.

## 2. Controles aplicados (1 minuto)

- A quantidade declarada em cada aba limita a leitura a 25 registros e exclui
  o rodapé da planilha.
- A Base_Referencia confirma a existência do lote (RN05).
- `OK` e `NOK` são normalizados, preservando o valor original para auditoria.
- A duplicidade usa `Counter` por execução diária: apenas a segunda ocorrência
  em diante é marcada, sem bloquear o mesmo lote em dias diferentes.
- A classificação tem precedência única: Erro de Entrada, Ambíguo,
  Divergência e Válido. Isso impede dados cruzados nas abas do relatório.

## 3. Leitura dos indicadores (1 minuto)

| Indicador | Quantidade | Percentual |
| --- | ---: | ---: |
| Válidos | 150 | 60% |
| Divergências | 50 | 20% |
| Ambíguos | 20 | 8% |
| Erros de Entrada | 30 | 12% |
| Total | 250 | 100% |

As 100 ocorrências não válidas estão comprovadas pela soma de 50 divergências,
20 casos ambíguos e 30 erros de entrada. O gráfico de rosca mostra a
distribuição e o gráfico de linhas permite priorizar os dias com mais alertas.

## 4. Decisões recomendadas (1 minuto e 30 segundos)

1. Corrigir primeiro os 30 erros de entrada: 20 ocorrências de data (RN12) e
   10 de campos obrigatórios (RN01–RN04). São impeditivos para a qualidade do
   dado e podem ser prevenidos no formulário de coleta.
2. Direcionar os 20 status desconhecidos (RN09) para revisão humana e definir
   um catálogo para termos recorrentes, como "EM AJUSTE" e "APROVADO PARCIAL".
3. Tratar as 50 divergências com o responsável da linha: há 10 lotes ausentes
   na referência (RN05), 20 repetições na execução (RN11) e 21 reprovações sem
   observação (RN10, uma delas também ausente na referência).
4. Manter a normalização rastreável: foram 25 `OK` (RN06) e 10 `NOK` (RN07).
   Esses valores foram corrigidos automaticamente, sem perda do texto original.

## 5. Encerramento (1 minuto)

O resultado executivo está em `data/output/relatorio_conferencia_lotes.xlsx`.
As seis abas são auditáveis e os dois gráficos da aba `Resumo` são objetos
nativos e editáveis do Excel. O dashboard Streamlit é a camada de consulta:
ele lê exclusivamente o relatório processado, evitando que a visualização
altere a regra de negócio ou os dados de origem.
