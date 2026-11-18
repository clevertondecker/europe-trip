# ARCH — Projeção ferroviária compartilhada (F-04)

**Escopo:** refatoração mínima, preservando todos os contratos e rótulos públicos.

## Antes

`dq32_macro_opportunities_model.opportunity_overview()` importava
`routes7_comparison_projection.decorate_comparison()`, criando uma dependência
de um modelo de domínio DQ3.2 sobre um módulo de projeção com ownership UX503.

## Agora

A única implementação de precedência e rótulos reside em
`rail_reference_projection_model.decorate_comparison()`, um módulo puro de
projeção read-only sem Streamlit. DQ3.2 passa a importá-lo diretamente.
`routes7_comparison_projection.py` é uma **fachada de compatibilidade**:
os imports existentes, incluindo `format_minutes` e a função de cache, continuam
resolvendo para os mesmos objetos Python. Os consumidores UX503 não precisam
ser alterados.

**Sem alterações** em datasets, tempos, fontes, critérios de confiança,
separação entre histórico/indicativo/local/não pesquisado, orçamento, retorno,
`TripPlan`, favoritos, estado de sessão ou layout.

## Testes

- Identidade de funções na fachada e no módulo compartilhado.
- Paridade em três categorias e imutabilidade do input.
- Mesmo resultado para Strasbourg → Karlsruhe na DQ3.2 e na fachada antiga.
- Executar CI completo para cobrir compatibilidade, AppTests e imports dinâmicos.

## Pendências não resolvidas neste PR

- **F-05:** DQ3.2 pode misturar `rail`/`exploration` injetados com defaults
  ROUTES7/DATA9 sem identidade conjunta de snapshot. A próxima etapa deve
  introduzir um contexto explícito de evidências carregadas/validadas por versão.
- **ARCH10B:** preservar política documental própria em `base_coverage_model`
  até reconciliar Lille → Luxembourg City, em vez de forçar equivalência.
- A projeção compartilhada ainda formata rótulos para duas telas; separá-los
  da estrutura tipada exigiria revisão de APIs e não é necessário neste patch.
- Os tempos de ida históricos não comprovaram retorno ou viabilidade 2027.
