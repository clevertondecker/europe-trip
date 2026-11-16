# Auditoria pós-merge — PRs #48, #49 e #50

**Base auditada:** branch `main` após merges #48 (commit `2804c9f`), #49 (`7f07217`) e #50 (`cd3857d`). Data: 16/11/2026.

## Inventário verificado no código

- **#48:** `continuity_ui.autosave_private_if_requested()` conserva `ux36_cloud_dirty` na falha e registra um fingerprint da tentativa falha para impedir requisições repetidas por rerun. `PrivateArchiveStore.save()` usa precondição `ifGenerationMatch`.
- **#49:** `private_city_studies.py` mantém coleção de estudos isolada da cópia `current.json`, com ids UUID, validação de conteúdo, limites de tamanho e `cloud_commit` usando CAS de geração. `private_city_studies_ui.py` oferece operações explícitas sem modificar `TripPlan`.
- **#50:** `known_route()` encontra quatro observações históricas de Nancy, Metz e Lille, marcadas como sem retorno e sem tarifa documentada; os dez pares prioritários de #47 seguem pesquisados.
- **Integração:** `city_decision_ui.py` embute os estudos no fluxo atual; `app.py` chama restauração e autosave antes de renderizar as páginas; `budget_sections_ui.py` lê referências financeiras sem novos lançamentos.

## Verificações desta auditoria

Testes `tests/test_postmerge_audit.py`: não perder dirty na falha, não alterar a coleção em conflito, quatro tempos históricos com tarifa desconhecida e plano imutável. Rodar em CI junto da suíte geral e AppTest já existente. Inspeção do Streamlit real, credenciais e duas sessões externas **não executada por esta auditoria**.

## Riscos / acompanhamento

- **P1 operacional (não reproduzido no CI):** implantação Streamlit, conexão GCS e isolamento entre navegadores reais não verificados. Solicitar teste manual autenticado antes de atribuir aceite E2E. Não introduzir gravações em produção neste PR.
- **P2 funcional:** dois fluxos de backup coexistem (arquivo UX3.6 e coleção privada de estudos UX3.4). A UI deve explicar claramente o que é salvo em cada um; não unificar nem migrar silenciosamente.
- **P2 técnico:** `calendar_visit_model.travel_fares_by_visit()` calcula ida+volta ilustrativa duplicando ida conhecida. **Não reutilizar como cotação real** em UX3.8.
- **P2 financeiro:** `unified_budget.scenario_total()` já substitui a verba de aluguel em uma simulação. Não somar a cotação sobre a verba novamente.
- Não foram comprovados defeitos P0/P1 em testes estáticos e de contrato que justificassem modificar a aplicação neste PR. Qualquer falha reproduzida pelo CI será corrigida antes de propor o merge.

**Escopo:** auditoria com testes e documentação, sem mutação de planos, Secrets, Drive ou GCS. Não mesclar automaticamente.
