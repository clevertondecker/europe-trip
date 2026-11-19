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


## DATA15.2 — Second verified operator-page batch

Twelve new direction-specific SNCF minima were checked in the original route-page content. These pages may be cached 2026 material. Source/minimum identity checks and 2027 caveats are identical to DATA15.1.

| Origin | Destination | Published 2026 minimum | Source |
|---|---|---:|---|
| haguenau | mulhouse | 1h34 (94 min) | https://www.sncf-connect.com/train/trajet/haguenau/mulhouse |
| haguenau | belfort | 2h01 (121 min) | https://www.sncf-connect.com/train/trajet/haguenau/belfort |
| belfort | saint_louis | 0h53 (53 min) | https://www.sncf-connect.com/train/trajet/belfort/saint-louis |
| belfort | selestat | 1h10 (70 min) | https://www.sncf-connect.com/train/trajet/belfort/selestat |
| belfort | beaune | 1h45 (105 min) | https://www.sncf-connect.com/train/trajet/belfort/beaune |
| belfort | haguenau | 2h07 (127 min) | https://www.sncf-connect.com/train/trajet/belfort/haguenau |
| reims | mulhouse | 3h08 (188 min) | https://www.sncf-connect.com/train/trajet/reims/mulhouse |
| reims | metz | 1h08 (68 min) | https://www.sncf-connect.com/train/trajet/reims/metz |
| reims | besancon | 4h32 (272 min) | https://www.sncf-connect.com/train/trajet/reims/besancon |
| reims | beaune | 3h45 (225 min) | https://www.sncf-connect.com/train/trajet/reims/beaune |
| reims | arras | 2h29 (149 min) | https://www.sncf-connect.com/train/trajet/reims/arras |
| reims | saint_louis | 3h24 (204 min) | https://www.sncf-connect.com/train/trajet/reims/saint-louis |

**Rejections and quality caveats:** Haguenau→Dijon yielded conflicting source retrievals (2h56 vs 2h48) and Haguenau→Lille differed (3h45 vs 4h01); both were omitted. No source evidence claims a 2027 date-specific return or station-to-attraction accessibility.

**Projection target for this branch:** 542/1350 (40.15%) if the actual display audit and CI pass. This is a testable target, not an observed outcome until the pipeline passes.


## DATA15.3 — Two additional source-checked routes

| Origin | Destination | Minimum from selected SNCF route page | Station / provenance caveat |
| --- | --- | ---: | --- |
| belfort | besancon | 1h10 (70 min) | Belfort-Ville → Besançon Viotte explicitly named on operator page — https://www.sncf-connect.com/train/trajet/belfort/besancon |
| saverne | saint_louis | 1h44 (104 min) | General route-page minimum 1h44; separate dated /horaires snapshot displayed 1h43, so not a date-specific guarantee — https://www.sncf-connect.com/train/trajet/saverne/saint-louis |

The route-specific `/train/trajet/` page for Saverne→Saint-Louis publishes 1h44; a separate September timetable snapshot includes a 1h43 trip. They are not automatically reconciled. The recorded value describes **the cited page's published minimum**, not a claim about universal network minimum or a 2027 itinerary.

If the app projection passes, total coverage becomes **544/1350 = 40.30%** and 401 further pairs are needed to reach 70%.

## Independent reviewer source reconciliation — 2026-11-19

A code review independently reopened all 18 cited SNCF `/train/trajet/` pages and compared their explicitly labeled "Durée du trajet le plus court" to the DATA15 manifest. **Five records did not match** the independently observed operator page; they have been corrected rather than silently accepted from internal fixtures:

| Pair | Previously captured | Independently rechecked page |
| --- | ---: | ---: |
| belfort → saint_louis | 54 min | 53 min |
| belfort → haguenau | 146 min | 127 min |
| reims → mulhouse | 158 min | 188 min |
| reims → besancon | 289 min | 272 min |
| reims → arras | 137 min | 149 min |

The other 13 source-page minima matched. Source HTML/index snapshots are time-sensitive: this audit establishes agreement with the page material available during this recheck, not that the duration is invariant across dates or that a train can be booked for the 2027 trip. The JSON remains an indicative outbound-only fallback and must not be treated as train-station-matched trip feasibility.
