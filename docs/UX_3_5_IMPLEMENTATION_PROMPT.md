# PROMPT EXECUTÁVEL — Nossa Europa 2027 · UX 3.5: Calendário inteligente

## Missão

Atue como integrador do repositório `clevertondecker/europe-trip`. Leia o código e dados atuais, `AGENTS_COORDINATION.md`, os PRs #36, #37, #38 e #39 e os documentos oficiais da pasta Google Drive **Living Europe**. Implemente a **UX 3.5 — Organizar viagem de maneira inteligente**, após validar a integração da UX 3.4 na `main`.

**Objetivo final:** permitir que duas pessoas planejem a lua de mel italiana e a temporada europeia, distribuindo passeios escolhidos entre **férias, instalação, dias de trabalho remoto, noites e fins de semana**, sem precisar entender a arquitetura interna do software. O calendário deve responder *quando visitar, por que aquela data funciona, o que está pendente de confirmação e quanto afeta o orçamento*.

A viagem começa **após o casamento em 04/09/2027**. A data de partida ainda é premissa editável, não passagem comprada. O `TripPlan` canônico usa defaults como 70 dias totais, 10 na Itália, 25 dias iniciais de férias e 4 de instalação na França; sempre ler os valores reais da instância antes de calcular. A janela é ilustrativa, não uma reserva.

## Experiência do usuário

Use a estrutura existente **Meu roteiro → Organizar viagem** como lugar único de organização. **Não criar mais uma aba principal** nem transformar a página em um scroll infinito. Adotar subvisões contextuais simples, sempre com retorno ao contexto anterior:

1. **Visão por etapas:** Itália / Temporada europeia. Mostrar total de dias, férias, instalação, trabalho remoto e finais de semana. Ao abrir um passeio, mostrar origem da escolha, atrações, categoria e período sugerido.
2. **Organizar por período:** manter o editor flexível UX 3.2 para quem ainda não conhece datas. Períodos são ideias, não compromissos. Os locais selecionados continuam visíveis mesmo sem data.
3. **Calendário visual:** grade semanal ou lista cronológica com data local, etapa e ocupação, com distinção textual e acessível entre férias, instalação, trabalho, fim de semana, proposta, confirmado no roteiro e **reserva não efetuada**. Sem datas exatas de 2027 para trens/ingressos não cotados.
4. **Sugestões explicáveis:** ação **Sugerir dias para meus passeios** gera de 1 a 3 propostas como rascunhos, explica a regra e a fonte de cada escolha, destaca conflitos e permite ajustar manualmente. **Nunca aplicar automaticamente**.
5. **Revisar e aplicar:** mostrar antes/depois das datas escolhidas, passeios que ficaram sem data, alertas de trabalho/retorno/pagamentos, diferença financeira conhecida e alterações que permanecem no oficial. Só confirmar após ação explícita, revisão de `plan_id` e `revision`.
6. **Continuidade:** ao consultar um passeio, orçamento ou pesquisa, voltar ao mesmo dia/período/passeio e preservar filtros, rascunho, etapa e estado de salvamento. Exibir CTA **Continuar organizando** quando recuperar contexto.

Principais dúvidas que a UI deve responder sem abrir outra ferramenta: *Posso encaixar este passeio em uma terça de férias? Um bate-volta de trem é realista depois do expediente? O que acontece se eu mover para sábado? Está cotado ou é só uma possibilidade?*

## Regras de calendário e conflitos

- **Fonte da verdade:** `TripPlan` validado. Reusar `calendar_model.calendar_plan` como calendário-base da viagem e `itinerary_flow_model.selected_rows` para passeios flexíveis; `packages` + `assignments` continuam a representação oficial dos passeios europeus com data. As propostas italianas e `flexible_visits.exact_date` devem permanecer na etapa italiana.
- **Férias e instalação:** bloquear passeios de dia inteiro na instalação, a menos que o usuário peça explicitamente atividade curta viável e um novo contrato permita isso. Não colocar visitas europeias dentro da Itália. Não sobrescrever dias aprovados.
- **Trabalho remoto:** em dia útil após as férias, o padrão é trabalho; **não** sugerir passeios de dia inteiro. Atividades curtas após o expediente só com horário configurado, fuso correto, duração e retorno plausíveis. Horário de trabalho remoto na Europa é uma preferência **a perguntar/configurar**, nunca inferir automaticamente do horário brasileiro (diferença de fuso / horário de verão importa).
- **Finais de semana:** priorizar excursões longas quando houver tempo observado de ida, deslocamento urbano, visita e margem de volta. Para roteiros de múltiplos dias, propor bloco de datas com possível pernoite, não forçar como bate-volta.
- **Rotas incertas:** duração mínima histórica apenas de ida **não comprova** bilhete, frequência, conexão, última milha ou retorno no dia. Ausência de rota/horário é **pendência**, não custo zero, impossibilidade ou indicação falsa de viagem viável.
- **Duração das atrações:** usar os dados de visita disponíveis; se faltarem abertura, tempo de retorno, transfer ou bilhete, manter a sugestão condicionada e explicar a informação pendente.
- **Repetição:** distinguir visitas diferentes ao mesmo destino em dias distintos (`visit_id`), preservar uma tarifa intermunicipal por visita e não por atração; validar conflitos de data, duplicidades, blocos e IDs.
- **Datas propostas ≠ reservas:** não atribuir status “reservado” ou “confirmado por operador” ao aceitar a sugestão. Confirmado no roteiro significa **data aprovada pelo usuário**, não passagem/hotel/reserva.
- **Movimentação manual:** permitir alterar data, devolver a período flexível e remover somente a atribuição de data sem apagar a seleção de atrações.

## Orçamento, fontes e coerência

- Reusar `advisor_finance`, `unified_budget`, `finance_margin_metrics`, `attractions_model`, `outing_cost_evidence` e a seleção canônica do usuário, sem novo motor de finanças nem rubricas duplicadas.
- Separar claramente: **provisão já alocada** para passeios, **custos conhecidos com fonte** e **pendências**. Diferenças de preço só aparecem quando os mesmos itens são comparáveis. Tarifas promocionais `desde` não devem virar preço normal de ida/volta.
- Valores desconhecidos permanecem `None`, não €0. Se nenhuma tarifa de retorno estiver verificada, **não** apresentar “economia exata” por reorganizar o passeio.
- Nunca somar custos de deslocamento de uma mesma visita por número de atrações; se houver dois dias distintos, são duas visitas distintas.
- Integrar a comparação com a UX 3.4: trocar de cidade-base na simulação recalcula disponibilidade de evidência, **sem alterar o calendário oficial**. Datas já aprovadas exigem reavaliação quando a base oficial realmente mudar.

## Arquitetura e persistência

Auditar antes de editar:

- `calendar_model.py`: calendário de etapas, férias/instalação/trabalho/fins de semana.
- `travel_optimizer.py`: heurística determinística atual; cuidado com seu score relativo, que **não** é uma verdade objetiva nem preço.
- `calendar_visit_model.py`: `validate_repeat_visits`, `legacy_to_visits`, `intercity_trip_count`, `travel_fares_by_visit`.
- `calendar_assignment_validation.py`: `validate_new_assignments`, compatibilidade com dados anteriores.
- `itinerary_flow_model.py`, `itinerary_flow_ui.py`: etapas, passeios selecionados, organizar por período ou data.
- `planning_session.py`, `planning_store.py`, `trip_plan_model.py`: operações oficiais, versionamento e sincronização legada.
- `draft_plan_store.py`, `draft_controls_ui.py`, `planning_status.py`: rascunhos, export/import e indicação honesta de salvamento.
- `outing_cost_evidence.py`, `advisor_finance.py`, `finance_margin_metrics.py`: cálculo de custos sem duplicidade.

**Não editar arquivos exclusivos de agentes sem coordenação.** Criar preferencialmente um modelo puro, por exemplo:
`smart_calendar_model.py`:
- `availability_matrix(plan, work_preferences)->list[dict]`
- `validate_calendar_preferences(settings)->dict`
- `suggest_calendar(plan, catalog, routes, preferences, *, max_options=3)->list[dict]`
- `assess_day(plan, visit, day, evidence, work_preferences)->dict`
- `review_calendar_change(plan, proposal)->dict`

E uma UI contextual `smart_calendar_ui.py`: `render_smart_calendar(plan,trip_data,sync_sources)->None`.

Propostas devem conter `plan_id`, `base_revision`, `base_city`, lista de mudanças, avisos, justificativas e status `draft_unapproved`. A proposta não pode alterar estado oficial ao ser gerada; aplicar exige confirmação e validação dos invariantes de viagem.

Persistência: rascunhos em sessão e exportação/importação JSON versionada, autenticada somente quando a infraestrutura privada permitir. **Não salvar rascunhos de viagem no GitHub público por padrão.** Preservar recuperação de planos legados e exigir migração explícita se houver mudança de schema. Reservas externas não são criadas.

## Testes e aceite

Criar testes unitários, propriedade/invariantes e `streamlit.testing.v1.AppTest`, além da suíte existente.

Demonstrar, pelo menos:

1. Com 10 dias italianos e dias de instalação depois da chegada à França, sugestão de passeio italiano nunca cai na etapa europeia e passeio europeu de dia inteiro nunca cai na instalação.
2. Dia útil com trabalho remoto **não recebe** sugestão de dia inteiro; uma atividade noturna só é marcada como possível se horário, fuso, duração e retorno forem sustentados por dados.
3. Férias e fins de semana podem receber sugestões onde há espaço; datas preexistentes permanecem intocadas.
4. Destino sem retorno verificado permanece pendente/condicional; proposta não diz “bate-volta garantido”.
5. Repetir o mesmo destino em dois dias consome duas visitas, mas cada visita cobra no máximo um deslocamento intermunicipal, não um por atração.
6. Alterar manualmente um dia não altera seleções, preferências, reservas ou base oficial.
7. Quando `plan_revision` muda entre sugestão e confirmação, a aplicação deve falhar e pedir nova revisão.
8. Simulação da UX 3.4 pode apresentar sugestão alternativa de calendário, mas não atualiza `assignments` ou `flexible_visits` do oficial.
9. Navegar do calendário para pesquisa ou orçamento e retornar recupera dia, etapa, filtros e visita em edição.
10. Planos v1 antigos, Itália já planejada, fases europeias, autenticação e finanças passam na suíte completa.
11. Mostrar resultado da operação (revisado, aplicado à sessão, ainda não salvo online) sem afirmar reserva, compra ou publicação.
12. Contar cliques/trocas de área na jornada: **Meu roteiro → Organizar viagem → sugerir → revisar → confirmar**, priorizando até três ações de decisão após abrir o organizador. Medir regressões de scroll e perda de contexto.

## Entrega

Criar **branch própria**, PR com descrição clara de decisões arquiteturais, fontes, screenshots/testes quando houver navegador disponível, resultados do CI e limitações de 2027. Não fazer merge nem deploy até conclusão dos testes e autorização explícita do usuário. Atualizar documentos operacionais do Drive **somente** quando autorizado e depois de conferir a versão atual, sem duplicá-los nem apagar histórico.

**Resultado esperado:** um calendário que organiza a viagem de forma humana, respeita férias e trabalho, reconhece incerteza e mantém um caminho simples entre passeio escolhido, data proposta, revisão e decisão oficial.
