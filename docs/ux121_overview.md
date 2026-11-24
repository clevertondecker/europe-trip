# UX121 — Visão geral

A tela usa project_planning e board_metrics para todos os números. next representa trabalho útil (build, organize, review ou descoberta), independente do salvamento; editor_next mantém a entrada direta para revisão e salvamento no editor até UX122. A etapa recebe intent identity/plan-gated existente. Os compromissos mostram datas individuais e intervalos/períodos de grupos separadamente, sem inferir data individual.

O cabeçalho usa a data/duração/base do TripPlan e private_status_label. O orçamento usa get_scenario do cenário oficial e _compact_budget, que reutiliza advisor_projection e package_cost; estimativas são parciais, sem duplicação de Itália, sem tarifas inventadas. A sidebar continua sendo o controle global de salvamento. Não há novo writer, consulta remota ou estado persistido.

Rotas antigas: mapa → Explorar/Mapa; pesquisas e decisões → rota existente; propostas italianas e guias → consultor/Itália; configurações e retomada → ações existentes; recuperação → continuity_ui. As métricas do dashboard anterior, seletor de cenário concorrente e imagens externas decorativas foram retirados. Acesso às pesquisas contextuais e recuperação permanece em painel secundário até UX122.

Validação: testes do modelo (Metz 10+60, pesquisa Paris, cinco destinos, grupos sem data/com intervalo, inclusão elegível, salvo/local) e AppTest de handoff e status. QA visual manual em resoluções reais não realizado.
