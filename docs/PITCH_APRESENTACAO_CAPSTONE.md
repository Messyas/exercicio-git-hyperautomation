# Roteiro de Pitch e Defesa Técnica — Projeto Final Capstone

**Organização:** LG Electronics do Brasil · AX Academy / IFAM / INOVA  
**Processo:** Conferência de Estoque e Pedidos (`RPA01–RPA06`)  
**Tempo Limite do Pitch:** 10 Minutos (Cronometrado pela Banca)  

---

## 1. Roteiro Estruturado do Pitch (10 Minutos)

```
[00:00 - 02:00] BLOCO 1: O Problema e o Cenário de Migração
[02:00 - 05:00] BLOCO 2: Arquitetura Multi-Bot Híbrida e Decisões Técnicas
[05:00 - 07:30] BLOCO 3: Demonstração ao Vivo do Pipeline e Resiliência
[07:30 - 09:30] BLOCO 4: Plano de Migração, Coexistência e Smoke Test
[09:30 - 10:00] BLOCO 5: Conclusão e Abertura para a Banca
```

### [Minuto 0 a 2] Bloco 1: O Desafio de Negócio
- **A Dor:** O processo de conferência de estoque diário rodava no BotCity legado, restrito a uma automação desktop de tela em um sistema Windows sem API.
- **O Objetivo:** Migrar para o Smart Office corporativo sem risco de parada (*zero downtime*), expandindo para um modelo híbrido (**Desktop + Web**) e acelerando a triagem de divergências com **Machine Learning** nunca crítico.

### [Minuto 2 a 5] Bloco 2: Arquitetura da Solução e Decisões-Chave
- **Por que 5+ Bots?** 
  - *Separação de responsabilidades e isolamento de falhas*: O bot desktop exige Runner gráfico dedicado (Prioridade 1); o bot web roda em paralelo (Prioridade 2); o bot core aplica as regras determinísticas com timeout (Prioridade 3); o bot ML enriquece divergências de forma assíncrona (Prioridade 4); e o bot de notificações entrega os relatórios com fallback multicanal (Prioridade 5).
- **Por que o ML é estritamente não crítico?**
  - O ML **enriquece, nunca decide**. Decisões de negócio dependem exclusivamente das regras determinísticas RN01–RN12. Se o ML falhar, houver timeout ou a confiança for < 0.70, o fallback determinístico é acionado imediatamente e registrado na coluna `origem_decisao`.

### [Minuto 5 a 7:30] Bloco 3: Demo ao Vivo e Resiliência sob Sabotagem
- Rodar o pipeline ao vivo processando a carga do dia:
  ```bash
  python scripts/demo_capstone.py
  ```
- Exibir a reação instantânea do pipeline sob provocação da banca:
  - *Queda da interface desktop:* 3 retries com backoff linear e encaminhamento controlado para revisão.
  - *Queda da API de ML:* Circuit Breaker trip após 5 falhas, fallback imediato para o restante da fila e alerta de modo degradado.
  - *Falha no Telegram:* Roteamento automático para canal secundário e log local de alta visibilidade.

### [Minuto 7:30 a 9:30] Bloco 4: Plano de Migração e Smoke Test
- Explicar a janela de **coexistência de 14 dias (Shadow Mode)**:
  - O BotCity legado roda às 07:00 (oficial); o Smart Office roda às 07:30 (shadow).
  - O `CoexistenceGuard` impede disputa física de tela caso ocorra sobreposição de horários.
- Apresentar o **Smoke Test de Corte (Capítulo 13 do Manual)**:
  - 6 tasks mínimas não críticas validadas com 100% de sucesso antes da ativação do Schedule.
  - Procedimento de Rollback documentado com RTO < 15 minutos.

### [Minuto 9:30 a 10:00] Bloco 5: Fechamento
- Síntese: Automação corporativa madura, resiliente, auditável e segura sob qualquer condição de falha.

---

## 2. Gabarito Técnico para a Arguição da Banca (Seção 12 do Enunciado)

Abaixo estão as respostas técnicas fundamentadas para as 5 perguntas obrigatórias da banca:

### Pergunta 1:
> *"Por que a automação desktop precisa de um Runner dedicado, e o que acontece se duas tarefas tentarem usar a mesma sessão gráfica ao mesmo tempo?"*

**Resposta Técnica:**  
A automação desktop sobre sistemas legados sem API depende de interação com o subsistema gráfico do Windows (renderização de janelas, reconhecimento de tela/OCR, envio de eventos de teclado e mouse). Duas automações concorrentes no mesmo desktop causam **roubo de foco de janela** (*focus stealing*), corrompendo o envio de teclas, clicando em coordenadas erradas e provocando falhas catastróficas em ambos os processos. Por isso, a automação desktop exige um **Runner com sessão gráfica dedicada** e mecanismo de **Mutex exclusivo (`CoexistenceGuard`)** para impedir sobreposição de execuções.

---

### Pergunta 2:
> *"Se o cutover para o Smart Office falhar no meio da janela de coexistência, quantos minutos (ou horas) a operação fica sem dado atualizado até o rollback restaurar o bot legado?"*

**Resposta Técnica:**  
Durante a janela de coexistência, o tempo de indisponibilidade é **zero (RTO = 0 e RPO = 0)**, pois o BotCity legado continua sendo a fonte oficial processando às 07:00. Caso a falha ocorra **após o cutover definitivo**, o nosso **Plano de Rollback** possui um RTO de no máximo **15 minutos**:
1. Desativação do agendamento no Smart Office (3 min);
2. Reativação do agendamento no BotCity Orchestrator legado (3 min);
3. Disparo manual da conferência do dia no BotCity (6 min);
4. Emissão de alerta de contingência à equipe de Operações (3 min).

---

### Pergunta 3:
> *"Por que o ML não pode decidir o status do item, mesmo quando a confiança da predição é altíssima — e o que isso protege especificamente neste processo?"*

**Resposta Técnica:**  
Modelos de Machine Learning são probabilísticos e sujeitos a **deriva de dados (*data drift*)**, vieses em observações não padronizadas e alucinações em casos de borda. No processo de conferência de estoque, uma decisão incorreta gerada por ML (ex.: aprovar automaticamente um lote com defeito físico ou saldo divergente) causaria a liberação indevida de mercadorias defeituosas para a linha de produção ou clientes, gerando retrabalho de fábrica, prejuízos financeiros e multas fiscais. As regras de negócio determinísticas (RN01–RN12) são o **guardião da conformidade**; o ML atua exclusivamente como **camada de recomendação e triagem de causas prováveis**, acelerando a análise humana sem assumir o risco da decisão.

---

### Pergunta 4:
> *"Qual seria o efeito de rodar o bot legado no BotCity Orchestrator e o novo bot no Smart Office no mesmo horário, apontando para runners diferentes? Isso resolveria o problema de conflito, ou criaria um novo?"*

**Resposta Técnica:**  
Apontar para Runners diferentes resolve a disputa física da sessão gráfica na máquina local, mas **cria um problema operacional e de negócio grave**: a **duplicidade de processamento sobre a mesma base de dados**. Se ambos os robôs executarem no mesmo horário, eles disputarão atualizações nas mesmas planilhas/tabelas de pedidos, poderão gerar relatórios divergentes para os analistas no mesmo dia e mascarar erros de transição. A estratégia correta de coexistência exige **Schedule Offset (diferença de horário de 30 min)** e a clara definição de que o robô do Smart Office opera em modo **Shadow (passivo)** até a conclusão do cutover.

---

### Pergunta 5:
> *"Se o canal principal de notificação e o bot desktop falharem ao mesmo tempo, o que a equipe operacional ainda consegue saber sobre o estado do pipeline?"*

**Resposta Técnica:**  
Mesmo com a queda simultânea do Telegram e do sistema desktop, a operação mantém visibilidade completa através de três camadas redundantes:
1. **Fallback Multicanal:** O `SistemaAlertas` detecta a falha do Telegram (erro 401/timeout) e roteia automaticamente o alerta de erro para o canal secundário (**Email SMTP / WhatsApp**) com o relatório em anexo;
2. **Log Local Estruturado em Disco:** O sistema grava um bloco de emergência destacado em `logs/` com timestamp, erro de infraestrutura e itens afetados;
3. **Dead Letter Queue e DataPool:** Os lotes que não puderam ser conferidos no desktop são marcados com status `PENDENTE_REVISAO_DESKTOP` e registrados na Dead Letter Queue (`data/dead_letter/dead_letter_items.jsonl`), permitindo que a equipe identifique exatamente quais itens exigem conferência física na doca.
