# Auditoria técnica — Nossa Europa 2027
Data: 15/11/2026 · Projeto: `clevertondecker/europe-trip`

## Escopo efetivamente inspecionado
Fluxos críticos em `app.py` (1.444 linhas), `destination_recommender.py`,
`unified_budget.py`, `advisor_finance.py`, `finance_lifestyle.py`,
`planning_store.py`, `planning_session.py`, `trip_plan_model.py`,
`trip_plan_repository.py`, `advisor_auth.py`, `travel_advisor_ui.py`,
`travel_optimizer.py`, `recommended_itineraries.py`,
`calendar_visit_model.py`, `calendar_model.py`, `drive_sync.py`,
`draft_plan_store.py`, `travel_profile_scenarios.py`,
`discovery_ui.py`, `scenario_board_ui.py`, `research_cost_model.py`,
`reconciled_trip_research.py`, `planning_status.py` e testes associados.

**Limite da auditoria:** inspeção focada nos fluxos de maior risco, não
revisão linha a linha de cada script, Markdown, dataset ou configuração
do repositório. Não foi feito pentest, acesso aos Streamlit Secrets ou
inspeção de toda a história Git. Não afirmar aprovação de segurança integral.

## Matriz de rastreabilidade

| Fonte de dados | Modelo/contrato | Transformação | Cálculo | Interface | Persistência |
|---|---|---|---|---|---|
| `data/trip.json` / planilha Google Drive XLSM (read-only) | `data_model` / `drive_sync` | `resolve_french_budget` (live vs snapshot) | `scenario_total`, `advisor_projection` | `app.py`, Orçamento, dashboard | Fonte externa Drive somente leitura; projeção não grava em Drive |
| Catálogo de atrações e matriz base×destino | `attractions_model` | `package_cost`, `route_for` | custos conhecidos EUR/CHF, `money_units` | `destination_recommender`, `outing_guide_ui`, Visão geral | Arquivos versionados no Git; preço 2027 não garantido |
| Cardápios, transporte, varejo 2026 | `research_cost_model` / `reconciled_trip_research` | filtros por dia/condição e cotação | custos parciais, reconciliação **não persistente** | Meus passeios, Orçamento, Simular | JSON/Markdown de pesquisa, não `TripPlan` |
| Intenções e ações explícitas | `TripPlan` v1 | `planning_store` / `planning_session` | revisões e propostas | Meus passeios, Calendário e controles | sessão; GitHub JSON após OIDC + confirmação |
| Propostas/drafts não aprovados | `travel_optimizer`, `scenario_editor_model` | `approve_profile_scenario` | proposta sem gravar | Simular, Calendário | somente sessão ou backup local até aprovação |
| Backup JSON v1 | `trip_plan_model.validate_plan` | importação com verificação do catálogo | reconstrução de estado | Meus passeios | sessão; salvamento público exige confirmação |

## Achados e correções

### P0-01 — Moedas somadas nominalmente (bug confirmado; corrigido)
**Causa:** `destination_recommender.py` somava os valores EUR e CHF de
`known_by_currency` sem conversão antes de calcular o custo na pontuação.

**Correção:** `money_units.known_eur_equivalent` normaliza CHF usando
as taxas EUR/BRL e CHF/BRL explícitas; recomendações da interface e
cenários recebem as mesmas taxas usadas no orçamento. Mantidas moedas
originais na UI e metadados de câmbio no resultado.

**Teste:** variação do CHF com EUR constante altera a pontuação do
recomendador, sem confundir valores 10 EUR + 10 CHF com €20.

### P0-02 — Economias rejeitadas (bug confirmado; corrigido)
**Causa:** `unified_budget.scenario_total` rejeitava todos os deltas
negativos, embora pudessem representar voos/transporte/aluguel mais baratos.

**Correção:** deltas finitos podem ser positivos ou negativos, porém
despesas por categoria e total final não podem ficar negativos.
Controles do orçamento aceitam economias dentro de limites baseados
na verba original da categoria. Não admitir câmbio nulo ou consumo negativo.

**Teste:** economias em quatro categorias reduzem total pela soma exata;
economia maior que verba e total negativo são rejeitados.

### P0-03 — Persistência JSON em repositório público (risco confirmado; parcialmente mitigado)
`GitHubPlanRepository.save` grava em `main:data/user_plans/` como texto
JSON. O repositório **é público**: leitura de arquivos/commits é pública,
mesmo se gravações exigirem autenticação Google OIDC e uma confirmação
`advisor_public_repo_ack`. Randomizar ID e ocultar o botão não
protege conteúdo nem histórico.

**Mitigação sem migração destrutiva:** novo `public_plan_safety` rejeita
campos extras ao schema v1 e e-mails introduzidos no JSON antes do PUT,
sem descartar silenciosamente dados. Fluxo de consentimento existente
preservado; nenhum plano foi apagado/movido.

**Pendente crítico:** separar dados pessoais num backend privado com
acesso autenticado, política de retenção, backups, revogação e migração
controlada. Revisar eventual histórico público antes de concluir
confidencialidade. Proteção adicional de payload **não** torna segura
a publicação do próprio itinerário, inclusive datas de viagem.
Nenhum conteúdo de plano pessoal foi aberto ou copiado nesta auditoria.

### P1-01 — Datas de agenda sem verificação do regime da viagem (bug confirmado; corrigido)
`planning_store.add_assignment` aceitava datas parseáveis mesmo durante
Itália, instalação, dias de trabalho remoto ou fora da viagem.

**Correção:** `calendar_assignment_validation.validate_new_assignments`
valida novas atribuições contra `calendar_plan`, destinos e atrações
confirmados; alterações na agenda passam por `planning_store.change_plan`
e `trip_plan_model.apply_proposal`.

**Compatibilidade:** datas antigas já aprovadas, mesmo se incoerentes,
permanecem carregáveis e podem ser mantidas até revisão explícita.
Não ocorreu alteração silenciosa de backups v1.

### P1-02 — Propostas poderiam alterar data existente (risco confirmado; corrigido)
`trip_plan_model.apply_proposal` exigia revision/base iguais, mas não
verificava se a proposta alterava datas aprovadas. Agora rejeita alterações
e propostas de outro `plan_id` (quando presente), e valida novos dias.

### P1-03 — Atrações de destino diferente em backup (risco confirmado; corrigido)
A importação validava IDs de atrações existentes e IDs de destinos,
mas não necessariamente se cada atração pertencia **ao destino escolhido**.
A validação pure `catalog_plan_validation` agora é usada na importação
e no seletor canônico `planning_session.select_package`.
Isso preserva schema v1 e rejeita backups/sugestões com dados deslocados,
sem alterar planos já salvos automaticamente.

### P1-04 — Duas representações de estado (risco parcialmente controlado)
`TripPlan` fica em `advisor_plan` na sessão; `explore_packages`,
`explore_calendar`, `unified_city` e chaves antigas são projeções.
`planning_session._commit` já sincroniza as representações e invalida
propostas obsoletas. Preservado o mecanismo; recomendado teste
end-to-end de restauração, troca de base, salvamento e duas sessões.

### P2-01 — Dados de 2026 versus preço final 2027 (limitação existente)
Matriz `base_destination_routes_2027.json` inclui tarifas promocionais
Carte Fluo sob condições, horários estação a estação e rotas faltantes.
`research_cost_model` e `reconciled_trip_research` já exibem
amostras e pendências, mas **não** equivalem a orçamento completo.
Não promover preços históricos a 'confirmados para 2027'.

### P3-01 — `app.py` muito grande (dívida técnica, não refatorado nesta fase)
Contém navegação, modelos antigos, controles financeiros e mapas.
A refatoração de 1.444 linhas requer extração incremental e testes
específicos, após estabilizar bugs financeiros e agenda.

### Pontos adequados confirmados pela inspeção
- OIDC `advisor_auth.is_verified_owner` faz verificação de issuer Google,
  e-mail, `email_verified` e expiração.
- `trip_plan_repository.save` usa SHA otimista, checagem de revision e
  trata 409/422 como conflito; não mostrou escrita sem autorização pela UI.
- `draft_plan_store` salva apenas rascunho em sessão ou backup local.
- `drive_sync` solicita somente escopo de leitura, valida abas/estrutura e
  preserva snapshot quando leitura falha.
- `planning_store.remove_package` remove datas vinculadas ao destino;
  `with_revision` cria revisão sem mutação in-place.
- `recommended_itineraries.approve_profile_scenario` preserva passeios
  e datas oficiais e exige aprovação.

## Rastreabilidade dos testes
Testes novos em `tests/test_audit_p0_regressions.py`. A validação de CI
deve confirmar carga do Streamlit, testes anteriores e regressões.
Não tratar sintaxe `compileall` isolada como prova de segurança.

## Próximas ações
1. Decidir armazenamento **privado** antes de acrescentar notas pessoais;
   a migração é alteração de arquitetura e retenção que requer aprovação.
2. Ampliar testes de round-trip import/export, duas sessões concorrentes,
   revisão de backups legados e restauração após falha de rede.
3. Centralizar `Decimal` e `ROUND_HALF_UP` em todo o orçamento,
   não apenas na pontuação de câmbio.
4. Extrair `app.py` por recursos, mantendo testes AppTest antes/depois.
