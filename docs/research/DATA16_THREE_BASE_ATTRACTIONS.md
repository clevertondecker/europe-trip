# DATA16 — Sélestat, Offenburg and Dijon vicinity discovery

Date: 2026-11-19. Research source: public, official municipal/tourism/operator pages. No private itinerary edited.

## Current canonical snapshot
- Sélestat: Bibliothèque Humaniste (DQ3.2).
- Offenburg: Museum im Ritterhaus (DQ3.2).
- Dijon: Palais des Ducs de Bourgogne and Parcours de la Chouette (DQ3.2).
- New attractions **nearby** are not automatically registered as destination-level places in the 46-destination registry; doing so would require new location IDs, coordinates, identity reconciliation and route research.

## New discovery
| Base | Candidate | Priority | Official evidence | Last-mile risk |
| --- | --- | --- | --- | --- |
| selestat | Château du Haut-Koenigsbourg (Orschwiller, França) | high | https://www.haut-koenigsbourg.fr/en/practical-informations/ | seasonal_shuttle_2026_only |
| selestat | Réserve naturelle de l’Illwald (Sélestat, França) | high | https://www.selestat-haut-koenigsbourg.com/decouvrir/incontournables/illwald/ | route_not_verified |
| selestat | Abbatiale Saint-Maurice d’Ebersmunster (Ebersmunster, França) | medium | https://www.selestat-haut-koenigsbourg.com/decouvrir/nos-communes/ebersmunster/ | unknown |
| selestat | Remparts et Tour des Sorcières (Châtenois, França) | medium | https://www.selestat-haut-koenigsbourg.com/a-voir-a-faire/monuments-remarquables/ | unknown |
| selestat | Volerie des Aigles / Château de Kintzheim (Kintzheim, França) | medium | https://www.visit.alsace/en/sit/222004436-chateau-de-kintzheim/ | seasonal_opening_unknown_2027 |
| offenburg | Altstadt Gengenbach (Gengenbach, Alemanha) | high | https://www.schwarzwald-tourismus.info/attraktionen/gengenbach-ceeaea1a49 | exact_timetable_unverified |
| offenburg | Schloss Staufenberg (Durbach, Alemanha) | high | https://www.ortenau-tourismus.de/kulturhighlights | last_mile_and_return_unknown |
| offenburg | Allerheiligen Wasserfälle (Oppenau, Alemanha) | high | https://www.schwarzwald-tourismus.info/attraktionen/allerheiligen-wasserfaelle-b9918d8834 | full_roundtrip_unknown |
| offenburg | Der Salmen (Offenburg, Alemanha) | medium | https://www.offenburg.de/de/leben-in-offenburg/kultur/freiheitsstadt-offenburg/der-salmen/ | local_walk_not_measured |
| offenburg | Gifiz-See (Offenburg, Alemanha) | medium | https://offenburg.de/de/zu-gast-in-offenburg/touristinfo/stadtfuehrungen/ | local_transport_not_verified |
| dijon | Cité internationale de la gastronomie et du vin (Dijon, França) | high | https://www.destinationdijon.com/destination/culture-patrimoine/cite-internationale-de-la-gastronomie-et-du-vin-dijon-fr-6024697/ | local_walk_not_measured |
| dijon | Château du Clos de Vougeot (Vougeot, França) | high | https://www.bourgogne-tourisme.com/chateaux/chateau-du-clos-de-vougeot-3 | last_mile_and_return_unknown |
| dijon | Abbaye de Fontenay (Marmagne, França) | high | https://www.destinationdijon.com/en/destination-dijon-metropole/culture-heritage/abbaye-de-fontenay-marmagne-en-6025654/ | no_car_access_unverified |
| dijon | Château et village de Châteauneuf-en-Auxois (Châteauneuf-en-Auxois, França) | medium | https://www.bourgogne-tourisme.com/sejourner/ou-aller-bourgogne-villes-villages-territoires/top-5-des-plus-beaux-villages-de-bourgogne/chateauneuf-en-auxois-village-et-chateau/ | unknown |
| dijon | Le Cassissium (Nuits-Saint-Georges, França) | medium | https://en.destinationdijon.com/cultural-heritage/le-cassissium/ | station_last_mile_unknown |

## Why this changes our base shortlist
- Sélestat now stands out for castles and nature as well as the fast Strasbourg–Colmar rail axis. **The 2026 Haut-Koenigsbourg L500 shuttle is documented**, but confirm autumn-2027 schedule; other trailheads may need bus or bicycle.
- Offenburg has more than cross-border Strasbourg access: Gengenbach's historic centre, Durbach/Staufenberg, and Allerheiligen waterfalls give it Black Forest weekend potential. Durbach bus 7142 and Oppenau area bus 425 are infrastructure references only; travel from lodging and returns remain unknown.
- Dijon adds vineyard heritage, gastronomy and UNESCO abbey/medieval villages. **Beaune is already a destination**, so don't create a duplicate; Clos de Vougeot, Cassissium and Fontenay are different POIs. Fontenay and Châteauneuf in particular need last-mile verification.

## Housing gap
Sélestat has no qualified short-let quote in the original research; its general property index is not a two-person apartment for 55–65 nights. Offenburg has examples of temporary furnished housing (including a boardinghouse), but no 2027 availability/two-person total. Dijon has 2026 market snapshots, not a 2027 quote. Do not turn any of these into a comparative housing score.

## Follow-up before promotion to app
1. Confirm precise municipality and location identity for each candidate. If outside existing destination registry, define new destination IDs *only once* and enforce duplicate checks.
2. Collect transport operator trips *from each selected base*, local last mile, weekend return and seasonality; do not infer from a nearby station or one-way minimum.
3. Verify opening in September–November 2027, prices and citations where published; otherwise keep null.
4. Reconcile existing canonical attractions and DQ3.2 POIs before adding candidates to UI.
5. Compare two-adult furnished apartments for 55–65 nights, taxes, deposit, internet, station distance. No live property qualifies yet.

This PR adds a vetted **research queue** without inflating rail coverage, tourism counts, costs, or TripPlan.
