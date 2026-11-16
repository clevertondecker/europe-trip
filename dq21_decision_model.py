"""DQ 2.1 D: compose independent evidence modules for the existing favorites.

Read-only; no changes to the existing 15-destination widget, user selections,
budget, private backups, or TripPlan. Missing modules fail soft until reviewed.
"""
from __future__ import annotations
from importlib import import_module

PILOT_CITIES=frozenset(("mulhouse","strasbourg","freiburg"))
MODULES=("dq21_weekend_model","dq21_living_model","dq21_travel_model")

def decision_research(selected:list[str],*,work_day:str|None=None,
                      brazil_hours:tuple[int,int]|None=None)->dict:
    if (not isinstance(selected,list) or not 2<=len(selected)<=3 or
        len(set(selected))!=len(selected) or not set(selected)<=PILOT_CITIES):
        raise ValueError("Comparação do piloto exige duas ou três cidades diferentes")
    if (work_day is None)!=(brazil_hours is None):
        raise ValueError("Horários exigem data e cenário explícitos")
    modules={}
    for name in MODULES:
        try:modules[name]=import_module(name)
        except ModuleNotFoundError as exc:
            if exc.name!=name:raise
            return {"status":"aguardando_modulos","missing_module":name,
                    "cities":list(selected),"plan_changed":False}
    a=modules[MODULES[0]]
    b=modules[MODULES[1]]
    c=modules[MODULES[2]]
    all_routes=a.weekend_research_matrix()
    # Two dates make explicit DST-sensitive conversion available without
    # assuming the user's work schedule or travel date.
    dates=(work_day,work_day) if work_day else None
    life=b.compare_living_depth(study_dates=dates,brazil_hours=brazil_hours)
    travel=c.evaluate_travel_options()
    return {"status":"available","cities":list(selected),
            "destinations":list(a.DESTINATIONS),
            "routes":[r for r in all_routes if r["base_id"] in selected],
            "urban":[r for r in life["cities"] if r["city_id"] in selected],
            "airports":[r for r in travel["cities"] if r["base_id"] in selected],
            "direct_flights_2026":travel["longhaul_examples"],
            "belgium":a.combined_belgian_weekend(),
            "sample_weekends":a.weekend_hypotheses(8),
            "validated_weekend_trip_count":0,
            "all_roundtrips_to_base_2027_verified":False,
            "complete_rental_and_airport_access":False,
            "climate_cross_station_fully_comparable":False,
            "ranking":None,"2027_total_cost_eur":None,
            "work_day":work_day,
            "plan_changed":False}
