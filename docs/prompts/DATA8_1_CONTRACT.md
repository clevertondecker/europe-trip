# DATA 8.1 — Contrato de evidências turísticas e qualidade

**Papel:** Senior Product Engineer + Data Architect + Python Engineer.
**Repositório:** `clevertondecker/europe-trip`.

## Objetivo
Estruturar as fichas de atrações **já reconciliadas** sem duplicar o catálogo principal ou afetar `TripPlan` e wishlist. O destino de uma atração é deduzido dos IDs de `build_destination_discovery()`, jamais inferido de título.

## Implementar
1. Modelagem aditiva de `experience`, `duration`, `admission`, `opening`, `seasonality`, `location` e suas evidências com URL HTTPS e `checked_at`.
2. Distinguir `unknown`, estimativa editorial, preço oficialmente publicado, entrada geral gratuita e passeio externo sem bilhete. Não transformar `unknown` ou `not_applicable` em zero monetário.
3. Rejeitar duplicatas, IDs não reconciliados, dados impossíveis e afirmações de disponibilidade 2027.
4. Preservar propostas de atrações de cidades ainda sem catálogo em `unreconciled_candidates` com `canonical_attraction_id=null`.
5. Prover `coverage_report` e `card_projection` puros, sem ranking ou persistência.
6. Testes de invariantes, identidade e não mutação do modelo oficial.

**Entrega:** `data8_attraction_evidence_model.py`, testes e este prompt. Sem alteração de `attractions_model.py`, `app.py` ou configuração, sem merge/deploy. PR 8.2 depende deste contrato.

**Aceite:** schema e testes completos; nenhuma tarifa, horário ou duração ferroviária fabricada; não selecionar cidades automaticamente.
