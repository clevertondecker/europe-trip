# UX131 — Centralizar inclusão de destinos no planejamento

**Status: proposta para implementação; nenhum código funcional alterado neste commit.**

## Objetivo e justificativa
Após separar exploração de planejamento, transformar desejos em visitas por meio do editor que já existe. Hoje há caminhos concorrentes de inclusão em Descobrir, inclusão em lote de wishlist e formulários antigos de adição. Evitar dois planejadores e preservar flexibilidade, especialmente quando o usuário já tem destinos no roteiro sem wishlist. A inclusão é uma decisão explícita e pode impactar orçamento; não ocorre ao salvar um desejo.

## Implementação proposta
- Auditar ux_planning_journey_ui.py (render_build, render_review, _workspace_cards), ux_planning_journey_model.py, ux61_destination_board_model.py, itinerary_flow_model.py, itinerary_flow_ui.py, itinerary_eligibility.py, rec03b_handoffs.py e continuidade/cloud/financeiro. Mapear todos os pontos que chamam commit_outing e inclusão em lote, inclusive Itália, consultor e guias. Não remover modelos compartilhados.
- Reutilizar Planejar → Meus destinos → Montar roteiro a partir da minha lista: seleção em lote por etapa, nomes/fotos/bandeiras e prioridade, seleção/deseleção explícita, quantidade selecionada e botão “Incluir N destinos no roteiro”. Não criar outro formulário de lote. Manter limite existente e validação no momento da confirmação.
- Mostrar destinos já incluídos e pendentes de inclusão de forma distinta. Não presumir que prioridade alta implica inclusão automática. Se oferecer seleção inicial, ela é apenas rascunho visível, nunca confirmação.
- Manter acesso explícito, no próprio Planejar, ao catálogo de passeios suportados para adicionar destino que ainda não esteja na wishlist (incluindo Itália), reutilizando o formulário/modelo existente ou oferecendo ida contextual à lista com retorno claro. Não perder capacidade de incluir destinos novos quando a lista estiver vazia. Não reintroduzir inclusão direta em Descobrir.
- Mostrar destinos não suportados somente quando relevantes para a decisão, em bloco compacto “Ainda não disponíveis para o roteiro”, com motivo e permanência na lista. Auditar lacunas de identidade e atrações; registrar dados faltantes e propostas em inventário, sem fabricar atrações, preços ou tempos; expansão de catálogo não comprovada fica fora deste PR.
- Separar estado de desejo (prioridades), seleção de lote temporária e TripPlan confirmado. Preservar visitas antigas que não estejam na wishlist; não sincronizar destrutivamente. Remover do roteiro não remove desejo; remover desejo não exclui visita. Sinalizar discrepâncias de forma discreta se necessário; não importar nem alterar desejos silenciosamente.
- Após confirmar, retornar à revisão de Meus destinos; ações Editar passeio e Organizar levam aos editores atuais/UX129. Período/data continuam opcionais. Reutilizar mecanismo de persistência, revisão e orçamento oficial UX127; nenhuma gravação financeira ao apenas selecionar. Garantir inclusão atômica, sem duplicação, por IDs canônicos, respeitando etapas e permissões.
- Eliminar entradas/renderizadores redundantes apenas após identificar equivalentes; não ocultar o antigo em expander. Preservar pesquisa de atrações e funções necessárias à Itália, inclusão individual e edição de visitas existentes.
- Revisar copy e handoffs entre Minha lista, Comparar bases, Meus destinos, Organizar e Orçamento; não exigir que cidade-base esteja definitivamente escolhida. Nenhum novo wizard obrigatório.

## Por que esta organização?
O planejamento deve responder “o que faremos?” e permitir confirmação informada de várias visitas de uma vez. O agrupamento por etapa e prioridade facilita seleção, e a revisão imediata mostra o efeito da decisão. Concentrar mutações no editor proprietário reduz estados concorrentes, mantém orçamento coerente e evita que limitações de dados determinem o que o usuário pode pesquisar.

## Critérios e testes
- Jornada Descobrir → Minha lista → Comparar bases (opcional) → Meus destinos → Organizar → Orçamento; testar lista vazia, lista só de pesquisa, mistura de prioridades, destinos das duas etapas e roteiro existente sem wishlist.
- Inclusão em lote/individual explícita, idempotência, validação de IDs/aliases, limites, estado restaurado, conflitos e erros sem inclusão parcial indevida. Verificar seleção de lote não altera plano/custos até confirmação.
- Confirmar que remover da lista não remove passeio e vice-versa; preservar visitas, atrações, datas, grupos e orçamento oficial de planos existentes.
- Testar elegibilidade única e ausência de CTA duplicado, continuidade privada e recálculo financeiro pelo contrato existente, sem criar uma segunda fonte de verdade.
- Suite completa + QA visual desktop/mobile, CI do HEAD final verde, review antes de merge.

## Dependências e ordem
Prioridade 3, coordenar com UX130. Validar a inclusão pelo planejador antes da remoção pública do caminho de Descobrir; se necessário, integrar UX131 primeiro ou publicar os dois juntos após rebase. Reutilizar o editor UX129, sem conflito com ele. DATA25 é independente. Não alterar a decisão oficial de base ou dados pesquisados.
