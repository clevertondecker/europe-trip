"""Data Quality 2.1 C: conditional Italy/airport access, sourced examples only.

Airline route examples from official carrier websites are not flight offers for
Sep–Nov 2027. Train time from city station to airport station != door to door.
"""
from __future__ import annotations
import json
from pathlib import Path
from copy import deepcopy
from dq20_trip_logistics_model import compare_airport_access
from italy_honeymoon_model import load_honeymoon

FILE=Path(__file__).resolve().parent/"data"/"dq21_airport_evidence_2026_11.json"
BASES=("mulhouse","strasbourg","freiburg")

def load_travel_extension(path:Path=FILE)->dict:
    j=json.loads(path.read_text(encoding="utf-8"))
    if j.get("schema_version")!=1:raise ValueError("Dados de viagens inválidos")
    codes={r["airport_code"] for r in j["longhaul_examples"]}
    if codes!={"ZRH","FRA"}:raise ValueError("Aeroportos sem fonte")
    if any(r["published_for_trip_date_2027"] or r["quote_for_couple_2027"] is not None
           for r in j["longhaul_examples"]):
        raise ValueError("Disponibilidade 2027 não confirmada")
    if any(not r["source_url"].startswith("https://") for r in j["longhaul_examples"]+j["ground_samples"]):
        raise ValueError("Fonte de rota inválida")
    for sample in j["ground_samples"]:
        if sample["base_id"] not in BASES or sample["full_door_to_door"] or sample["minutes"]<=0:
            raise ValueError("Trecho de acesso inválido")
    return j

def evaluate_travel_options(*,italy_variant:str|None=None,
                            italy_exit_airport:str|None=None,
                            final_brazil_airport:str|None=None)->dict:
    j=load_travel_extension()
    if italy_exit_airport not in (None,"NAP","FCO"):
        raise ValueError("Aeroporto italiano inválido")
    if final_brazil_airport not in (None,"GRU"):
        raise ValueError("Aeroporto brasileiro final ainda não pesquisado")
    old=compare_airport_access(itinerary_variant=italy_variant)
    scenarios={r["id"]:r for r in load_honeymoon()["scenarios"]}
    if italy_variant is not None and italy_variant not in scenarios:
        raise ValueError("Cenário italiano inválido")
    alloptions=[]
    for city in old["cities"]:
        base=city["base_id"]
        known=deepcopy(city["airport_options"])
        for code,name in (("ZRH","Zürich Flughafen"),("FRA","Frankfurt Flughafen")):
            samples=[dict(r) for r in j["ground_samples"]
                     if r["base_id"]==base and r["airport_code"]==code]
            known.append({"airport_code":code,"airport_name":name,
                          "known_segment_observations":samples,
                          "door_to_door_minutes":None,
                          "brazil_flight_confirmed":False,
                          "route_exists_in_2026":True,
                          "published_2027_complete_itinerary":False,
                          "ground_status":"station_partial" if samples else "not_researched",
                          "sources":[r["source_url"] for r in samples]})
        alloptions.append({"base_id":base,"airport_options":known})
    return {"cities":alloptions,"longhaul_examples":deepcopy(j["longhaul_examples"]),
            "italy_variant":italy_variant,"italy_exit_airport_hypothesis":italy_exit_airport,
            "italy_last_day_place":old["italy_scenario_last_day_location"],
            "naples_alibus_reference":deepcopy(j["naples_transfer_restriction"]),
            "final_brazil_airport_hypothesis":final_brazil_airport,
            "GRU_is_final_destination_confirmed":False,
            "flight_2027_confirmed":False,
            "full_trip_door_to_door_min":None,"price_couple_2027":None,
            "overnight_preflight_required":None,
            "missing":list(j["missing"]),"plan_changed":False}

def airport_decision_rows(result:dict)->list[dict]:
    return [{"base_id":row["base_id"],"airport_code":a["airport_code"],
             "ground_examples":len(a["known_segment_observations"]),
             "complete_door_to_door_min":None,"2027_airfare_couple":None,
             "2027_flight_confirmed":False}
            for row in result["cities"] for a in row["airport_options"]]
