# Dashboard executivo de lotes

Este diretório reúne o gerador do relatório em Excel e o dashboard Streamlit
da conferência de lotes. A entrada é a planilha de 10 dias em
`data/samples/inspecao_lotes_10dias_sem gabarito.xlsx`.

## Executar com Docker

Na raiz do repositório, execute:

```bash
docker compose -f dashboard/docker-compose.yml up --build
```

O serviço gera o relatório antes de iniciar o dashboard. Quando a inicialização
terminar, abra `http://localhost:8501`.

Para encerrar o serviço:

```bash
docker compose -f dashboard/docker-compose.yml down
```

## Executar localmente

Instale as dependências e gere os arquivos:

```bash
python -m pip install -r dashboard/requirements.txt
python dashboard/gerar_relatorio.py
```

Inicie a interface web:

```bash
streamlit run dashboard/app.py
```

## Arquivos gerados

O comando de geração grava estes artefatos em `data/output/`:

- `relatorio_conferencia_lotes.xlsx`: relatório principal;
- `resumo_conferencia_lotes.pdf`: resumo para compartilhamento;
- `execucao_dashboard.log`: horário da execução e totais por classificação.

O Excel possui seis abas: `Resumo`, `Todos`, `Válidos`, `Divergências`,
`Ambíguos` e `Erros de Entrada`. A aba `Resumo` contém os indicadores, um
gráfico de rosca e a evolução diária dos alertas como objetos nativos do Excel.

## O que o dashboard mostra

- Totais de Válidos, Divergências, Ambíguos e Erros de Entrada;
- Rosquinha com a participação percentual de cada classificação;
- Linha de alertas por dia, que soma Divergências e Ambíguos;
- Tabela filtrável dos registros processados;
- Download do relatório Excel gerado.

A amostra possui 250 registros e 100 casos não válidos: 50 divergências,
20 ambíguos e 30 erros de entrada. A distribuição simulada mantém sete alertas
(Divergências + Ambíguos) em cada um dos dez dias.

## Estrutura

- `servico_validacao.py`: concentra `RegistroValidado` e a aplicação das
  regras RN01–RN12 por `validar_registro()`;
- `gerar_relatorio.py`: consolida as abas diárias, aplica as regras e gera os
  artefatos;
- `app.py`: interface Streamlit para consulta do relatório;
- `docker-compose.yml`: inicia a geração e o dashboard em um único comando;
- `requirements.txt`: dependências exclusivas desta parte do projeto.
