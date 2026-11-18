# ROUTES 7B — source-labeled planning times in UX 5.0.5

This is a stacked PR based on ROUTES 7A (#126). It does not alter `compare_wishlist_bases()` or historical data. UI now displays `~25 min · mínimo publicado` in previously blank cells, keeps `75 min · ida histórica` when a legacy record exists, and expands a read-only panel with sources and any separately published average.

The original researched coverage count remains historical-only. A new concise text reports number of historical, additional reference, local, and still unknown cells.

Source references do not prove exact stations, a weekend return, tariffs, or published 2027 availability. The interface remains a comparable 2–5-base matrix of the *same* chosen destinations. `TripPlan`, wishlist and current official base are never modified.

Accept: with the five public example destinations × three bases, 15 cells = 5 historical, 9 new reference, 1 local; 0 lacking any planning time. The test derives these counts from the current legacy model and checks source precedence. Scope intentionally avoids redesign of other screens.
