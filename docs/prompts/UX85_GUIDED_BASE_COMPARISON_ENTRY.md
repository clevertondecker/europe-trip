# UX85 — Entrada única e seleção útil de cidades-base | PR #201

> **Status:** implementação funcional do UX85 aplicada nesta branch para revisão. UX86 (#202) está absorvido. A validação automatizada e visual do HEAD final deve ser conferida antes de aprovar o PR.

## Objetivo e critério de simplicidade
Atue como Principal Product Designer, Staff Python/Streamlit Engineer e Accessibility Reviewer. Em **Explorar > Comparar bases**, responder: **"Dos destinos que desejo conhecer, quais cidades-base merecem investigação?"** Mostrar resultados úteis sem wizard, sem escolha de modo e sem duplicar escopo ou seleção.

## Contratos reais a confirmar no HEAD antes da implementação
- `rec03a_suggestions_ui.render_recommendation_activity` ainda inicia `MANUAL` e expõe um radio; `render_suggestions` duplica destaques e cartões completos; `_render_scope` oferece múltiplas CTAs.
- `recommendation_scope_model.confirm_scope/reconcile_scope` é a autoridade para `rec03a_scope`. Novos destinos ativos entram como `pending_ids`, nunca são incluídos automaticamente. Escopo com `state=ready` não precisa de nova confirmação; restauração/identidade inválida exige revisão. Não editar o modelo para simplificar a UI.
- `rec03b_handoffs.CHOICE` (key `rec03a_handoff_base_selection`) representa bases escolhidas; `queue_handoff(kind="manual")/apply_handoff` já transfere **2–5 bases** e destinos do escopo para UX503, com `PREVIOUS` e `MANUAL_KEYS` para recuperar filtros antigos. `profile`/`map` são intenções individuais.
- `app.py` atualmente coloca Ajustes avançados da simulação e Atividades anteriores antes dos resultados, e acrescenta título duplicado em `page == "Comparar cidades"`.
- Reutilizar categorias e motivos `highlight_sections`/`highlight_ids` da REC02 e componentes UX81. **Não calcular novo ranking.**

Auditar novamente os HEADs e testes de REC02, REC03A/B, UX503, UX64 e CSS10 antes de editar.

## P1 — Entrada direta e confirmação mínima
1. Apenas um `page_header` e um resumo compacto de **Temporada europeia · N destinos**; colocar "Editar destinos" e "Minha lista" como ações secundárias próximas ao escopo, não botões verticais repetidos.
2. Se `reconcile_session_scope` indicar `ready`, exibir imediatamente as sugestões. Uma análise de pesquisa **não** é decisão oficial de base.
3. Na primeira visita ou escopo que exija revisão, propor os destinos ativos da wishlist em uma seleção editável, explicar o recorte de temporada europeia e exigir **uma única CTA** `Analisar estes destinos`, delegando a `confirm_scope`. Não inferir destino de temporada por país nem selecionar automaticamente como decisão confirmada.
4. Mudança da wishlist usa `reconcile_scope` exatamente: novos ativos aguardam revisão; removidos não são substituídos; prioridades reconciliáveis não provocam confirmação extra; revisão retrocedida, documento/identidade incompatível não reaproveitam contexto antigo. Não descartar seleções válidas silenciosamente.
5. Em `app.py`, tirar do **caminho visual inicial desta atividade** os expanders globais de ajustes de simulação e atividades legadas, o título duplicado e a duplicação de atalhos. Preservar caminhos legados acessíveis fora da primeira dobra; não mover/destruir suas keys/callbacks ou afetar outras abas.

## P1 — Divulgação progressiva, sem ranking disfarçado
1. Mostrar inicialmente **até quatro** destaques documentais, seguindo a ordem e os grupos originais REC02 (`complete_reference_groups`, `conditional_all_must_identified`, `conditional_must_pending`), sem reordenar por velocidade, pontuação nova, custo ou ordem alfabética apresentada como preferência.
2. O limite é **de exibição**, não de recomendação: sinalizar quantidade de outras candidatas; disponibilizar `Ver todas as cidades (N)` com busca, categorias e paginação existentes. Não esconder cidades selecionadas fora da página atual; manter uma faixa compacta com a seleção ativa.
3. Cada ID de cidade aparece em **um único cartão na renderização corrente** mesmo se houver múltiplos motivos; preservar tags e os `reasons` do motor. Se os destaques REC02 não são sustentados por evidência, **não eleger outros arbitrariamente**; exibir estado de ausência de destaques e permitir explorar o catálogo.
4. Card curto: nome/país, por que consta na pesquisa, cobertura separando **histórico, indicativo, local, sem tempo** e principal lacuna. Se a projeção não oferece separação confiável, não inventar contagens; apresentar a ressalva e aprofundamento por fonte quando solicitado. Não transformar cobertura documental em qualidade logística.
5. Metodologia, referências completas e REC05 ficam acessíveis sob demanda, sem dominar a primeira dobra. Avisos essenciais (tempos mínimos de ida, retorno/2027 não confirmados, ausência de custo real) permanecem visíveis.

## P1 — Seleção que funciona antes do PR #203
**Decisão:** preservar TEMPORARIAMENTE a comparação UX503 já existente, consumindo a seleção do próprio cartão. Essa opção evita nova feature flag, terceira experiência, sistema de estado paralelo ou seleção morta enquanto o PR #203 não estiver integrado.
- Checkbox/controle nativo de cada cartão atualiza unicamente `CHOICE`. Não criar `shortlist`, `selected_bases`, outro multiselect obrigatório nem sincronização bidirecional paralela.
- Uma cidade pode ser investigada individualmente via handoffs REC03B/REC04 já válidos; **duas** permitem comparar e **cinco** é o máximo atual. Não truncar seleções anteriores, nem pré-selecionar bases automaticamente.
- Enquanto somente #201 estiver em `main`, mostrar **uma única CTA contextual** `Comparar N cidades` quando houver 2–5 escolhas; acioná-la encaminha `CHOICE` + escopo confirmado para o UX503 legado usando `queue_handoff(kind="manual")` e `apply_handoff` existentes. **Não mostrar o multiselect antigo novamente na entrada**. A UX503 legada permanece editável e permite recuperar filtros anteriores pelo contrato `PREVIOUS/MANUAL_KEYS`.
- O PR #203 **substituirá somente essa CTA transitória** por comparação automática na mesma atividade. Não será necessário reescrever a seleção de #201.
- Selecionar, desmarcar, abrir cards ou filtrar **não** dispara handoff, simulação ou mutação oficial na renderização. Comparar é pesquisa read-only.

**Alternativa considerada e rejeitada:** publicar apenas cartões selecionáveis sem resultado até o #203. Isso criaria uma promessa vazia entre merges. Publicar ambos simultaneamente atrasaria a melhoria do catálogo sem necessidade; o handoff validado já existe.

## P2 — Limites e compatibilidade
Preservar `rec03a_scope`, `rec03a_draft`, `rec03a_activity`, `rec03a_identity`, `rec03a_navigation_intent`, `CHOICE`, `PREVIOUS`, `MANUAL_KEYS`, `ux503_bases`, `ux503_visible_destinations`, `TripPlan`, UX64, REC01/REC02/REC04/REC05 e contratos de fontes. Os modos `SUGGESTED/MANUAL` continuam internamente para deep links, transição e recuperação, mas **não como radio principal**. Não criar persistência de seleção, novos schemas, novos pesos nem Design System paralelo.

## Testes de aceite verificáveis
- Cold start com wishlist: uma confirmação e resultados; escopo `ready`: zero confirmações e sugestões imediatas; escopo vazio, identidade alterada, restauração incompatível, `pending_ids`, removidos e mudanças apenas de prioridade.
- Catálogo com 0, 1, 4, dezenas de candidatas; destaques inexistentes ou duplicados em vários grupos; busca/paginação preservadas; **não** duplicar o mesmo cartão.
- `CHOICE` conserva seleção fora da página/filtragem; 0,1,2,3,5 e 6 escolhas (limite explicado e não truncado); a mesma seleção chega ao UX503 pelo handoff canônico; `PREVIOUS` restaura filtros manuais.
- Não há segundo multiselect obrigatório na tela de sugestões; antes do #203 a CTA de comparação gera **resultado real** em UX503. Perfil/mapa/simulação de uma cidade não dependem de duas bases.
- Navegação de/para Minha lista, Planejar e Orçamento preserva wishlist, plano e orçamento; nenhum efeito colateral em render/rerun.
- `app.py`: a primeira área útil mostra a tarefa de comparar, não ajustadores gerais, títulos repetidos nem menus legados.
- Comparar, quando possível, a sequência REAL de decisões/CTAs antes e depois com AppTest; não inventar percentual de melhoria.
- `python -m compileall -q .`, `python -m unittest discover -s tests -v`, CI no HEAD; browser 1440/768/390 px, foco/teclado, contraste WCAG AA, disabled, overflow e DOM real; declarar explicitamente se não validado.

## Entrega
Implementar apenas nesta branch **depois da revisão do prompt**, sem alterar algoritmos ou persistência. O #201 deve ser funcional e revisável isoladamente. PR permanece **draft** enquanto só houver documentação. Sem novos PRs ou merge automático.
