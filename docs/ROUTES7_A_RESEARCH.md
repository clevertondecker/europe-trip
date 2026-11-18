# ROUTES 7A — historical route-summary research, 15 fixed pairs

Three existing cities (Mulhouse, Strasbourg, Lille) × five selected public demo destinations (Belfort, Haguenau, Mulhouse, Brussels, Ghent). Nine cells previously without time gain an explicitly identified **published fastest travel-time reference**. This is not an observed itinerary, typical service, a weekend schedule, or a 2027 quote.

Dataset: `data/routes7_priority_reference_2026_11.json`. Loader: `routes7_reference_model.py`. Source of baseline research: `europa2027_pesquisa_15_pares.csv` checked 17 Nov 2026. One local movement has no railway duration. Sources are the direct SNCF Connect route-summary pages and three Trainline aggregate overview pages, supplied per row with caveats.

Rules: source summaries without an explicit exact platform/station are `station_not_reconciled`; in particular **Belfort-Ville versus Belfort-Montbéliard TGV**, **Lille-Flandres versus Lille-Europe**, and Ghent Gent-Sint-Pieters. Numeric values are reference minima, not 2027 date-specific timetables. A source average is included only if stated in the research CSV, with weaker confidence and no inference of transfer count, fares or weekend frequency.

**Do not overwrite** `get_rail_evidence()`, `rail_evidence_unified_model.py`, historical data, TripPlan, wishlist, or city-base preferences. Existing 75-minute Lille→Ghent and 49-minute Strasbourg→Mulhouse remain authoritative in legacy presentation. This overlay also carries 68-minute and 49-minute route references separately; differences are not collapsed into a 'best' service.

Acceptance: 15 unique directional pairs, 14 external minimum references + 1 local, 9 additional reference minima, one-way only, 0 fabricated return/cost/connection, exact baseline preserved. Next: separate UX consumer PR and a sparse estimates/caveats PR; no automatic merge.
