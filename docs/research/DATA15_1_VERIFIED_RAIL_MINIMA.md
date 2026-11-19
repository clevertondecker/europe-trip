# DATA15.1 — First independently reviewed directional rail minima

**Research date:** 2026-11-19  
**Baseline:** 526/1350 displayable directed base→destination pairs (38.96%).  
**Target:** 945/1350 (70%; +419 beyond baseline). No target completion is claimed from this batch.

## Admitted evidence (operator pages opened and checked)
| Origin | Destination | 2026 published minimum | Operator route URL | Caveat |
| --- | --- | --- | --- | --- |
| belfort | lille | 4h58 (298 min) | https://www.sncf-connect.com/train/trajet/belfort/lille | Belfort Ville listed; Lille Europe/Flandres; station-specific fastest service not inferred |
| reims | lausanne | 6h22 (382 min) | https://www.sncf-connect.com/train/trajet/reims/lausanne | Route may involve connections; dated return unverified |
| belfort | reims | 3h55 (235 min) | https://www.sncf-connect.com/train/trajet/belfort/reims | Belfort Montbeliard TGV/Meroux appears on source; station equivalence not assumed |
| reims | lyon | 3h24 (204 min) | https://www.sncf-connect.com/train/trajet/reims/lyon | Route may involve connections; dated return unverified |

All records are outbound-only, source-specific `official_operator_minimum` and have a matched manifest. The displayed minimum is an observed published value, not a guarantee of direct train, particular station, fare, weekend return, late arrival, or 2027 service.

## Rejected evidence
**Belfort → Arras**: search index returned 3h55, but the operator page directly opened showed 4h55. This disagreement is unresolved; **no record promoted**.

## Quality gate
1. Every pair is an allowed base and catalog destination and was not in DATA10/11/12/13, rail gap, ROUTES7, five-base, expanded rail or legacy route source inventory reviewed at ingestion time.
2. Every admitted page displays the precise `Durée du trajet le plus court` label for the requested direction.
3. `validate_record_url` verifies official host and origin/destination slugs.
4. The new fixture and independent manifest date/URL/value/status must agree.
5. Coverage increase is reported only by `python tools/audit_data13_coverage.py --json`, not assumed from appended row count.
6. No reciprocal journeys inferred. Human review is still required for future schedule and station-specific feasibility.

## Next batches
Continue round-robin `tools/data13_research_queue.py` across undercovered bases; reject search-only snippets without exact page observation, stale mismatches and station ambiguity that changes interpretation. PR scope remains incremental; no fabricated bulk dataset to meet 50%/70%.
