# DATA17 — Liège-origin visibility in destination discovery

**Checked:** 2026-11-19. **Scope:** Liège-Guillemins one-way minimums only, without claiming valid 2027 service, return, local travel, or attraction access.

The user confirmed the missing-times screenshot's selected base was **Liège**, not Saint-Louis. Baseline projection (DATA15): 544 / 1350 displayable directed pairs. Four source-matched pairs should yield 548 / 1350 (40.59%) **only if projection CI confirms**.

| Origin | Destination | Operator minimum | Source | Specific caution |
|---|---|---:|---|---|
| liege | dijon | 5h01 (301 min) | https://www.sncf-connect.com/train/trajet/liege/dijon | Liège-Guillemins to Dijon; SNCF page states 5h01 as shortest, connections; no 2027 schedule |
| liege | reims | 3h53 (233 min) | https://www.sncf-connect.com/train/trajet/liege/reims | Liège-Guillemins to Reims; SNCF page states 3h53 as shortest; transfer in Paris requires station change |
| liege | mulhouse | 5h51 (351 min) | https://www.sncf-connect.com/train/horaires/liege/mulhouse | Liège-Guillemins to Mulhouse; SNCF timetable dated 2026-10-02 states 5h51 and 2 changes |
| liege | besancon | 7h35 (455 min) | https://www.sncf-connect.com/train/trajet/liege/besancon | Liège-Guillemins to Besançon Viotte; SNCF route page states 7h35 as shortest with connections |

Liège already had DATA13 minima for Paris, Lille, Strasbourg, Basel, Luxembourg, Metz, Nancy, Colmar, Lyon, Amsterdam, Ghent, Bruges; and older references for Brussels, Cologne, Luxembourg, Aachen. These are **not duplicates** and were left untouched.

**Rejected from this batch:** Liège → Belfort operator arrival was Belfort–Montbéliard TGV, which is not equivalent to central Belfort without extra transport. Liège → Namur has operator line timetables but no route-specific minimum reconciled in this batch. No route is computed by adding neighboring minima or reversing directions.

CI acceptance must include `python -m compileall -q .`, `python tools/validate_research_data.py`, `python -m unittest discover -s tests`, and `python tools/audit_data13_coverage.py --json`. The main screen should show the four references only when Liège is chosen as base, while preserving "unknown" for gaps.
