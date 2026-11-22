# UX88 — Ações contextuais, simulação de custo e QA visual | Prompt de implementação

## Missão
Atue como Staff Streamlit Engineer, Senior Product Designer, Finance UX Engineer, Accessibility Reviewer e Code Reviewer. Fechar a experiência 'Meus destinos → bases sugeridas → comparar → simular custo' usando EXCLUSIVAMENTE os handoffs REC03B/REC04/REC05 existentes, com ações contextuais e pouco ruído. Implementar depois de UX85, UX86 e UX87 integrados.

## Estado real (auditar HEAD antes de tocar)
- rec03b_handoff_ui.py.render_card_actions() exibe Conhecer cidade, Ver no mapa e Simular esta cidade por cartão.
- rec03b_handoffs.py valida escopo, mantém PREVIOUS e navega por intents para perfil, mapa e planejador.
- rec04_simulation_handoff.py.request_simulation/apply_simulation_request/return_to_source/return_to_official mantém o orçamento oficial imutável e exige capability.
- rec04_candidate_capabilities.py distingue scenario_selectable, detailed_budget_supported, official_plan_supported e cita limites de dados.
- rec04_simulation_ui.py apresenta limitações no orçamento.
- rec05_priority_research_ui.py produz pendências para coletar fontes; não é um ranking de bases.
- UX81 já implementado em ux_shared_ui_presentation.py; não criar outra biblioteca de componentes.

## Entrega de UX
1. Fluxo principal: depois de selecionar uma base ou shortlist, uma única 'Próxima ação' em posição contextual. Por padrão 'Comparar' quando há 2–3 bases; após comparação, 'Simular custo de [base]' se e somente se capability permite, caso contrário 'Consultar o que falta pesquisar'. Não colocar 3 CTAs primárias por card.
2. Ações secundárias discretas por cidade selecionada: 'Conhecer cidade' e 'Ver no mapa', usando funções REC03B existentes e callbacks reais. Deve ser óbvio de qual cidade o botão trata; sem botões dispostos em colunas distantes sem contexto.
3. Handoff para simulação EXPLICITAMENTE acionado e validado por capability_for(); valores não disponíveis devem permanecer 'Não verificados' / 'Estimativa geral', nunca R$ 0 nem quote real. Preços e datas de 2027 não confirmados.
4. Ao chegar em Orçamento > Simulações, exibir contexto da cidade e distinção entre oficial, exploratório e orçamento detalhado suportado. Preservar unified_scenario, unified_style, budget_cap_confirm, scenario_base_selected, ux_mode, CONTEXT/ERROR e reset de unified_override_rent.
5. 'Voltar à comparação' restaura o escopo confirmado e a shortlist onde válido; alterações de identidade, plano ou scope invalidam contexto com mensagem útil, jamais reusam estado antigo. O retorno para Meu planejamento deve continuar dependendo do fluxo REC03B, sem autoescolher base ou incluir destino.
6. Simplificar repetição de botões: ações gerais da wishlist ficam no cabeçalho/escopo, ações da cidade ficam no detalhe contextual e pesquisas REC05 ficam no final/expanders. Manter compatibilidade com chaves/callbacks antigos quando necessários à continuidade.
7. Revisar labels e microcopy, explicando de maneira breve a diferença entre 'tempos mínimos de ida pesquisados', 'ainda sem tempo', 'custos de referência' e 'não há reserva'. Sem usar 'ótima opção' ou outra avaliação sem evidência.
8. Visual final conjunto usando UX81: no máximo um cabeçalho por atividade, um CTA principal por contexto, cards uniformes, tipografia e espaçamento coerentes com Meus destinos/Orçamento. Evitar banner forte duplicado ou accordions avançados antecedendo resultados úteis.

## Integração e riscos
- Manter request_simulation de origem suggestions/profile; se nova origem guiada for realmente necessária, ampliar o contrato com testes de identidade e retorno SEM contornar validações.
- Respeitar limitação 'official_plan_supported' para seleção oficial e não oferecer ação de oficializar bases candidatas não suportadas.
- Não atualizar TripPlan, base_city oficial, wishlist, favs, plan_id, budget_scenario ou controles financeiros por renderização/navegação.
- Não mudar algoritmo REC02, fonte, a matriz de REC01 nem prioridade REC05. Nenhuma pesquisa externa ou novos dados.
- Verificar componentes HTML de ação: botões de Streamlit são nativos e não devem ser simulados por markup clicável decorativo.

## Testes obrigatórios
- End-to-end AppTest: Descobrir → Minha lista → Comparar bases (confirmar escopo) → escolher 2–3 bases → comparação → simulação de uma base → retornar → continuar planejando sem alteração do plano.
- Sem cidade suportada, sem quote, cidade com orçamento geral apenas, opção oficial vs candidata, mudança de sessão/identidade/scope/plan, invalidação e retorno.
- Idempotência de callbacks, permissão, deep links, estado de widget após rerun, evitar duplicate keys.
- Regressões completas REC03A, REC03B, REC04, UX503/UX504, UX64, UX82/UX83/UX84 e CSS10.
- Inspeção real em browser a 1440/768/390: sem overflow horizontal, legibilidade dos cards, hover/focus/disabled, contraste AA, navegação por teclado, no máximo uma CTA por foco e ausência de sobreposição com controles do Streamlit.
- python -m compileall -q .; python -m unittest discover -s tests -v; GitHub Actions no HEAD. Relatar qualquer validação visual não executada como pendente.

## Entrega para review
Modificar apenas rec03a_suggestions_ui.py, rec03b_handoff_ui.py, rec04_simulation_ui.py / rec04_simulation_handoff.py se necessários, e testes, preservando API pública. Documentar antes/depois e impactos em Planejar/Orçamento. Só marcar como pronto após testes e review; não criar fluxo paralelo nem efetuar merge automático. Esta branch inicia como prompt-only draft.
