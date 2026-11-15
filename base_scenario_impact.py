"""Read-only scenario impact preview for supported route matrices.

Never reassigns TripPlan; unavailable fares and rentals remain pending, not zero.
"""
from __future__ import annotations
from copy import deepcopy
from base_scenario_model import base_options,choose_exploratory_base
from attractions_model import load_attractions,load_base_routes,package_cost
from advisor_finance import advisor_projection

SUPPORTED_ROUTE_BASES=frozenset({"mulhouse","strasbourg","metz","nancy"})


def scenario_impact(plan:dict,trip_data:dict,finance_live:bool,base_id:str,
                    eurfx:float=6.3,chffx:float=7.1)->dict:
    choose_exploratory_base(base_id,base_options())
    if base_id not in SUPPORTED_ROUTE_BASES:
        return {"city_id":base_id,"ready":False,"total_brl":None,
                "known_tickets_brl":None,"missing":[
                    "Tarifas e tempos para a cidade-base selecionada não integram "
                    "a matriz completa de atrações",
                    "Hospedagem mobiliada de 2027 não cotada"],
                "reason":"Apenas pesquisa exploratória disponível"}
    preview=deepcopy(plan)
    preview["base_city"]=base_id
    ids=[key for picks in preview["packages"].values() for key in picks]
    costs=package_cost(load_attractions(),load_base_routes(),base_id,ids)
    finance=advisor_projection(trip_data,finance_live,preview,costs,
                               eurfx,chffx,use_city_rent=True)
    return {
        "city_id":base_id,"ready":not finance["has_unknown_costs"],
        "total_brl":finance["result"]["total"],
        "known_tickets_brl":finance["known_billets_brl"],
        "missing":list(costs.get("missing",[]))+
                  ["Hospedagem de 2027 não cotada"],
        "rent_eur_month_reference_2026":finance["rent_eur_month"],
        "reason":"Projeção histórica e parcial, não cotação de 2027",
    }
