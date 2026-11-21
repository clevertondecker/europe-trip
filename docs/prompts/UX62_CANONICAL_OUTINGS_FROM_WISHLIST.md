# UX 6.2 — Planejar uma cidade antes de escolher atrações

**Status:** PROMPT REVISADO — sem implementação; **P0 / mais alto risco de domínio**.
**Review:** REDESENHAR. A proposta anterior obrigava escolher de 1 a 5 atrações para incluir qualquer cidade; isso contraria o objetivo de planejar progressivamente.
**Dependência:** UX 6.1 para entrada visual; pode definir contrato e migração em paralelo, mas não implementar telas antes da aprovação da evolução do TripPlan.

## Papel
Atue como Staff Python/Streamlit Engineer, Domain Architect, UX Designer, Migration/Test Engineer.

## Experiência pretendida
Usuário seleciona **Obernai → Adicionar cidade ao roteiro** e imediatamente passa a ver `No roteiro · atrações a escolher`, mesmo com zero atrações, sem data. Depois, quando quiser, abre o **mesmo cartão/editor canônico**, conhece fotos/fontes/durações, seleciona atrações opcionais, período/data e confirma. Pode também pesquisar/editar antes de incluir, sem exigir uma decisão de tudo ou nada.

Um destino **desejado** continua distinto de um destino **planejado**: apenas o botão explícito `Adicionar cidade ao roteiro` cria uma visita confirmada no TripPlan. `Atrações escolhidas` é metadado opcional da visita. Não converter automaticamente todos os favoritos em visitas.

## Gate obrigatório — proposta de contrato ANTES da implementação
O código atual confirma uma barreira de domínio, não só visual:
- `itinerary_flow_model._validated_choice()` exige `1 <= len(attractions) <= 5`.
- `ux45_outing_contract.apply_outing()` rejeita lista vazia.
- `catalog_plan_validation.validate_catalog_packages()` exige 1–5.
- `itinerary_flow_model.selected_rows()` ignora destinos franceses em `flexible_visits` quando não estão em `packages`.
- `planning_session.commit_outing()` carrega `load_attractions()`; portanto o catálogo suplementar de Obernai e Lucerna aparece em explorar mas não pode ser confirmado hoje.
- `continuity_archive_model.validate_archive()` chama `validate_flow_backup()`; todas as mudanças em catálogo/schema precisam ser compatíveis com dados antigos e GCS.

**Apresentar uma ADR curta e testes de migração na branch antes de implementar UI.** Comparar: (A) estender `flexible_visits` para visitas sem atrações, deixando `packages` conter somente escolhas efetivas de atrações francesas; (B) introduzir campo canônico adicional no TripPlan, com custo de duplicação. **Preferir (A)** se os invariantes e bibliotecas downstream puderem ser mantidos de forma comprovada. Não introduzir uma segunda lista persistida de `visitas` fora do TripPlan. Se a migração for insegura, dividir em PRs técnicos menores e bloquear a UI até contrato validado.

## Escopo futuro proposto
1. Evoluir o contrato canônico para visita confirmada **0 a 5 atrações**, sem tratar `[]` como reserva, visita detalhada ou passagem paga. **Preservar o limite superior de cinco provisoriamente** para compatibilidade; questionar o limite em estudo próprio se houver evidência, sem mudá-lo de passagem.
2. Reutilizar `commit_outing(...,confirmed=True)` como **ponto único de confirmação**, suportando inclusão com zero atrações e atualização posterior. `flow_pending_attractions` continua draft UI, nunca segunda fonte autoritativa. `delete_outing` mantém confirmação explícita.
3. Adaptar `selected_rows`, `choice_counts`, `upsert_choice`, validação do catálogo, `TripPlan`, `catalog_plan_validation`, `ux45_outing_contract`, calendário, `package_cost`, relatórios e grupos de fim de semana para interpretar `[]` como `sem seleção de atrações`, **não** `€0` nem `ausente`. Nenhum lugar perde dados por alternar a etapa.
4. Resolver complemento `trip01_supplemental_discovery` → modelo tipado de viagem para Obernai e Lucerna, com IDs estáveis e atrações oficiais pesquisadas: **camada de catálogo curada e validada** separada dos snapshots históricos de evidência ferroviária. Preço/tempo/retorno desconhecido permanecem desconhecidos. Não fazer união irrestrita de fontes exploratórias em `load_attractions()` sem revisão de schema e testes.
5. Atualizar `trip_plan_model.SCHEMA_VERSION` e `continuity_archive_model` **somente se necessário pela decisão documentada**. Testar importação de backups antigos, transformação explícita quando exigida, conflitos, versionamento, conservação de IDs e ausência de perda de `packages`/datas; nunca editar arquivo de usuário silenciosamente por schema inválido.
6. UI: cartão tem `Adicionar cidade ao roteiro`, `Ver/editar atrações` e `Organizar data`, cada ação independente. O editor de atrações `ux55_visual_outing_ui.py` deve mostrar foto licenciada/fallback, descrição, tempo editorial, ticket.currency, ticket.per (inclusive `adult_return` ida/volta), ticket.validity, notes e fontes. Preço desconhecido não é zero.
7. `Atrações a escolher` não bloqueia calendário, mas alertas de viagem/logística permanecem pendentes. Um destino planejado sem data não vira `Organizado`; data/período salvo não vira `Reservado`.
8. Remover visita do TripPlan com confirmação **não** remove da wishlist. Mudança da cidade-base não altera visitas nem cria horários de trem; análises continuam hipotéticas até decisão explícita.
9. Itália permanece em etapa separada. Não criar `packages` franceses para Roma; não apagar proposta de lua de mel ou conflitar com excursões italianas. Preservar `ux45_navigation_context` de ida e volta a Explorar/Comparar.
10. **Condições de bloqueio:** não apresentar botão ativo para confirmar destino ainda inválido no catálogo canônico; se cobertura insuficiente, mostrar estado legível `Informações em revisão` com ação de pesquisa, não exceção.

## Gate P0 — Fechamento do contrato completo de cidade sem atrações

**Antes da UI, entregar uma ADR verificável**, com a matriz de leitores/escritores e uma decisão sobre schema, migração e rollback. A preferência arquitetural continua sendo usar `flexible_visits` para presença da visita e `packages` exclusivamente para atrações selecionadas, **mas isso é hipótese condicionada a testes**, não autorização para adaptar somente um método.

### Invariantes propostos e consumidores obrigatórios
1. **Presença canônica:** `flexible_visits` identifica a visita confirmada mesmo com `attractions: []`. `packages` não pode conter pacote vazio como sentinela nem pode ser utilizado sozinho como contador de visitas novas. Para registros legados onde existe pacote sem `flexible_visits`, preservar leitura e edição sem perda; definir regra de reconciliação explícita para manter representação canônica consistente.
2. **Consistência:** uma visita francesa com atrações selecionadas deve ter `packages[dest]` consistente com `flexible_visits.attractions`; uma visita com zero atrações **não** tem pacote fictício. `assignments[date] = destination_id` somente pode apontar para uma visita francesa válida e agendável, com ou sem atrações. Datas italianas continuam em `flexible_visits.exact_date`.
3. **Validação ponta a ponta:** auditar `trip_plan_model.validate_plan` (atualmente exige 1–5), `itinerary_flow_model._validated_choice`/`selected_rows`/`choice_counts`/`validate_flow_backup`, `ux45_outing_contract.apply_outing`, `catalog_plan_validation.validate_catalog_packages`, `planning_store.set_package`/`remove_package`/`add_assignment`/`summary`, `calendar_assignment_validation.validate_new_assignments` e `planning_session.schedule_package`. Não liberar UX enquanto qualquer escritor rejeitar a visita vazia ou qualquer leitor ocultá-la.
4. **Calendário e grupos:** `smart_calendar_model.availability_matrix`/`assess_day`/`suggest_calendar`, `calendar_model` e `ux48_weekend_groups_model._selected`/`validate_groups` devem aceitar visita de zero atrações sem criar outra reserva ou ocupar data por simples agrupamento. A regra legada de **um destino francês principal por dia** permanece nesta etapa; não reescrever a cardinalidade do calendário.
5. **Custos e relatórios:** `attractions_model.package_cost()` atualmente agrega **pelos IDs das atrações** e ignora cidade sem atrações. A projeção financeira precisa receber destinos confirmados para exibir *transporte a estimar / atividades a definir*, sem somar custo zero nem inventar rota/tarifa; preservar API legada onde possível por adaptador ou nova projeção tipada. Auditar dashboard, estimadores, métricas, `planning_store.summary()`, relatórios e compatibilidade das telas de orçamento.
6. **Catálogo:** integrar Obernai e Lucerna por adaptação tipada e auditada; permitir cidade planejada com atrações ainda em pesquisa, sem importar todo catálogo de descoberta para validações canônicas e sem modificar os registros históricos de transporte.
7. **Schemas/arquivos:** decidir explicitamente se a nova semântica é retrocompatível em `TripPlan.schema_version=1` ou exige versão nova; avaliar o que acontece se um leitor antigo abre arquivo novo. `continuity_archive_model`, backup local, GCS, export/import e recuperação devem aceitar arquivos legados com 1–5 atrações e arquivos novos com zero atrações **no leitor atualizado**. Se não houver leitura bidirecional segura, declarar formato novo e migração unidirecional idempotente com fixture e rollback, nunca afirmar que versões antigas lerão visitas vazias.
8. **Mutação atômica:** confirmar entrada, alteração de 0→N e N→0 atrações, agendamento, reagendamento, desagendamento, remoção e restauração como transições de uma única visita; impedir duplicatas, órfãos em `assignments`, perda de dates, ou reset de estado da wishlist. Registros de catálogo removidos devem gerar diagnóstico explícito, não descarte silencioso.

**Decisão de projeto:** implementar o contrato mais simples possível **somente depois** de provar os invariantes acima. Se não der para garantir agenda e custos com `flexible_visits` sem uma migração ampla, isolar o trabalho técnico antes do botão `Adicionar cidade ao roteiro`. Não inserir `[]` em `packages` como atalho.

### Critérios bloqueantes de aceitação
- **GIVEN** Colmar e Obernai confirmadas com zero atrações **WHEN** programo uma delas em data francesa permitida, agrupo em fim de semana e abro calendário inteligente **THEN** ambas permanecem elegíveis, nenhuma exceção pede ingresso/atração, e o calendário registra somente as decisões temporais efetivamente confirmadas.
- **GIVEN** cidade francesa confirmada sem atrações **WHEN** abro o orçamento **THEN** transporte e atividades aparecem como itens pendentes (sem preço zero presumido), mesmo se o pacote de atrações ainda não existir.
- **GIVEN** visita com zero atrações e data **WHEN** seleciono atrações e edito/removo **THEN** `packages`, `flexible_visits` e `assignments` ficam consistentes sem duplicação; datas só desaparecem mediante confirmação de impacto.
- **GIVEN** plano legado com pacote e sem visita flexível **WHEN** faço importação no leitor novo **THEN** continua visível, editável, agendável e exportável; histórico não é reescrito sem consentimento/migração definida.
- **GIVEN** plano novo e antigo **WHEN** exporto, salvo no GCS simulado e recupero **THEN** IDs, estágio, zero ou N atrações, datas, grupos, custo pendente e revision não divergem.

## Cenários Given / When / Then
- **GIVEN** Obernai está na wishlist e não há passeios **WHEN** clico `Adicionar cidade ao roteiro` **THEN** um único registro é confirmado no TripPlan com `[]` atrações, estado `No roteiro`, sem data, e a wishlist continua inalterada.
- **GIVEN** um registro com zero atrações **WHEN** abro `Ver atrações` **THEN** posso salvar seleção válida depois, sem nova cidade/ID e sem perder período/data existentes.
- **GIVEN** a visita tem 5 atrações **WHEN** tento selecionar uma sexta **THEN** validação exibe limite e não altera TripPlan.
- **GIVEN** a visita já existe **WHEN** clico novamente `Adicionar` **THEN** não duplica nem revisa por engano.
- **GIVEN** há backup legado com 1–5 atrações **WHEN** restauro **THEN** o plano permanece validado e idêntico; vice-versa, backup novo com zero atrações restaura no contrato novo, sem corromper o antigo.
- **GIVEN** destino suplementar sem pesquisa ferroviária **WHEN** planejo a cidade **THEN** aparece sem inventar trem, preço, retorno ou reserva.
- **GIVEN** removo a visita da agenda **WHEN** confirmo remoção **THEN** as datas dependentes são reconciliadas/confirmadas, mas a wishlist continua.
- **GIVEN** uso Itália, França, mudo base, troco de destino e volto **WHEN** retorno ao editor **THEN** stage, draft e contexto permanecem corretos.

## Mapa de testes obrigatório
Testes de unidade do contrato `0–5`, validação antiga/nova e aliases; integração `planning_session.commit_outing`, `ux45_outing_contract`, `selected_rows`, `package_cost`, `weekend_groups`, smart calendar e relatórios; testes AppTest de confirmação, edição, exclusão e navegação com Obernai/Colmar/Roma; export/import de arquivo de continuidade e simulação GCS owner; CI com validação de pesquisa preservando 30×46. Verificar manualmente mobile + labels/acessibilidade. Documentar tamanho/impacto da migração e rollback.

## Direção transversal da UX 6.0
Arquitetura futura de três áreas: **Explorar · Planejar · Orçamento**. Uma visão dos destinos composta de wishlist + TripPlan, sem um segundo editor ou duplicação de fontes. Pesquisa, comparação, seleção, calendário e orçamento são etapas iterativas, não barreiras sequenciais. Estados: `Quero conhecer` (wishlist), `No roteiro` (TripPlan com ou sem atrações), `Atrações escolhidas` (detalhe), `Organizado` (período/data) e `Reservado` (somente evidência externa). Datas e preços de 2027 não podem ser inventados. Mudanças confirmadas afetam o TripPlan via ponto único; mudanças de pesquisa/favorito nunca o alteram. Preservar compatibilidade da Itália, dados 30×46, segurança, OIDC/GCS/GitHub separados. **Este PR ainda é apenas especificação.**
