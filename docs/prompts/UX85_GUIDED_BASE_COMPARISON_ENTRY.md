# UX85 — Entrada guiada para Comparar bases | Prompt de implementação

## Papel e objetivo
Atue como Staff Python/Streamlit Engineer, Principal Product Designer, Accessibility Engineer e Code Reviewer. No repositório clevertondecker/europe-trip, transformar a porta de entrada Explorar > Comparar bases em uma jornada clara e ÚNICA, preservando os dois motores existentes e o histórico de seleção, sem reescrever REC02/REC03.

## Auditoria antes de editar
Ler o HEAD atualizado e revisar rec03a_suggestions_ui.py, rec03a_session.py, rec03b_handoff_ui.py, rec03b_handoffs.py, ux503_destination_base_comparison_ui.py, ux64_navigation_model.py, ux64_navigation_ui.py, ux502_destination_interests_ui.py, ux_shared_ui_presentation.py e respectivos testes AppTest. Confirmar a ordem e estrutura DOM real: app.py renderiza os controles públicos UX64 antes de render_recommendation_activity(). Não assumir que o HEAD continua igual ao planejamento.

## Problemas atuais confirmados
- A atividade pública única Comparar bases contém um radio técnico entre Comparação personalizada e Cidades sugeridas; dois caminhos diferentes aparecem como tarefas concorrentes.
- Há cabeçalho visual compartilhado no modo manual, mas o modo Cidades sugeridas ainda usa título genérico e vários controles sem hierarquia.
- A seleção de destinos é exposta antes da pergunta principal; há ações de retorno/revisão repetidas e banners que competem com o resumo.
- A análise é de uma temporada confirmada (REC02 scope): não se deve reconstituir esse escopo silenciosamente a partir de país, estágio, filtros temporários ou lista desatualizada.

## Contrato de UI proposto (P1)
1. UMA entrada pública Explorar > Comparar bases, com UM page_header UX81 e descrição curta: 'Encontre cidades estratégicas para investigar saindo dos destinos que você escolheu'. Evitar outro título/hero no interior de render_suggestions() ou render_wishlist_base_comparison_ui().
2. Resumo visível: 'Temporada europeia · N destinos considerados' + chips acessíveis de destinos já confirmados. Ações secundárias ao lado: 'Editar destinos' e 'Voltar à minha lista'. Não colocar quatro botões verticalmente antes do resultado.
3. Estado sem escopo confirmado ou stale: usar a própria _render_scope e confirm_scope, com explicação do impacto. Só analisar com confirmação explícita; preview opcional não equivale a confirmação.
4. Após confirmação: exibir base candidates primeiro, depois seleção para comparação, com um único CTA primário real. Não misturar ranking/seleção com alterações oficiais.
5. Ocultar o radio de modos no fluxo principal e disponibilizar 'Personalizar comparação' no espaço avançado, sem apagar valores MANUAL, SUGGESTED, ACTIVITIES ou rec03a_activity_widget. Usuários retornando à comparação manual devem recuperar a seleção anterior. Não criar um segundo roteador.
6. Separar conteúdo do usuário de 'Ferramentas avançadas' e não puxar os ajustes avançados da simulação para o topo da tela de comparação. Detalhes REC05 permanecem acessíveis sob demanda.
7. Definir/explicitar a escolha do modo inicial para NOVAS sessões sem substituir contextos ativos. Manter o modo atual se o usuário estiver retomando uma comparação ou um handoff REC03B.
8. Fazer a orquestração em rec03a_suggestions_ui.py e apresentação auxiliar *somente se justificado*, alimentada por projeções canônicas. Não duplicar dados em session_state, não persistir escolhas exploratórias.

## Compatibilidade e estados
- Preservar public task UX64: Explorar > Comparar bases e TARGETS legado.
- Respeitar rec03a_scope, rec03a_draft, identidade, pending_ids, no_destinations, ready, erro do carregamento e mudanças da wishlist.
- Preservar ux503_bases/ux503_visible_destinations, PREVIOUS e retorno de REC03B.
- Voltar de mapa/perfil/orçamento deve manter contexto validado, ou explicar quando escopo expirar.
- Zero-state: sem destinos, todos descartados, escopo com interesse novo, pesquisa indisponível, dados parciais.

## Testes
1. AppTest cold start, seleção de escopo e sessão restaurada com modo manual.
2. Uma única hierarquia de cabeçalho, uma CTA primária por estado; sem duplicação de componentes/IDs.
3. Switch guiado -> manual -> guiado -> wishlist preserva estado e filtros.
4. Identidade alterada/escopo invalidado não mostra resultados antigos nem muda TripPlan.
5. Clique em callback legítimo; não escrever em TripPlan, ux502_interests, favorites, persisted budget ao renderizar.
6. Preservar deep links e testes existentes (tests/test_rec03a_suggestions.py, tests/test_rec03b_handoffs.py, tests/test_ux503_destination_base_comparison.py, tests/test_ux64_public_navigation.py).
7. Visual real 1440/768/390 px, foco visível e leitura sem rolagem horizontal da página.

## Qualidade e entrega
Implementar código/testes nesta mesma branch após autorização, não apenas alterar prompts; CI no HEAD; logar screenshot ou ausência explícita. Não alterar algoritmos, tempos, scores, fontes, confirm_scope nem schemas. Não marcar como pronto para merge enquanto não houver implementação e testes. NÃO FAZER MERGE AUTOMÁTICO.
