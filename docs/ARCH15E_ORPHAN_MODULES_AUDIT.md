# ARCH15E — Decisões e evidências

Baseline: HEAD `53da382`, CI [46177163334](https://github.com/clevertondecker/europe-trip/actions/runs/46177163334), job 141078364811. Histórico Git completo; referências coletadas por git grep -n -w no conteúdo versionado. A análise AST encontrou precisamente os nove módulos abaixo. Não foi realizado grep em arquivos não versionados.

| Módulo | Origem | Intenção original | Decisão |
|---|---|---|---|
| arch10b_documentary_parity | 132664a | Auditoria de 450 pares ferroviários | Mover para tools, preservar testes |
| arch14_macro_coverage_cache | 9f987af | Cache DQ32 de oportunidades macro | Manter allowlist: UX132 usa DATA24 rail_coverage, inventário de atrações e cobertura de moradia; não são projeções equivalentes. Não integrar/remover automaticamente. |
| calendar_visit_model | 978fdd8 (#7) | Protótipo de visitas repetidas e custo por visita | Remover módulo e apenas VisitsTests; preservar DraftTests |
| corridor_priority_pilot_model | c3d922f (#121) | Piloto de corredores | Mover para tools, preservar dados e testes |
| geographic_base_screening_model | 9539485 (#117) | Triagem geográfica exploratória | Mover para tools, preservar testes |
| regional_opportunity_research_model | 68d33a7 (#118) | Propostas regionais documentadas | Mover para tools, preservar dados e testes |
| route_research_evidence_model | e04a623 (#116) | Contrato de observações ferroviárias | Mover para tools, preservar testes |
| rec02_diagnostics | 3ff5fc8 | Diagnóstico e benchmark do motor REC02 | Mover para tools, preservar testes |
| rec01_feasibility | 2563cd5 | Benchmark e auditoria REC01 | Mover para tools, preservar testes |

Os JSONs data/corridor_priority_pilot_2026_11.json e data/regional_opportunities_pilot_2026_11.json permanecem; os caminhos dos leitores foram ajustados para a raiz. Nenhum JSON removido. Nenhum script de auditoria existente removido; rail_gap_coverage_audit_model e rail_component_contract permanecem. Executar benchmarks com python -m tools.rec01_feasibility [--benchmark] e python -m tools.rec02_diagnostics na raiz.

Símbolos: remover os 18 definidos e sem consumidores Python, manter referências históricas nos documentos. _format_brl já removido pelo ARCH15B (referência remanescente no teste de contrato). VALID_DISTANCE_KINDS e VALID_MODES removidos: _walking_route e published_walking_itineraries já exigem walking e walking_route, de modo que usar os conjuntos mais amplos afrouxaria a validação. Nenhuma alteração na regra vigente. Testes de ferramentas movidas têm apenas imports atualizados; nenhuma asserção alterada.

## Evidência original da CI
```text
ORIGIN arch10b_documentary_parity.py
132664ab5cc6f662eeb0f896dd8d91f2ef00e98f ARCH 1.0b: auditoria documental com 450 pares e divergência comprovada

ORIGIN arch14_macro_coverage_cache.py
9f987af6bc91548290f41e12d5672ed1b564550d ARCH 1.4: cache de cobertura turística com medições e invalidação

ORIGIN calendar_visit_model.py
978fdd80c8186283f713d4357a92ff4192e0086d Rascunhos: backup validado e modelo de visitas repetidas (#7)

ORIGIN corridor_priority_pilot_model.py
c3d922ffa071cb12fdfcb0d596dc3bcdbefbba66 routes: integrate reviewed PR #121

ORIGIN geographic_base_screening_model.py
95394857023d9393b1f193482aacc26e39a0b06e routes: integrate reviewed PR #117

ORIGIN regional_opportunity_research_model.py
68d33a79ebb467c3c2a0b8d8f5e2004358aa391e routes: integrate reviewed PR #118

ORIGIN route_research_evidence_model.py
e04a6237b3fbfed27a0a6354c9e3811a59234ea5 routes: integrate reviewed PR #116

ORIGIN rec02_diagnostics.py
3ff5fc816abf607683ea45f27e0adbf847bd9fde feat(rec02): reproducible product examples and separate matrix/engine benchmark

ORIGIN rec01_feasibility.py
2563cd528009de1bfc577c89cf6281ea32f2f7b5 feat(rec01): reproducible feasibility audit with validated runtime datasets

REFERENCES upsert_flexible_choice
docs/UX45_UNIFIED_JOURNEY_DELIVERY.md:7:| Meu roteiro → Meu planejamento (incluir/editar) | `upsert_flexible_choice` sem feedback estruturado | `packages` + `flexible_visits` no TripPlan; Itália só flexible | `commit_outing`: mesmo domínio, resultado `OutingResult` |
planning_session.py:97:def upsert_flexible_choice(destination:str,attraction_ids:list[str],
tools/audit_root_module_reachability.py:29:    "upsert_flexible_choice", "remove_flexible_choice", "delete_package",

REFERENCES remove_flexible_choice
docs/UX45_UNIFIED_JOURNEY_DELIVERY.md:8:| Meu planejamento (remover) | `remove_flexible_choice` com confirmação | Remove pacote, metadados e assignments | `delete_outing(confirmed=True)` e comunica datas |
docs/UX45_UNIFIED_JOURNEY_DELIVERY.md:10:| Explorar → Passeios (remover) | Removia no primeiro clique | `remove_flexible_choice` | Confirma impacto e usa `delete_outing`; modo simulação ainda bloqueado |
docs/prompts/UX119_PLANNING_DESTINATION_WORKSPACE.md:35:- Confirmado: planning_session._commit não reconcilia grupos; ux48_weekend_groups_ui._state e continuity_ui._private_archive fazem isso posteriormente. _current_decisions_fingerprint chama _private_archive, que pode escrever grupos e dirty durante leitura. Antecipar reconciliação de remoções no limite canônico da alteração, reutilizando reconcile_removed_outings, com candidato de plano+grupos validado antes de publicar qualquer mutação. Revisar também remove_flexible_choice/delete_package e demais entradas equivalentes. Remover associações e grupos vazios, manter ordem, notas, datas válidas, demais destinos, wishlist e identidade. Confirmação informa datas e grupos afetados; explicar grupo que ficará vazio. Nenhuma necessidade de abrir Organizar ou salvar para corrigir. Se reconciliação falhar, não publicar alteração parcial. Não introduzir política de exclusão paralela.
planning_session.py:135:def remove_flexible_choice(destination:str)->dict:
tools/audit_root_module_reachability.py:29:    "upsert_flexible_choice", "remove_flexible_choice", "delete_package",

REFERENCES delete_package
docs/UX45_UNIFIED_JOURNEY_DELIVERY.md:12:| Meu roteiro → editor legado Meus passeios | `select_package`/`delete_package`, estados próprios | Plan canônico | Usa `commit_outing` e `delete_outing`; tela legada mantida |
docs/archive/PROMPT_EDITOR_MEUS_PASSEIOS_2027.md:11:- Exclusão usa planning_session.delete_package, inclusive limpando assignments do destino.
docs/prompts/UX119_PLANNING_DESTINATION_WORKSPACE.md:35:- Confirmado: planning_session._commit não reconcilia grupos; ux48_weekend_groups_ui._state e continuity_ui._private_archive fazem isso posteriormente. _current_decisions_fingerprint chama _private_archive, que pode escrever grupos e dirty durante leitura. Antecipar reconciliação de remoções no limite canônico da alteração, reutilizando reconcile_removed_outings, com candidato de plano+grupos validado antes de publicar qualquer mutação. Revisar também remove_flexible_choice/delete_package e demais entradas equivalentes. Remover associações e grupos vazios, manter ordem, notas, datas válidas, demais destinos, wishlist e identidade. Confirmação informa datas e grupos afetados; explicar grupo que ficará vazio. Nenhuma necessidade de abrir Organizar ou salvar para corrigir. Se reconciliação falhar, não publicar alteração parcial. Não introduzir política de exclusão paralela.
planning_session.py:153:def delete_package(destination:str)->dict:
tools/audit_root_module_reachability.py:29:    "upsert_flexible_choice", "remove_flexible_choice", "delete_package",

REFERENCES active_plan_view
planning_session.py:174:def active_plan_view()->dict:
tools/audit_root_module_reachability.py:30:    "active_plan_view", "PrivateQuoteStore", "validate_predefined_budget",

REFERENCES PrivateQuoteStore
docs/UX38_SIMPLE_QUOTES_IMPLEMENTATION.md:9:- `PrivateQuoteStore` reutiliza `PrivateArchiveStore`, identidade de proprietário verificada pela UX3.6 e o bucket existente. O objeto separado é `ux36/owners/<hash>/ux38_quotes.json`. Nunca escreve no GitHub público.
quote_research_model.py:206:class PrivateQuoteStore(PrivateArchiveStore):
tools/audit_root_module_reachability.py:30:    "active_plan_view", "PrivateQuoteStore", "validate_predefined_budget",

REFERENCES validate_predefined_budget
predefined_budget_model.py:39:def validate_predefined_budget(plan:dict,option:dict)->None:
tools/audit_root_module_reachability.py:30:    "active_plan_view", "PrivateQuoteStore", "validate_predefined_budget",

REFERENCES close_overlays
planning_context_ui.py:57:def close_overlays()->None:
tools/audit_root_module_reachability.py:31:    "close_overlays", "_draft_all", "lot_coverage", "_by_city", "_format_brl",

REFERENCES _draft_all
rec03a_suggestions_ui.py:246:def _draft_all(ids):
tools/audit_root_module_reachability.py:31:    "close_overlays", "_draft_all", "lot_coverage", "_by_city", "_format_brl",

REFERENCES lot_coverage
data8_priority_tourism_model.py:14:def lot_coverage(*, discovery=None):
tools/audit_root_module_reachability.py:31:    "close_overlays", "_draft_all", "lot_coverage", "_by_city", "_format_brl",

REFERENCES _by_city
dq20_urban_life_model.py:97:def _by_city(comparison:dict,city_id:str)->dict:
tools/audit_root_module_reachability.py:31:    "close_overlays", "_draft_all", "lot_coverage", "_by_city", "_format_brl",

REFERENCES _format_brl
tests/test_arch15b_formatting_contract.py:10:         "_format_brl", "_format_eur", "compact_money", "_duration"}
tools/audit_root_module_reachability.py:31:    "close_overlays", "_draft_all", "lot_coverage", "_by_city", "_format_brl",

REFERENCES MANUAL_KEYS
docs/UX85_88_BASE_COMPARISON_REDESIGN_ROADMAP.md:30:- #203 deve atualizar a branch com #201 integrado antes de implementar, remover CTA transitória e manter `PREVIOUS/MANUAL_KEYS` apenas para acesso manual legado.
docs/prompts/UX85_GUIDED_BASE_COMPARISON_ENTRY.md:11:- `rec03b_handoffs.CHOICE` (key `rec03a_handoff_base_selection`) representa bases escolhidas; `queue_handoff(kind="manual")/apply_handoff` já transfere **2–5 bases** e destinos do escopo para UX503, com `PREVIOUS` e `MANUAL_KEYS` para recuperar filtros antigos. `profile`/`map` são intenções individuais.
docs/prompts/UX85_GUIDED_BASE_COMPARISON_ENTRY.md:35:- Enquanto somente #201 estiver em `main`, mostrar **uma única CTA contextual** `Comparar N cidades` quando houver 2–5 escolhas; acioná-la encaminha `CHOICE` + escopo confirmado para o UX503 legado usando `queue_handoff(kind="manual")` e `apply_handoff` existentes. **Não mostrar o multiselect antigo novamente na entrada**. A UX503 legada permanece editável e permite recuperar filtros anteriores pelo contrato `PREVIOUS/MANUAL_KEYS`.
docs/prompts/UX85_GUIDED_BASE_COMPARISON_ENTRY.md:42:Preservar `rec03a_scope`, `rec03a_draft`, `rec03a_activity`, `rec03a_identity`, `rec03a_navigation_intent`, `CHOICE`, `PREVIOUS`, `MANUAL_KEYS`, `ux503_bases`, `ux503_visible_destinations`, `TripPlan`, UX64, REC01/REC02/REC04/REC05 e contratos de fontes. Os modos `SUGGESTED/MANUAL` continuam internamente para deep links, transição e recuperação, mas **não como radio principal**. Não criar persistência de seleção, novos schemas, novos pesos nem Design System paralelo.
docs/prompts/UX87_COMPARABLE_EVIDENCE_MATRIX.md:11:- `rec03b_handoffs` valida escopo, identidade/contexto, PREVIOUS, MANUAL_KEYS e caminhos profile/map/planning. REC04 mantém `request_simulation`, `apply_simulation_request`, `valid_context` e `return_to_source`. `rec04_candidate_capabilities.capability_for` distingue capacidades.
docs/prompts/UX87_COMPARABLE_EVIDENCE_MATRIX.md:18:4. **Selecionar/desmarcar** atualiza apenas `CHOICE` e a projeção visual. Não mover automaticamente o usuário para uma segunda interface nem atualizar filtros do UX503 legado. Preserve o acesso manual avançado e `PREVIOUS/MANUAL_KEYS` sem sincronização desnecessária.
docs/prompts/UX89_CONTEXTUAL_NAVIGATION_SIMPLIFICATION.md:43:- Preservar `TripPlan`, prioridades e persistência da wishlist, `rec03a_scope`, `CHOICE`, `PREVIOUS`, `MANUAL_KEYS`, REC04 e orçamento, fontes REC05, configuração UX81 e roteamento UX64.
docs/prompts/UX93_COMPARE_MAP_DECISION_FIRST.md:18:4. Manter comparação manual PREVIOUS/MANUAL_KEYS e estudo histórico em acesso avançado, preservando deep links e handoffs; não oferecer dois fluxos principais concorrentes.
rec03b_handoffs.py:20:MANUAL_KEYS = (
tools/audit_root_module_reachability.py:32:    "MANUAL_KEYS", "DEPARTURE_MIN_DATE", "SOURCE_URL", "RECHECK", "LEGACY",

REFERENCES DEPARTURE_MIN_DATE
city_research_packs_model.py:13:DEPARTURE_MIN_DATE="2027-09-04"
tools/audit_root_module_reachability.py:32:    "MANUAL_KEYS", "DEPARTURE_MIN_DATE", "SOURCE_URL", "RECHECK", "LEGACY",

REFERENCES SOURCE_URL
finance_lifestyle.py:12:SOURCE_URL = "https://drive.google.com/file/d/1_PgDDM-wPR5hlUyTRjdpxAwrnE0hhaqu/view"
tools/audit_root_module_reachability.py:32:    "MANUAL_KEYS", "DEPARTURE_MIN_DATE", "SOURCE_URL", "RECHECK", "LEGACY",

REFERENCES RECHECK
base_coverage_model.py:31:RECHECK="A confirmar"
tools/audit_root_module_reachability.py:32:    "MANUAL_KEYS", "DEPARTURE_MIN_DATE", "SOURCE_URL", "RECHECK", "LEGACY",

REFERENCES LEGACY
italy_honeymoon_ui.py:28:LEGACY={"60k":12545,"70k":14636}
tools/audit_root_module_reachability.py:32:    "MANUAL_KEYS", "DEPARTURE_MIN_DATE", "SOURCE_URL", "RECHECK", "LEGACY",

REFERENCES OFFICIAL_FARE_BASES
outing_base_coverage_model.py:16:OFFICIAL_FARE_BASES = frozenset({"mulhouse", "strasbourg", "metz", "nancy"})
tools/audit_root_module_reachability.py:33:    "OFFICIAL_FARE_BASES", "VALID_DISTANCE_KINDS", "VALID_MODES",

REFERENCES VALID_DISTANCE_KINDS
dq30_walking_access_model.py:16:VALID_DISTANCE_KINDS = {"walking_route", "straight_line", "rail_distance"}
tools/audit_root_module_reachability.py:33:    "OFFICIAL_FARE_BASES", "VALID_DISTANCE_KINDS", "VALID_MODES",

REFERENCES VALID_MODES
dq30_walking_access_model.py:17:VALID_MODES = {"walking", "rail", "public_transport"}
tools/audit_root_module_reachability.py:33:    "OFFICIAL_FARE_BASES", "VALID_DISTANCE_KINDS", "VALID_MODES",
```
