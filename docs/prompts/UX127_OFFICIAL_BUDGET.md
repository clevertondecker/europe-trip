# UX127 — Um número oficial de orçamento, simulação só em Simulações

## Contexto
QA desktop de 24/11/2026 apontou contradição: Planejar → Visão geral mostrava R$ 71.209 e margem −R$ 1.209; Orçamento → Visão financeira mostrava R$ 69.683,18 e margem +R$ 316,82. Investigar no HEAD atual e reproduzir antes de corrigir. Números acima são observações, não resultados esperados hardcoded.

## Escopo
- Uma projeção oficial compartilhada baseada em calculate_scenario + known_excursions_overage_brl, usando as premissas e cenário oficiais vigentes. Todos os resumos oficiais devem consumir o mesmo total, margem e estado de completude; despesas desconhecidas permanecem desconhecidas.
- Simulações somente em Orçamento → Simulações; preservar advisor_projection e seus consumidores legítimos. Separar estado, KPIs, deltas e rótulos da simulação dos números oficiais. Não aplicar cenário hipotético automaticamente ao planejamento.
- Auditar Planejar, Orçamento → Visão financeira e Simulações, componentes de resumo e mensagens de teto; distinguir valores parciais de previsão completa. Formatação monetária consistente e arredondamento apenas na apresentação. Evitar duplicar cards ou introduzir nova navegação.
- Executar em três commits/revisões lógicas: A projeção oficial e testes; B isolamento das simulações; C acabamento visual e regressão integrada. Dividir em PRs dependentes somente se a auditoria demonstrar necessidade, sem publicar estado contraditório intermediário.
- Não mudar planilha, premissas, teto, cenário oficial, TripPlan, cotações, datasets de pesquisa, regras financeiras ou persistência. Não interferir em DATA24/UX125/UX126B.
## Aceite
Reproduzir o caso original, testar plano vazio e com passeios, alterações legítimas do plano e simulação ativa/inativa, margem positiva/negativa, fontes e valores desconhecidos. Testar paridade exata entre telas, isolamento da simulação e ausência de mutação. Rodar suíte e CI no HEAD exato; QA visual real quando disponível, declarar limitações. Manter draft até revisão, sem merge sem autorização específica.
## Prioridade
Após validação UX126B (#254), antes de DATA24A. Independente da DATA24.
