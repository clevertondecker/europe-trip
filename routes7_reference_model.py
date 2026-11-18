"""ROUTES 7 sourced *planning reference* overlay for fifteen fixed pairs.

Never replaces get_rail_evidence() or writes TripPlan/wishlist. Fastest
published route-summary times are not dates, stations, or weekend services.
"""
from __future__ import annotations
from copy import deepcopy
from datetime import date
from pathlib import Path
from urllib.parse import urlparse
import json

from rail_evidence_unified_model import canonical_place
from evidence_query_model import get_rail_evidence

DATA = Path(__file__).resolve().parent / "data/routes7_priority_reference_2026_11.json"
SOURCES = {"official_operator", "secondary_timetable_aggregator", "local"}
STATES = {"public_reference_checked", "local"}

def _positive_or_none(value, field):
    if value is not None and (type(value) is not int or value <= 0):
        raise ValueError(f"{field} must be positive integer or null")
    return value

def load_route_references(path=DATA):
    payload=json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if payload.get("schema_version") != 1 or payload.get("scope") != "planning_reference_not_bookable_2027":
        raise ValueError("invalid route reference scope")
    date.fromisoformat(payload["checked_at"])
    bases=payload["bases"]
    destinations=payload["destinations"]
    if (len(bases)!=3 or len(destinations)!=5 or
        len(set(bases))!=3 or len(set(destinations))!=5):
        raise ValueError("expected fixed 3 by 5 public research basket")
    registered={(canonical_place(b),canonical_place(d)) for b in bases for d in destinations}
    observed={}
    for raw in payload["records"]:
        row=deepcopy(raw)
        origin,destination=canonical_place(row["origin_id"]),canonical_place(row["destination_id"])
        key=(origin,destination)
        if key not in registered or key in observed:
            raise ValueError("duplicate/unexpected base-destination pair")
        if row["source_kind"] not in SOURCES or row["source_research_status"] not in STATES:
            raise ValueError("invalid source type/status")
        date.fromisoformat(row["checked_at"])
        if row["checked_at"] > payload["checked_at"]:
            raise ValueError("source research date after snapshot")
        fastest=_positive_or_none(row.get("fastest_min"),"fastest")
        average=_positive_or_none(row.get("average_min"),"average")
        if average is not None and (fastest is None or average < fastest):
            raise ValueError("published average incompatible with minimum")
        if origin==destination:
            if fastest is not None or average is not None or row["source_kind"]!="local":
                raise ValueError("intra-city movement is not train time")
        else:
            url=urlparse(row.get("source_url") or "")
            if url.scheme!="https" or not url.netloc or fastest is None:
                raise ValueError("external route reference needs positive duration and HTTPS source")
            if row["source_research_status"]!="public_reference_checked":
                raise ValueError("route reference does not have a documented source")
        if row.get("fare_for_two_eur") is not None or row.get("transfer_count") is not None:
            raise ValueError("pilot does not verify fares or transfers")
        if row.get("weekend_return_status")!="unknown":
            raise ValueError("outbound reference cannot validate weekend return")
        if row.get("station_status") not in ("station_not_reconciled","not_applicable"):
            raise ValueError("station identity cannot be inferred from city names")
        observed[key]=row
    if set(observed)!=registered or len(observed)!=15:
        raise ValueError("research matrix not complete")
    return {"schema_version":1,"checked_at":payload["checked_at"],
            "records":list(observed.values()),"by_pair":observed,
            "bases":list(bases),"destinations":list(destinations)}

def planning_reference(base_id,destination_id, *, references=None, legacy=None):
    """Separate overlay: never alter legacy source precedence or estimate a return."""
    base_id,destination_id=canonical_place(base_id),canonical_place(destination_id)
    ref=references if references is not None else load_route_references()
    original=legacy if legacy is not None else get_rail_evidence(base_id,destination_id)
    row=ref["by_pair"].get((base_id,destination_id))
    if original.get("status")=="local":
        return {"status":"local","fastest_min":None,"average_min":None,
                "display_min":None,"display_basis":"local_not_rail",
                "source_url":None,"confidence":"not_applicable",
                "legacy_min":None,"weekend_return_known":False}
    legacy_min=original.get("minimum_oneway_min")
    if row is None:
        return {"status":"legacy_only" if legacy_min is not None else "unknown",
                "fastest_min":None,"average_min":None,
                "display_min":legacy_min,"display_basis":"legacy_historical" if legacy_min is not None else "unknown",
                "source_url":original.get("source_url"),"confidence":"unknown",
                "legacy_min":legacy_min,"weekend_return_known":False}
    return {"status":"published_reference",
            "fastest_min":row["fastest_min"],"average_min":row["average_min"],
            "display_min":legacy_min if legacy_min is not None else row["fastest_min"],
            "display_basis":"legacy_historical" if legacy_min is not None else "published_fastest_reference",
            "source_url":row["source_url"],"confidence":row["confidence"],
            "source_kind":row["source_kind"],"checked_at":row["checked_at"],
            "station_status":row["station_status"],"legacy_min":legacy_min,
            "conflict_with_legacy":legacy_min is not None and legacy_min != row["fastest_min"],
            "weekend_return_known":False,
            "typical_time_known":row["average_min"] is not None}
