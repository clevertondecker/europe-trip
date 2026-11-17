# ARCH 1.0b — Contratos documental e ferroviário

Este PR implementa um relatório auditável, **sem alterar o cálculo de documentação**.
A matriz `base_coverage_model._dataset_routes()` escolhe fontes para 15 destinos,
preservando amostras de frequência, conexões e tarifa histórica. A função
`get_rail_evidence()` escolhe uma evidência de apresentação com sua própria
precedência, e ambas podem divergir legitimamente.

`documentary_rail_parity()` compara os 30 × 15 pares, duração mínima,
URL de origem, disponibilidade de frequência/conexão e quantidade de
observações na camada compartilhada. O retorno `safe_to_migrate_without_review`
exige igualdade de tempo **e** fonte em todos os pares; mesmo essa igualdade
não autoriza eliminar critérios documentais distintos sem uma auditoria de flags.

Escopo: investigação e proteção de compatibilidade; nenhuma alteração em
`coverage_matrix()`, TripPlan, pesos, decisão final, fontes originais ou UI.
Próxima ação depois da revisão: migrar apenas indicadores equivalentes
documentados, em PR separado se houver mudanças de resultados.

## Resultado concreto da auditoria — 17/11/2026

Execução da suíte do PR #94, 30 bases × 15 destinos:

| Métrica | Total |
|---|---:|
| Pares examinados | 450 |
| Tempo e fonte idênticos | 449 |
| Tempos diferentes | 1 |
| Fontes diferentes | 1 |
| Migração automática segura | Não |

A divergência é **Lille → Luxemburgo** (`lille` →
`luxembourg_city`). A matriz documental não possui tempo ou URL
para esse par, enquanto `get_rail_evidence()` encontra
**231 minutos históricos de ida**, fonte
`https://www.sncf-connect.com/en-en/train/route/lille/luxembourg`.

**Causa:** conjuntos de fontes e políticas de seleção distintos entre
a matriz documental legada e o adaptador unificado. A observação adicional
é válida como referência histórica para descoberta; não comprova retorno,
custo total ou uma viagem de 2027.

**Conclusão:** NÃO migrar silenciosamente os critérios documentais.
Primeiro decidir se a evidência deve compor a cesta de 15 destinos e
avaliar impacto em frequência, trocas, tarifas e percentuais. Os testes
agora detectam uma divergência artificial injetada (tempo e URL), além
de proteger os números reais desse snapshot. Evidência em
`ARCH10B_AUDIT_JSON` nos logs do CI do PR #94.
