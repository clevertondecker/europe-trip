# Contrato 1 — evidências ferroviárias aditivas (implementação)

Origem: especificação de revisão do [PR #109](https://github.com/clevertondecker/europe-trip/pull/109), mantendo o PR #109 como documento de governança.

- Módulo puro `route_research_evidence_model.py`: três eixos independentes `source_nature`, `evidence_state` e `temporal_validity`, além da identidade direcional de estações, horários, fonte e data.
- `observation_id()` é determinístico e idempotente, enquanto `journey_identity()` permite preservar fontes e durações conflitantes da mesma viagem, em vez de selecionar a menor entre serviços diferentes.
- Resumos de operador sem horário, notas editoriais e observações históricas são mantidos separados. Validade futura exige data/horário específicos e fonte de operador; a validação estrutural **não substitui verificação humana da página para a data**.
- `legacy_projection()` delega diretamente a `get_rail_evidence()`; o adaptador de exibição, `TripPlan`, wishlist, registros históricos e prioridade de fontes permanecem imutáveis.
- Não inclui rotas novas, custos, retorno, nem UI.

## Riscos e critérios de aceite
**P1:** colapsar fonte, prova e validade temporal; fixado por enums independentes. **P1:** perder conflito/direção; fixado por `journey_identity()` e agrupamento. **P2:** interpretar `unknown` como inexistência; tempo ausente permanece `None`. **P2:** substituir o adaptador antigo; sem alteração de compatibilidade.

Testes unitários de duas direções, duas estações, serviço, URL HTTPS, data inválida, duração negativa, alias, duplicação, fontes divergentes, validade histórica/futura e projeção read-only.

**Dependência:** #108 concluído, snapshots de origem versionados. **Integração:** módulos futuros podem usar esse contrato em seus próprios PRs após revisão; este PR não publica dados novos.

**Proibição:** sem merge/deploy automático; revisão do conjunto pelo usuário ao término.
