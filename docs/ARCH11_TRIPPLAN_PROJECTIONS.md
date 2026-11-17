# ARCH 1.1 — TripPlan como fonte única

O TripPlan versionado permanece a única autoridade. Chaves
`explore_packages`, `explore_calendar`, `explore_base`, `unified_city`
e `unified_scenario` continuam compatíveis com fluxos antigos.

`plan_read_models.legacy_plan_projection()` centraliza a projeção pura;
`read_plan_view()` cria cópia defensiva para consumidores read-only e
`legacy_drift()` informa divergências sem executar alterações.
`planning_session.bootstrap()` usa a projeção apenas para **chaves ausentes**,
evitando escrever em widgets já instanciados. `planning_store.sync_legacy_view()`
passa a reutilizar o mesmo contrato para a parte compatível.

Não removemos nenhuma chave legada, não mudamos `create_from_legacy()`,
schemas, revisionamento, persistência privada/Drive, autenticação ou
comportamento de autosave. Migração dos consumidores restantes depende de
inventário de widgets e testes, não de remoção cega.
