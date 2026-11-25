# UX125 — Mapa de migração de navegação legada

Este inventário separa remoções implementadas das migrações ainda em avaliação. Não constitui novo inventário global de destinos nem modifica o plano.

| Entrada | Arquivo / ação / estado | Destino e preservação | Situação e verificação |
|---|---|---|---|
| Visualização anterior (Descobrir e Minha lista) | ux502_destination_interests_ui.render_wishlist; ux502_view | Abas públicas ux64_public_task; ux502_view passa a projeção de compatibilidade; mantém recuperação de seleção temporária e snapshot UX126B | Removido no app principal; testes de navegação, restauração e filtros |
| Comparação personalizada anterior | ux502_destination_interests_ui.render_wishlist; ux503_open_from_wishlist → request_navigation | Comparar bases e Comparar cidades-base (rec03a_open_from_wishlist); modo manual permanece no comparador canônico, inclusive handoffs | Atalho removido; validar comparação e retorno |
| Indicadores do catálogo de desejos | ux502_destination_interests_ui.render_wishlist; ux82_wishlist_metrics | Contagens desejados, imperdíveis, interessados e talvez no resumo da própria lista; nenhuma métrica privada exportada ao DATA24 | Removido; preferências e prioridades intactas |
| Acessar outras etapas | ux_planning_journey_ui.render_planning_journey; flow_journey_step_* | Abas Meus destinos/Organizar, CTA principal, ações contextuais de incluir/revisar/organizar; flow_journey_view e deep links mantidos | Removido; teste de navegação e plano intacto |
| Pesquisar por cidade-base | app.py, Explorar atrações; render_explorer e filtros próprios | Avaliar ficha UX124, descoberta e logística por base; preservar ações sem equivalente antes de remover | Pendente |
| Pesquisas e estudos preservados | app.py, Comparar cidades; ux_compare_mode; render_city_decision; comparador histórico | Evidências e lacunas pertencem ao DATA24A; preservar estudos privados, revisão de troca, referências históricas e recuperação de cenários | Pendente, depende de DATA24A |
| Explorar atrações turísticas por cidade-base | app.py, Mapa; map_go_attractions | Unificar com Descobrir; preservar navegação de retorno e escopo | Pendente |
| Pesquisas e mapa | app.py, Visão geral; home_continue_bases, home_go_map, home_next_tasks, home_open_consultor | Mapa/Explorar pelos controles públicos; decisões e pendências/REC05 mantidas em Planejar; verificar guias e ações de recuperação | Pendente |
| Ajustes avançados e Outras ferramentas financeiras | app.py, Simulações; ux_mode, ux_days, ux_budget_view | Não editar antes da integração autorizada de UX127; manter estudo financeiro e confirmar equivalência | Dependência UX127 |
| Comparar alternativa | planning_context_ui.render_context, workflow_open_alternative | Preservar comparação de dias Itália/França, perfil e base até comprovar equivalência | Dependência UX127 |
| Fontes e ferramentas | app.py, sidebar; main_navigation, ux_section, scenario_sidebar, ux_mode, ux_days | Consolidar fontes, manter recuperação de estudos/rotas legadas por compatibilidade; remover seletores duplicados somente após testes de handoff | Pendente |
| Fontes e documentação / rodapé | app.py, bottom_source, Fontes & atualização | Uma localização global; preservar origem/data do Drive, snapshot, avisos, links e crédito fotográfico | Pendente |

Os testes UX125 exercitam o caminho público no aplicativo. Os testes antigos que acionavam o rádio removido passam a acionar a aba pública equivalente. Nenhuma alteração no modelo, persistência, dados de origem ou orçamento. Não remover renderizadores ou estilos compartilhados sem verificar consumidores.
