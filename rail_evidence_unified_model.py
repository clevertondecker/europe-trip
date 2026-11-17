"""Read-only railway evidence adapter across canonical 2026 data sources.

Preserves all observations, never combines incompatible fares/schedules or
infers a return service. Missing is unknown, not impossible.
"""
from __future__ import annotations
from collections import defaultdict
from pathlib import Path
from copy import deepcopy
import json

ROOT=Path(__file__).resolve().parent/"data"
ALIASES={"luxembourg":"luxembourg_city","luxembourg_city":"luxembourg_city",
         "bruxelles":"brussels","bruxelas":"brussels","brussels":"brussels",
         "bruges":"bruges_be","brugge":"bruges_be","bruges_be":"bruges_be",
         "köln":"cologne","koln":"cologne","cologne":"cologne"}

def canonical_place(value:str)->str:
    if not isinstance(value,str) or not value.strip():
        raise ValueError("Identificador inválido")
    return ALIASES.get(value.strip().casefold(),value.strip().casefold())

def _read(filename:str)->dict:
    return json.loads((ROOT/filename).read_text(encoding="utf-8"))

def _positive(value):
    return value if isinstance(value,(int,float)) and not isinstance(value,bool) and value>0 else None

def _record(origin,destination,source,source_date,minimum=None,typical=None,
            regional=None,transfers=None,fare=None,fare_conditions=None,
            url=None,origin_station=None,destination_station=None,
            mode="rail",kind="historical",notes="",missing=()):
    return {"origin_id":canonical_place(origin),"destination_id":canonical_place(destination),
            "source_dataset":source,"evidence_date":source_date,
            "minimum_oneway_min":_positive(minimum),"typical_oneway_min":_positive(typical),
            "regional_oneway_min":_positive(regional),
            "transfers":transfers if type(transfers) is int and transfers>=0 else None,
            "fare_from_eur_person_oneway":_positive(fare),
            "fare_conditions":fare_conditions,"source_url":url,
            "origin_station":origin_station,"destination_station":destination_station,
            "mode":mode,"observation_type":kind,"notes":notes,
            "missing":list(missing),"return_2027_verified":False,
            "comparable":False}

def load_rail_evidence()->dict:
    rows=[]
    five=_read("five_base_comparison_evidence_2026_11.json")
    for x in five["verified_time_routes"]:
        rows.append(_record(x["base_id"],x["destination_id"],"five_base_operator_2026",
                            x["checked_at"],x["fastest_train_oneway_min"],
                            regional=x.get("regional_example_min"),
                            transfers=x.get("transfers"),
                            fare=x.get("advertised_from_eur_person_oneway"),
                            fare_conditions="advertised_from_not_normal_verified",
                            url=x["source_url"],origin_station=x.get("origin_station"),
                            destination_station=x.get("destination_station"),
                            notes=x.get("notes",""),
                            missing=("return_weekend","last_mile","2027_schedule")))
    expanded=_read("base_city_rail_evidence_expanded_2026_11.json")
    for x in expanded["segments"]:
        rows.append(_record(x["from"],x["to"],"expanded_rail_sample_2026",
                            expanded["basis_date"],x["fastest_minutes"],
                            typical=x.get("average_minutes"),
                            regional=x.get("representative_regional_minutes"),
                            fare=x.get("advertised_fare_from_eur_person_oneway"),
                            fare_conditions="advertised_from_not_normal_verified",
                            url=x["source_url"],origin_station=x.get("origin"),
                            destination_station=x.get("destination"),
                            notes=x.get("notes",""),
                            missing=("return_weekend","last_mile","2027_schedule")))
    legacy=_read("base_destination_routes_2027.json")
    for x in legacy["routes"]:
        if x.get("mode")=="local":
            continue
        rows.append(_record(x["base_id"],x["destination_id"],"four_base_routes_2026",
                            x.get("retrieved_at",legacy["checked_at"]),
                            x.get("train_minutes_one_way"),
                            transfers=x.get("transfers"),fare=x.get("fare_eur_person_oneway"),
                            fare_conditions=x.get("fare_type"),url=x.get("source_url"),
                            origin_station=x.get("departure_point"),
                            destination_station=x.get("arrival_point"),
                            mode=x.get("mode","rail_candidate"),
                            kind=x.get("status","historical"),
                            notes=x.get("notes",""),missing=x.get("missing",[])))
    # DQ3.0 adds dated observations as provenance, not a competing route system.
    # Existing display precedence remains stable and no second fare is summed.
    from dq30_mobility_evidence_model import load_mobility_pilot
    pilot=load_mobility_pilot()
    for x in pilot["rail_service_observations"]:
        rows.append(_record(
            x["origin_id"],x["destination_id"],"dq30_dated_operator_2026",
            x["source_snapshot_at"],minimum=x["duration_min"],
            transfers=x["transfers"],fare=x["fare_from_eur_person_oneway"],
            fare_conditions=x["fare_kind"],url=x["source_url"],
            origin_station=x["origin_station"],
            destination_station=x["destination_station"],
            kind="dated_weekday_service_2026",
            notes=x["notes"]+" Observado: "+x["observation_date"]+
                  " "+x["departure_local"]+"–"+x["arrival_local"],
            missing=("weekend_return","last_mile","2027_schedule")))
    for x in pilot["operator_route_summaries"]:
        rows.append(_record(
            x["origin_id"],x["destination_id"],"dq30_operator_overview_2026",
            x["checked_at"],minimum=x["minimum_oneway_min"],
            typical=x["typical_oneway_min"],
            fare=x["fare_from_eur_person_oneway"],
            fare_conditions=x["fare_kind"],url=x["source_url"],
            kind="operator_overview_not_date_specific",notes=x["notes"],
            missing=("dated_weekend_return","last_mile","2027_schedule")))
    # Only records containing a documented time count as a researched journey.
    by_pair=defaultdict(list)
    for row in rows:
        by_pair[(row["origin_id"],row["destination_id"])].append(row)
    return {"observations":rows,"by_pair":dict(by_pair),"sources":(
        "five_base_operator_2026","expanded_rail_sample_2026","four_base_routes_2026",
        "dq30_dated_operator_2026","dq30_operator_overview_2026")}

def route_evidence(data:dict,origin:str,destination:str)->dict:
    origin,destination=canonical_place(origin),canonical_place(destination)
    if origin==destination:
        return {"status":"local","minimum_oneway_min":None,
                "typical_oneway_min":None,"regional_oneway_min":None,
                "transfers":None,"fare_from_eur_person_oneway":None,
                "source_url":None,"observations":[],"comparable":False,
                "return_2027_verified":False}
    observations=deepcopy(data["by_pair"].get((origin,destination),[]))
    timed=[x for x in observations if x["minimum_oneway_min"] is not None]
    if not timed:
        return {"status":"not_researched" if not observations else "partial",
                "minimum_oneway_min":None,"typical_oneway_min":None,
                "regional_oneway_min":None,"transfers":None,
                "fare_from_eur_person_oneway":None,"source_url":None,
                "observations":observations,"comparable":False,
                "return_2027_verified":False}
    # Stable source preference is for display ONLY, not taking the minimum
    # across dissimilar evidence. The complete provenance is returned.
    priority=("five_base_operator_2026","expanded_rail_sample_2026","four_base_routes_2026",
              "dq30_dated_operator_2026","dq30_operator_overview_2026")
    best=sorted(timed,key=lambda x:priority.index(x["source_dataset"]))[0]
    return {"status":"historical_time","minimum_oneway_min":best["minimum_oneway_min"],
            "typical_oneway_min":best["typical_oneway_min"],
            "regional_oneway_min":best["regional_oneway_min"],
            "transfers":best["transfers"],"fare_from_eur_person_oneway":best["fare_from_eur_person_oneway"],
            "source_url":best["source_url"],"observations":observations,
            "comparable":False,"return_2027_verified":False,
            "source_dataset":best["source_dataset"],
            "source_date":best["evidence_date"]}
