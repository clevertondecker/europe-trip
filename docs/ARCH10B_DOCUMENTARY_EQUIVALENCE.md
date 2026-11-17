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
