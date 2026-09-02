# Evidências de Avaliação — Projeto Final Capstone de Hyperautomation

**Curso:** Técnicas de Hyperautomation (240h) · LG Electronics / IFAM / INOVA  
**Processo:** Conferência de Estoque e Pedidos (`RPA01`–`RPA06`)  
**Data:** 28/08/2026 | **Ambiente:** Smart Office Orchestrator & The DX Way  

---

## 1. Rastreabilidade com a Rubrica de Avaliação (100 Pontos)

| Eixo de Avaliação | Pontos | Requisito Exigido | Evidência Comprovada no Repositório |
| :--- | :---: | :--- | :--- |
| **1. Orquestração Multi-Bot Híbrida** | **20** | 5+ bots registrados com dependências rastreáveis, automação Desktop e Web funcionais e prioridades coerentes. | • [`src/orchestrator.py`](file:///c:/Users/User/Documents/projects/hyperauto/exercicio-git-hyperautomation/src/orchestrator.py)<br/>• [`desktop_app/sistema_estoque.py`](file:///c:/Users/User/Documents/projects/hyperauto/exercicio-git-hyperautomation/desktop_app/sistema_estoque.py)<br/>• [`bots/RPA01_ColetaEstoque_DESKTOP`](file:///c:/Users/User/Documents/projects/hyperauto/exercicio-git-hyperautomation/bots/RPA01_ColetaEstoque_DESKTOP)<br/>• [`reports/rastreabilidade_pipeline_capstone.json`](file:///c:/Users/User/Documents/projects/hyperauto/exercicio-git-hyperautomation/reports/rastreabilidade_pipeline_capstone.json) |
| **2. Decisão Híbrida RPA+ML** | **15** | Feature flag funcional, limiar de confiança, ML nunca crítico, auditoria de origem (`origem_decisao` e `confianca_ml`). | • [`src/classificador_divergencia.py`](file:///c:/Users/User/Documents/projects/hyperauto/exercicio-git-hyperautomation/src/classificador_divergencia.py)<br/>• [`bots/RPA04_ClassificadorML_HYBRID`](file:///c:/Users/User/Documents/projects/hyperauto/exercicio-git-hyperautomation/bots/RPA04_ClassificadorML_HYBRID)<br/>• Colunas visíveis em [`data/output/relatorio_conferencia_lotes.xlsx`](file:///c:/Users/User/Documents/projects/hyperauto/exercicio-git-hyperautomation/data/output/relatorio_conferencia_lotes.xlsx) |
| **3. Resiliência sob Sabotagem** | **20** | Comportamento correto nos 6 cenários de falha ao vivo sem travamento manual. | • [`scripts/simular_cenarios_sabotagem.py`](file:///c:/Users/User/Documents/projects/hyperauto/exercicio-git-hyperautomation/scripts/simular_cenarios_sabotagem.py)<br/>• [`reports/evidencias_sabotagem/resumo_evidencias_capstone.json`](file:///c:/Users/User/Documents/projects/hyperauto/exercicio-git-hyperautomation/reports/evidencias_sabotagem/resumo_evidencias_capstone.json) (6/6 Aprovados) |
| **4. Notificação Multicanal** | **10** | Dois canais ativos, roteamento por severidade e fallback automático comprovado. | • [`src/sistema_alertas.py`](file:///c:/Users/User/Documents/projects/hyperauto/exercicio-git-hyperautomation/src/sistema_alertas.py)<br/>• Alerta de modo degradado e fallback para Log/Email demonstrados. |
| **5. Plano de Migração e Coexistência** | **15** | Coexistência, cutover, prevenção de conflito de Runner e plano de rollback. | • [`docs/PLANO_MIGRACAO_COEXISTENCIA.md`](file:///c:/Users/User/Documents/projects/hyperauto/exercicio-git-hyperautomation/docs/PLANO_MIGRACAO_COEXISTENCIA.md)<br/>• [`src/coexistence_guard.py`](file:///c:/Users/User/Documents/projects/hyperauto/exercicio-git-hyperautomation/src/coexistence_guard.py)<br/>• [`scripts/smoke_test_cutover.py`](file:///c:/Users/User/Documents/projects/hyperauto/exercicio-git-hyperautomation/scripts/smoke_test_cutover.py) |
| **6. Governança The DX Way e Docs** | **10** | GitFlow, commits semânticos, MR com revisor, PDD completo e pacotes .zip corretos. | • [`scripts/build_smartoffice_packages.py`](file:///c:/Users/User/Documents/projects/hyperauto/exercicio-git-hyperautomation/scripts/build_smartoffice_packages.py)<br/>• [`docs/pdd/PDD_Process_Design_Document.md`](file:///c:/Users/User/Documents/projects/hyperauto/exercicio-git-hyperautomation/docs/pdd/PDD_Process_Design_Document.md)<br/>• [`dist/smartoffice/`](file:///c:/Users/User/Documents/projects/hyperauto/exercicio-git-hyperautomation/dist/smartoffice) |
| **7. Pitch e Arguição** | **10** | Apresentação em até 10 min sustentando escolhas de arquitetura e respostas técnicas. | • [`docs/PITCH_APRESENTACAO_CAPSTONE.md`](file:///c:/Users/User/Documents/projects/hyperauto/exercicio-git-hyperautomation/docs/PITCH_APRESENTACAO_CAPSTONE.md) |

---

## 2. Evidências dos 6 Cenários de Sabotagem (Seção 6 do Enunciado)

Os seis ensaios de crise foram executados de forma automatizada via `python scripts/simular_cenarios_sabotagem.py`. O resumo abaixo consolida os resultados obtidos:

```json
{
  "total_cenarios": 6,
  "total_aprovados": 6,
  "taxa_sucesso": "100%",
  "cenarios": [
    {
      "cenario": 1,
      "titulo": "Bot desktop indisponível",
      "status": "APROVADO",
      "comportamento": "Retry acionado (3 tentativas com backoff); item marcado para revisão; alerta disparado; pipeline não travou."
    },
    {
      "cenario": 2,
      "titulo": "Timeout de dependência",
      "status": "APROVADO",
      "comportamento": "Deadline expirado; bot de consolidação tratou o timeout sem bloqueio indefinido."
    },
    {
      "cenario": 3,
      "titulo": "Serviço de ML fora do ar",
      "status": "APROVADO",
      "comportamento": "API de ML respondeu 503; item processado via fallback determinístico com origem_decisao=fallback sem lançar exceção."
    },
    {
      "cenario": 4,
      "titulo": "Canal de alerta principal falha",
      "status": "APROVADO",
      "comportamento": "Token do Telegram invalidado (401); alerta roteado automaticamente para canal secundário e log local destacado."
    },
    {
      "cenario": 5,
      "titulo": "Coexistência de orquestradores",
      "status": "APROVADO",
      "comportamento": "BotCity e Smart Office acionados no mesmo instante; CoexistenceGuard reteve execução concorrente via Mutex."
    },
    {
      "cenario": 6,
      "titulo": "Item com dado irrecuperável",
      "status": "APROVADO",
      "comportamento": "Registro corrompido encaminhado para Dead Letter Queue após tentativas, permitindo conclusão do restante do lote."
    }
  ]
}
```

---

## 3. Evidência do Smoke Test de Corte (Smart Office - Capítulo 13)

Validação automatizada pré-agendamento executada com 100% de aprovação via `python scripts/smoke_test_cutover.py`:

```
================================================================================
RESULTADO DO SMOKE TEST: 6/6 TASKS APROVADAS COM SUCESSO!
DECISÃO DO REVISOR: ✅ APROVADO — Pipeline pronto para agendamento (Schedule)!
Relatório salvo em: 'reports/smoke_test_report.json'
================================================================================
```

---

## 4. Evidência do Empacotamento de Deploy no Smart Office

Conforme o **Capítulo 4 do Manual**, os robôs foram empacotados com `bot.py` e `requirements.txt` rigorosamente na **raiz** dos arquivos `.zip`:

* `dist/smartoffice/RPA01_ColetaEstoque_DESKTOP.zip` (Entrypoint: `bot.py` na raiz)
* `dist/smartoffice/RPA02_ColetaPedidos_WEB.zip` (Entrypoint: `bot.py` na raiz)
* `dist/smartoffice/RPA03_ConsolidacaoRegras_CORE.zip` (Entrypoint: `bot.py` na raiz)
* `dist/smartoffice/RPA04_ClassificadorML_HYBRID.zip` (Entrypoint: `bot.py` na raiz)
* `dist/smartoffice/RPA05_RelatorioAlertas_NOTIF.zip` (Entrypoint: `bot.py` na raiz)
* `dist/smartoffice/RPA06_ReprocessadorDeadLetter_SCHED.zip` (Entrypoint: `bot.py` na raiz)
