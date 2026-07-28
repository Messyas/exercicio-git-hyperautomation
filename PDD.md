# PDD — Cadastro automatizado de lotes

## 1. Objetivo

Realizar login no sistema local, cadastrar lotes fictícios e produzir
evidências auditáveis sem misturar regras do fluxo com locators da interface.

## 2. Escopo

O processo cobre login de demonstração, preenchimento do formulário, validação
da confirmação, logs, screenshots e resumo JSON. Sistemas produtivos,
credenciais reais e a implementação Selenium não fazem parte desta branch.

## 3. Pré-condições

- Docker e Docker Compose instalados;
- porta 3000 disponível;
- `playwright/datapool.json` válido;
- diretório `evidencias/` disponível para o volume Docker.

## 4. Entradas

| Entrada | Origem | Uso |
|---|---|---|
| `BOT_URL` | Ambiente | Endereço do front-end |
| `BOT_USUARIO` | Ambiente | Usuário de demonstração |
| `BOT_SENHA` | Ambiente | Senha de demonstração |
| `BOT_HEADLESS` | Ambiente | Modo de execução do navegador |
| `lote` | DataPool | Número do lote |
| `produto` | DataPool | Produto selecionado |
| `status` | DataPool | Status selecionado |
| `screenshot` | DataPool | Nome da evidência |

## 5. Arquitetura Page Object Model

| Componente | Responsabilidade |
|---|---|
| `playwright/bot.py` | Compor dependências, carregar DataPool, configurar logs e salvar o resultado |
| `main.py` | Orquestrar login, validação, formulário e tratamento por item |
| `playwright/web_automation.py` | Abrir, navegar e encerrar o Chromium |
| `LoginPage` | Locators e ações da tela de login |
| `FormPage` | Locators, ações e estado visual do formulário |
| `EvidenceService` | Criar diretórios e capturar screenshots |

```text
bot ─┬→ sessão Playwright
     └→ orquestrador
          ├─ LoginPage
          ├─ FormPage
          └─ EvidenceService
```

As regras de entrada e a construção do resultado não ficam nos Page Objects.
Uma mudança de seletor deve exigir alteração somente em `src/pages/`. A sessão
do navegador é injetada no orquestrador pelo entry-point.

## 6. Fluxo principal

1. O Compose inicia o front-end.
2. O healthcheck confirma que a página está saudável.
3. O bot carrega os dez itens do DataPool.
4. A infraestrutura abre Chromium e navega para `BOT_URL`.
5. `LoginPage.fazer_login()` autentica com dados de demonstração.
6. Para cada item, o orquestrador valida os campos obrigatórios.
7. `FormPage.preencher_lote()` preenche e envia o formulário.
8. `FormPage.is_sucesso()` valida a mensagem final.
9. `EvidenceService` captura o comprovante.
10. O bot grava `resultado.json`.

## 7. Exceções

Falhas de locator, timeout ou dados inválidos são registradas por item. Uma
captura de página é salva com prefixo `erro_`, e os itens seguintes continuam.
Ao final, qualquer falha faz o container retornar código diferente de zero.

## 8. Saídas

| Artefato | Descrição |
|---|---|
| `evidencias/evidencia_*.png` | Comprovante de sucesso |
| `evidencias/erro_*.png` | Evidência de falha |
| `evidencias/resultado.json` | Totais, data e detalhes por item |
| stdout do container | Logs de login, sucesso, falha e encerramento |

## 9. Segurança e versionamento

Os dados são fictícios e não há credenciais reais. Evidências, caches e
artefatos gerados são ignorados pelo Git.

## 10. Execução

```bash
docker compose up --build --abort-on-container-exit --exit-code-from playwright-bot
```
