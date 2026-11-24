"""Live, transparent financial projection for the travel advisor.

City housing figures are *editorial 2026 monthly reference values*, never
quotes for 2027. Rent replaces the already-budgeted rent component.
Changing an optimization profile alone changes recommendation weights, not
the price of a trip: no invented financial impact.
"""
from __future__ import annotations
from decimal import Decimal
from city_compare import load_cities
from data_model import get_scenario, calculate_scenario
from unified_budget import resolve_french_budget,scenario_total
from attractions_model import excursions_overage_brl

# Simulation assumptions only; never used by official_projection.
DEFAULT_OUTINGS_WEEKLY = 2
DEFAULT_OUTING_COUPLE_EUR = 60

def official_projection(data:dict,finance_live:bool,plan:dict,
                        costs:dict,eur_fx:float,chf_fx:float)->dict:
    """Preserve the spreadsheet total; add only known excursion overage."""
    scenario=get_scenario(data,plan["budget_scenario"])
    baseline=calculate_scenario(scenario)
    french=resolve_french_budget(scenario,finance_live)
    french_days=plan["total_days"]-plan["italy_days"]
    allocation=float(french["amounts"]["excursions"])*french_days/french["french_days"]
    overage=excursions_overage_brl(costs["known_by_currency"]["EUR"],
                                  costs["known_by_currency"]["CHF"],
                                  eur_fx,chf_fx,allocation)
    total=round(baseline["total"]+overage,2) if overage else baseline["total"]
    return {"baseline_total":baseline["total"],"baseline_margin":baseline["balance"],
            "known_excursions_overage_brl":overage,"total":total,
            "margin":round(scenario["cap_brl"]-total,2),
            "missing_count":len(costs.get("missing",[])),
            "budget_excursions_allowance_brl":allocation}

def official_plan_costs(plan:dict,catalog:dict,routes:dict)->dict:
    """Use the same selected visits and transport basket in every official view."""
    from itinerary_flow_model import selected_rows, FRANCE_STAGE
    from attractions_model import package_cost
    selected=[a for group in plan["packages"].values() for a in group]
    cities=[row["id"] for row in selected_rows(plan,catalog)
            if row["stage"]==FRANCE_STAGE]
    return package_cost(catalog,routes,plan["base_city"],selected,
                        planned_destination_ids=cities)

def city_reference_rent(base:str,cities:dict|None=None)->float|None:
    data=cities if cities is not None else load_cities()
    for item in data["cities"]:
        if item["name"].casefold()==base.casefold():
            return float(item["reference_rent_eur"])
    return None

def advisor_projection(data:dict,source_live:bool,plan:dict,
                       costs:dict,eur_fx:float,chf_fx:float,
                       use_city_rent:bool=True,cities:dict|None=None)->dict:
    """Simulate totals using behavioral assumptions, not official budget values."""
    scenario=get_scenario(data,plan["budget_scenario"])
    french=resolve_french_budget(scenario,source_live)
    french_days=plan["total_days"]-plan["italy_days"]
    rent=city_reference_rent(plan["base_city"],cities) if use_city_rent else None
    allocation=float(french["amounts"]["excursions"])*french_days/french["french_days"]
    overage=excursions_overage_brl(costs["known_by_currency"]["EUR"],
                                  costs["known_by_currency"]["CHF"],
                                  eur_fx,chf_fx,allocation)
    result=scenario_total(scenario,french,french_days=french_days,
        outings_weekly=DEFAULT_OUTINGS_WEEKLY,outing_couple_eur=DEFAULT_OUTING_COUPLE_EUR,fx_brl_per_eur=eur_fx,
        rent_override_eur_month=rent,excursions_delta_brl=overage)
    known_brl=(Decimal(str(costs["known_by_currency"]["EUR"]))*Decimal(str(eur_fx))
               +Decimal(str(costs["known_by_currency"]["CHF"]))*Decimal(str(chf_fx)))
    return {"result":result,"scenario":scenario,"rent_eur_month":rent,
            "city_rent_mode":"reference_2026" if rent is not None else "budget_baseline",
            "known_billets_brl":round(float(known_brl),2),
            "budget_excursions_allowance_brl":allocation,
            "known_excursions_overage_brl":overage,
            "has_unknown_costs":bool(costs.get("missing")),
            "profile_affects_price":False}
