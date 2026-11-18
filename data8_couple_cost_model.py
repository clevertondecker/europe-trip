"""DATA 8.4: defensible couple cost planning, never a 2027 booking quote.

One intercity transport range per *destination outing*, not per attraction.
An explicit user-editable range is a scenario assumption, not a sourced fare.
Unknown ticket, food or transport remains unknown; zero must be justified.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import date
from math import isfinite
from pathlib import Path
from urllib.parse import urlparse
import json

from data8_priority_tourism_model import load_priority_lot

DATA = Path(__file__).resolve().parent / "data" / "data8_cost_reference_2026_11.json"


def _nonnegative(v):
    return type(v) in (int,float) and isfinite(v) and v >= 0


def _https(value):
    p = urlparse(value or "")
    return p.scheme == "https" and bool(p.hostname)


def load_cost_addons(path=DATA):
    doc=json.loads(Path(path).read_text(encoding="utf-8"))
    if (doc.get("schema_version") != 1 or
            doc.get("scope") != "historical_optional_activity_reference_only"):
        raise ValueError("cost source version mismatch")
    date.fromisoformat(doc["checked_at"])
    seen = set()
    for row in doc["optional_activities"]:
        key=(row.get("attraction_id"),row.get("activity_id"))
        if key in seen or not all(key):
            raise ValueError("activity duplicated or missing identity")
        seen.add(key)
        if (row.get("status") != "operator_published_historical" or
                row.get("valid_for_2027") is not False or
                not _https(row.get("source_url"))):
            raise ValueError("activity price needs source and historic status")
        date.fromisoformat(row["checked_at"])
        if (row.get("currency") != "EUR" or row.get("unit") not in
                ("adult","person","couple") or not _nonnegative(row.get("amount"))):
            raise ValueError("optional activity price invalid")
    return deepcopy(doc)


def _scenario_range(component, category):
    if component is None:
        return None
    if not isinstance(component, dict):
        raise ValueError(f"{category}: scenario must be explicitly supplied")
    a, b = component.get("min_eur"), component.get("max_eur")
    if (not _nonnegative(a) or not _nonnegative(b) or
            a > b or component.get("state") != "user_editorial_assumption" or
            not component.get("method")):
        raise ValueError(f"{category}: invalid range or method")
    return [float(a),float(b)]


def estimate_couple_excursion(attraction_ids, *, research=None, addons=None,
                              selected_addons=(), intercity_couple=None,
                              local_couple=None, dining_couple=None,
                              eur_to_brl=None, travelers=2):
    research=research if research is not None else load_priority_lot()
    addons=addons if addons is not None else load_cost_addons()
    if type(travelers) is not int or travelers != 2:
        raise ValueError("this calculation is explicitly for two adults")
    if not attraction_ids or len(set(attraction_ids))!=len(attraction_ids):
        raise ValueError("select unique attraction IDs")
    if any(x not in research["by_id"] for x in attraction_ids):
        raise ValueError("unknown attraction")
    selected=[research["by_id"][x] for x in attraction_ids]
    destinations={x["destination_id"] for x in selected}
    if len(destinations)!=1:
        raise ValueError("one outing per destination; never repeat the railway fare")
    if eur_to_brl is not None and (type(eur_to_brl) not in (int,float)
                                   or not isfinite(eur_to_brl) or eur_to_brl <= 0):
        raise ValueError("manual planning FX rate must be positive")
    addon_index={a["activity_id"]:a for a in addons["optional_activities"]}
    if (len(set(selected_addons))!=len(selected_addons) or
            any(x not in addon_index for x in selected_addons)):
        raise ValueError("optional activities must be uniquely researched")
    amounts=[]
    missing=[]
    exterior=[]
    detailed=[]
    for r in selected:
        ticket=r["admission"]
        kind=ticket["state"]
        if kind in ("free_general_entry","published_price"):
            factor=travelers if ticket.get("unit") in ("person","adult") else 1
            amount=float(ticket["amount"])*factor
            amounts.append(amount)
            detailed.append({"name":r["attraction_id"],"category":"general_admission",
                             "known_eur":round(amount,2),
                             "status":kind,"source_url":ticket.get("source_url")})
        elif kind=="external_no_ticket":
            exterior.append(r["attraction_id"])
            detailed.append({"name":r["attraction_id"],"category":"external_visit",
                             "known_eur":None,"status":"no_main_exterior_ticket",
                             "source_url":ticket.get("source_url")})
        else:
            missing.append("ingresso:"+r["attraction_id"])
    for aid in selected_addons:
        opt=addon_index[aid]
        if opt["attraction_id"] not in attraction_ids:
            raise ValueError("selected addon belongs to another attraction")
        factor=travelers if opt["unit"] in ("person","adult") else 1
        amount=float(opt["amount"])*factor
        amounts.append(amount)
        detailed.append({"name":aid,"category":"optional_activity",
                         "known_eur":round(amount,2),"status":"published_historical",
                         "source_url":opt["source_url"]})
    components={}
    for name,scenario in (
        ("intercity_couple",intercity_couple),
        ("local_couple",local_couple),
        ("dining_couple",dining_couple)):
        values=_scenario_range(scenario,name)
        components[name]=values
        if values is None:
            missing.append(name)
    reference_sum=round(sum(amounts),2)
    minimum=reference_sum+sum(v[0] for v in components.values() if v is not None)
    maximum=reference_sum+sum(v[1] for v in components.values() if v is not None)
    total_complete=not missing
    estimated_range=[round(minimum,2),round(maximum,2)]
    return {
        "destination_id":selected[0]["destination_id"],
        "travelers":travelers,"attractions":list(attraction_ids),
        "known_general_and_optional_eur":reference_sum,
        "known_reference_breakdown":detailed,
        "exterior_without_main_ticket":exterior,
        "user_assumption_components":components,
        "partial_planning_range_eur":estimated_range,
        "full_scenario_range_eur":estimated_range if total_complete else None,
        "incomplete_estimate":not total_complete,
        "missing":sorted(set(missing)),
        "partial_planning_range_brl":([round(x*eur_to_brl,2) for x in estimated_range]
                                      if eur_to_brl is not None else None),
        "fx_eur_to_brl":eur_to_brl,
        "fx_source":"user_assumption_not_live_fx" if eur_to_brl is not None else "unset",
        "fare_counted_once_per_destination":True,
        "valid_for_2027":False,"plan_mutated":False,
    }
