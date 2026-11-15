"""Sourced weekend meals and an explicit *non-persistent* budget reconciliation.

Safeguards:
- Grocery unit-price examples do not equal daily food expenditure.
- Weekend menus are used only on assigned matching days.
- No regular rail fare means no complete couple rail cost.
- A meal already represented by the baseline dining envelope is never added twice.
- Reconciled preview is suppressed for incomplete meal/fare coverage.
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path
import json

from attractions_model import package_cost
from advisor_finance import advisor_projection
from outing_guide_model import build_outing_guide
from research_cost_model import load_research,menu_examples,rail_cost_options

PATH=Path(__file__).resolve().parent/"data"/"grocery_weekend_evidence_2026_11.json"
PROFILES={"economy":"low","balanced":"median","experience":"high"}


def load_extended_research(path:Path=PATH)->dict:
    data=json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema_version")!=1 or not data.get("checked_at"):
        raise ValueError("Extended evidence schema not supported")
    for row in data.get("groceries",[]):
        price=Decimal(str(row["amount_eur"]))
        if not price.is_finite() or price<=0 or not row["source_url"].startswith("https://"):
            raise ValueError("Invalid grocery observation")
    for row in data.get("weekend_restaurants",[]):
        price=Decimal(str(row["price_per_person"]))
        if (not price.is_finite() or price<=0 or
            not set(row["days"])<= {"sat","sun"} or not row["days"] or
            not row["source_url"].startswith("https://")):
            raise ValueError("Invalid weekend restaurant")
    return data


def grocery_reference(data:dict|None=None)->dict:
    """Total of only four photographed unit prices, NOT a food budget."""
    rows=(data if data is not None else load_extended_research())["groceries"]
    return {"rows":rows,"sample_basket_eur":round(sum(float(x["amount_eur"]) for x in rows),2),
            "not_complete_food_basket":True,"not_city_specific":True}


def day_of_outing(plan:dict,destination:str)->dict:
    entries=sorted(day for day,place in plan.get("assignments",{}).items()
                   if place==destination)
    if not entries:
        return {"date":None,"day":"undated","status":"not_scheduled"}
    travel_date=date.fromisoformat(entries[0])
    return {"date":entries[0],
            "day":("sat" if travel_date.weekday()==5
                   else "sun" if travel_date.weekday()==6 else "weekday"),
            "status":"assigned_provisionally"}


def meal_observations(city:str,day:str,base_research:dict,
                      extended:dict)->dict:
    """Return only day-eligible restaurant examples, without inferred menus."""
    if day in {"sat","sun"}:
        rows=[{"city":x["city"],"venue":x["venue"],
               "price_per_person":x["price_per_person"],
               "currency":x["currency"],"menu":x["menu"],
               "source_url":x["source_url"],"notes":x["notes"],
               "availability":"fim de semana: "+", ".join(x["days"])}
              for x in extended["weekend_restaurants"]
              if x["city"]==city and day in x["days"]]
        return {"items":rows,"day":day,
                "confidence":"published_weekend_menu_not_date_confirmed"}
    if day=="weekday":
        result=menu_examples(city,base_research)
        return {"items":result["items"],"day":day,
                "confidence":"published_weekday_menu_not_date_confirmed"}
    return {"items":[],"day":day,"confidence":"date_needed_to_select_meal"}


def _sample(values:list[float],profile:str)->float:
    if profile not in PROFILES:raise ValueError("Invalid profile")
    ordered=sorted(values)
    if profile=="economy":return ordered[0]
    if profile=="experience":return ordered[-1]
    n=len(ordered)
    return (ordered[(n-1)//2]+ordered[n//2])/2


def reconcile_researched_itinerary(plan:dict,catalog:dict,routes:dict,
                                   financial_data:dict,source_live:bool,
                                   eurfx:float,chffx:float,
                                   use_city_rent:bool=True,
                                   base_research:dict|None=None,
                                   extended:dict|None=None)->dict:
    """Return reversible preview; never writes to TripPlan, file or global budget.

    All selected destinations require a normal fare or local-journey status
    and a date-appropriate published lunch to offer a reconciled scenario.
    Even then the result is a *partial 2026 comparison*, not a full 2027 quote.
    """
    if eurfx<=0 or chffx<=0:raise ValueError("Invalid exchange rate")
    evidence=base_research if base_research is not None else load_research()
    new_data=extended if extended is not None else load_extended_research()
    all_ids=[item for ids in plan["packages"].values() for item in ids]
    historical=package_cost(catalog,routes,plan["base_city"],all_ids)
    financial=advisor_projection(financial_data,source_live,plan,historical,
                                 eurfx,chffx,use_city_rent)
    outings=[];total_train_tickets=0.;total_meal=0.;unpriced=[];unknown_admissions=[]
    for dest,ids in plan["packages"].items():
        guide=build_outing_guide(plan,catalog,routes,dest,ids)
        day=day_of_outing(plan,dest)
        meal=meal_observations(dest,day["day"],evidence,new_data)
        route=rail_cost_options(plan["base_city"],dest,2,evidence)
        rail_eur=0.0 if guide["local"] else route["regular_roundtrip_eur"]
        sample_prices=[float(m["price_per_person"]) for m in meal["items"]]
        currencies={m["currency"] for m in meal["items"]}
        meal_cost=None
        if sample_prices and len(currencies)==1:
            currency=next(iter(currencies))
            rate=eurfx if currency=="EUR" else chffx
            meal_cost=round(_sample(sample_prices,plan["profile"])*2*rate,2)
        tickets=round(guide["known_admission"]["EUR"]*eurfx+
                      guide["known_admission"]["CHF"]*chffx,2)
        rails_brl=round(rail_eur*eurfx,2) if rail_eur is not None else None
        if rails_brl is None or meal_cost is None:unpriced.append(dest)
        if guide["cost_missing"]:
            unknown_admissions.append(dest)
        if rails_brl is not None:total_train_tickets+=rails_brl+tickets
        if meal_cost is not None:total_meal+=meal_cost
        outings.append({"destination":dest,"day":day,
                        "meal_examples":meal["items"],
                        "meal_status":meal["confidence"],
                        "meal_couple_brl":meal_cost,
                        "normal_rail_couple_brl":rails_brl,
                        "verified_ticket_brl":tickets,
                        "complete_reference":rails_brl is not None and meal_cost is not None,
                        "unknown_ticket_or_transport_components":guide["cost_missing"],
                        "fare_status":route["status"]})
    complete=bool(outings) and not unpriced
    excursion_allowance=float(financial["budget_excursions_allowance_brl"])
    dining_allocation=float(financial["result"]["new_components"]["dining"])
    already_in_baseline=float(financial["known_excursions_overage_brl"])
    additional_excursions=max(0.,total_train_tickets-excursion_allowance)
    # One lunch per trip is covered by existing dining envelope first.
    additional_dining=max(0.,total_meal-dining_allocation)
    indicative_delta=round(additional_excursions-already_in_baseline+additional_dining,2)
    current=float(financial["result"]["total"])
    return {
        "plan_revision":plan["revision"],"profile":plan["profile"],
        "base_city":plan["base_city"],"outings":outings,
        "priced_count":len(outings)-len(unpriced),
        "total_count":len(outings),"unpriced_destinations":unpriced,
        "unknown_admissions":unknown_admissions,
        "observed_lunch_brl":round(total_meal,2),
        "documented_rail_and_tickets_brl":round(total_train_tickets,2),
        "dining_allowance_brl":round(dining_allocation,2),
        "excursion_allowance_brl":round(excursion_allowance,2),
        "baseline_excursion_overage_brl":round(already_in_baseline,2),
        "covered_lunch_brl":round(min(total_meal,dining_allocation),2),
        "covered_excursions_brl":round(min(total_train_tickets,excursion_allowance),2),
        "indicated_increment_brl":indicative_delta if complete else None,
        "partial_reference_projection_brl":round(current+indicative_delta,2)
                                            if complete else None,
        "current_projected_brl":round(current,2),
        "can_compare_all":complete,
        "complete_2027_cost":False,
        "does_not_change_official_budget":True,
        "excluded_costs":["outras refeições","café e bebidas","transporte urbano e local",
                          "custos do cartão Fluo","ingressos sem preço","pernoite",
                          "aumento de preços em 2027","imprevistos e retorno real"],
    }
