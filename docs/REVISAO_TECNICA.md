# Revisão técnica consolidada — Aulas 17, 18 e 19

Data: 2026-07-28

Branch revisada: `feature/page-objects`

Revisor técnico: Codex

## Checklist de aceite

| Item | Resultado | Evidência |
|---|---|---|
| Branch correta criada | Sim | `feature/page-objects` |
| Pasta `src/pages/` criada | Sim | `test/src/pages/` |
| Page Object Playwright criado | Sim | `playwright_pages.py` |
| Page Object Selenium criado | Sim | `selenium_pages.py` |
| Locators centralizados | Sim | Constantes e locators somente nos Page Objects |
| Regra de negócio fora do Page Object | Sim | `test/src/runner.py` |
| Bot executa após refatoração | Sim | `docker compose up --build` |
| Evidências continuam funcionando | Sim | PNG por item e de erro, por ferramenta |
| Logs continuam funcionando | Sim | `test/logs/<ferramenta>/execucao.log` |
| DataPool continua funcionando | Sim | Dez itens e campo `screenshot` por ferramenta |
| README atualizado | Sim | Execução, arquitetura, artefatos e comparação |
| PDD atualizado | Sim | Componentes, sequência, decisões e segurança |
| Sem arquivos gerados no Git | Sim | Regras específicas no `.gitignore` |
| Revisão por pares feita | Sim | Esta revisão técnica consolidada |
| Commit semântico | Sim | `feat(tests): integrar Playwright e Selenium no Docker` |

## Verificações dos formulários

- Selenium consta em `test/requirements.txt`.
- `test/selenium/selenium_automation.py` mantém Selenium separado do fluxo
  principal.
- Selenium usa somente `WebDriverWait`; Playwright usa locators semânticos e
  auto-wait.
- Cada interação usa os dados do item e valida a mensagem final do lote.
- Toda divergência gera log, resultado individual e tentativa de screenshot.
- O destino é restringido ao ambiente local e nenhum dado sensível é usado.
- Playwright e Selenium têm implementações, DataPools, evidências e logs
  comparáveis e separados.

## Síntese

Pontos fortes: orquestração única, baixo volume de código duplicado, Page
Objects específicos por tecnologia, saída rastreável e encerramento seguro do
front-end.

Risco residual: a assinatura formal de um grupo revisor humano, caso exigida
pela instituição, deve ser adicionada ao formulário original. A revisão técnica
do código e da execução foi concluída neste documento.

Recomendação: aprovado para merge.
