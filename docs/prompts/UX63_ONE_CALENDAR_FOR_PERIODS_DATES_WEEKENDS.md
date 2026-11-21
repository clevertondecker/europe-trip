# UX 6.3 — Organização flexível por etapa, período e fim de semana

**Status:** PROMPT REVISADO; sem implementação. **P1**.
**Veredito:** AJUSTAR: o erro da versão anterior foi assumir que um *calendário único* é necessariamente a interface central. Priorizar lista/timeline das visitas com transição opcional para calendário.
**Dependências:** UX 6.2 (visitas canônicas podem não ter atrações); UX 6.4 só muda navegação externa, sem ser requisito de domínio.

## Papel
Atue como Principal UX Designer, Staff Python Engineer, Travel Planning Domain Engineer e Test Engineer.

## Nova experiência
Em **Planejar → Organizar** (ou rota antiga `Meu roteiro → Organizar viagem`) apresentar **linha do tempo/lista por etapa**, separando `Itália` e `Temporada europeia`. Cada visita confirmada no TripPlan possui configuração gradual: `Decidir depois`, `Período flexível`, `Data específica` ou `Agrupar em viagem de fim de semana`. O usuário não precisa escolher data ao confirmar uma cidade. Alternar para `Calendário completo` é uma **visualização**, não outro editor autoritativo.

Exemplo na etapa europeia:
- **Sem data:** Obernai · Strasbourg (ações: escolher período, sugerir fim de semana, ver detalhes).
- **Período:** Basel · outubro (sem inferir fim de semana específico).
- **Data:** Colmar · 23/10/2027 (somente se usuário confirmar data).
- **Fim de semana:** Lucerna e Interlaken (grupo com data e pernoite quando definido).
- **Sem planejamento de tempo:** destinos apenas desejados aparecem como atalhos de pesquisa, NÃO como eventos programados.

## Escopo
1. Criar projeção somente leitura de `TripPlan` + grupos de fim de semana, organizada por etapa, período e data; não duplicar `assignments`, `flexible_visits` e `ux48_weekend_groups` em uma nova estrutura mutável.
2. Reutilizar `itinerary_flow_ui._render_organize`, `ux48_weekend_groups_model/UI` e `smart_calendar_model/UI` com **uma hierarquia visual**: lista/timeline padrão → ações `Definir período`, `Definir data`, `Criar viagem` → calendário completo avançado. `Calendário inteligente` oferece sugestões opt-in, nunca confirma automaticamente.
3. Visitas com zero atrações (nova capacidade da UX 6.2) devem aparecer normalmente. Wishlist não convertida em visita fica fora das métricas de ocupação.
4. `Decidir depois` pode ser mantido sem erro. Ao limpar período/data, preservar destino/atrações; se desfizer configuração existente, exibir prévia e confirmação (incluindo impacto em grupos e datas).
5. Agrupar passeios em `weekend_groups` já existente; evitar evento duplicado no calendário quando uma visita integra grupo. Edição/remoção de grupo deve preservar escolhas individuais e reconciliação existente.
6. Calendário de trabalho remoto: respeitar campos efetivamente configurados em `smart_calendar_model.validate_calendar_preferences` (timezone, work_start, work_end, allow_evenings). Não importar implicitamente horário brasileiro ou assumir folgas. Mostrar dias úteis/fins de semana, descanso, passeios longos e pernoites como categorias visuais. Se configurações ausentes, usar estado `Horário de trabalho não definido` e convidar a definir, sem bloquear o planejamento.
7. Mostrar restrições de estágio: partida depois do casamento (04/09/2027), Itália dentro de `italy_days`, temporada europeia no restante de `total_days` — sempre ler do TripPlan (70/10 somente como fixture de teste). Mudança de dias/partida exige reconciliação de datas anteriores, sem descarte silencioso.
8. Transporte sem evidência, volta não verificada, tempo desconhecido, possível conflito de data/pernoite, noites de descanso e carga de trabalho são **alertas**, não falsa disponibilidade. Nenhuma viagem é reservada porque foi agendada.
9. Cada alteração de data/agrupamento passa por ponto de escrita canônico existente: `schedule_package`, `schedule_italy_visit`, `commit_outing` (quando editar visita) e `ux48_weekend_groups_model` com confirmação. Garantir que ação de `Organizar` não reescreve wishlist nem orçamentos.
10. Evitar novas abas para os mesmos dados. Incluir referências visuais de custo de logística e link para Orçamento, mas o usuário pode rever custos a qualquer momento (não apenas depois do calendário).

## Alternativas avaliadas e decisão
- **A — Incremental:** manter três controles independentes de período, calendário inteligente e calendário completo, com nomenclatura melhor. Barato, mas mantém duplicidade conceitual.
- **B — Redesenho recomendado:** **timeline/lista autoritativa + visões alternativas**, com reutilização dos validadores atuais; maior custo de integração mas mais claro para uma temporada de 60 dias e trabalho remoto. Escolher B, migrando em duas etapas sem quebrar os calendários legados.

## Cenários Given / When / Then
- **GIVEN** visitas confirmadas, 2 sem data, 1 com período, 1 datada e 1 agrupada **WHEN** abro Planejar → Organizar **THEN** todas aparecem uma vez no grupo correto; origem do dado está clara.
- **GIVEN** destino apenas desejado **WHEN** abro calendário **THEN** não é contado como evento nem recebe data automaticamente.
- **GIVEN** visita sem atrações **WHEN** defino período ou data **THEN** salvo o horário sem forçar seleção de atrações, e o TripPlan permanece válido.
- **GIVEN** visita com data **WHEN** mudo para `Decidir depois` **THEN** vejo prévia de impactos e confirmo antes de remover vínculo temporal; visita permanece.
- **GIVEN** grupo de fim de semana tem 2 passeios **WHEN** abro calendário **THEN** vejo um agrupamento e detalhes dos membros, sem duplicar a ocupação.
- **GIVEN** não há hora de trabalho configurada **WHEN** peço sugestão **THEN** a UI avisa que não conhece meu expediente, e não agenda durante dia útil por suposição.
- **GIVEN** uma data sai da etapa após alterar duração **WHEN** volto à agenda **THEN** há estado de reconciliação visível, sem perda silenciosa do passeio.
- **GIVEN** falta informação de trem/último retorno **WHEN** planejo fim de semana **THEN** status permanece `Logística a verificar`, não `Viável confirmado`.

## Arquivos e testes
`itinerary_flow_ui.py`, `itinerary_flow_model.py`, `planning_session.py`, `ux48_weekend_groups_ui.py`, `ux48_weekend_groups_model.py`, `smart_calendar_model.py`, `smart_calendar_ui.py`, `calendar_model.py`, `continuity_archive_model.py`, `ux_navigation.py`.

Testar matriz de conflito/mesma data; duas etapas 10+60; alterações 8–12 dias na Itália, total 65–75; roundtrip JSON/GCS; migração de período/data, grupo/ungroup, editar/excluir sem perder atração; AppTest de troca de etapas, volta da agenda, calendário avançado, reinício de sessão, mobile e acessibilidade. Ações não confirmadas não escrevem.

## Direção transversal UX 6.0
Três áreas-alvo **Explorar · Planejar · Orçamento**, jornada não linear, status de interesse separado de status de visita, sem reserva inventada. TripPlan é autoridade de visitas, wishlist de interesses, GCS é privado e GitHub pode ser público. Este PR está somente documentado; revisar branch contra main, implementar após aprovação, CI e novo review antes de merge.
