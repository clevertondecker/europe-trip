# UX82 — Padronização visual de Explorar | Prompt de implementação

## Papel e objetivo
Atue como Staff Streamlit Engineer + Principal Product Designer. Modernizar as quatro atividades de Explorar com o Design System compartilhado do UX81 e o padrão visual aprovado no PR #196, mantendo a descoberta e os filtros funcionais. Não redesenhar a arquitetura de navegação.

## Dependência
Implementar depois do UX81. Atualizar a branch a partir de main com UX81 integrado e reutilizar seus componentes, tokens e contratos. Não criar componentes quase idênticos nem um CSS próprio de Explorar sem necessidade demonstrada.

## Telas reais / módulos a auditar
- Explorar > Descobrir — ux501_destination_discovery_ui.py (render_independent_destination_discovery) e ux502_destination_interests_ui.py.
- Explorar > Minha lista — ux502_destination_interests_ui.py (render_wishlist).
- Explorar > Comparar bases — ux503_destination_base_comparison_ui.py, ux505_base_comparison_presentation.py, ux506_decision_readiness_projection.py e seus serviços.
- Explorar > Mapa — rota pública em ux64_navigation_model.py / app.py; localizar o renderer real antes de editar.
- Navegação pública: ux64_navigation_ui.py, ux64_navigation_model.py e filtros salvos em ux502_discovery_filters.

## Requisitos por tela
### Descobrir
- Cabeçalho idêntico ao contrato UX81; KPI cards compactos de destinos/atrações/países derivados de discovery.
- Agrupar país, experiências e busca numa toolbar responsiva sem retirar filtros nem alterar chaves ux501_*.
- Dar prioridade à fotografia/licenciamento/fallback, à descrição das atrações e ao único CTA contextual "Adicionar à minha lista" por card.
- Preservar estado temporário ux501_interest_session e distinguir claramente seleção temporária de wishlist persistida.
- Não colocar banner gigante acima das fotos nem tornar os cards irreconhecíveis.

### Minha lista
- Cabeçalho, status real de salvamento privado e KPIs de prioridades consistentes com UX81.
- Card contextual de próxima ação: montar roteiro quando houver elegíveis; revisar rascunho quando houver incluídos; descobrir compatíveis quando todos forem exploratórios.
- Somente uma ação primária por contexto; comparação e cidades-base como ações secundárias.
- Respeitar revisões, importação/exportação, conflitos e ux502_private_saved_revision / ux36_cloud_dirty; nenhum sucesso falso.
- Não alterar dados de ux502_interests, nem inclusão confirmada, nem o handshake flow_journey_from_wishlist.

### Comparar bases
- Cabeçalho e resumo compacto; priorizar a própria matriz e os filtros de 2 a 5 cidades-base.
- KPIs de evidência distinguem histórico, referência indicativa, desconhecido e deslocamento local, sem equivaler "sem tempo" a 0.
- Usar os mesmos cards/typography/status do UX81, sem eleger cidade vencedora ou promover estimativas a fatos.
- Preservar filtros ux503_bases, ux503_visible_destinations, shadow state, referências e fluxo de volta à lista.
- Respeitar modo read-only e desempenho; tabelas complexas com overflow contido no componente e acesso por teclado.

### Mapa
- Cabeçalho compacto de UX81 + legenda e filtros acessíveis; mapa é o conteúdo central.
- Evitar KPIs ou banner que empurrem o mapa para fora da primeira dobra.
- Preservar markers, status, zoom/centro, seleções e callbacks existentes. Não inventar rotas/tempo/distâncias.
- Ações secundárias de navegar para uma ficha/lista; dados sem geocoordenadas com fallback textual legítimo.

## Regras transversais e experiência
- A mesma família de header, KPI, card, section heading, status e CTA do UX81.
- Hero forte apenas se agregar clareza; nas telas densas usar próximo passo compacto.
- Uma ação primária por contexto e status em texto, WCAG AA >= 4,5:1, foco visível, keyboard, contraste de hover e disabled.
- 1440/768/390 px: filtros empilham, cards adaptam sem largura fixa, grid de fotos não quebra, mapa não gera scroll horizontal da página.
- Zero-state: lista vazia, apenas exploratórios, nenhuma cidade elegível, nenhuma pesquisa/mapa disponível, fontes ausentes.
- Não renomear atividade pública, não duplicar roteador, não alterar schema / TripPlan / persistência.

## Testes e entrega
Testar transição Descobrir -> Minha lista -> Comparar bases -> Mapa e retorno; filtros antes/depois da navegação; adicionar/retirar interesses; casos de cloud save e conflito; matriz read-only; fallback de fotos e mapas; foco e UI no mobile. Testes AppTest não provam layout, exigem evidência real em browser ou pendência declarada.

Executar python -m compileall -q ., python -m unittest discover -s tests -v e CI no HEAD; revisar diff e corrigir regressões. Implementar código nesta branch, não somente design. Manter PR como draft até testes. Não fazer merge automático.

---

## Reconciliação de fluxo e precedência (obrigatória)

**Estado atual:** PR somente de especificação. O código de \`ux502_destination_interests_ui.render_wishlist\` **já usa** \`project_planning\` para escolher o CTA contextual \`flow_journey_from_wishlist\`. Preservar essa regra canônica e NÃO construir uma nova função \`next_action\` que compute elegibilidade ou substitua \`project_planning\`. O componente UX81 recebe apenas copy/variant/estado projetado.

Sequência a cobrir explicitamente:
1. \`Descobrir → Minha lista → Descobrir\`: \`ux501_interest_session\` temporário, \`ux502_discovery_filters\` e \`ux502_interests\` permanecem coerentes; sem autosave implícito.
2. \`Minha lista → Montar roteiro → Revisar\`: só destino elegível entra em \`TripPlan\` após confirmação explícita; dados exploratórios permanecem exploratórios; \`flow_journey_from_wishlist\` e salvar privado continuam com callbacks/keys originais.
3. \`Comparar bases → Minha lista\`: filtros de \`ux503_bases\` e \`ux503_visible_destinations\` não reescrevem a wishlist; comparação permanece read-only.
4. \`Mapa\`: usar a rota real e mapa real da \`main\` antes de editar; visual compactado sem ocupar a área principal com hero/KPIs.
5. Evitar dois headers, status contraditórios e duas CTAs primárias na mesma viewport. Manter a consistência de \`page_header\`, \`kpi_cards\`, \`section_heading\` e variantes do UX81.

**Bloqueio:** implementar apenas com UX81 integrado à \`main\`; revisar HEAD, atualizar branch e manter draft até testes no HEAD. Não fazer merge automático.
