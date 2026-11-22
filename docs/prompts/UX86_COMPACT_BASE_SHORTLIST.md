# UX86 — Cards compactos e shortlist de cidades-base | Prompt de implementação

## Papel e objetivo
Atue como Staff Streamlit Engineer e Senior Product Designer. Substituir a listagem longa e duplicada do modo Cidades sugeridas por cartões legíveis e seleção de alternativas, permitindo comparar 2–3 bases rapidamente sem perder o rigor de evidência. Implementar APÓS UX85 integrado à main.

## Antes de alterar
Auditar HEAD de rec03a_suggestions_ui.py (_card, evidence_examples, render_suggestions, _render_comparison_groups), base_recommendation_model.py (highlight_sections, group, candidates, reasons, evidence), rec03b_handoff_ui.py (render_compare_selection), rec03b_handoffs.py, recommendation_scope_model.py e ux_shared_ui_presentation.py. Checar nomes reais das chaves e escopo; sem derivar ordenação pelo menor tempo ou supostos rankings.

## Componentes e conteúdo proposto
- Área principal 'Cidades que vale investigar', acompanhada de disclaimer curto: sugestões documentais, não escolha oficial.
- Card resumido por cidade: nome/país; referência oficial (quando verdadeiro), motivo em português simples baseado em reason já existente; cobertura exata com N históricos, M indicativos, K locais e U sem tempo, separadamente; 2–3 exemplos por prioridade e fonte/semântica correta.
- Converter frases técnicas longas em português claro SEM trocar o significado de algoritmo: comparação do mesmo conjunto / subconjunto ou apenas evidência disponível. Não proclamar uma 'melhor cidade' quando categorias diferirem ou faltarem dados.
- Mostrar destaques documentais primeiro e depois 'Ver outras cidades' como lista filtrável, sem replicar a mesma base duas vezes na mesma página. Preservar a paginação onde necessária para performance.
- Se a mesma cidade aparece em duas seções do motor, mostrar um card com tags descritivas; não perder classificações, nem recategorizar grupos arbitrariamente.
- Seleção visível no card para a shortlist comparativa; usar projeção ou a seleção REC03B existente (CHOICE e widgets) como única fonte de estado. Evitar outra seleção simultânea em card+multiselect sem sincronização.
- UI padrão: 2–3 selecionadas para uso rápido, até 5 pelo modo avançado, aplicando validação e seleção explícita. NÃO auto-selecionar destinos, NÃO alterar cidade-base oficial, NÃO truncar seleção anterior.
- Ação primária contextual única: 'Comparar cidades selecionadas (N)'; ações secundárias são perfil, mapa e simular, disponíveis em local apropriado, não repetidas por toda a dobra.
- Fontes, datas, divergências e caveats aparecem em 'Ver evidências e limitações' sob demanda. Manter renderização lazy usando checkbox/controle real, não apenas st.expander que renderiza tudo.
- Indicadores devem ter rótulos explícitos (histórico, indicativo, local, sem tempo), nunca cores como único portador de significado.

## Contratos imutáveis
Não modificar REC02 POLICY_VERSION, criteria, weights, categories, evidence_examples por heurística de rapidez, modelos de research, cálculo de média ponderada, TripPlan/ux502_interests.
Preservar ids e callbacks de REC03A e REC03B; se mover o renderer de controles para um componente novo, fornecer wrappers compatíveis e teste dos IDs de handoff.
Sem usar st.button com chave duplicada para cada renderização e sem listas full repetidas de cards.

## Testes
- mesmas candidates/IDs, groups/estatísticas/reasons antes e depois, mesmo número de origens com evidência.
- 0,1,2,3,5,6+ candidatas; sem tempo, local-only, mixed evidence, sem grupo completo, must_visit pendente.
- validar shortlist 2–3 em modo simples e até 5 avançado; filtros não gravam lista nem apagam CHOICE/PREVIOUS.
- card incluído apenas uma vez; não renderizar links de evidência quando collapsed; paginação estável.
- contraste AA e visual 1440/768/390, ordem de tabulação, sem grids que comprimam botões.
- AppTest de seleção, retorno, reload e reconciliação; suíte completa + GitHub Actions no HEAD.

## Entrega
Alterações esperadas em rec03a_suggestions_ui.py, rec03b_handoff_ui.py e testes relacionados; módulo de apresentação puro adicional permitido apenas se necessário. Não implementar comparação ou orçamento antecipadamente. Atualizar a branch com UX85 implementado e integrado antes de editar. PR inicialmente DRAFT apenas com prompt; **sem merge automático**.
