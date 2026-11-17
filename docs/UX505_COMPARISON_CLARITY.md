# UX 5.0.5 — Clareza e interpretação do comparador

## Diagnóstico

O comparador da UX 5.0.3 é **exploratório**, não um recomendador: a mesma cesta de destinos é comparada nas cidades-base escolhidas manualmente. A implementação existente preserva `TripPlan.base_city` e usa `get_rail_evidence()`, mas o título antigo sugeria escolha da melhor base, e a seção principal expunha métricas de pesquisa sem interpretação.

A imagem compartilhada pelo usuário serviu de referência para hierarquia; esta entrega mantém componentes nativos Streamlit e não copia seu layout/CSS.

## Mudanças propostas e implementadas

- Título passa a **Como seria visitar nossos destinos a partir de cada cidade?**, com subtítulo explicando dados históricos e escolhas manuais.
- Seletor de 2–5 cidades-base e filtro visual de destinos continuam com as mesmas chaves `ux503_bases` e `ux503_visible_destinations` e regras originais.
- `ux505_base_comparison_presentation.py` é uma projeção **pura** sobre o resultado existente de `compare_wishlist_bases()`, sem chamar novos serviços ou alterar domínio. Conta combinações, tempos documentados, ausência de tempo identificado e deslocamentos locais; produz rótulos fiéis a casos parciais/divergentes e achados **estritamente descritivos**.
- Resumo interpretativo vem antes da matriz, com ênfase explícita de que **cobertura documental não é qualidade logística**.
- A matriz mantém a mesma estrutura `Destino · prioridade` × cidades-base e dados originais. A terminologia é mais clara, distinguindo: tempo histórico, local, parcialmente pesquisado e sem pesquisa.
- Achados e pendências aparecem após a matriz; dados detalhados (fonte, datas, transferências, divergências, moradia histórica e condições não verificadas) permanecem disponíveis num único expander.
- Nenhum ranking, vencedor, dado ferroviário novo, tarifa 2027, alteração oficial ou escrita remota.

## Restrições preservadas

Não houve mudança em `compare_wishlist_bases()`, `get_rail_evidence()`, `trip_plan_model.py`, `planning_store.py`, persistência, backups, lista de desejos, favoritos ou comparação avançada. Não alteramos como os indicadores do modelo são calculados: as métricas exibidas apenas agregam as linhas resultantes.

## Testes e limitação visual

Testes unitários e AppTests cobrem vazio, desejos ativos, evidências parciais, locais, divergentes, nenhum tempo histórico, navegação e preservação de `TripPlan` e interesses. A inspeção visual real em desktop/mobile não é afirmada a menos que um navegador seja efetivamente usado. CI é verificado no HEAD do PR, sem merge nem deploy automático.
