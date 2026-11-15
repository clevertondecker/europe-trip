"""Profile-based financial scenario comparisons using concrete catalog outings.

These are what-if plans, not bookings or verified full-price 2027 quotes.
"""
from __future__ import annotations
from copy import deepcopy
from attractions_model import package_cost
from advisor_finance import advisor_projection
from destination_recommender import recommend_destinations
from travel_optimizer import propose_schedule

PROFILE_COUNTS={"economy":2,"balanced":4,"experience":6}
PROFILE_LABELS={"economy":"Econômico","balanced":"Equilibrado","experience":"Aproveitar ao máximo"}

def build_profile_scenarios(plan:dict,catalog:dict,routes:dict,
                            financial_data:dict,source_live:bool,
                            eur_fx:float,chf_fx:float,use_city_rent:bool=True,
                            allow_overnight:bool=False)->list[dict]:
    """Generate candidate budgets from actual attractions, never % multipliers."""
    options=[]
    for profile in ("economy","balanced","experience"):
        suggestions=recommend_destinations(plan,catalog,routes,profile=profile,
                                           allow_overnight=allow_overnight,limit=11,
                                           eur_fx=eur_fx,chf_fx=chf_fx)
        # Existing chosen excursions cannot be silently removed.
        proposal=deepcopy(plan)
        proposal["profile"]=profile
        new=[]
        capacity=max(0,PROFILE_COUNTS[profile]-len(plan["packages"]))
        for rec in suggestions:
            if len(new)>=capacity:break
            if rec["missing"] and profile=="economy":
                # Still allow historical conditional routes if otherwise no contenders;
                # missing prices will be reported, never considered zero.
                continue
            proposal["packages"][rec["destination_id"]]=rec["selected_attractions"]
            new.append(rec)
        if profile=="economy" and not new and capacity:
            for rec in suggestions[:capacity]:
                proposal["packages"][rec["destination_id"]]=rec["selected_attractions"]
                new.append(rec)
        all_ids=[a for picks in proposal["packages"].values() for a in picks]
        cost=package_cost(catalog,routes,plan["base_city"],all_ids)
        financial=advisor_projection(financial_data,source_live,proposal,cost,
                                     eur_fx,chf_fx,use_city_rent=use_city_rent)
        itinerary=propose_schedule(proposal,catalog,routes,profile=profile,max_variants=1)
        best=itinerary[0] if itinerary else None
        options.append({
            "profile":profile,"label":PROFILE_LABELS[profile],
            "plan_id":plan["plan_id"],"base_revision":plan["revision"],
            "base_city":plan["base_city"],
            "new_destinations":[r["destination_id"] for r in new],
            "new_recommendations":new,
            "proposal_packages":deepcopy(proposal["packages"]),
            "preview_assignments":best["assignments"] if best else deepcopy(plan["assignments"]),
            "unresolved":best["unresolved"] if best else [],
            "scheduled_count":len(best["assignments"]) if best else len(plan["assignments"]),
            "known_cost_by_currency":cost["known_by_currency"],
            "missing_costs":cost["missing"],
            "conditional_discounts":cost["conditional"],
            "financial":financial,
            "budget_exceeded":financial["result"]["margin"]<0,
            "quote_complete_for_2027":False,
            "assumptions":"Valores históricos e rubricas da planilha. Nenhuma tarifa ou abertura de 2027 confirmada.",
        })
    return options
