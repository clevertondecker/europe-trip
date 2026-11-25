"""UX127: shared official reference, independent of simulation widget state."""
from __future__ import annotations

from data_model import calculate_scenario, get_scenario
from unified_budget import resolve_french_budget
from attractions_model import excursions_overage_brl

# Existing reference FX assumptions, not a new quote or live exchange rate.
REFERENCE_EUR_BRL = 6.3
REFERENCE_CHF_BRL = 7.1


def official_budget_projection(data, source_live, plan, costs):
    """Keep the selected spreadsheet scenario, plus known excursion excess.

    The spreadsheet scenario is a reference for its stated duration. Changes
    to itinerary days are shown as context, not silently repriced by simulator
    assumptions. Unknown excursion prices are not zero or a saving.
    """
    scenario = get_scenario(data, plan["budget_scenario"])
    baseline = calculate_scenario(scenario)
    french = resolve_french_budget(scenario, source_live)
    allowance = french["amounts"]["excursions"]
    known = costs["known_by_currency"]
    overage = excursions_overage_brl(known["EUR"], known["CHF"],
                                    REFERENCE_EUR_BRL, REFERENCE_CHF_BRL, allowance)
    total = round(baseline["total"] + overage, 2)
    margin = round(scenario["cap_brl"] - total, 2)
    return {"scenario": scenario, "baseline": baseline, "french": french,
            "total": total, "margin": margin, "cap": scenario["cap_brl"],
            "known_excursions_overage_brl": overage,
            "missing": tuple(costs.get("missing", ())),
            "has_unknown_costs": bool(costs.get("missing")),
            "reference_days": scenario["days"], "planned_days": plan["total_days"],
            "source": french["source"]}


def official_budget_for_plan(data, source_live, plan, catalog=None, routes=None):
    """Use the same France outing scope for every official screen."""
    from attractions_model import load_attractions, load_base_routes, package_cost
    from itinerary_flow_model import selected_rows, FRANCE_STAGE
    catalog = load_attractions() if catalog is None else catalog
    routes = load_base_routes() if routes is None else routes
    selected = [row["id"] for row in selected_rows(plan, catalog)
                if row["stage"] == FRANCE_STAGE]
    chosen = [item for dest in selected for item in plan["packages"].get(dest, [])]
    costs = package_cost(catalog, routes, plan["base_city"], chosen,
                         planned_destination_ids=selected)
    return official_budget_projection(data, source_live, plan, costs)
