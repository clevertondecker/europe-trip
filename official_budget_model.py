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
            "outings_available": costs.get("available", True),
            "known_by_currency": dict(known),
            "destination_ids": tuple(costs.get("destination_ids", ())),
            "reference_days": scenario["days"], "planned_days": plan["total_days"],
            "source": french["source"]}


def official_budget_for_plan(data, source_live, plan, catalog=None, routes=None):
    """Use the same France outing scope for every official screen."""
    from attractions_model import load_attractions, load_base_routes, package_cost
    from itinerary_flow_model import selected_rows, FRANCE_STAGE
    catalog = load_attractions() if catalog is None else catalog
    routes = load_base_routes() if routes is None else routes
    from destination_identity import outing_destination_id
    try:
        rows = [row for row in selected_rows(plan, catalog) if row["stage"] == FRANCE_STAGE]
        selected = [row["id"] for row in rows]
        # selected_rows deliberately skips obsolete destinations in old drafts.
        # Detect that omission here rather than treating it as a zero-cost trip.
        requested = {outing_destination_id(key) for key in plan.get("packages", {})}
        requested.update(outing_destination_id(row["destination_id"])
                         for row in plan.get("flexible_visits", [])
                         if row["stage"] == FRANCE_STAGE)
        if not requested <= set(selected):
            raise ValueError("Passeios do plano ausentes no catálogo atual")
        chosen = [item for row in rows for item in row["attractions"]]
        costs = package_cost(catalog, routes, plan["base_city"], chosen,
                             planned_destination_ids=selected)
        costs = {**costs, "destination_ids": selected}
    except ValueError:
        # A legacy selection may no longer be valid. Keep the spreadsheet's
        # entire reference (including its original outing allowance), without
        # presenting an unverified additional amount as a calculated zero.
        costs = {"known_by_currency": {"EUR": 0., "CHF": 0.},
                 "missing": ["Passeios do plano não validados no catálogo atual"],
                 "available": False}
    return official_budget_projection(data, source_live, plan, costs)



def official_simulation_result(snapshot):
    """Read-only initial simulation state, exactly equal to official reference."""
    original = snapshot["french"]["amounts"]
    components = {key: round(amount, 2) for key, amount in original.items()}
    overage = snapshot["known_excursions_overage_brl"]
    components["excursions"] = round(original["excursions"] + overage, 2)
    margin = snapshot["margin"]
    cap = snapshot["cap"]
    status = ("acima_do_teto" if margin < 0 else
              "apertado" if margin < cap * .05 else "margem_condicional")
    return {"total": snapshot["total"], "margin": margin, "status": status,
            "reserve_already_in_total": snapshot["scenario"]["emergency_reserve_brl"],
            "new_components": components,
            "deltas": {key: overage if key == "excursions" else 0. for key in original},
            "flight_delta": 0., "source": snapshot["source"],
            "budget_fraction": round(snapshot["total"] / cap, 4),
            "days": snapshot["french"]["french_days"]}
