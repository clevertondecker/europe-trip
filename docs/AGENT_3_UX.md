# Agente 3 — Rascunhos e calendário

- `draft_plan_store.py`: backup JSON válido por `plan_id`/perfil/revisão e seleção de atrações validada no catálogo. `save_draft`/`get_draft` implementam store injetável em memória, sem escrita no GitHub. O rascunho entre navegadores só é recuperável baixando/subindo o backup. Para persistência automática privada, é necessário backend separado e consentimento.
- `draft_controls_ui.py`: baixar backup e restaurar por arquivo com validação e confirmação explícitas.
- `calendar_visit_model.py`: lista explícita de visitas; pode representar múltiplas idas ao mesmo destino em dias diferentes sem repetir custo de trem por atração; preserva representação `assignments` legada por adaptador. Integração da modelagem no calendário oficial **não** faz parte deste PR.
- Testes de serialização, desatualização, edições isoladas e datas de trabalho remoto.

Integração: o integrador injeta `render_draft_controls(board,plan,catalog,profile=...)` no editor `scenario_board_ui.py`, fazendo `_update(profile,restored)` somente quando retorno não for None. Não alterar plano oficial antes de aprovação. Integração das visitas repetidas é trabalho separado por exigir migração do schema e o motor de custos existente.
