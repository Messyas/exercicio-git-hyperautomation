# Auditoria de Robustez, Viés e Calibração do Modelo

**Status:** APROVADO  
**Modelo:** rf-lotes-1.0.0

Este relatório não detecta uma intenção do modelo; ele mede evidências de risco em um classificador tabular.

## Políticas verificadas

| Teste | Resultado | Critério |
| --- | --- | --- |
| integridade_dataset | PASSOU | SHA-256 do dataset confere com o bundle |
| features_sem_proxies | PASSOU | Somente as três features aprovadas estão no bundle |
| calibracao_ece | PASSOU | ECE <= 0.05 |
| confianca_alta | PASSOU | Acurácia em alta confiança >= 0,85 |
| gap_por_turno | PASSOU | Gap de accuracy <= 0.05 |
| contrafactual_turno | PASSOU | Mudança contrafactual <= 0.10 |
| ood_sem_automacao | PASSOU | OOD não gera ação automática de alta confiança |

## Métricas

- ECE: 0.0114
- Cobertura de alta confiança: 49.75%
- Gap máximo de accuracy por turno: 3.17%
- Mudança contrafactual de classe ao variar somente o turno: 0.00%
- Casos OOD com ação automática de alta confiança: 0

## Limitações

Os dados são sintéticos. Uma auditoria real deve usar dados históricos representativos, grupos relevantes ao negócio, monitoramento de drift e revisão humana dos alertas.
