# Evidências de avaliação — Exercício 24-A (ML + RPA)

Esta é uma leitura rápida para avaliação **sem executar o projeto**. Consolida
os requisitos do exercício, a localização do código e resultados obtidos nos
ensaios locais. Os números não são a nota do Torneio: o lote oculto e o
gabarito pertencem à equipe avaliadora.

## Visão geral e rastreabilidade

As regras RN01–RN12 continuam sendo a primeira camada de decisão. O modelo é
consultado somente para lotes ambíguos; se a API falhar, o bot registra
`REVISAO_ML_OFFLINE` e segue para o próximo item.

| Entrega solicitada | Evidência no repositório |
| --- | --- |
| Dataset, treino e manifesto | [`scripts/train_model.py`](../scripts/train_model.py), [`data/ml/dataset_manifest.json`](../data/ml/dataset_manifest.json) e [`data/ml/historico_lotes_sintetico.csv`](../data/ml/historico_lotes_sintetico.csv) |
| Random Forest serializada e métricas | [`models/classificador_lotes.pkl`](../models/classificador_lotes.pkl) e [`models/classificador_lotes.metrics.json`](../models/classificador_lotes.metrics.json) |
| API FastAPI e validação Pydantic | [`api_ml/main.py`](../api_ml/main.py) e [`api_ml/schemas.py`](../api_ml/schemas.py) |
| Docker Compose e healthcheck | [`docker-compose.yml`](../docker-compose.yml) e [`api_ml/Dockerfile`](../api_ml/Dockerfile) |
| MLClient e circuit breaker | [`src/ml_client.py`](../src/ml_client.py) e [`src/ml_client_factory.py`](../src/ml_client_factory.py) |
| Fallback, logs e Excel | [`src/item_processor.py`](../src/item_processor.py), [`src/structured_logging.py`](../src/structured_logging.py), [`src/report_generator.py`](../src/report_generator.py) |
| Fila, carga e sabotagem | [`scripts/demo_torneio.py`](../scripts/demo_torneio.py) |
| Auditoria de robustez e viés | [`scripts/auditar_modelo_ml.py`](../scripts/auditar_modelo_ml.py) e [`reports/model_audit`](../reports/model_audit) |

## Dataset e modelo

- Dataset sintético de **12.000 linhas** (mais que as 200 exigidas), com
  `status_raw`, `turno`, `tem_obs` e três classes balanceadas:
  `valido_automatico`, `revisar` e `recusar_automatico`.
- O gerador usa seed fixa e split estratificado por `classe + turno`.
  `lote_id`, produto, linha, responsável, data e observação são excluídos das
  features para evitar leakage e proxies indevidos.
- Turnos A/B/C são distribuídos de forma uniforme e não alteram a chance de
  classe durante a geração, permitindo teste explícito de disparidade.
- O modelo é `RandomForestClassifier` (200 árvores) calibrado por
  `CalibratedClassifierCV` sigmoid com validação cruzada de cinco folds.

| Métrica registrada no artefato | Resultado |
| --- | ---: |
| Accuracy no teste | 83,83% |
| Macro F1 | 83,89% |
| ECE (erro de calibração esperado) | 0,0114 |
| Cobertura com `p >= 0,85` | 49,75% |
| Maior diferença de accuracy entre turnos | 3,17 p.p. |
| Latência unitária — P50 / P95 | 29,77 ms / 32,50 ms |

Essas métricas se aplicam ao conjunto sintético atual; não substituem validação
com dados históricos reais, observação de deriva e revisão humana.

## API, contrato e concorrência

`POST /predict` aceita exclusivamente `lote_id`, `status_raw`, `turno` e
`tem_obs`. Os schemas são estritos: turno fora de A/B/C, campos extras e
booleanos usados como números recebem HTTP 422. `GET /health` informa se o
modelo foi carregado.

| Probabilidade | Nível | Ação |
| --- | --- | --- |
| `>= 0,85` | `ALTA` | automática para válido/recusar; `revisar` permanece revisão |
| `>= 0,65` e `< 0,85` | `MEDIA` | `REVISAR` |
| `< 0,65` | `BAIXA` | `REVISAO_PRIORITARIA` |

A inferência é síncrona porque scikit-learn é CPU-bound; FastAPI a executa no
pool de threads. O middleware assíncrono limita concorrência por
`ML_MAX_CONCURRENCY` (padrão 1), aplicando backpressure. Todas as respostas
expõem `X-Inference-Latency-Ms`, `X-Request-Latency-Ms` e
`X-Queue-Wait-Ms`.

## Resiliência, auditoria e relatório

- `MLClient.classificar()` devolve `None` em timeout, erro de rede, HTTP
  inválido ou JSON malformado; nenhuma exceção chega ao bot.
- A resposta é validada no cliente (campos, `lote_id`, enums e probabilidade
  finita entre 0 e 1) antes de ser usada.
- Após cinco falhas consecutivas, o circuit breaker abre. As próximas chamadas
  não tentam a rede até `reset_circuit()` ou reinício.
- O `ItemProcessor` transforma `None` em `REVISAO_ML_OFFLINE`, sem parar a
  fila de itens.
- O log JSON Lines tem evento `ML_DECISION` com lote, classe, probabilidade,
  nível, ação, latência e estado do circuito — sem texto livre de observação.
- O Excel consolidado possui nove abas; a nona, **Decisões de ML**, recebe uma
  linha por lote classificado.

## Testes e resultados observados

A suíte executada nesta revisão retornou:

```text
146 passed, 1 skipped, 12 deselected, 1 xfailed, 6 subtests passed
```

| Tema | Testes | Cobertura |
| --- | --- | --- |
| API e contrato | [`test_api_ml.py`](../tests/unit/test_api_ml.py) | payload válido/inválido, tipos estritos, health e headers de latência |
| Cliente e circuit breaker | [`test_ml_client.py`](../tests/unit/test_ml_client.py) | sucesso, API indisponível, JSON inválido e cinco falhas |
| Fallback do bot | [`test_item_processor_ml.py`](../tests/unit/test_item_processor_ml.py), [`test_sabotagem_ml.py`](../tests/integration/test_sabotagem_ml.py) | `REVISAO_ML_OFFLINE` sem interromper lote |
| Dataset, treino e Excel | [`test_dataset_ml.py`](../tests/unit/test_dataset_ml.py), [`test_model_training.py`](../tests/unit/test_model_training.py), [`test_relatorio_ml.py`](../tests/unit/test_relatorio_ml.py) | volume, features, artefato, limiares e 9ª aba |
| Fila e carga | [`test_demo_torneio.py`](../tests/unit/test_demo_torneio.py) | fila limitada, 50 chamadas, JSON e resumo de latência |
| Viés e robustez | [`test_auditar_modelo_ml.py`](../tests/unit/test_auditar_modelo_ml.py) | integridade, OOD, calibração e alertas de política |

### Ensaios de integração registrados

| Ensaio | Configuração | Resultado observado |
| --- | --- | --- |
| Normal | 50 registros, 5 workers, fila 20 | 50/50 sucessos; 0 fallback; três JSONs inválidos rejeitados com 422 |
| Sabotagem | mesma fila; `api-ml` derrubada após 10 chamadas | 50/50 processados; 10 sucessos e 40 fallbacks; circuito aberto em 36 registros após falhas em voo |
| Carga | 1.000 registros, 10 workers, fila 50 | 1.000/1.000 sucessos; 0 fallback; sem criar 1.000 requisições simultâneas |

Os relatórios brutos estão em
[`ensaio_torneio_normal.json`](../data/output/ensaio_torneio_normal.json),
[`ensaio_torneio_sabotagem.json`](../data/output/ensaio_torneio_sabotagem.json)
e [`ensaio_torneio_1000.json`](../data/output/ensaio_torneio_1000.json).

### Validação do Compose isolado de sabotagem (19/08/2026)

Foi validado o arquivo
[`docker-compose.sabotagem.yml`](../docker-compose.sabotagem.yml), criado para
o ensaio de carga com queda real da API sem afetar o Compose principal.

| Verificação | Comando | Resultado observado |
| --- | --- | --- |
| Sintaxe do Compose | `docker compose -f docker-compose.sabotagem.yml -p sabotagem-ml config --quiet` | concluído com código 0 |
| Inicialização da API | `docker compose -f docker-compose.sabotagem.yml -p sabotagem-ml up -d --build` | container `sabotagem-ml-api-ml-1` saudável |
| Health real | `GET http://localhost:8001/health` | HTTP 200, `model_loaded: true`, versão `rf-lotes-1.0.0` |
| Limites efetivos | `docker inspect sabotagem-ml-api-ml-1` | `Memory=268435456` (256 MB) e `NanoCpus=500000000` (0,5 CPU) |
| Log de inicialização | `docker compose ... logs api-ml` | modelo carregado e requisições `/health` respondendo 200 |

O roteiro completo para carga e sabotagem está no
[README](../README.md#ensaio-isolado-de-carga-com-queda-real-da-api). Ele envia
1.000 requisições com 16 workers e fila de 64 itens, derruba
deliberadamente a API isolada após 100 chamadas e grava
`data/output/ensaio_sabotagem_carga.json`. Essa etapa deve ser executada antes
da apresentação para guardar o JSON e o log da queda como evidência.

## Auditoria de robustez do classificador

Random Forest não interpreta instruções, logo não sofre *prompt injection* no
sentido literal de LLM. Os equivalentes testados são entradas fora da
distribuição, envenenamento de dados, correlação espúria, leakage e confiança
excessiva. A auditoria verificou:

- SHA do dataset e ordem das features coerentes com o bundle;
- ECE abaixo de 0,05 e accuracy de alta confiança acima de 85%;
- diferença entre turnos abaixo de 5 p.p.;
- teste contrafactual que altera apenas o turno, sem mudança de classe em 500
  casos analisados;
- 24 entradas OOD (instrução, HTML, SQL e status desconhecido) sem decisão
  automática de alta confiança.

O resultado detalhado está em
[`auditoria_modelo_ml.md`](../reports/model_audit/auditoria_modelo_ml.md) e
[`auditoria_modelo_ml.json`](../reports/model_audit/auditoria_modelo_ml.json).

## Revalidação opcional

Para reproduzir o fluxo principal, basta Docker Desktop:

```bash
docker compose --profile ml up --build --abort-on-container-exit --exit-code-from bot-classificador api-ml bot-classificador
```

Os comandos de ensaio e auditoria estão no
[README](../README.md#camada-de-machine-learning-aula-24-a). Para avaliação
documental, as evidências e links desta página permitem localizar cada artefato
sem executar containers ou testes.
