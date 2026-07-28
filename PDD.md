# PDD — Process Definition Document

## Cadastro Automatizado de Lotes de Produção

### 1. Objetivo do Processo

Automatizar o preenchimento e envio de lotes de produção no sistema "Cadastro de Lotes", gerando evidências visuais (screenshots) de cada operação realizada.

### 2. Escopo

- **Inclui**: Preenchimento automático do formulário de cadastro, seleção de produto e status, captura de comprovantes visuais.
- **Não inclui**: Acesso a sistemas reais de produção; todos os dados são fictícios e o sistema é local.

### 3. Pré-condições

- Docker e Docker Compose instalados na máquina.
- Acesso à porta 3000 (localhost).

### 4. Entradas

| Dado | Origem | Formato |
|------|--------|---------|
| Número do lote | DataPool (`datapool.json`) | `LT-AAAA-NNNN` |
| Produto | DataPool (`datapool.json`) | Texto livre |
| Status | DataPool (`datapool.json`) | Pendente / Em processamento / Concluído |
| Nome do screenshot | DataPool (`datapool.json`) | `evidencia_LT-AAAA-NNNN.png` |

### 5. Fluxo Principal

```
┌─────────────────────────────────────────────────────────────┐
│  1. docker compose up --build                               │
│     ├─ Sobe front-end Next.js na porta 3000                 │
│     └─ Aguarda healthcheck (front saudável)                 │
│                                                             │
│  2. Bot Selenium inicia                                     │
│     ├─ Carrega datapool.json                                │
│     └─ Abre Chrome headless                                 │
│                                                             │
│  3. Para cada item do DataPool:                             │
│     ├─ Navega até http://frontend:3000                      │
│     ├─ Preenche "Número do lote"                            │
│     ├─ Seleciona "Produto" no dropdown                      │
│     ├─ Clica no status (radio button)                       │
│     ├─ Clica em "Processar lote"                            │
│     ├─ Aguarda mensagem de sucesso (role=status)            │
│     └─ Captura screenshot do comprovante                    │
│                                                             │
│  4. Gera resultado.json com resumo da execução              │
│                                                             │
│  5. Evidências ficam em ./evidencias/ (volume Docker)       │
└─────────────────────────────────────────────────────────────┘
```

### 6. Saídas

| Artefato | Descrição |
|----------|-----------|
| `evidencias/evidencia_LT-XXXX-NNNN.png` | Screenshot do comprovante de sucesso de cada lote |
| `evidencias/erro_LT-XXXX-NNNN.png` | Screenshot de falha (quando aplicável) |
| `evidencias/resultado.json` | Resumo JSON com status de cada item processado |

### 7. Exceções e Tratamento

| Cenário | Tratamento |
|---------|------------|
| Timeout ao carregar comprovante | Captura screenshot de erro, registra no log, segue para próximo item |
| Elemento não encontrado | Log de erro com detalhes, screenshot de fallback |
| Front-end indisponível | Bot falha na conexão (depends_on healthcheck previne isso) |

### 8. Restrições de Segurança

- **Nenhum sistema real é acessado** — o front-end roda localmente em container.
- **Dados fictícios** — lotes, produtos e status são dados de teste.
- **Sem credenciais** — nenhuma senha ou token é utilizado.
- **Screenshots fora do Git** — pasta `evidencias/` está no `.gitignore`.

### 9. Tecnologias Utilizadas

- Python 3.11 + Selenium 4 (automação)
- Google Chrome headless (navegador)
- Next.js 16 + React 19 (front-end)
- Docker + Docker Compose (orquestração)
