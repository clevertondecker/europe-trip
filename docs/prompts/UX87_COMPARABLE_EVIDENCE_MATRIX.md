# UX87 — Comparação lado a lado e evidências | Prompt de implementação

## Missão
Atue como Staff Streamlit Engineer, Data Quality Engineer, Accessibility Engineer e UX Lead. Transformar uma shortlist REC03B de 2 a 3 cidades (até 5 em avançado) em comparação lado a lado clara, no mesmo fluxo de Explorar > Comparar bases, SEM criar outro algoritmo de ranking nem editor paralelo. Implementar só após UX85 e UX86 integrados à main.

## Leitura obrigatória no HEAD
Revisar rec03a_suggestions_ui.py, rec03b_handoff_ui.py, rec03b_handoffs.py (CHOICE, PREVIOUS, CONTEXT, MANUAL_KEYS), ux503_destination_base_comparison_ui.py, ux503_destination_base_comparison_model.py, routes7_comparison_projection.py, rail_reference_projection_model.py, ux505_base_comparison_presentation.py, ux506_decision_readiness_projection.py, base_recommendation_model.py, rec05_priority_research_ui.py e testes. Conferir a matriz realmente emitida por compare_wishlist_bases() e decorate_comparison(), o scope confirmado por REC02 e a política de categories: historical, reference_only, local e no_time.

## Jornada e hierarquia
1. Após selecionar as bases em UX86, colocar uma seção única 'Compare suas alternativas' logo abaixo da shortlist, sem exigir que o usuário entenda um segundo modo. Manter seleção explícita: o resultado NÃO muda a cidade-base oficial.
2. Mostrar cabeçalho da matriz com o escopo efetivo: N destinos, M cidades; 'Tempos mínimos de ida pesquisados, não tempos totais'. Uma linha por destino e uma coluna por cidade selecionada; prioridades da wishlist exibidas.
3. Cada célula rotulada textualmente: tempo histórico, referência indicativa, acesso local pendente, ou sem tempo pesquisado. Formatar unidade h/min corretamente; NUNCA usar 0 para informação ausente, não inferir viagem de volta ou tarifa, não converter indicativo em histórico.
4. Priorizar por padrão um quadro resumido de cobertura (N histórico, M indicativo, K local, U sem tempo) e a matriz; pesquisa turística, moradia, alertas e detalhes extensos abaixo de uma seção 'Evidências e limitações'.
5. Quando houver grupo completo equivalente, explicar a métrica REC02 existente para bases comparáveis no MESMO conjunto. Quando houver apenas interseção parcial, explicitar destinos omitidos e comparação condicional. Não gerar ranking global, somar trajetos incompatíveis nem concluir 'melhor cidade' por contagem de fontes.
6. Evitar duas matrizes: comparar no modo guiado reutilizando projeções existentes, e manter a comparação manual/avançada acessível para cenários que precisam de edição detalhada. Não copiar nem reimplementar REC01/REC02/UX503 para obter labels diferentes.
7. Aplicar layout responsive: desktop tabela por destinos x bases, mobile cards por destino ou scroll interno com cabeçalho/cidade contextual; nunca rolagem horizontal de toda a página. Atalhos de teclado, texto alternativo e significado não baseado apenas em cores.
8. Histórico de observações, links fonte, datas, transferências, cobertura histórica, pesquisa REC05 e evidência de aluguel devem continuar disponíveis sob demanda usando controls lazy (não montar dezenas de tabelas em st.expander renderizado automaticamente).
9. Se uma cidade foi retirada do escopo, revalidar seleção sem mutar TripPlan ou wishlist. Manter seleção de 2–5, corrigir stale filters de forma explícita; permitir recuperar seleção manual anterior com PREVIOUS.

## Restrições técnicas
- A única seleção exploratória continua em REC03B CHOICE/ux503_bases conforme o contrato definido no UX86. Não introduzir uma terceira seleção persistente em sessão.
- Projeções puras novas são permitidas somente se derivadas de matrizes canônicas, sem alterar semântica de source URLs, gap_checked_at, observation date, display_min, historical/reference_only ou categorias.
- Nunca usar pontos, distâncias, datas ou preços inventados. Falta de evidência não significa impossibilidade de conexão.
- Não modificar schemas, regras de prioridades, autosave privado, UX64, rec04, base_recommendation_model.evaluate_matrix nem TripPlan.

## Matriz de testes
- 2, 3 e 5 bases; 0/1/N destinos; tabela parcialmente preenchida; todas as células no_time; local_only.
- Base histórica vs indicativa; dados divergentes; estações e fontes ausentes; último trecho desconhecido.
- full comparable vs conditional subset vs unavailable: nenhum ranking fictício, contagens consistentes e exclusões visíveis.
- Revisar scope e alternar guiado/manual/restaurar sem perder favoritos, prioridades nem filtros válidos.
- Invariância: N linhas x M colunas, conteúdo de label idêntico às projeções UX503 e URLs preservadas; testes AppTest.
- 1440/768/390 px em navegador real, contraste WCAG AA, nenhum overflow de página e sem loading gigantesco de fontes fechadas.
- python -m compileall -q .; python -m unittest discover -s tests -v; GitHub Actions no HEAD; registrar limitações visuais não verificadas.

## Arquivos e limite de escopo
Prováveis alterações: rec03a_suggestions_ui.py, ux503_destination_base_comparison_ui.py, camada pura de apresentação/projeção opcional e tests/test_rec03a_suggestions.py, tests/test_ux503_destination_base_comparison.py, tests/test_ux505_base_comparison_clarity.py. Evitar refatorar todo o app.py. Não antecipar handoffs do UX88, merge ou trabalho de pesquisa externa.

## Prontidão
PR de especificação em draft. Depois da aprovação do prompt: atualizar branch com UX85/UX86 integrados; implementar, testar e solicitar review. Não fazer merge automático.
