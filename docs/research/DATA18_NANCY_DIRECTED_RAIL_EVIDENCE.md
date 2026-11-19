# DATA18 — Nancy base railway gap enrichment

Research date: 2026-11-19. Nancy is the selected origin in the user screenshot (Nancy is "Local" in the table). Saint-Louis is the selected *destination*, not the origin.

## New source-matched direction-specific minimums

| Origin | Destination | Published minimum | Source tier | URL | Caveat |
| --- | --- | ---: | --- | --- | --- |
| Nancy | saverne | 0h56 (56 min) | official_operator_minimum (medium) | https://www.sncf-connect.com/train/trajet/nancy/saverne | SNCF route and dated timetable both show shortest published 0h56; several other departures take 0h58+ |
| Nancy | selestat | 1h43 (103 min) | official_operator_minimum (medium) | https://www.sncf-connect.com/train/horaires/nancy/selestat | SNCF timetable snapshot dated 2026-11-03 shows shortest 1h43; not a 2027 schedule |
| Nancy | freiburg | 2h52 (172 min) | official_operator_minimum (medium) | https://www.sncf-connect.com/train/horaires/nancy/fribourg-en-brisgau | SNCF timetable 2026-11-07 explicitly shows 2h52; do not reverse Freiburg->Nancy |
| Nancy | cologne | 4h39 (279 min) | official_operator_minimum (medium) | https://www.sncf-connect.com/train/trajet/nancy/cologne | SNCF published 4h39, via Strasbourg/Mannheim on sample; connections not included in weekend feasibility |
| Nancy | kehl | 1h49 (109 min) | secondary_route_minimum (low) | https://www.thetrainline.com/en/train-times/nancy-to-kehl | Trainline Nancy–Kehl published fastest 1h49; at least one connection |
| Nancy | esch | 1h38 (98 min) | secondary_route_minimum (low) | https://www.thetrainline.com/en/train-times/nancy-to-esch-sur-alzette | Trainline Nancy–Esch-sur-Alzette published fastest 1h38; connection needed |
| Nancy | namur | 3h51 (231 min) | secondary_route_minimum (low) | https://www.thetrainline.com/en/train-times/nancy-to-namur | Trainline Nancy–Namur published fastest 3h51; connection required |
| Nancy | bruges_be | 4h46 (286 min) | secondary_route_minimum (low) | https://www.thetrainline.com/en/train-times/nancy-to-bruges-brugge | Trainline destination is Bruges (Brugge), Belgium, not Bruges (France); at least two changes |
| Nancy | beaune | 3h07 (187 min) | secondary_route_minimum (low) | https://www.thetrainline.com/en/train-times/nancy-to-beaune | Trainline Nancy–Beaune published fastest 3h07; no 2027 return evidence |

## Existing data preserved

Nancy already had published time references for Paris, Metz, Strasbourg, Luxembourg, Colmar, Lille, Reims, Mulhouse, Thionville, Arras, Épernay, Saint-Louis, Belfort, Amsterdam, Karlsruhe, Brussels, Haguenau, Besançon, Lyon, Basel, Lausanne, Liège and Rotterdam. No existing pair was overwritten.

For Freiburg, the legacy `base_destination_routes_2027` metadata was an undated broad route link **without a verified minimum**; the DATA18 directional operator value is a low-precedence fallback, not replacement of a validated timetable.

## Source discipline and rejected candidates

- The 4 SNCF pages were directly opened and their published shortest-time text reconciled. The Nancy→Saverne search snippet was 0h58, but two opened SNCF pages unambiguously give 0h56, so 0h56 is recorded with the discrepancy flagged as a snapshot issue.
- The five Trainline sources are individually directional and identify the correct destination, including Belgium's Bruges (Brugge). Their `secondary_route_minimum` records have **low confidence** rather than being presented as operator proof.
- Nancy→Gent-Sint-Pieters was not admitted as generic Ghent because the named station vs city identity has not been reconciled.
- Missing Lörrach, Interlaken, Lauterbrunnen and other tourist destinations stay unresearched until route-specific operator or comparable source can be checked.
- No two shortest trips were summed, no reverse direction inferred, no fare or 2027 return recorded. No operator minimum proves door-to-door access to a particular attraction.

Projection gate: baseline DATA17 548/1350. If all nine are displayed, DATA18 reaches **557/1350 (41.26%)**, leaving 793 unknown pairs. Do not claim the new coverage until CI/audit succeeds.
