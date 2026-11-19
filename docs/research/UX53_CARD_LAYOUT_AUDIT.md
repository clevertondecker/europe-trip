# UX 5.3 — Card layout audit (2026-11-19)

## Confirmed source-level problem
The 3-column discovery grid rendered text/credits, optional source links and native action widgets in independent `st.container(border=True)` instances without an opt-in equal-height layout and fixed footer position. Variable text changes card height and action placement.

## Targeted implementation
- Discovery: scoped equal-height rows/cards; group native source, expander and add-to-list action in bottom footer.
- DQ3.2 cards: scoped equal-height two-column rows/cards and bottom actions.
- Five base comparison: scoped two-column rows/cards and bottom detail button.
- CSS: `st-key-ux53_*` selectors only; no global rules for all Streamlit containers.
- Expanders remain native and readable, may grow the entire row; no text truncation or artificial clipping.

## Inventory (source-level risk, not measured visual defect)
| Screen/module | Layout | Decision |
| --- | --- | --- |
| `ux501_destination_discovery_ui.py` | Discovery 3-column grid | Fix |
| `attractions_ui.py` | DQ3.2 rail 2-column grid | Fix |
| `base_research_expanded_ui.py` | Five-base comparison pairs | Fix |
| `base_explorer_ui.py` | Standalone detail panels | Keep natural height |
| `scenario_board_ui.py` | Sequential editable panels | Keep natural height |
| `my_outings_ui.py` | Sequential itinerary panels | Keep natural height |
| `italy_honeymoon_ui.py` | Mixed report/summary panels | Keep natural height |
| `five_base_comparison_ui.py` | Detailed comparison | Keep natural height |
| `city_profiles_ui.py` | Selected profile detail | Keep natural height |
| `discovery_ui.py` | Sequential recommendation panels | Keep natural height |

## Acceptance
Structural tests cannot certify rendered geometry. Browser test desktop 1440/1024 px; tablet 768 px and mobile 390 px. Check >=3 cards with different lengths, source absent/present, local/remote/fallback photos, saved state, and expanded details. Card bottoms within <=2px in desktop row, native buttons aligned, no lost attribution or keyboard controls, no overflow. Screenshots should be attached to PR before visual sign-off.

This change does not update TripPlan, persisted interests, route evidence, budgets or authentication.
