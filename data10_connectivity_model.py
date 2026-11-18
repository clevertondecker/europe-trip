"""DATA 10: sourced city-pair connectivity minimums; never 2027 timetables.

Additive reference overlay only. A published minimum demonstrates a researched
one-way rail connection in the source scope; it does not prove a train on a
specific future date, return service, frequency, fare, station or excursion.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import date
import json
from pathlib import Path
from urllib.parse import urlparse

from rail_evidence_unified_model import canonical_place

DATA = Path(__file__).resolve().parent / "data" / "data10_connectivity_2026_11.json"
KINDS = {
    "official_operator_minimum": ("sncf-connect.com", "medium"),
    "secondary_route_minimum": ("thetrainline.com", "low"),
    "secondary_station_top_routes": ("thetrainline.com", "low"),
}

def validate_connectivity_dataset(payload, *, base_ids=None, destination_ids=None):
    """Validate provenance, direction and identity without inventing connections."""
    if not isinstance(payload, dict) or payload.get("schema_version") != 1 or (
        payload.get("scope") != "data10_city_pair_connectivity_2026_snapshot"
        or payload.get("selection_policy") !=
            "fallback_only_after_historical_and_routes7_and_data9"
    ):
        raise ValueError("DATA 10 contract version or selection policy incompatible")
    snapshot = date.fromisoformat(payload["checked_at"])
    if snapshot.year != 2026:
        raise ValueError("Only historical 2026 connectivity reference supported")
    if base_ids is None:
        from base_research_expanded_model import load_research
        base_ids = [x["id"] for x in load_research()["cities"]]
    if destination_ids is None:
        from ux501_destination_discovery_model import build_destination_discovery
        destination_ids = [x["id"] for x in build_destination_discovery()["destinations"]]
    allowed_bases = {canonical_place(x) for x in base_ids}
    allowed_destinations = {canonical_place(x) for x in destination_ids}
    seen = set()
    records = []
    for original in payload.get("records", []):
        if not isinstance(original, dict):
            raise ValueError("DATA 10 route observation is not an object")
        row = deepcopy(original)
        origin, dest = row.get("origin_id"), row.get("destination_id")
        if not isinstance(origin,str) or not isinstance(dest,str):
            raise ValueError("Missing route identity")
        key = (canonical_place(origin), canonical_place(dest))
        if (origin != key[0] or dest != key[1]
                or origin not in allowed_bases or dest not in allowed_destinations
                or origin == dest or key in seen):
            raise ValueError("Unknown, duplicate, non-canonical or local rail pair")
        seen.add(key)
        kind = row.get("reference_kind")
        if kind not in KINDS:
            raise ValueError("Unknown DATA 10 source kind")
        expected_host, confidence = KINDS[kind]
        url = urlparse(row.get("source_url") or "")
        if (url.scheme != "https" or
                url.hostname not in {expected_host,"www."+expected_host} or
                not url.path.strip("/")):
            raise ValueError("Route needs supported HTTPS source")
        if row.get("confidence") != confidence:
            raise ValueError("Evidence confidence does not match source kind")
        observed = date.fromisoformat(row["source_checked_at"])
        if observed > snapshot:
            raise ValueError("Reference checked after dataset snapshot")
        minutes = row.get("minimum_oneway_min")
        if type(minutes) is not int or not 1 <= minutes <= 1440:
            raise ValueError("Rail duration must be a sourced positive integer")
        if (row.get("mode") != "rail" or
                row.get("direction") != "outbound_only" or
                row.get("return_2027_verified") is not False or
                row.get("valid_for_2027") is not False):
            raise ValueError("Undated 2026 one-way reference cannot prove 2027 service")
        for field in ("return_oneway_min","fare_couple_eur","transfer_count",
                      "origin_station_id","destination_station_id",
                      "service_date_2027"):
            if row.get(field) is not None:
                raise ValueError("Unresearched detail cannot become confirmed evidence")
        records.append(row)
    if not records:
        raise ValueError("DATA 10 research batch is empty")
    return {
        "schema_version": 1,
        "checked_at": payload["checked_at"],
        "scope": payload["scope"],
        "records": records,
        "by_pair": {(r["origin_id"],r["destination_id"]): r for r in records},
        "mutates_catalog": False,
        "verified_2027_services": 0,
    }

def load_connectivity_references(path=DATA, *, base_ids=None, destination_ids=None):
    data=json.loads(Path(path).read_text(encoding="utf-8"))
    return validate_connectivity_dataset(
        data,base_ids=base_ids,destination_ids=destination_ids)
