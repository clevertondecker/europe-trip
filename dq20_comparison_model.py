"""Data Quality 2.0 (D): aggregation for the existing favorites screen.

The three research PRs remain independent until approved/merged. This module
degrades gracefully on main while their files are absent, and becomes active
without schema changes when those independently reviewed modules arrive.
"""
from __future__ import annotations
from importlib import import_module

PILOT_BASES=frozenset(("mulhouse","strasbourg","freiburg"))
REQUIRED_MODULES=("dq20_weekend_routes_model","dq20_urban_life_model",
                  "dq20_trip_logistics_model")

def pilot_comparison(selected_ids:list[str], *, work_hours:tuple[int,int]|None=None)->dict:
    if (not isinstance(selected_ids,list) or
        not 2<=len(selected_ids)<=3 or len(set(selected_ids))!=len(selected_ids) or
        any(x not in PILOT_BASES for x in selected_ids)):
        raise ValueError("Piloto restrito a duas ou três cidades prioritárias")
    modules={}
    for name in REQUIRED_MODULES:
        try:
            modules[name]=import_module(name)
        except ModuleNotFoundError as err:
            if err.name!=name:
                raise
            return {"status":"aguardando_pesquisas","missing_module":name,
                    "cities":list(selected_ids),"plan_mutated":False}
    train=modules["dq20_weekend_routes_model"]
    daily=modules["dq20_urban_life_model"]
    travel=modules["dq20_trip_logistics_model"]
    rail=[r for r in train.route_matrix() if r["base_id"] in selected_ids]
    city_life=daily.compare_urban_life(brazil_work_window=work_hours)
    city_logistics=travel.compare_airport_access()
    return {"status":"research_available",
            "cities":list(selected_ids),
            "destinations":list(train.DESTINATIONS),
            "routes":rail,
            "urban":[r for r in city_life["cities"] if r["city_id"] in selected_ids],
            "logistics":[r for r in city_logistics["cities"] if r["base_id"] in selected_ids],
            "brussels_bruges":train.combined_brussels_bruges(),
            "illustrative_weekends":train.illustrative_weekends(8),
            "verified_roundtrips":sum(r["feasibility"]=="bate_volta_comprovado" for r in rail),
            "complete_transport_minutes":None,
            "complete_financial_cost":None,
            "overall_winner":None,
            "plan_mutated":False,
            "note":"Dados exploratórios de 2026, sem trens de volta de fim de semana "
                   "nem aeroportos/voos confirmados para 2027."}
