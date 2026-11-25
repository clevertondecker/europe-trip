## UX129A — Hotfix imediato de Organizar visita

**Problema confirmado:** em `ux_planning_journey_ui.py`, o callback `focus_visit` seleciona o destino e limpa os rascunhos de organização, mas não fecha `flow_add_open`. O ramo de adição continua montado em vez de `_render_organize`.

## Alteração mínima
Dentro de `focus_visit`, fechar o modo de adição antes de selecionar o destino (`state["flow_add_open"]=False`). Reutilizar `_show_organize` caso isso seja necessário para manter os flags coerentes, sem refatoração ampla. Não modificar contratos, layout, fotos, calendário ou agrupamento. Não gravar TripPlan nem wishlist ao clicar.

## Teste obrigatório
AppTest do aplicativo real: preparar uma visita francesa incluída, abrir Planejar → Organizar → Visitas, abrir adição, clicar no botão `ux120_visit_<id>` de uma visita diferente da selecionada. Verificar no mesmo rerun que adição está fechada, editor de período/data está montado, destino selecionado é o clicado e plano/wishlist permanecem iguais. Verificar também clique sem formulário de adição aberto. Não simular sucesso apenas por inspeção do código. CI completa do HEAD final.

## Entrega
Hotfix independente, prioridade imediata. Redesign de cards/editor contextual fica exclusivamente no #264 (UX129B). Não aguardar os outros PRs; solicitar review após CI verde, sem merge automático.
