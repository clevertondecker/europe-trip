# UX87 revisado — Comparação contínua e ações contextuais | PR #203

> **Escopo consolidado:** UX87 + UX88 (antigo PR #204). Esta especificação substitui a sequência "abrir comparação manual → escolher novamente → simular". É um **PR de implementação futura**; o único PR anterior obrigatório é **#201 / UX85 revisado**.

## Papel e objetivo
Atue como Staff Streamlit Engineer, Principal Product Designer, Finance UX Engineer, Accessibility Reviewer e Data Quality Engineer. Na aplicação `clevertondecker/europe-trip`, fazer a comparação aparecer **dentro da mesma atividade Explorar > Comparar bases**, sem nova configuração, preservando a integridade dos dados. Permitir consultar uma cidade individualmente e simular custos **sem exigir comparação com outra cidade**.

**Meta observável:** o usuário escolhe duas cidades nos cards já disponíveis (PR #201), vê imediatamente uma matriz compreensível e pode ajustar cidades sem recomeçar nem selecionar os mesmos destinos novamente.

## Dependência / auditoria obrigatória
- Implementar **depois** de #201 integrado à `main`, atualizando esta branch com a fundação UX85+UX86 consolidada.
- Auditar no novo HEAD `rec03a_suggestions_ui.py`, `rec03a_session.py`, `rec03b_handoff_ui.py`, `rec03b_handoffs.py`, `ux503_destination_base_comparison_ui.py`, `ux503_destination_base_comparison_model.py`, `rail_evidence_unified_model.py`, `rail_pair_projection_model.py`, `base_recommendation_model.py`, `rec05_priority_research_ui.py`, `rec04_simulation_handoff.py`, `rec04_simulation_ui.py`, `rec04_candidate_capabilities.py`, `ux64_navigation_model.py`, `ux_shared_ui_presentation.py` e `app.py`.
- Verificar a semântica de evidências das projeções REC02 e UX503: **não** assumir que contagens de cobertura ponderada REC02 equivalem às métricas de linhas ferroviárias UX503. Não reutilizar renderização manual extensa quando isso exigir mais um filtro.

## Jornada de interface (sem segundo modo)
1. O header, escopo REC02, cards e seleção `CHOICE` vêm do **#201**. Este PR **não renderiza um segundo cabeçalho, segundo filtro de destinos nem outro multiselect**. A comparação ocupa o espaço imediatamente abaixo da seleção.
2. **0–1 base selecionada:** não exibir matriz vazia; comunicar "Selecione outra cidade para comparar" de forma discreta, mantendo **perfil, mapa e custo da única cidade** acessíveis se a capability permitir.
3. **2–5 bases selecionadas:** renderizar automaticamente a comparação read-only, na mesma página e escopo, sem CTA "Substituir filtros e comparar", `queue_handoff(kind="manual")` obrigatório ou navegação até uma segunda interface. Seleções alteradas atualizam apenas projeção visual. Debounce/caching puro é permitido se necessário; não gravar decisão por renderização.
4. **Escopo:** utilizar EXATAMENTE `rec03a_scope["destination_ids"]` após `reconcile_scope()` indicar `ready`. Não recorrer a todos os destinos ativos da wishlist nem ao filtro UX503 antigo silenciosamente; não inferir país ou estágio. Se o escopo está stale/invalidado, suspender a matriz e solicitar revisão no bloco já existente do #201.
5. **Matriz:** uma linha por destino considerado, uma coluna por base selecionada; prioridade da wishlist ao lado do destino; cada célula expressa textualmente `histórico`, `referência indicativa`, `local/acesso a verificar` ou `sem tempo pesquisado`, juntamente com tempo mínimo de ida quando realmente existente. Retorno/frequência/última milha/tarifas/2027 seguem não confirmados.
6. **Projeção canônica:** reutilizar, após checar compatibilidade de catálogos, `compare_wishlist_bases(..., discovery=..., research=..., visible_destination_ids=scope_ids)` (2–5 bases) ou `build_wishlist_matrix` do UX503. Fornecer o mesmo catálogo de exploração e pesquisa compatível com REC02, inclusive destinos suplementares. Não criar novo cálculo de rotas, média ou cobertura. Se a projeção REC01/REC02 divergir legitimamente, identificar a diferença ao usuário sem combiná-las.
7. **Resumo responsável:** antes da tabela, mostrar apenas um quadro pequeno de cobertura por base (histórico, indicativo, local, sem tempo), usando categorias e unidades separadas. Comparações "complete" versus "conditional" preservam explicitamente o conjunto comparado e os destinos excluídos. Não gerar rank global, "ganhadora", economias financeiras ou equivalência entre evidência documental e viabilidade.
8. **Mobile:** desktop pode mostrar tabela por destinos × bases; em 768/390 px escolher scroll **interno** com cabeçalhos legíveis, ou cards por destino. Nenhuma rolagem horizontal da página inteira, nomes truncados sem acesso, ou células somente por cor. Legenda e alerta mínimo permanecem visíveis.
9. **Fontes sob demanda:** mostrar referência e categoria básica no contexto do dado; links, datas, observações divergentes, metodologia REC02/UX503, pesquisa REC05 e habitação podem expandir ao pedir, com avaliação lazy para não montar toda a pesquisa atrás de expanders fechados.

## Ações contextuais (UX88 absorvido)
10. Para **uma cidade em foco**, permitir "Conhecer cidade", "Ver no mapa" e "Simular custo" como ações secundárias em menu/área de detalhe contextual — não repetir 3 botões em cada card e ao final da matriz. Não criar um botão obrigatório de "Concluir comparação". A possibilidade de investigar uma só cidade **não depende de selecionar duas**.
11. Usar `rec03b_handoffs.queue_handoff/apply_handoff` para perfil e mapa, e `rec04_simulation_handoff.request_simulation/apply_simulation_request` para orçamento. Cada intenção requer clique explícito, validação de escopo, identidade e cidade. Verificar `capability_for(...)` antes de oferecer/acionar simulação: `scenario_selectable`, `detailed_budget_supported`, `official_plan_supported` são conceitos distintos.
12. Em Orçamento > Simulações, o contexto deixa explícito **"simulação exploratória"**, `base_city` oficial inalterada, informação de custo específica ausente quando for o caso e despesas desconhecidas, sem R$ 0 inventado. Manter `unified_scenario`, `unified_style`, `budget_cap_confirm`, `scenario_base_selected`, `ux_mode`, `unified_override_rent` e REC04 context.
13. "Voltar à comparação" recupera a mesma seleção `CHOICE` e escopo validado **durante a sessão**, tanto após perfil/mapa quanto após simulação. Se plano, identidade ou wishlist tornaram o contexto inválido, mostrar explicação e propor nova revisão, sem reutilizar estado antigo.
14. É permitido sair a qualquer momento para Minha lista, Meus destinos, Organizar ou Orçamento. Não exigir escolha oficial da base nem datas no roteiro. Montagem/salvamento continuam canônicos por REC03B/UX83; não inserir automaticamente destinos nem decidir uma base.
15. Evitar CTA primária concorrente: seleção 0–1 oferece ações individuais, seleção 2+ destaca comparação **já visível**; a simulação é contextual ao item focado, não "próxima etapa obrigatória". Não ressuscitar a navegação manual extensa por trás de uma CTA enganosa.
16. Recuperação de filtros manuais legados: `PREVIOUS`, `MANUAL_KEYS`, `ux503_bases` e `ux503_visible_destinations` permanecem íntegros; acesso avançado legítimo continua possível, mas o caminho principal não sobrescreve filtros por simples seleção de base.

## Invariantes técnicos
- Fonte única de seleção: `rec03b_handoffs.CHOICE` fornecida pelo PR #201, não um novo `shortlist`, `selected_bases` paralelo ou estado persistente. O escopo `rec03a_scope` mantém confirmação explícita para destinos.
- Sem mudança em `TripPlan`, `advisor_plan`, `ux502_interests`, favorites, `budget_scenario`, arquivo privado ou `base_city` oficial ao selecionar/comparar/simular. Atualização oficial requer caminho canônico independente e confirmação.
- Sem alterações em algoritmos de REC01/REC02, sua metodologia, datas de fonte e categorias `historical`, `reference_only`, `local`, `no_time`. Mínimo de ida não é deslocamento de ida e volta; ausência de evidência não significa ausência de transporte.
- Sem nova navegação pública, schema, wizard, camada financeira paralela ou biblioteca CSS concorrente. Usar componentes UX81; botões precisam ser Streamlit nativos com callbacks.
- Minimizar diffs: preferir renderização/projeção read-only e ajustes pequenos em REC03A/B e REC04; não reestruturar todo `app.py`.

## Matriz de testes de aceitação (bloqueante)
A. **Fluxo mais curto:** com escopo pronto e duas cidades selecionadas, a matriz aparece sem clique extra; troca de cidade atualiza colunas, não datas nem roteiro.
B. **Uma cidade:** perfil/mapa/simulação acessíveis sem seleção adicional; ausência de capability não oferece preço/CTA falso.
C. **Escopo:** first-time confirm, valid resume, novo destino pendente, exclusão, prioridade alterada, revisão/reconciliação, identidade alterada; visualização não usa scope stale.
D. **Evidência:** 2,3,5 cidades; ausência ou divergência de dados, referência indicativa, local-only, "sem tempo", subconjunto condicional, empate e destinos excluídos; comparar só o que é comparável.
E. **Handoffs e retorno:** REC03B profile/map/planning, REC04 simulation/return_to_source/return_to_official, recuperar `CHOICE` e `PREVIOUS`, evitar duplicate keys e contexto de conta antiga.
F. **Invariância financeira:** custo desconhecido permanece não verificado; simulação nunca altera teto nem base oficiais. Fórmulas, cotações, histórico e cenários 60k/70k intactos.
G. **UI/QA:** um header, apenas seleção única, sem botão redundante de comparação, estado de foco/hover/disabled, navegação teclado, zero-state, mobile 390, tablet 768 e desktop 1440 px, sem overflow horizontal global. Inspeção em navegador **real** ou declarar explicitamente pendente.
H. **Gates:** `python -m compileall -q .`, `python -m unittest discover -s tests -v`, testes AppTest de ponta a ponta, GitHub Actions no HEAD e diff adversarial de UX82/UX83/UX84.

## Entrega
Implementar na **branch existente do #203**, somente após #201 estar integrado. Atualizar o prompt se a inspeção do HEAD mostrar contratos diferentes. Não criar PR novo, não implementar o #204 separadamente, não fazer merge automático e não chamar pipeline de documentação de validação funcional.
