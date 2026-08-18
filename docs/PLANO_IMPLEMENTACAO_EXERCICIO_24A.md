# Plano de implementação — Exercício 24-A (ML + RPA)

## 1. Objetivo e regra de ouro

Adicionar uma camada de Machine Learning apenas aos registros que o motor
RN01–RN12 já classificou como `Ambíguo`. As regras existentes continuam sendo
a primeira camada de decisão e não devem ser reescritas nem substituídas pelo
modelo.

Fluxo final esperado:

```text
planilha -> RN01–RN12 -> registro não ambíguo -> resultado atual
                         |
                         `-> registro ambíguo -> MLClient -> API FastAPI
                                                  |-> resposta válida -> ação por confiança
                                                  `-> qualquer falha -> REVISAO_ML_OFFLINE
                                                       (o lote continua)

resultados + decisões de ML -> relatório Excel com 9 abas + JSON Lines
```

Este plano usa como fluxo canônico da Aula 24 o módulo `dashboard/main.py`,
pois ele é o único caminho atual que aplica RN01–RN12 e gera exatamente as 8
abas do relatório consolidado. O fluxo legado `consumer.py` ainda aplica
RN01–RN07 e `src/relatorio.py` gera 6 abas; ele não deve ser escolhido como
ponto principal da nova entrega sem antes unificar essas duas implementações.

## 2. Diagnóstico do repositório atual

### 2.1 O que deve ser reaproveitado

- `dashboard/servico_validacao.py`: contém `RegistroValidado`,
  `validar_registro()` e `validar_registros_lista()`, com RN01–RN12.
- `dashboard/main.py`: contém `executar_pipeline_dashboard()` e
  `gerar_excel_consolidado()`, responsável pelas 8 abas oficiais.
- `src/operational_indicators.py`: deve continuar sendo a fonte única dos
  indicadores. Não recalcular indicadores dentro da camada de ML.
- `src/maestro_client.py`: já configura log estruturado JSON Lines e pode
  receber os eventos `ML_DECISION`.
- `src/datapool_gateway.py`: já implementa a fila do processo por meio dos
  protocolos `DatapoolPublisher`/`DatapoolConsumer` e dos adaptadores local e
  BotCity. Não criar outra fila para chamadas HTTP nesta entrega.
- `config.py`: deve centralizar URL, timeout e limite do circuit breaker.
- `docker-compose.yml`: deve receber o serviço `api-ml` e as variáveis do
  cliente.

### 2.2 O começo de microserviço já existente

O diretório não rastreado `micro-service-ml/` é um template funcional de Iris:

- `micro-service-ml/app/main.py` carrega `iris_model.pkl` no import e expõe
  somente `POST /predict`;
- `micro-service-ml/model/train_model.py` treina Iris e usa `pickle`;
- `micro-service-ml/app/Dockerfile` e `requirements.txt` são bases úteis;
- os manifests Kubernetes são placeholders, têm portas divergentes e não são
  necessários para os critérios desta entrega.

Esse conteúdo deve ser **adaptado**, não mantido em paralelo. Recomendação:

1. mover a lógica útil do template para o pacote raiz `api_ml/`, exigido no
   enunciado;
2. substituir completamente os contratos de Iris pelos contratos de lotes;
3. trocar `pickle` por `joblib`;
4. carregar o artefato no `lifespan`, nunca durante o import do módulo;
5. deixar somente um entrypoint FastAPI para evitar executar o Iris por engano;
6. manter Kubernetes fora do MVP ou atualizar os manifests somente depois que
   Docker Compose, testes e sabotagem estiverem aprovados.

O diretório `micro-service-ml/` aparece como `??` no Git. Antes de mover seus
arquivos, confirmar que não há trabalho local de outra pessoa e então adicionar
a nova estrutura ao versionamento.

### 2.3 Dados de referência encontrados

`data/samples/inspecao_lotes_dia.xlsx` possui 25 registros e os campos:

```text
lote_id, produto, linha, turno, status, responsavel, data, observacao
```

Na amostra diária aparecem `APROVADO`, `REPROVADO`, `OK`, `NOK`, `PENDENTE`,
`REPROV.` e `APROVADO PARCIAL`. Os turnos são `A`, `B` e `C`.

`data/samples/inspecao_lotes_10dias_sem gabarito.xlsx` possui 250 registros.
Distribuições relevantes:

- turno: A=91, B=69, C=90;
- observação: preenchida=86, vazia=164;
- status: `APROVADO`=101, `REPROVADO`=57, `PENDENTE`=35, `OK`=25,
  `NOK`=10, `AGUARDANDO REINSPEÇÃO`=6, `EM AJUSTE`=6,
  `APROVADO PARCIAL`=6, `CANCELADO`=2 e vazio=2.

Essas planilhas servem para descobrir esquema e vocabulário. As 10.000+ linhas
de treinamento devem ser geradas por código novo; não duplicar as 250 linhas.

## 3. Estrutura de arquivos alvo

```text
api_ml/
  __init__.py
  main.py                 # FastAPI, lifespan, /predict e /health
  schemas.py              # LoteInput, PredictionOutput e HealthOutput
  model_service.py        # ModelService e regras de confiança
  features.py             # normalização compartilhada e ordem das 3 features
  Dockerfile
  requirements.txt

models/
  classificador_lotes.pkl
  classificador_lotes.metrics.json

data/ml/
  historico_lotes_sintetico.csv
  dataset_manifest.json

scripts/
  train_model.py
  demo_torneio.py         # opcional, mas recomendado para os 50 casos

src/
  ml_client.py            # MLClient + CircuitBreaker + DTOs/Protocol
  ml_client_factory.py    # create_ml_client(settings, logger)
  item_processor.py       # chama ML somente para Ambíguo e cria auditoria

tests/unit/
  test_dataset_ml.py
  test_model_training.py
  test_api_ml.py
  test_ml_client.py
  test_item_processor_ml.py
  test_relatorio_ml.py

tests/integration/
  test_pipeline_ml.py
  test_sabotagem_ml.py
```

Não criar um segundo `main.py` de API dentro de `micro-service-ml/app/`. Depois
da migração, qualquer arquivo Iris remanescente deve ser removido para evitar
dois modelos e dois contratos concorrentes.

## 4. Bibliotecas e versões

Manter Python 3.11, já usado no Dockerfile atual. Dependências diretas do
microserviço, pinadas em `api_ml/requirements.txt`:

```text
fastapi==0.140.8
uvicorn[standard]==0.51.0
pydantic==2.13.4
scikit-learn==1.9.0
joblib==1.5.3
```

Adicionar ao `requirements.txt` da raiz:

```text
httpx==0.28.1
```

`pytest`, `pytest-cov`, `pandas`, `openpyxl` e `python-json-logger` já existem
no projeto. Gerar um lock/constraints com as dependências transitivas e treinar
o modelo no mesmo ambiente usado para servi-lo. Um artefato `joblib` não deve
ser considerado portável entre versões arbitrárias de scikit-learn.

## 5. Contratos e constantes canônicas

Usar tokens internos sem espaços para impedir variações acidentais:

```python
class ClasseML(str, Enum):
    VALIDO_AUTOMATICO = "valido_automatico"
    REVISAR = "revisar"
    RECUSAR_AUTOMATICO = "recusar_automatico"

class NivelConfianca(str, Enum):
    ALTA = "alta"
    MEDIA = "media"
    BAIXA = "baixa"

class AcaoML(str, Enum):
    VALIDO_AUTOMATICO = "VALIDO_AUTOMATICO"
    RECUSAR_AUTOMATICO = "RECUSAR_AUTOMATICO"
    REVISAR = "REVISAR"
    REVISAO_PRIORITARIA = "REVISAO_PRIORITARIA"
    REVISAO_ML_OFFLINE = "REVISAO_ML_OFFLINE"
```

Se a banca exigir os rótulos com acento no artefato, converter somente na
borda de apresentação. Código, logs e testes devem usar uma representação
canônica única.

### 5.1 Entrada da API

```python
class LoteInput(BaseModel):
    lote_id: str = Field(min_length=1, max_length=80)
    status_raw: str = Field(min_length=1, max_length=100)
    turno: str
    tem_obs: bool

    @field_validator("turno")
    @classmethod
    def validar_turno(cls, value: str) -> str:
        turno = value.strip().upper()
        if turno not in {"A", "B", "C"}:
            raise ValueError("turno deve ser A, B ou C")
        return turno
```

`lote_id` é contexto de auditoria, não feature. O vetor do modelo deve conter
exatamente, nesta ordem:

```python
FEATURE_ORDER = ("status_raw", "turno", "tem_obs")
```

### 5.2 Saída da API

```python
class PredictionOutput(BaseModel):
    lote_id: str
    classe: ClasseML
    probabilidade: float = Field(ge=0.0, le=1.0)
    nivel_confianca: NivelConfianca
    acao: AcaoML
    modelo_versao: str
```

Regra em `def determinar_acao(classe, probabilidade) -> tuple[NivelConfianca,
AcaoML]`:

- `probabilidade >= 0.85`: confiança alta; executar a classe automática, mas
  uma predição `revisar` continua `REVISAR`;
- `0.65 <= probabilidade < 0.85`: confiança média e ação `REVISAR`;
- `probabilidade < 0.65`: confiança baixa e ação `REVISAO_PRIORITARIA`.

Criar testes exatos para `0.649999`, `0.65`, `0.849999` e `0.85`.

## 6. Dataset sintético com no mínimo 10.000 linhas

Gerar **12.000 linhas** por padrão para deixar margem acima do aceite. Usar
`random.Random(seed)` e/ou `numpy.random.Generator` com `seed=42`.

### 6.1 Colunas do CSV

```text
sample_id,status_raw,turno,tem_obs,classe
```

Somente `status_raw`, `turno` e `tem_obs` entram no treino. `sample_id` existe
apenas para rastreabilidade. Não usar `lote_id`, `produto`, `linha`,
`responsavel`, data ou o texto da observação: esses campos seriam identificadores
ou proxies sem justificativa no enunciado.

### 6.2 Vocabulário inicial

Gerar apenas cenários que chegariam à camada ambígua, incluindo os valores
observados na amostra e variações plausíveis:

- `PENDENTE`;
- `EM ANALISE` / `EM ANÁLISE`;
- `EM AJUSTE`;
- `ESPECIFICACAO EM REVISAO` / `ESPECIFICAÇÃO EM REVISÃO`;
- `AGUARDANDO REINSPECAO` / `AGUARDANDO REINSPEÇÃO`;
- `APROVADO PARCIAL`;
- `CANCELADO`;
- `AJUSTE CONCLUIDO`;
- `AJUSTE REPROVADO`;
- `REINSPECAO REPROVADA`;
- `FORA DE ESPECIFICACAO`.

`normalizar_status_raw(value)` deve remover espaços duplicados, converter para
maiúsculas e normalizar acentos de forma determinística. A mesma função deve
ser chamada pelo gerador, pelo treino e pela API para evitar training-serving
skew.

### 6.3 Lógica de geração sem alvo determinístico demais

Definir uma tabela versionada de probabilidades condicionais por status e
`tem_obs`. Exemplos de tendência, não regras absolutas:

- `APROVADO PARCIAL` e `AJUSTE CONCLUIDO`: maior probabilidade de
  `valido_automatico` quando há observação;
- `PENDENTE`, `EM ANALISE`, `ESPECIFICACAO EM REVISAO` e
  `AGUARDANDO REINSPECAO`: maior probabilidade de `revisar`;
- `CANCELADO`, `AJUSTE REPROVADO`, `REINSPECAO REPROVADA` e
  `FORA DE ESPECIFICACAO`: maior probabilidade de `recusar_automatico`;
- manter sobreposição de 10%–20% entre classes para que a probabilidade tenha
  significado e o modelo não seja apenas uma tabela de decisão perfeita.

O turno **não deve alterar a probabilidade da classe** no gerador. Ele é uma
feature obrigatória do exercício, mas não há evidência local para penalizar um
turno. Assim, o treino pode provar que não aprendeu um tratamento diferente
somente por ser A, B ou C.

Gerar 4.000 exemplos por classe. Dentro de cada classe, distribuir turnos de
forma quase exata (diferença máxima de uma linha) e garantir que `tem_obs=true`
e `false` apareçam em todas as combinações classe/turno.

### 6.4 Funções obrigatórias de `scripts/train_model.py`

```python
def gerar_dataset(*, total: int = 12_000, seed: int = 42) -> list[dict]: ...
def normalizar_status_raw(value: str) -> str: ...  # importar de api_ml.features
def validar_dataset(rows: Sequence[Mapping[str, object]]) -> None: ...
def salvar_dataset(rows, csv_path: Path, manifest_path: Path) -> None: ...
def build_pipeline(*, random_state: int = 42): ...
def split_estratificado(X, y, grupos, *, random_state: int = 42): ...
def avaliar_modelo(model, X_test, y_test, turnos_test) -> dict: ...
def treinar_modelo(dataset_path: Path, model_path: Path) -> dict: ...
def main() -> int: ...
```

`validar_dataset()` deve falhar claramente se:

- houver menos de 10.000 linhas;
- as três classes não existirem;
- alguma classe ou turno estiver sub-representado além da tolerância;
- houver nulo nas três features ou no alvo;
- `turno` estiver fora de A/B/C;
- uma coluna proibida for usada como feature.

O `dataset_manifest.json` deve registrar seed, total, contagem por classe,
turno, `tem_obs`, status e combinações classe/turno, além do SHA-256 do CSV.

## 7. Treinamento, calibração e avaliação

### 7.1 Pipeline scikit-learn

Criar toda a transformação dentro de um `Pipeline`, evitando codificação manual
em dicionários diferentes no treino e na API:

```python
preprocessor = ColumnTransformer(
    transformers=[
        (
            "categoricas",
            OneHotEncoder(
                handle_unknown="infrequent_if_exist",
                min_frequency=20,
            ),
            [0, 1],  # status_raw e turno
        ),
        ("booleano", "passthrough", [2]),
    ]
)

forest = RandomForestClassifier(
    n_estimators=200,
    max_depth=8,
    min_samples_leaf=10,
    class_weight="balanced_subsample",
    random_state=42,
    n_jobs=-1,
)

base_pipeline = Pipeline([
    ("preprocessor", preprocessor),
    ("classifier", forest),
])

model = CalibratedClassifierCV(
    estimator=base_pipeline,
    method="sigmoid",
    cv=5,
    ensemble=False,
)
```

O classificador exigido continua sendo `RandomForestClassifier`;
`CalibratedClassifierCV` corrige suas probabilidades para que os limiares 0,65
e 0,85 tenham sustentação. `ensemble=False` mantém um único classificador final,
reduz o tamanho do `.pkl` e a latência.

Fazer split 80/20 antes de qualquer `fit`, estratificado por
`classe + turno`. O conjunto de teste fica intocado até a avaliação final.

### 7.2 Métricas mínimas registradas

- accuracy;
- macro precision, recall e F1;
- matriz de confusão geral;
- log loss;
- Brier score multiclasse ou equivalente documentado;
- erro esperado de calibração (ECE) por faixas;
- cobertura de confiança alta (`p >= 0.85`);
- accuracy, macro-F1 e recall por classe separados por turno;
- latência p50, p95 e média para predição unitária.

Gates iniciais recomendados para o dataset sintético:

- macro-F1 geral >= 0,80;
- recall de cada classe >= 0,75;
- diferença de accuracy entre o melhor e o pior turno <= 0,05;
- diferença máxima de recall da mesma classe entre turnos <= 0,05;
- ECE <= 0,08.

Se um gate falhar, corrigir o gerador ou a modelagem e documentar a causa. Não
ajustar o teste oculto nem usar seus rótulos no treino.

### 7.3 Artefato do modelo

Salvar com `joblib.dump()` um dicionário simples:

```python
bundle = {
    "pipeline": model,
    "model_version": "rf-lotes-1.0.0",
    "feature_order": list(FEATURE_ORDER),
    "classes": [item.value for item in ClasseML],
    "thresholds": {"alta": 0.85, "media": 0.65},
    "dataset_sha256": dataset_sha256,
    "trained_at": trained_at_iso,
    "sklearn_version": sklearn.__version__,
}
```

Destino obrigatório: `models/classificador_lotes.pkl`. Escrever as métricas
também em `models/classificador_lotes.metrics.json`; não depender de carregar o
pickle para auditar o treino.

## 8. API FastAPI

### 8.1 `ModelService`

Em `api_ml/model_service.py`:

```python
class ModelUnavailableError(RuntimeError): ...

class ModelService:
    def __init__(self, model_path: Path): ...
    def load(self) -> None: ...
    @property
    def is_loaded(self) -> bool: ...
    @property
    def model_version(self) -> str | None: ...
    def predict(self, lote: LoteInput) -> PredictionOutput: ...
```

Responsabilidades:

- carregar e validar todas as chaves do bundle;
- rejeitar artefato com `feature_order` diferente;
- chamar `predict_proba()` uma única vez;
- obter classe e probabilidade pela mesma posição de `classes_`;
- aplicar `determinar_acao()`;
- nunca inventar predição se o modelo não estiver carregado.

### 8.2 `api_ml/main.py`

Usar `@asynccontextmanager` no `lifespan`. Capturar falha de carga, registrar
erro sem stack/segredo na resposta e manter a aplicação de pé para que
`/health` informe indisponibilidade.

Endpoints:

- `GET /health`
  - `200`: `{"status":"ok","model_loaded":true,"modelo_versao":"..."}`;
  - `503`: `{"status":"unavailable","model_loaded":false,...}`.
- `POST /predict`
  - `200`: `PredictionOutput`;
  - `422`: payload/turno inválido;
  - `503`: modelo não carregado;
  - `500`: somente erro inesperado, com mensagem pública genérica.

Não retornar caminho local, traceback ou conteúdo do artefato.

## 9. MLClient e circuit breaker

### 9.1 Tipos e interfaces em `src/ml_client.py`

```python
@dataclass(frozen=True)
class MLPrediction:
    lote_id: str
    classe: str
    probabilidade: float
    nivel_confianca: str
    acao: str
    modelo_versao: str

class MLClassifier(Protocol):
    def classificar(
        self, *, lote_id: str, status_raw: str, turno: str, tem_obs: bool
    ) -> MLPrediction | None: ...

class CircuitBreaker:
    def allow_request(self) -> bool: ...
    def record_success(self) -> None: ...
    def record_failure(self) -> None: ...
    def reset(self) -> None: ...
    @property
    def is_open(self) -> bool: ...

class MLClient:
    def __init__(..., client: httpx.Client | None = None): ...
    def classificar(...) -> MLPrediction | None: ...
    def reset_circuit(self) -> None: ...
    def close(self) -> None: ...
```

O breaker tem apenas `CLOSED` e `OPEN`, conforme o enunciado. Não implementar
half-open ou recuperação por tempo: ele volta a tentar somente após
`reset_circuit()` ou reinício do processo.

### 9.2 Semântica obrigatória

`MLClient.classificar()` deve capturar e converter para `None`:

- `httpx.TimeoutException`;
- `httpx.NetworkError`/`httpx.TransportError`;
- status HTTP não 2xx;
- JSON inválido;
- campos ausentes ou tipos fora do contrato;
- qualquer outra exceção inesperada na fronteira HTTP.

Cada falha incrementa o contador. A quinta falha abre o circuito. Da sexta
chamada em diante, retornar `None` imediatamente e comprovar em teste que o
transport não foi chamado. Qualquer sucesso antes da quinta falha zera o
contador.

Reusar uma única instância de `httpx.Client` para aproveitar connection pool.
Timeout sugerido:

```python
httpx.Timeout(timeout=1.0, connect=0.20)
```

O método nunca usa `raise_for_status()` sem capturar a exceção na própria
fronteira.

### 9.3 Factory e injeção de dependência

Em `src/ml_client_factory.py`:

```python
def create_ml_client(
    settings: Settings,
    logger: logging.Logger,
    *,
    transport: httpx.BaseTransport | None = None,
) -> MLClient: ...
```

A factory lê configuração e monta cliente/breaker uma vez por execução. O
`transport` opcional permite `httpx.MockTransport` nos testes. O processador
depende do protocolo `MLClassifier`, não da implementação concreta.

## 10. Integração em `src/item_processor.py`

Criar tipos auditáveis e não alterar `RegistroValidado` em lugar:

```python
@dataclass(frozen=True)
class MLDecision:
    timestamp: str
    lote_id: str
    status_raw: str
    turno: str
    tem_obs: bool
    classe: str | None
    probabilidade: float | None
    nivel_confianca: str
    acao_final: str
    latencia_ms: float
    tentou_rede: bool
    circuit_open: bool
    modelo_versao: str | None
    erro_tipo: str | None = None

    def to_dict(self) -> dict[str, object]: ...
    def to_log_dict(self) -> dict[str, object]: ...

class ItemProcessor:
    def __init__(self, ml_client: MLClassifier, logger: logging.Logger): ...
    def processar(self, registro: RegistroClassificavel) -> MLDecision | None: ...
    def processar_lote(self, registros: Iterable[RegistroClassificavel]) \
            -> list[MLDecision]: ...
```

Regras:

1. se `registro.classificacao != "Ambíguo"`, retornar `None` e não chamar a
   rede;
2. montar `tem_obs = bool(registro.observacao.strip())`;
3. medir o tempo total com `time.perf_counter()`;
4. chamar `MLClient.classificar()`;
5. resposta válida: preservar classe, probabilidade, confiança e ação;
6. resposta `None`: criar decisão com `acao_final="REVISAO_ML_OFFLINE"`;
7. sempre emitir um `ML_DECISION` no logger e adicionar uma decisão à lista
   para o Excel, inclusive quando o circuito já estiver aberto.

`processar_lote()` deve continuar após qualquer erro defensivo por item. O
fallback nunca muda o resultado das regras: ele define apenas a ação posterior
para o registro que já era ambíguo.

### Por que não criar outra fila

O projeto já usa DataPool como fila durável entre produtor e consumidor. Uma
fila assíncrona adicional entre `ItemProcessor` e `MLClient` aumentaria o risco
de perder logs no encerramento e tornaria a contagem de cinco falhas concorrentes
menos determinística. Para o lote didático e os 50 casos do torneio, executar as
chamadas em sequência é mais auditável. Paralelismo só deve entrar depois, com
fila limitada e breaker protegido por lock, se a medição provar necessidade.

## 11. Configuração

Adicionar ao `Settings` de `config.py`:

```python
ml_enabled: bool
ml_api_url: str
ml_timeout_ms: int
ml_failure_threshold: int
```

Adicionar a `.env.example`:

```env
ML_ENABLED=true
ML_API_URL=http://api-ml:8000
ML_TIMEOUT_MS=1000
ML_FAILURE_THRESHOLD=5
ML_MODEL_PATH=models/classificador_lotes.pkl
```

Para execução fora de Docker, documentar `ML_API_URL=http://127.0.0.1:8000`.
Validar `ML_TIMEOUT_MS >= 1` e `ML_FAILURE_THRESHOLD >= 1` usando os helpers já
existentes em `config.py`.

## 12. Relatório e auditoria

### 12.1 Integração no orquestrador

Alterar `executar_pipeline_dashboard()` na seguinte ordem:

1. carregar dados e base;
2. executar `validar_registros_lista()` uma única vez;
3. calcular indicadores uma única vez, como hoje;
4. criar `MLClient` pela factory;
5. executar `ItemProcessor.processar_lote(validados)`;
6. passar `decisoes_ml` a `gerar_excel_consolidado()`;
7. fechar o cliente em `finally`;
8. gerar os demais artefatos atuais sem regressão.

Os indicadores atuais continuam descrevendo a saída das regras. Não reclassificar
silenciosamente `Ambíguo` como `Válido` nas abas históricas; a nova ação fica
auditada na 9ª aba.

### 12.2 Nona aba

Alterar a assinatura:

```python
def gerar_excel_consolidado(
    validados: Sequence[RegistroValidado],
    indicadores: OperationalIndicators,
    destino: Path,
    *,
    decisoes_ml: Sequence[MLDecision] = (),
) -> Path: ...
```

Criar `_montar_aba_decisoes_ml(ws, decisoes_ml)` e adicionar a aba, por último,
com nome exato `Decisões de ML`.

Colunas recomendadas:

```text
Timestamp
Lote
Status original
Turno
Tem observação
Classe predita
Probabilidade
Nível de confiança
Ação final
Latência total (ms)
Tentou rede
Circuit breaker aberto
Versão do modelo
Tipo de erro
```

Formatar probabilidade como `0.00%`, latência como `0.00`, congelar cabeçalho,
ativar filtro e criar tabela no mesmo padrão visual das outras abas. Uma aba
vazia ainda deve conter o cabeçalho.

Garantia de completude:

```text
quantidade de linhas de decisão == quantidade de registros Ambíguos
```

Isso inclui sucesso, erro de rede e chamadas não tentadas porque o breaker já
estava aberto.

### 12.3 Log estruturado

Emitir um evento por lote:

```python
logger.info("ML_DECISION", extra=decision.to_log_dict())
```

Campos mínimos no JSON Lines:

```text
event, timestamp, lote_id, classe, probabilidade, nivel_confianca,
acao_final, latencia_ms, tentou_rede, circuit_open, modelo_versao, erro_tipo
```

Não registrar texto integral de observação nem payload completo; `tem_obs` é
suficiente e reduz exposição de dados.

## 13. Docker Compose e container

Substituir/adaptar o Dockerfile do template. O modelo deve ser copiado para a
imagem e o processo deve rodar como usuário não root.

Serviço recomendado em `docker-compose.yml`:

```yaml
api-ml:
  build:
    context: .
    dockerfile: api_ml/Dockerfile
  ports:
    - "8000:8000"
  environment:
    ML_MODEL_PATH: /service/models/classificador_lotes.pkl
    TZ: America/Manaus
  healthcheck:
    test:
      - CMD
      - python
      - -c
      - "import urllib.request; urllib.request.urlopen('http://localhost:8000/health', timeout=2)"
    interval: 5s
    timeout: 3s
    retries: 10
    start_period: 10s
  restart: "no"
```

Adicionar `ML_API_URL=http://api-ml:8000` aos serviços que executarem o
`ItemProcessor`.

Não criar dependência obrigatória `condition: service_healthy` entre o bot e a
API: o bot também deve iniciar quando a API já estiver indisponível. O
healthcheck existe para observabilidade, não para impedir o fallback.

Durante a sabotagem, não usar `docker compose up --abort-on-container-failure`,
pois a parada intencional do container da API pode fazer o Compose encerrar os
demais serviços. Subir os serviços em background e executar o bot separadamente.

## 14. Testes automatizados

Implementar mais do que os cinco mínimos para proteger os critérios de aceite.

### 14.1 API — `tests/unit/test_api_ml.py`

1. `test_predict_payload_valido_retorna_contrato()`;
2. `test_predict_turno_invalido_retorna_422()`;
3. `test_health_com_modelo_retorna_200()`;
4. `test_health_sem_modelo_retorna_503()`;
5. `test_predict_sem_modelo_retorna_503()`;
6. `test_limites_de_confianca_065_e_085()`.

Injetar um modelo fake; os testes da API não devem depender do `.pkl` real.

### 14.2 Cliente — `tests/unit/test_ml_client.py`

1. `test_classificar_sucesso_retorna_prediction()`;
2. `test_timeout_retorna_none_sem_propagar()`;
3. `test_erro_http_retorna_none_sem_propagar()`;
4. `test_json_invalido_retorna_none_sem_propagar()`;
5. `test_cinco_falhas_abrem_circuito()`;
6. `test_sexta_chamada_nao_tenta_rede()`;
7. `test_sucesso_zera_falhas_consecutivas()`;
8. `test_reset_manual_fecha_circuito()`.

Usar `httpx.MockTransport` e contador de chamadas, sem rede real e sem sleeps.

### 14.3 Processador e auditoria

1. não ambíguo não chama o cliente;
2. predição válida gera uma decisão e um log;
3. `None` gera `REVISAO_ML_OFFLINE` e o próximo item continua;
4. circuito aberto gera uma linha para cada lote restante;
5. nenhum texto de observação aparece no log.

### 14.4 Dataset/modelo

1. gerador é reprodutível com a mesma seed;
2. dataset possui >=10.000 linhas, três features e três classes;
3. classe/turno respeita tolerância de balanceamento;
4. nenhuma coluna proibida entra em `FEATURE_ORDER`;
5. artefato salvo pode ser recarregado e predizer;
6. métricas e SHA do dataset existem no bundle/JSON.

### 14.5 Relatório

Atualizar `test_relatorio_consolidado_8_abas_e_markdown` para um nome de 9
abas e para a ordem:

```text
Resumo, Todos, Válidos, Divergências, Ambíguos, Erros de Entrada,
Ranking de Regras, Dicionário, Decisões de ML
```

Testar colunas, formato da probabilidade e igualdade entre quantidade de
ambíguos e linhas de decisão.

### 14.6 Integração/sabotagem

Executar um lote com pelo menos 8 registros ambíguos usando transport que
responda aos três primeiros e falhe nos seguintes. Verificar:

- processamento chega ao último item;
- quinta falha consecutiva abre o breaker;
- itens restantes recebem `REVISAO_ML_OFFLINE` sem nova chamada;
- todas as decisões aparecem no log e Excel.

Fazer também um ensaio real:

```powershell
docker compose up -d --build api-ml
docker compose run --rm bot-classificador
docker compose kill api-ml
```

Para permitir sabotagem durante a execução rápida, `scripts/demo_torneio.py`
pode aceitar `--intervalo-ms` com padrão `0`; esse atraso é exclusivo da demo e
não entra na medição de latência da API.

## 15. Ordem de implementação para um modelo de código mais leve

Executar uma etapa por vez e rodar apenas os testes relacionados antes de
avançar.

### Etapa 0 — baseline

- registrar `git status`;
- rodar a suíte existente sem alteração;
- guardar quantidade de testes e falhas conhecidas;
- não alterar RN01–RN12.

### Etapa 1 — migrar o template

- criar `api_ml/` a partir de `micro-service-ml/app/`;
- remover toda referência a Iris;
- criar schemas/enums e testes de validação;
- só então aposentar o entrypoint antigo.

### Etapa 2 — gerador e validação de dados

- implementar `features.py` e `train_model.py`;
- gerar CSV/manifest com 12.000 linhas;
- aprovar testes de volume, esquema, equilíbrio e reprodutibilidade.

### Etapa 3 — treino e calibração

- implementar pipeline, split, métricas e gates;
- gerar `.pkl` e JSON de métricas;
- testar round-trip de serialização.

### Etapa 4 — API

- implementar `ModelService`, lifespan, `/health` e `/predict`;
- aprovar testes 200/422/503 e fronteiras 0,65/0,85.

### Etapa 5 — cliente resiliente

- implementar DTO, protocolo, breaker, `MLClient` e factory;
- provar que nenhuma falha escapa e que a sexta chamada não usa rede.

### Etapa 6 — processador/auditoria

- implementar `ItemProcessor` e `MLDecision`;
- integrar somente após `Ambíguo`;
- provar fallback por item e continuidade do lote.

### Etapa 7 — nona aba

- adicionar parâmetro opcional para não quebrar chamadas atuais;
- montar `Decisões de ML` na nona posição;
- atualizar testes do relatório.

### Etapa 8 — Compose

- adicionar `api-ml`, healthcheck e variáveis;
- validar `docker compose config --quiet`;
- testar API saudável e API ausente.

### Etapa 9 — regressão e demo

- rodar unitários, integração, regressão e cobertura;
- treinar ensaio de sabotagem;
- medir os 50 casos sem atraso artificial;
- guardar logs e relatório como evidências.

### Etapa 10 — documentação

Atualizar o `README.md` raiz com:

- como as 12.000 linhas são geradas;
- seed, classes, vocabulário e tabela probabilística;
- justificativa de não usar identificadores/proxies;
- métricas gerais, calibração e diferenças por turno;
- comandos de treino e execução local/Docker;
- contratos `/predict` e `/health`;
- como resetar o circuit breaker (reinício ou método explícito);
- roteiro do torneio e da sabotagem;
- limitações: dado sintético não prova ausência de viés em produção.

## 16. Critérios de conclusão rastreáveis

| Critério | Evidência obrigatória |
| --- | --- |
| 10.000+ amostras | CSV, manifest e teste de volume |
| 3 features/3 classes | `FEATURE_ORDER`, manifest e teste |
| RandomForest | bundle e métricas de treino |
| Probabilidade calibrada | `CalibratedClassifierCV`, ECE/Brier e testes de limiar |
| `/predict` | TestClient 200 e contrato completo |
| turno inválido | TestClient 422 |
| `/health` | 200 carregado e 503 indisponível |
| MLClient nunca lança | testes de timeout, rede, HTTP, JSON e erro inesperado |
| breaker após 5 falhas | contador do MockTransport e sexta chamada sem rede |
| bot nunca para | integração até o último item após falha |
| fallback exato | `REVISAO_ML_OFFLINE` em log e Excel |
| auditoria completa | uma linha/evento por ambíguo, inclusive offline |
| relatório de 9 abas | teste de nomes, ordem, linhas e formatos |
| Compose | `docker compose config --quiet` + healthcheck |
| sem regressão | toda a suíte anterior continua passando |

## 17. Respostas técnicas que a implementação deve sustentar na banca

- **Por que 0,85?** É o compromisso fixado pelo exercício entre cobertura e
  risco. A calibração permite interpretar aproximadamente a confiança; elevar
  para 0,95 reduz ações automáticas e falsos positivos, mas aumenta revisão
  humana. A decisão final deve observar custo por classe.
- **Breaker abre no meio do lote:** o lote atual e os seguintes recebem
  `REVISAO_ML_OFFLINE`; eles não ficam sem rastreabilidade e podem ser
  reprocessados após reset/reinício, conforme política documentada.
- **Retreino sem derrubar serviço:** gerar artefato versionado e validado,
  construir nova imagem/instância, aprovar `/health` e trocar tráfego. Nunca
  sobrescrever o arquivo que uma instância ativa está lendo.
- **Custos assimétricos:** liberar incorretamente e recusar incorretamente têm
  custos diferentes. Em produção, os limiares deveriam ser definidos por
  classe com matriz de custo; nesta entrega, manter 0,85/0,65 exatamente para
  atender ao enunciado e registrar essa limitação.

## 18. Fora do escopo do MVP

- Kubernetes/HPA/Ingress;
- banco de dados para auditoria;
- fila assíncrona adicional;
- retreino online;
- recuperação automática half-open do breaker;
- usar texto livre da observação como NLP;
- alterar regras RN01–RN12 ou os indicadores existentes.

Esses itens só entram depois que os critérios de aceite, os testes de sabotagem
e a rastreabilidade da versão básica estiverem completos.
