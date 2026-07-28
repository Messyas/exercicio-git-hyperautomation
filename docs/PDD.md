# PDD — Automação web com Playwright e Selenium

## 1. Objetivo

Executar, em ambiente local e controlado, o cadastro de lotes orientado por
DataPool com Playwright e Selenium. O desenho deve manter rastreabilidade por
item, preservar evidências após os containers terminarem e separar interface,
regra de negócio e infraestrutura de navegador.

## 2. Escopo

Inclui:

- front-end Next.js de demonstração;
- dez itens independentes por DataPool e por ferramenta;
- login fictício e cadastro de lote;
- screenshot de sucesso ou erro para cada item;
- resultado JSON e log de execução por ferramenta;
- execução sequencial e encerramento automático via Docker Compose.

Não inclui sistemas externos, credenciais reais, banco de dados ou integração
com APIs de produção.

## 3. Componentes e responsabilidades

| Componente | Responsabilidade |
|---|---|
| `frontend/` | Interface local, estado no `localStorage` e mensagem de sucesso |
| `frontend/start-and-wait.sh` | Mantém o servidor ativo até receber o sinal final |
| `test/main.py` | Executa Playwright, depois Selenium, e sempre envia o shutdown |
| `test/*/bot.py` | Entry-point independente de cada ferramenta |
| `test/*/*automation.py` | Cria e encerra o navegador e adapta sua API |
| `test/src/pages/` | Centraliza locators, waits e ações de interface |
| `test/src/runner.py` | Valida DataPool e destino, processa itens, registra logs e resultados |
| `test/evidencias/` | Screenshots e `resultado.json`, separados por ferramenta |
| `test/logs/` | `execucao.log`, separado por ferramenta |

## 4. Sequência de execução

```text
docker compose up --build
        │
        ├─ constrói e inicia frontend
        │        └─ healthcheck aprovado
        │
        └─ inicia tests
                 ├─ Playwright: login → 10 itens → evidências/log
                 ├─ Selenium:   login → 10 itens → evidências/log
                 └─ cria /run-status/tests-finished
                              └─ frontend encerra o servidor
```

O `finally` de `test/main.py` cria o sinal mesmo quando um bot retorna erro.
Assim, a falha de teste não deixa o front em execução. O runner também chama
Selenium após uma falha do Playwright para preservar a comparação completa.

## 5. Page Object Model

Há Page Objects próprios porque os tipos de locator e espera são diferentes:

- `playwright_pages.py` usa IDs, roles, nomes acessíveis e `expect`;
- `selenium_pages.py` usa IDs, roles, seletores estáveis, `WebDriverWait` e
  `expected_conditions`.

Os objetos de página não validam DataPool, produto permitido, status, lote
duplicado, destino de rede ou resultado global. Essas regras ficam no runner
compartilhado. Captura e persistência também são solicitadas pelo runner e
executadas pelos adaptadores de infraestrutura.

## 6. DataPool e rastreabilidade

Campos obrigatórios:

| Campo | Uso |
|---|---|
| `lote` | Identificação e validação da mensagem final |
| `produto` | Seleção da opção correspondente |
| `status` | Seleção do radio correspondente |
| `screenshot` | Nome seguro do PNG individual |

Para cada item, o log registra início da interação, envio, validação visual e
caminho da evidência. `resultado.json` contém totais e o resultado individual,
incluindo o caminho efetivo em `evidencia`.

## 7. Tratamento de falhas

Uma divergência de item:

1. gera screenshot de página inteira;
2. registra stack trace no log;
3. adiciona o item como `FALHA` no resultado;
4. não impede o processamento dos demais itens.

Falhas estruturais, como DataPool inválido, URL não permitida ou navegador
indisponível, encerram o bot com código diferente de zero. O orquestrador ainda
executa a segunda tecnologia e encerra o front.

## 8. Segurança e dados

- Hosts permitidos: `frontend`, `localhost` e `127.0.0.1`.
- Credenciais são fictícias e o front não as valida.
- Nenhum `time.sleep()` é usado na automação.
- Logs não registram senha.
- `.env`, screenshots, resultados, logs, caches e `.pyc` não são versionados.
- Artefatos persistem somente por bind mounts dentro de `test/`.

## 9. Decisões técnicas

- Uma imagem de testes instala Chromium e ChromeDriver do mesmo repositório do
  sistema, usados pelas duas ferramentas.
- Um runner comum reduz duplicação de regra e padroniza evidências e logs.
- DataPools permanecem separados para que cada `bot.py` seja independente.
- O shutdown usa arquivo em volume nomeado, sem montar o socket Docker e sem
  exigir argumentos adicionais no comando de execução.

## 10. Histórico

| Data | Alteração |
|---|---|
| 2026-07-28 | Integração de Playwright, Selenium, POM, artefatos separados e ciclo Docker completo |
