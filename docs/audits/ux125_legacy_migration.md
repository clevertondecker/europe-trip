# UX125 — Mapa de migração de navegação legada

Este inventário separa remoções implementadas das migrações ainda em avaliação. Não constitui novo inventário global de destinos nem modifica o plano.

| Entrada | Arquivo / ação / estado | Destino e preservação | Situação e verificação |
|---|---|---|---|
| Visualização anterior (Descobrir e Minha lista) | ux502_destination_interests_ui.render_wishlist; ux502_view | Abas públicas ux64_public_task; ux502_view passa a projeção de compatibilidade; mantém recuperação de seleção temporária e snapshot UX126B | Removido no app principal; testes de navegação, restauração e filtros |
| Comparação personalizada anterior | ux502_destination_interests_ui.render_wishlist; ux503_open_from_wishlist → request_navigation | Comparar bases e Comparar cidades-base (rec03a_open_from_wishlist); modo manual permanece no comparador canônico, inclusive handoffs | Atalho removido; validar comparação e retorno |
| Indicadores do catálogo de desejos | ux502_destination_interests_ui.render_wishlist; ux82_wishlist_metrics | Contagens desejados, imperdíveis, interessados e talvez no resumo da própria lista; nenhuma métrica privada exportada ao DATA24 | Removido; preferências e prioridades intactas |
| Acessar outras etapas | ux_planning_journey_ui.render_planning_journey; flow_journey_step_* | Abas Meus destinos/Organizar, CTA principal, ações contextuais de incluir/revisar/organizar; flow_journey_view e deep links mantidos | Removido; teste de navegação e plano intacto |
| Pesquisar por cidade-base | app.py, Explorar atrações; render_explorer e filtros próprios | Descobrir e Minha lista não montam mais render_explorer. Filtros de pesquisa, calendário, custos, fontes, recuperação e ações exclusivas do explorador permanecem no guia Passeios por cidade-base, acessível em Planejar → Visão geral → Pendências e continuidade. Guia usa o identificador legado Explorar atrações para manter compatibilidade | Migrado: CI 45658341651 verde; manter ações de backup, filtros e pacotes enquanto existirem usuários/sessões legadas |
| Pesquisas e estudos preservados | app.py, Comparar cidades; ux_compare_mode; render_city_decision; comparador histórico | Evidências e lacunas pertencem ao DATA24A; estudos de troca, referências históricas, fontes e recuperação de estudos movidos para o guia especializado Estudos de cidades-base, acessível por CTA contextual em Comparar bases. Revisão oficial UX114 continua na comparação | Implementado: testar ida, retorno, restauração e preservação do plano; CI 45659852093 verde antes dos ajustes de revisão |
| Explorar atrações turísticas por cidade-base | app.py, Mapa; map_go_attractions | CTA Descobrir destinos abre a aba pública mantendo snapshot UX126B | Implementado; CI 45659852093 verde antes dos ajustes de revisão |
| Pesquisas e mapa | app.py, Visão geral; home_continue_bases, home_go_map, home_next_tasks, home_open_consultor | Removidos atalhos de Mapa/Explorar; Pendências e continuidade mantém recuperação, ações UX37, Pendências/REC05, Decisões oficiais e guias | Implementado; CI 45659852093 verde antes dos ajustes de revisão |
| Ajustes avançados e Outras ferramentas financeiras | app.py, Simulações; ux_mode, ux_days, ux_budget_view | Modo/duração duplicados retirados; checkbox ux127_custom_simulation e slider unified_stay são canônicos. Revisão de alternativa migrada para Planejar; consultor com propostas de estilos e guias movido para Planejar → Melhorar meu roteiro. Entradas antigas redirecionam; Simulações não monta controles de aprovação do consultor | Implementado; CI 45659852093 verde antes dos ajustes de revisão |
| Comparar alternativa | planning_context_ui.render_context, workflow_open_alternative | Revisão de alternativa de roteiro em Planejar → Visão geral; preserva dias Itália/França, perfil, base, revisão explícita e encaminhamento ao estudo de impacto. Simulações não monta a revisão que escreve no TripPlan | Implementado; CI 45659852093 verde antes dos ajustes de revisão |
| Fontes e ferramentas | app.py, sidebar; main_navigation, ux_section, scenario_sidebar, ux_mode, ux_days | Seletores de cidade, modo e duração retirados da sidebar; usar simulador UX127; manter chaves de estado e rotas legadas por compatibilidade. Navegação secundária mantida por compatibilidade: permite acessar Cidades-base, Melhorar meu roteiro (guias privados/especializados), Detalhamento financeiro, Pendências e Decisões, sem duplicar as abas públicas. Não retirar até haver equivalentes para todos os destinos internos | Preservação deliberada de acesso secundário; testes de navegação e handoff |
| Fontes e documentação / rodapé | app.py, render_source_documents, Google Drive · detalhes | Rodapé global retirado; links, crédito, data do Drive, snapshot, avisos e atualização consolidados na barra lateral; fontes contextuais mantidas | Implementado; CI 45659852093 verde antes dos ajustes de revisão |

Os testes UX125 exercitam o caminho público no aplicativo. Os testes antigos que acionavam o rádio removido passam a acionar a aba pública equivalente. Nenhuma alteração no modelo, persistência, dados de origem ou orçamento. Não remover renderizadores ou estilos compartilhados sem verificar consumidores.

Validação integrada do HEAD 82bc7b9: CI 45659852093, 1392 testes, 2 ignorados (planilha original não montada), zero falhas. Ajustes de revisão posteriores exigem nova CI. QA visual não realizado.

## Destino dos guias especializados

| Guia | Classificação | Justificativa / saída |
|---|---|---|
| Itália e Costa Amalfitana | Permanente | Pesquisa específica e fontes da lua de mel. |
| França e escapadas | Transitório | Consolidar informações únicas nos destinos e na ficha da base; aposentar duplicações só após equivalência. |
| Transportes e custos | Transitório | Consolidar fontes únicas em Logística e Detalhamento financeiro. |
| Calendário de pesquisa | Transitório | Preservar hipóteses e fontes até integração equivalente em Organizar. |
| Cronograma oficial | Permanente | Referência documental e decisões, distinta do calendário editável. |
| Passeios por cidade-base (Explorar atrações) | Transitório | Filtros, pacotes, calendário e backup técnico ainda usados; migração incremental ao editor e ficha canônicos. |
| Estudos de cidades-base | Transitório | Preservar estudos privados, recuperação, referências e fontes históricas até equivalência contextual. |

A classificação indica intenção de produto, não nova autorização de remoção. Os acessos diretos de comparação e pesquisa mostram apenas o guia e retorno contextual; nenhuma aba pública é selecionada quando a seção interna está ativa. A seleção nula é ignorada. As entradas genéricas permanecem disponíveis pela navegação secundária.
