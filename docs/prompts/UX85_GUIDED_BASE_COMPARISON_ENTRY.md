# UX85 revisado — Uma entrada, cidades sugeridas e seleção direta | PR #201

> **Escopo consolidado:** UX85 + UX86 (antigo PR #202). Esta versão substitui o fluxo guiado em etapas, o modo manual como escolha principal e a proposta de criar uma shortlist separada. **É uma especificação para implementação futura, não código implementado.**

## Papel e objetivo
Atue como Principal Product Designer, Staff Python/Streamlit Engineer e especialista em acessibilidade. No repositório \`clevertondecker/europe-trip\`, torne **Explorar > Comparar bases** compreensível sem conhecer REC02, REC03A ou o conceito de "modo personalizado".

**Meta observável:** alguém com destinos já escolhidos deve conseguir ver quais cidades-base vale investigar e por quê, sem escolher entre modos nem repetir uma confirmação válida.

## Evidências do HEAD auditado (2026-11-22)
- \`rec03a_suggestions_ui.py\` usa \`st.radio("Tipo de comparação", ACTIVITIES)\`, inicializa \`MANUAL\` para novas sessões, traz múltiplos controles em \`_render_scope\` e repete cidades em destaques/listagem.
- \`rec03b_handoff_ui.render_compare_selection\` possui um segundo \`st.multiselect\` e uma CTA para entrar na comparação manual. \`rec03b_handoffs.CHOICE\` já guarda a seleção de cidades.
- \`app.py\` (no HEAD auditado) mostra "Ajustes avançados da simulação" antes das abas, "Atividades anteriores · avançado" antes dos resultados e um título duplicado em \`page == "Comparar cidades"\`.
- \`recommendation_scope_model.confirm_scope/reconcile_scope\` preserva um contrato necessário: novos destinos da wishlist não entram em escopo confirmado sem aprovação; alterações de prioridade existentes podem reconciliar sem nova pergunta.
- O resultado REC02 é orientação de pesquisa, NÃO um ranking global de viabilidade, de custo ou uma cidade oficialmente escolhida.

**Audite novamente o HEAD do PR ao implementar**. Inspecione \`rec03a_suggestions_ui.py\`, \`rec03a_session.py\`, \`rec03b_handoff_ui.py\`, \`rec03b_handoffs.py\`, \`recommendation_scope_model.py\`, \`base_recommendation_model.py\`, \`ux503_destination_base_comparison_ui.py\`, \`ux64_navigation_model.py\`, \`ux_shared_ui_presentation.py\`, \`app.py\` e os testes REC03A/REC03B/UX503/UX64.

## O fluxo obrigatório (SEM wizard)
1. A atividade **Comparar bases** exibe **um só** \`page_header\` UX81, uma frase sobre a pesquisa e um resumo compacto dos destinos considerados.
2. **Escopo já confirmado e reconciliado (\`ready\`):** mostrar imediatamente as cidades candidatas. **Sem** novo formulário, "Continuar", rádio de modo ou confirmação.
3. **Primeiro acesso ou escopo inválido:** propor visualmente os destinos ativos da wishlist em uma seleção editável (não confirmar automaticamente). Explicar que a pesquisa considera somente essa seleção e que ela não altera o roteiro. **Uma única CTA** "Analisar estes destinos" chama o \`confirm_scope()\` existente. Não selecionar implicitamente a etapa por país ou inferir que Itália/França são equivalentes ao estágio \`europe_season\`.
4. **Wishlist modificada:** \`reconcile_scope()\` decide. Novos ativos aparecem como **pendentes de revisão**, sem entrar silenciosamente; removidos saem do escopo sem inclusão de substitutos; somente alteração de prioridade não deve exigir uma nova confirmação sem necessidade. Identidade/documento incompatível invalida a análise. Exibir uma ação para revisar as mudanças, sem descartar silenciosamente escolhas válidas.
5. **Resultados:** cada cidade aparece **uma única vez**, incluindo aquelas presentes em múltiplos destaques REC02. Ordem/grupos obedecem às projeções existentes, sem criar score, ranking ou "cidade vencedora" por contagem de fontes.
6. Card compacto por cidade: (a) nome e país; (b) justificativa curta fundamentada no motivo existente; (c) presença de evidência como **histórico, indicativo, local e sem tempo** separadamente; (d) principal lacuna de pesquisa; (e) controle de **selecionar para comparar**. Tempos e fontes detalhados ficam disponíveis na comparação ou no detalhe contextual, sem ocultar a ressalva essencial.
7. **Selecionar cidades no próprio resultado** com \`rec03b_handoffs.CHOICE\` como única seleção de bases. A mesma escolha alimentará a matriz do UX87 (PR #203). Não criar estrutura \`shortlist\` adicional, segundo multiselect obrigatório, novo state manager nem cópia da seleção no TripPlan.
8. A seleção de **uma cidade** já permite explorar perfil, mapa ou simulação pelo handoff canônico (aprimoramento final no PR #203). **Duas cidades** bastam para habilitar a comparação; até **cinco** pelo contrato de comparação existente. Não exigir três; não truncar uma seleção anterior de 4–5. Não disparar comparação/simulação como efeito colateral de renderização.
9. A experiência principal usa um único conjunto de resultados; **não expor radio público entre SUGGESTED/MANUAL**. Preservar \`ACTIVITY\`, \`MANUAL\`, \`SUGGESTED\`, \`rec03a_activity_widget\`, handoffs e seleção manual anteriores como **compatibilidade interna**, com retorno/recuperação explícitos se aplicáveis; não transformar "personalizada" em uma segunda jornada obrigatória dentro de expander.
10. **\`app.py\` faz parte do escopo:** remover títulos duplicados e impedir que "Ajustes avançados da simulação", "Atividades anteriores · avançado" e outros blocos técnicos apareçam ANTES dos resultados de Comparar bases. Preservar acesso às ferramentas legadas quando requisitadas, mas não mantê-las no caminho principal nem criar mais um menu genérico de controle.
11. Ações de retorno à wishlist e edição dos destinos ficam junto ao contexto do escopo, sem botões verticalmente repetidos. Pesquisa REC05 e metodologia podem estar abaixo dos resultados; manter avisos essenciais à vista, não esconder toda a incerteza.

## Contratos de estado e de arquitetura — não negociáveis
- \`TripPlan\`, \`ux502_interests\`, revisões de wishlist, \`advisor_plan\`, fontes e orçamento oficial são somente leitura durante pesquisa e seleção de cidades.
- Preservar \`rec03a_scope\`, \`rec03a_draft\`, \`rec03a_activity\`, \`rec03a_navigation_intent\`, \`rec03a_identity\`, \`rec03a_handoff_base_selection\` (\`CHOICE\`), \`CONTEXT\`, \`PREVIOUS\`, \`MANUAL_KEYS\`, \`ux503_bases\` e \`ux503_visible_destinations\`, sem novos IDs que representem a mesma seleção.
- Respeitar \`confirm_scope()\`, \`reconcile_scope()\`, REC02 e UX64; não alterar \`TARGETS\`, classes de evidência, pesos, cálculo de mínimos, URLs de fonte ou prioridades.
- Se o modo manual legado possuir filtros diferentes, não sobrescrever nem perder filtros salvos. Preservar \`PREVIOUS\` e o caminho de recuperação.
- Mudança de identidade, documento ou conta invalida contextos transitórios; nunca renderizar análise de pessoa/escopo anterior.
- \`page_header\`, \`section_heading\`, \`kpi_cards\` e variantes UX81 são os únicos padrões visuais reutilizados. HTML dinâmico escapado, CTA nativa e foco WCAG AA.

## Limite de entrega entre PRs
Este PR entrega **a porta de entrada, o escopo, os cartões únicos e a seleção direta**. A matriz automática sob a seleção e as ações/retornos financeiros completos pertencem ao **UX87 consolidado (#203)**. O #201 deve demonstrar valor sozinho: cidades sugeridas visíveis sem entrar em fluxo manual. **Não** criar uma tela transitória "passo 1/4"; preparar um contrato único de seleção que o #203 possa consumir sem nova confirmação.

## Testes obrigatórios de comportamento
- Cold start com wishlist: uma confirmação de escopo, resultados sem escolha de modo.
- Acesso com escopo \`ready\`: resultados imediatos sem repetição de confirmação.
- Escopo vazio, nenhum ativo, seleção de apenas 1 destino, \`pending_ids\`, nova wishlist, removidos, somente mudança de prioridade, revision backwards ou documento restaurado, mudança de identidade.
- Cada ID de cidade só aparece uma vez no resultado; casos \`complete\`, \`conditional\`, \`investigation\`, sem histórico, local-only, sem tempo.
- Seleção por card 0,1,2,3,5,6 candidatas disponíveis; máximo 5 para comparação, 2 suficiente; CHOICE é autoritativo; sem multiselect concorrente.
- Alternar/retomar comparação manual legado, preservar \`PREVIOUS\`, \`MANUAL_KEYS\`, IDs de callback existentes e filtros.
- Nenhuma renderização escreve \`TripPlan\`, wishlist, favorita ou orçamento; ausência de botões fictícios HTML; no máximo uma CTA principal contextual.
- \`app.py\`: nenhum título/expander global de simulação ou ferramentas antigas antes dos resultados em Comparar bases.
- AppTests + \`python -m compileall -q .\` + \`python -m unittest discover -s tests -v\` + CI no HEAD. Verificar realmente em navegador a 1440/768/390 px, foco, disabled, overflow, regressões e captura de tela; se indisponível, dizer **não validado**.

## Entrega / restrições
Modificar apenas a camada de apresentação e orquestração e os testes pertinentes; não refatorar REC01/REC02, persistência, cálculos ou UX64. Após revisar o prompt, implementar na **branch existente do #201**, mantendo draft até testes. **Não criar PR novo; não fazer merge automático; não declarar implementação pronta com base na pipeline documental.**
