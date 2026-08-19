# Resultado do ensaio de carga e sabotagem da API de ML

**Data e hora da execução:** 19/08/2026 09:09 (America/Manaus)  
**Cenário:** Compose isolado `sabotagem-ml`, com a API limitada a 256 MB de
RAM e 0,5 CPU. A API foi derrubada deliberadamente após a primeira fase de
carga.

## Configuração executada

| Parâmetro | Valor |
| --- | ---: |
| Requisições solicitadas | 1.000 |
| Workers concorrentes | 16 |
| Tamanho máximo da fila | 64 |
| Timeout por requisição | 500 ms |
| API | `http://127.0.0.1:8001` |
| Sabotagem | `docker compose kill api-ml` após 100 requisições |

## Resultado

| Indicador | Resultado |
| --- | ---: |
| Itens processados | 1.000 / 1.000 |
| Sucessos antes da queda | 100 |
| Fallbacks `REVISAO_ML_OFFLINE` | 900 |
| Decisões com circuit breaker aberto | 896 |
| Primeiro fallback | item 101 |
| Fallbacks que ainda tentaram a rede antes da abertura | 4 |
| Latência P50 | 1,21 ms |
| Latência P95 | 425,80 ms |
| Latência média | 46,81 ms |
| Latência máxima | 495,17 ms |

As validações de contrato também passaram: `turno` inválido, campo extra e
booleano coagido receberam HTTP 422.

## Conclusão

O ensaio terminou sem perda de itens. Após a indisponibilidade real da API,
o cliente aplicou o fallback `REVISAO_ML_OFFLINE`; depois das falhas
consecutivas, o circuit breaker passou a evitar novas tentativas de rede. O
resultado demonstra que a interrupção do serviço não interrompe o
processamento do lote.

O dado bruto completo está em
[ensaio_sabotagem_carga.json](ensaio_sabotagem_carga.json).
