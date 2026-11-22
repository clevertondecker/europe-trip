# UX83 — Padronização visual de Planejar | Prompt de implementação

## Papel e objetivo
Atue como Staff Python/Streamlit Engineer e UX Design Lead. Padronizar a experiência da área pública Planejar (Visão geral, Meus destinos, Organizar), mantendo o design de Meu roteiro aprovado no PR #196 como referência e reutilizando exclusivamente os componentes compartilhados disponibilizados no UX81.

## Dependência e auditoria inicial
Executar após o UX81. Ler código do HEAD atualizado, em especial app.py, ux64_navigation_model.py, ux64_navigation_ui.py, ux_planning_journey_ui.py, ux_planning_journey_presentation.py, ux_planning_journey_model.py, ux504_guided_journey_ui.py, itinerary_flow_ui.py, planning_session.py, continuity_ui.py e os testes existentes. Confirmar quais páginas usam render_planning_journey(..., summary_only=True) e quais usam a versão completa. Não presumir que app.py ainda corresponde ao PR #196.

## Padrão visual obrigatório
- Cabeçalho, tipografia, cards, níveis de botão, marcadores de estado, cores de salvamento e espaçamento devem ser os MESMOS do UX81 e da tela Meu roteiro.
- A hierarquia visual define: contexto da viagem -> indicadores confiáveis -> próxima ação real -> área de trabalho.
- Não repetir um banner forte em cada seção. Uma ação principal e navegação secundária consistente com as abas Explorar/Orçamento.
- Datas são opcionais para salvar rascunhos. Planejamento desejado, incluído, organizado, salvo e reservado NÃO são sinônimos.

## Telas
### Planejar > Visão geral
- Evoluir o resumo compacto sem duplicar o cabeçalho full-page ou competir com os cards de Meu roteiro.
- Exibir a visão do que já foi decidido, o que está pendente e qual a próxima ação, usando projeções canônicas e estados verdadeiros de armazenamento.
- Seguir estrutura visual comum, com navegação direta para Meus destinos ou Organizar.
- Evitar KPI/recommendation fabricado, porcentagem arbitrária ou informação de conclusão que sugira reserva.
- Preservar os blocos legados sob "avançado" e seus acessos existentes.

### Planejar > Meus destinos
- Preservar o PR #196: identidade, cards de Desejados/Incluídos/Organizados, próxima ação e etapas.
- Ajustar somente a integração com componentes de UX81 se necessário, sem fazer um segundo redesign.
- Evitar a reprodução simultânea do resumo compacto e da tela completa.
- Status em foco e salvamento são independentes: "Salvo em espaço privado" só após confirmação, alterações locais continuam visíveis.
- Preservar inclusão em lote, ida à wishlist, revisão, salvamento, âncoras e keys flow_journey_*.

### Planejar > Organizar
- Aplicar o mesmo cabeçalho/card/seção de Meu roteiro ao organizador existente, sem criar um segundo calendário ou editor de passeios.
- Organizar por etapa (Itália, temporada europeia), período/data e, quando disponível, timeline. Evidenciar visitas sem data.
- Hierarquia: conteúdo principal (visitas) e ações de definir período/data; salvar/revisar continua acessível mesmo que nenhuma data tenha sido definida.
- Manter os modos existentes Por período ou data / Calendário inteligente / Calendário completo e as rotas antigas no expander avançado.
- Respeitar edição individual, adição de atrações, máximo de seleção, retomada do explorador, orçamento integrado e condições de permissão.

## Restrições técnicas
Não modificar TripPlan, schema, selected_rows, commit_undated_destinations, project_planning, planejamento privado, rec03b_handoff, rec04/rec05 ou os TARGETS do UX64. Não duplicar Session State em widgets de navegação. Não reordenar os componentes de maneira que destrua keys após rerun. Não atualizar store por simples renderização.

## Testes de regressão
- Visão geral vs Meus destinos full: cabeçalho não duplicado, counts idênticos e componentes comuns.
- Wishlist vazia, somente exploração, compatíveis pendentes, destinos incluídos sem datas, parcialmente organizados e roteiro revisado/salvo.
- Mudança Itália ↔ França, deep link, cancelamento de seleção, confirmações explícitas, edição sem efeitos colaterais.
- Salvamento privado confirmado, conflitos, identidade e restauração, retornos entre abas e ausência de alterações fictícias.
- 1440/768/390: stepper sem botões espremidos, controles de período e timeline legíveis; keyboard/focus/WCAG AA.

## Execução e aceite
Implementar na própria branch depois da fundação, rodar python -m compileall -q . e python -m unittest discover -s tests -v, verificar GitHub Actions no HEAD e documentar prints antes/depois quando houver navegador. Se browser indisponível, relatar explicitamente. Testar que datas continuam opcionais para salvar. PR inicial é somente prompt, draft até implementação; não fazer merge automático.

---

## Revisão de arquitetura P1 — responsabilidades reais da navegação (bloqueante)

**Auditoria do HEAD \`64497287\`:** \`ux64_navigation_model.PUBLIC_TASKS\` expõe Planejar = \`Visão geral\`, \`Meus destinos\`, \`Organizar\`. \`TARGETS\` mapeia essas atividades para \`("Minha viagem","Resumo")\`, \`("Meu roteiro","Meu planejamento")\`, \`("Meu roteiro","Organizar viagem")\`. **Preservar esse contrato**. Atualmente \`app.py\` renderiza \`render_planning_journey(..., summary_only=True)\` em Visão geral e também em Meus destinos, enquanto Organizar recebe a jornada completa no modo Por período ou data. Isso é o P1 a corrigir, não o comportamento esperado.

### Contrato funcional obrigatório após implementação
1. **Visão geral**: dashboard **compacto** com contagens canônicas, estado de armazenamento, próxima ação e atalhos; sem duplicar montagem/revisão. \`summary_only=True\` somente neste contexto.
2. **Meus destinos**: tela de trabalho **completa** baseada na UI já integrada do #196; revisar wishlist/compatibilidade, montar por confirmação explícita, editar inclusão, revisar e salvar rascunho sem datas. Roteamento em \`app.py\` não pode usar \`summary_only=True\` nessa atividade. Reusar \`render_build\`, \`render_review\` e \`project_planning\`, sem novo editor.
3. **Organizar**: visitas existentes por etapa/periodicidade/data, calendário e edição. Deve **não** ser o único caminho para montagem/revisão. Manter retorno contextual para revisão e salvar, incluindo rascunhos sem data. Se a reutilização de \`render_planning_journey\` for necessária, concentrar a apresentação no modo \`organize\` sem executar silenciosamente a seleção/montagem. Preservar os modos legados.

### Regressões prioritárias
- \`Planejar > Visão geral > Meus destinos > Organizar > Meus destinos\` conserva \`TripPlan\`, wishlist, filtros e seleções confirmadas.
- \`Meus destinos\` expõe o editor completo, chaves \`flow_journey_*\`, inclusão explícita e revisão/salvamento sem datas.
- \`Organizar\` não cria uma segunda montagem nem exige datas.
- Deep links e \`TARGETS\` legados permanecem aceitos; nenhuma gravação por renderização.
- Cabeçalho, estado e KPIs não se duplicam entre \`app.py\`, resumo e jornada completa.

**Ordem de execução:** esta especificação corrigida pode ser commitada agora; **somente implementar após o #197 ser integrado à main**, atualizando o HEAD antes do trabalho. Não fazer merge automático. Enquanto só houver Markdown, manter draft e marcar status como *especificação corrigida, implementação pendente*.
