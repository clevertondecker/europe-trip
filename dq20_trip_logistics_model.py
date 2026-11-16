"""Data Quality 2.0 (C): read-only whole-journey access comparison.

Separates factual airport access legs from unconfirmed flight choices and from
the Italy proposal. A train/bus duration is NEVER a hotel-to-airport time.
"""
from __future__ import annotations
import json
from pathlib import Path
from italy_honeymoon_model import load_honeymoon

FILE=Path(__file__).resolve().parent/"data"/"dq20_airport_logistics_delta_2026_11.json"
BASES=("mulhouse","strasbourg","freiburg")

def load_airport_links(path:Path=FILE)->dict:
    data=json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema_version")!=1 or len(data.get("bases",[]))!=3:
        raise ValueError("Referências logísticas incompletas")
    if {b["base_id"] for b in data["bases"]}!=set(BASES):
        raise ValueError("Base ausente ou duplicada")
    for city in data["bases"]:
        if not city["airport_options"]:raise ValueError("Sem acesso aeroportuário")
        for option in city["airport_options"]:
            if option["total_door_to_door_min"] is not None or option["airline_to_brazil_verified"]:
                raise ValueError("Acesso completo ou voo futuro não comprovado")
            for known in option["known_segments"]:
                if not known["url"].startswith("https://"):
                    raise ValueError("Trecho sem fonte")
                a,b=known["approx_min_range"]
                if not 0<a<=b:raise ValueError("Duração de trecho inválida")
    return data

def compare_airport_access(data:dict|None=None, *,
                           italy_exit_candidate:str|None=None,
                           itinerary_variant:str|None=None)->dict:
    data=load_airport_links() if data is None else data
    if (italy_exit_candidate is not None and
        italy_exit_candidate not in data["italy_candidates"]):
        raise ValueError("Ponto de saída italiano inválido")
    italy=load_honeymoon()
    variants={x["id"]:x for x in italy["scenarios"]}
    if itinerary_variant is not None and itinerary_variant not in variants:
        raise ValueError("Proposta italiana desconhecida")
    proposal=variants.get(itinerary_variant)
    # The proposal can expose a last calendar-day candidate, but cannot
    # select a train station or an airport or validate a flight.
    italy_last_day=(proposal["days_detail"][-1][1] if proposal else None)
    rows=[]
    for base in BASES:
        original=next(x for x in data["bases"] if x["base_id"]==base)
        options=[]
        for item in original["airport_options"]:
            options.append({"airport_code":item["airport_code"],
                            "airport_name":item["airport_name"],
                            "path":list(item["path"]),
                            "transport_modes":list(item["modes"]),
                            "structural_legs":len(item["modes"]),
                            "known_segment_observations":list(item["known_segments"]),
                            "door_to_door_minutes":None,"brazil_flight_confirmed":False,
                            "fare_brl_couple":None,"source_kind":"official_operator",
                            "notes":item["notes"]})
        rows.append({"base_id":base,"airport_options":options,
                     "arrival_from_italy_confirmed":False,
                     "return_to_brazil_confirmed":False,
                     "official_base_changed":False})
    return {"cities":rows,
            "italy_exit_candidate":italy_exit_candidate,
            "italy_scenario_label":proposal["label"] if proposal else None,
            "italy_scenario_last_day_location":italy_last_day,
            "naples_airport_ground_leg":dict(data["naples_italy_connection"]),
            "italy_to_base_mode_options":list(data["flight_or_rail_from_italy"]["candidates"]),
            "italy_to_base_door_to_door_minutes":None,
            "roundtrip_airfare_2027_eur":None,
            "flight_to_brazil_from_each_airport_verified":False,
            "known_gaps":list(data["global_missing"]),
            "comparison_status":"structural_access_only_no_flights",
            "plan_mutated":False}

def airport_comparison_rows(result:dict)->list[dict]:
    return [{"city":city["base_id"],"airport":option["airport_name"],
             "structural_legs":option["structural_legs"],
             "segments_with_evidence":len(option["known_segment_observations"]),
             "known_segment_descriptions":[x["leg"] for x in option["known_segment_observations"]],
             "total_time_min":None,"flight_brazil_verified":False}
            for city in result["cities"] for option in city["airport_options"]]
