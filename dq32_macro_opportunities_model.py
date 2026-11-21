"""DQ 3.2: broad, read-only tourism discovery for all 30 candidate bases.

Sources are kept separate: verified local tourist POIs, existing destination
catalogs, and historical railway observations. A place's existence never
establishes that it can be reached from a particular base.
"""
from __future__ import annotations

from copy import deepcopy
import json
import re
import unicodedata
from pathlib import Path

from attractions_model import load_attractions
from base_explorer_model import load_exploration
from base_research_expanded_model import load_research
from base_scenario_model import base_options
from rail_evidence_unified_model import (
    canonical_place, load_rail_evidence,
)
from evidence_query_model import get_rail_evidence
from rail_pair_projection_model import pair_projection_row
from rail_reference_projection_model import decorate_comparison

DEFAULT=Path(__file__).resolve().parent/"data"/"dq32_macro_tourism_2026_11.json"


def load_macro_tourism(path=DEFAULT):
    data=json.loads(Path(path).read_text(encoding="utf-8"))
    validate_macro_tourism(data)
    return deepcopy(data)


def validate_macro_tourism(data):
    if data.get("schema_version") != 1 or not data.get("checked_at"):
        raise ValueError("Versão ou data de pesquisa inválida")
    seen=set()
    valid={"heritage","museum","urban_walk","nature"}
    for row in data.get("attractions",[]):
        if row["id"] in seen or not row["id"].startswith("dq32_"):
            raise ValueError("ID duplicado ou inválido")
        seen.add(row["id"])
        if (not row.get("city_id") or not row.get("name")
                or row["category"] not in valid
                or not row.get("source_url","").startswith("https://")
                or row["source_kind"]!="official_tourism_or_city"):
            raise ValueError("Atração sem prova turística individual")
        for key in ("ticket_eur","visit_duration_min","walk_distance_m",
                    "station_access_min","availability_2027"):
            if row[key] is not None:
                raise ValueError("Dado não coletado não pode ser preenchido")


def _identity_key(name):
    """Conservative exact-name key; other semantic aliases require declaration."""
    normalized=unicodedata.normalize("NFKD", name.casefold())
    without_accents="".join(x for x in normalized if not unicodedata.combining(x))
    return re.sub(r"[^a-z0-9]+"," ",without_accents).strip()


def reconcile_attractions(catalog, macro):
    """Deduplicate documented equivalences without rewriting original IDs.

    Exact normalized titles within the same canonical city match automatically.
    Non-exact semantic matches require `canonical_attraction_id` in the
    source row. Ambiguous matches fail validation instead of silently merging.
    """
    originals={}
    keys={}
    for row in catalog["attractions"]:
        city=canonical_place(row["destination_id"])
        originals[row["id"]]=row
        k=(city,_identity_key(row["name"]))
        if k in keys:
            raise ValueError("Nome canônico ambíguo na mesma cidade")
        keys[k]=row["id"]
    canonical_by_city={}
    for row in catalog["attractions"]:
        city=canonical_place(row["destination_id"])
        canonical_by_city.setdefault(city,[]).append({
            "id":row["id"],"name":row["name"],
            "source_url":row["source_urls"][0],
            "kind":"legacy_catalog","additional_sources":[],
            "reconciled_source_ids":[],
        })
    new_by_city={}
    seen_keys=set()
    reconciled=[]
    for row in macro["attractions"]:
        city=canonical_place(row["city_id"])
        name_key=(city,_identity_key(row["name"]))
        if name_key in seen_keys:
            raise ValueError("Atrações DQ3.2 duplicadas semanticamente na mesma cidade")
        seen_keys.add(name_key)
        exact=keys.get(name_key)
        declared=row.get("canonical_attraction_id")
        if declared is not None and (
                declared not in originals or
                canonical_place(originals[declared]["destination_id"])!=city):
            raise ValueError("Equivalência canônica desconhecida ou de outra cidade")
        if declared is not None and exact is not None and declared != exact:
            raise ValueError("Equivalência semântica contradiz correspondência exata")
        match=declared or exact
        if match is not None:
            item=next(item for item in canonical_by_city[city] if item["id"]==match)
            item["reconciled_source_ids"].append(row["id"])
            if row["source_url"] != item["source_url"] and (
                    row["source_url"] not in item["additional_sources"]):
                item["additional_sources"].append(row["source_url"])
            reconciled.append({"source_id":row["id"],"canonical_id":match,
                               "reason":"explicit_alias" if declared else "exact_name"})
        else:
            new_by_city.setdefault(city,[]).append({
                "id":row["id"],"name":row["name"],
                "source_url":row["source_url"],"kind":"dq32_sourced_local",
                "additional_sources":[],"reconciled_source_ids":[],
            })
    return {"canonical_by_city":canonical_by_city,"new_by_city":new_by_city,
            "reconciled":reconciled}


def _registry(catalog, exploration, research, macro):
    """Canonical IDs avoid creating parallel entries for Luxembourg/Bruges."""
    destinations={}
    def add(row,source):
        id=canonical_place(row["id"])
        if id not in destinations:
            destinations[id]={"destination_id":id,"name":row["name"],
                              "country":row["country"],"registry_sources":[source]}
        elif source not in destinations[id]["registry_sources"]:
            destinations[id]["registry_sources"].append(source)
    for row in catalog["destinations"]:
        add(row,"attractions_2027")
    for row in exploration["destinations"]:
        add(row,"exploration_bases_2027")
    for row in research["cities"]:
        add(row,"base_city_research_2026")
    # Some exploration destinations have no local-POI evidence yet.
    for row in macro["attractions"]:
        id=canonical_place(row["city_id"])
        if id not in destinations:
            raise ValueError("Atração sem cidade cadastrada: "+id)
    return destinations


def opportunity_overview(base_id, *, macro=None,catalog=None,exploration=None,
                         research=None,rail=None,options=None):
    """Independent broad-screening view; NO ranking, return, fare or reachability claims."""
    macro=macro if macro is not None else load_macro_tourism()
    catalog=catalog if catalog is not None else load_attractions()
    exploration=exploration if exploration is not None else load_exploration()
    research=research if research is not None else load_research()
    rail=rail if rail is not None else load_rail_evidence()
    options=options if options is not None else base_options()
    valid_bases={canonical_place(row["id"]):row for row in options}
    origin=canonical_place(base_id)
    if origin not in valid_bases:
        raise ValueError("Cidade-base desconhecida")
    destinations=_registry(catalog,exploration,research,macro)
    reconciled=reconcile_attractions(catalog,macro)
    catalog_attractions=reconciled["canonical_by_city"]
    local_new=reconciled["new_by_city"]
    entries=[]
    projection_rows=[]
    for dest_id,meta in destinations.items():
        local=dest_id==origin
        evidence=get_rail_evidence(
            origin,dest_id,rail=rail,exploration=exploration)
        minutes=evidence["minimum_oneway_min"]
        typical=evidence["typical_oneway_min"]
        source=evidence["source_url"]
        checked=evidence["source_date"]
        dataset=evidence["source_dataset"]
        projection_rows.append(pair_projection_row(origin, dest_id, evidence))
        attrs=local_new.get(dest_id,[])+catalog_attractions.get(dest_id,[])
        canonical_count=len(catalog_attractions.get(dest_id,[]))
        new_count=len(local_new.get(dest_id,[]))
        status=("local_access_unresearched" if local else
                "historical_train_time_only" if minutes is not None else
                "unresearched_from_base")
        entries.append({
            **deepcopy(meta),"local":local,
            "attractions":deepcopy(attrs),"attraction_count":len(attrs),
            "canonical_attraction_count":canonical_count,
            "new_attraction_count":new_count,
            "minimum_train_oneway_min":minutes,
            "typical_train_oneway_min":typical,
            "train_source_url":source,"train_checked_at":checked,
            "train_source_dataset":dataset,
            "status":status,"reachable_confirmed":False,
            "weekend_return_verified":False,"full_trip_cost_eur":None,
            "walk_between_attractions_m":None,
            "journey_scope":"historical_minimum_station_to_station_only" if minutes is not None
                            else "not_available",
        })
    # Reuse the exact same precedence and DATA 9 projection as Explorar → Comparar.
    # No new rail estimator, no synthetic reverse, and no mutation of historical
    # records. Keep indicative observations distinct from historical evidence.
    projection=decorate_comparison({"rows":projection_rows})
    for entry in entries:
        cell=projection["cells"][(origin,entry["destination_id"])]
        if cell["category"]=="reference_only":
            entry["status"]="indicative_rail_reference_only"
            entry["indicative_train_oneway_min"]=cell["display_min"]
            entry["indicative_train_label"]=cell["label"]
            entry["indicative_source_url"]=cell.get("reference_source_url") or cell.get("source_url")
            entry["indicative_source_checked_at"]=cell.get("gap_checked_at") or cell.get("checked_at")
            entry["indicative_confidence"]=cell.get("confidence")
            entry["indicative_evidence_type"]=(
                cell.get("gap_evidence_type")
                or ("data13_directed_reference" if cell.get("data13_connectivity_applied")
                    else "data12_lille_reference" if cell.get("lille_connectivity_applied")
                    else "data11_priority_reference" if cell.get("priority_connectivity_applied")
                    else "data10_connectivity_reference" if cell.get("connectivity_applied")
                    else "routes7_reference"))
            entry["indicative_source_dataset"]=(
                "data13_directed_connectivity_2026_11" if cell.get("data13_connectivity_applied")
                else "data12_lille_connectivity_2026_11" if cell.get("lille_connectivity_applied")
                else "data11_priority_connectivity_2026_11" if cell.get("priority_connectivity_applied")
                else "data10_connectivity_2026_11" if cell.get("connectivity_applied")
                else "data9_rail_gap_2026_11" if cell.get("gap_applied")
                else "routes7_2026_11")
        else:
            entry["indicative_train_oneway_min"]=None
            entry["indicative_train_label"]=None
            entry["indicative_source_url"]=None
            entry["indicative_source_checked_at"]=None
            entry["indicative_confidence"]=None
            entry["indicative_evidence_type"]=None
            entry["indicative_source_dataset"]=None
    entries.sort(key=lambda item:(
        0 if item["local"] else 1 if item["minimum_train_oneway_min"] is not None else 2,
        item["minimum_train_oneway_min"] if item["minimum_train_oneway_min"] is not None else 999999,
        item["name"]))
    local_rows=[x for x in entries if x["local"]]
    observed=[x for x in entries if x["minimum_train_oneway_min"] is not None]
    indicative=[x for x in entries if x["status"]=="indicative_rail_reference_only"]
    unknown=[x for x in entries if x["status"]=="unresearched_from_base"]
    return {
        "base_id":origin,"base_name":valid_bases[origin]["name"],
        "registry_destinations":len(entries),
        "known_local_attractions":sum(x["attraction_count"] for x in local_rows),
        "canonical_local_attractions":sum(x["canonical_attraction_count"] for x in local_rows),
        "new_local_attractions":sum(x["new_attraction_count"] for x in local_rows),
        "reconciled_duplicate_count":len(reconciled["reconciled"]),
        "semantic_equivalences":deepcopy(reconciled["reconciled"]),
        "local_destinations":deepcopy(local_rows),
        "historical_rail_destinations":deepcopy(observed),
        "unresearched_destinations":deepcopy(unknown),
        "rail_time_documented_count":len(observed),
        "indicative_rail_destinations":deepcopy(indicative),
        "indicative_rail_reference_count":len(indicative),
        "unresearched_count":len(unknown),
        "rail_reference_total_count":len(observed)+len(indicative),
        "rail_coverage_audit":{
            "historical":len(observed),"indicative":len(indicative),
            "local":len(local_rows),"unknown":len(unknown),
            "total":len(entries),
        },
        "destinations":deepcopy(entries),
        "feasible_destinations_count":None,
        "comparison_score":None,
        "read_only":True,
        "official_plan_modified":False,
        "limits":"Atrações catalogadas e ligações históricas não comprovam passeio viável; "
                 "sem dados não significa inacessível",
    }
