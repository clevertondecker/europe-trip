**Draft — redesign separado do hotfix UX129A.**

## Objetivo e justificativa
Em Planejar → Organizar → Visitas, clicar em “Organizar visita” (ex.: Basel) parece não fazer nada. O callback de timeline apenas altera flow_organize_destination e limpa rascunhos, enquanto flow_add_open continua true e impede a montagem de _render_organize. Mesmo quando o editor está aberto, ele fica acima da lista sem feedback visual local. O usuário não deve procurar um formulário distante do botão. O hotfix UX129A corrige primeiro o bloqueio. Este PR cuida apenas do redesign contextual após sua integração.

## Implementação proposta
- Auditar ux_planning_journey_ui.py (focus_visit e _workspace_organize), itinerary_flow_ui.py (_render_organize, _show_organize, _organize_destination_changed), ux63_timeline_ui.py, app.py e estados de navegação UX120.
- Criar uma única intenção de organização focalizada por ID e etapa, validada contra visitas incluídas. Aplicá-la antes dos widgets. Fechar o modo adição e outros editores concorrentes; não descartar silenciosamente rascunhos não confirmados (pedir confirmação se houver alterações relevantes).
- Em Visitas, manter uma lista compacta de cards com nome, bandeira, foto existente com crédito e fallback, atrações escolhidas (ou “Atrações a escolher”), situação temporal e viagem agrupada quando houver.
- Ao clicar em Organizar visita, abrir o editor canônico dentro ou imediatamente após o card selecionado; apenas um editor aberto. Extrair componente reutilizável de _render_organize, não copiar regras de período/data nem criar outro fluxo de persistência. Se limitações de Streamlit impedirem encaixe seguro, usar painel focalizado imediatamente visível e retorno explícito, sem formulário concorrente.
- Mostrar destino escolhido no título, seleção de período/data, ações Concluir edição e Cancelar; salvar somente por ação explícita, cancelamento sem mutar plano. Preservar data já confirmada, validação de conflito, etapa Itália/temporada europeia, grupos de viagem, permissões, autosave existente.
- Garantir que o destino focalizado permaneça visível após rerun/paginação; evitar duplicação de keys, widgets montados duas vezes e saltos de tela. Reusar design system e imagens existentes, sem novo serviço de fotos.
- Preservar Calendário e Viagens agrupadas; revisar entradas de Meus destinos e links contextuais. Manter edição de atrações no editor proprietário, não adicionar edição paralela.

## Por que esta organização?
Uma ação deve mostrar seu resultado ao lado do objeto afetado. Cards compactos permitem varrer as visitas pendentes, e a edição contextual reduz deslocamento visual e desorientação. As datas são opcionais: o editor não deve parecer uma etapa obrigatória. O calendário e os agrupamentos continuam ferramentas complementares, não cópias do editor.

## Critérios e testes
- Reproduzir o cenário com flow_add_open ativo, clicar Basel/Colmar e verificar editor visível e destino correto no mesmo rerun.
- Testar clique em segundo card, fechar/cancelar, confirmar período/data, trocar etapa, retorno de Meus destinos, item fora da primeira página e grupos existentes.
- Testar conflitos de datas, não mutação ao abrir/cancelar, ausência de widget duplicado e preservação de plano/wishlist/orçamento sem confirmação.
- Cobrir seleção antiga/stale e restauração de sessão. QA desktop e mobile; verificar posição real do editor no navegador, pois AppTest não mede scroll.
- Suite completa e checks do HEAD final verdes antes de solicitar review. Não mergear sem autorização.

## Escopo
Redesign de Visitas, após UX129A. Não bloquear o hotfix com alterações visuais. Não alterar catálogo, elegibilidade ou fluxo de inclusão em Descobrir nesta entrega. Prioridade 1; independente de UX130/UX131 e DATA25.

## Revisão de escopo
Depende do hotfix UX129A (#267). Partir da main já corrigida; revalidar a regressão do clique com modo adição ativo. O redesign é independente da entrega da correção e não deve atrasar UX131. Manter a lógica de persistência existente.

## UX aprovado — contrato de implementação
- Visitas abre com os cards, sem seletor genérico de destino nem editor pré-aberto. Card selecionado recebe destaque, título com nome e editor imediatamente dentro dele. Usar o mesmo componente de período/data da tela antiga, preservando os handlers e keys de gravação; nenhuma duplicação de regras.
- Reusar o catálogo e a política de fotos/licença de Meus destinos. Mostrar bandeira derivada do país, atrações escolhidas por nome e estados de período/data individual e de grupo sem inferir datas. Cards compactos, responsivos, com texto acessível.
- Salvar por ação explícita; Cancelar limpa somente rascunho. Troca de card ou abertura do catálogo com rascunho alterado exige confirmação explícita. Preservar rascunhos de inclusão existentes em vez de descartá-los. Entrada via Meus destinos deve abrir o card certo; a paginação expõe o card focalizado. Invalidar seleção na troca de etapa, identidade ou plano. Manter fluxo proprietário de edição de atrações e calendário/grupos.
- AppTest com navegação real: card em repouso, foco, troca de card, confirmação de descarte, cancelamento, período/data, catálogo aberto e retorno, proteção de dados e ausência de seletor redundante. Testes puros de paginação e rascunho. QA visual desktop/mobile obrigatório antes de considerar a experiência validada. Não mergear sem autorização.