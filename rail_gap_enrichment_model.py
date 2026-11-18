"""DATA 9: additive historical rail references for previously unresearched pairs.

Not a timetable, not verified 2027 reachability, and NEVER a substitute for
legacy operator observations or the immutable ROUTES 7 audit.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import date
from pathlib import Path
from urllib.parse import urlparse
import json

from rail_evidence_unified_model import canonical_place

DATA = Path(__file__).resolve().parent / "data" / "rail_gap_enrichment_2026_11.json"
KINDS = {
    "official_route_minimum": ("operator_city_level", "medium"),
    "official_timetable_sample": ("operator_schedule_sample", "medium"),
    "secondary_sample": ("third_party_sample", "low"),
}
OPERATOR_HOSTS = {"www.sncf-connect.com", "sncf-connect.com",
                  "www.bahn.de", "bahn.de"}
THIRD_PARTY_HOSTS = {"www.thetrainline.com", "thetrainline.com",
                     "www.rome2rio.com", "rome2rio.com",
                     "www.pickthetrain.com", "pickthetrain.com"}


def validate_gap_dataset(payload, *, destination_ids=None, base_ids=None):
    """Reject fabricated identities, ungrounded numbers, and 2027 guarantees."""
    if (payload.get("schema_version") != 1 or
            payload.get("scope") != "audited_historical_route_gap_overlay"):
        raise ValueError("rail gap research contract incompatible")
    snapshot = date.fromisoformat(payload["checked_at"])
    if destination_ids is None or base_ids is None:
        from ux501_destination_discovery_model import build_destination_discovery
        from base_research_expanded_model import load_research
        if destination_ids is None:
            destination_ids = {row["id"] for row in
                               build_destination_discovery()["destinations"]}
        if base_ids is None:
            base_ids = {row["id"] for row in load_research()["cities"]}
    destinations = {canonical_place(x) for x in destination_ids}
    bases = {canonical_place(x) for x in base_ids}
    seen = set()
    records = []
    for original in payload.get("records", []):
        row = deepcopy(original)
        origin, dest = row.get("origin_id"), row.get("destination_id")
        if not isinstance(origin, str) or not isinstance(dest, str):
            raise ValueError("missing pair identity")
        key = canonical_place(origin), canonical_place(dest)
        if (origin != key[0] or dest != key[1] or key[0] not in bases or
                key[1] not in destinations or key[0] == key[1] or key in seen):
            raise ValueError("duplicate, unknown or local rail gap pair")
        seen.add(key)

        kind = row.get("evidence_type")
        if kind not in KINDS:
            raise ValueError("unknown historical evidence kind")
        level, confidence = KINDS[kind]
        if row.get("evidence_level") != level or row.get("confidence") != confidence:
            raise ValueError("unsubstantiated evidence level or confidence")
        url = urlparse(row.get("source_url") or "")
        expected_hosts = (OPERATOR_HOSTS if kind != "secondary_sample"
                          else THIRD_PARTY_HOSTS)
        if url.scheme != "https" or url.hostname not in expected_hosts:
            raise ValueError("unrecognized or non-HTTPS source")
        observed = date.fromisoformat(row["source_checked_at"])
        if observed > snapshot:
            raise ValueError("route source newer than dataset snapshot")
        if kind == "official_timetable_sample":
            if not row.get("service_date"):
                raise ValueError("timetable sample requires a service date")
        elif kind == "official_route_minimum" and row.get("service_date") is not None:
            raise ValueError("undated route minimum cannot claim a service date")
        if row.get("service_date"):
            service_date = date.fromisoformat(row["service_date"])
            if service_date.year != 2026:
                raise ValueError("only historical 2026 service samples permitted")
        if (type(row.get("oneway_min")) is not int or
                not 1 <= row["oneway_min"] <= 1440):
            raise ValueError("unsupported time or duration")
        if (row.get("direction") != "outbound_only" or
                row.get("station_status") != "not_reconciled" or
                row.get("origin_station_id") is not None or
                row.get("destination_station_id") is not None or
                row.get("return_weekend_verified") is not False or
                row.get("door_to_door_verified") is not False or
                row.get("valid_for_2027") is not False or
                row.get("fare_couple_eur") is not None or
                row.get("transfer_count") is not None):
            raise ValueError("historical observation cannot qualify as complete outing")
        if not isinstance(row.get("note"), str) or not row["note"].strip():
            raise ValueError("evidence provenance note is required")
        records.append(row)
    if not records:
        raise ValueError("empty rail research batch")
    candidates = payload.get("known_unlinked_candidates", [])
    if (not isinstance(candidates, list) or len(set(candidates)) != len(candidates)
            or any(not isinstance(c, str) or c in destinations for c in candidates)):
        raise ValueError("unreconciled candidates may not silently become destinations")
    return {
        "checked_at": payload["checked_at"],
        "scope": payload["scope"],
        "records": records,
        "by_pair": {(r["origin_id"], r["destination_id"]): r for r in records},
        "known_unlinked_candidates": list(candidates),
        "mutates_catalog": False,
        "verified_2027_services": 0,
    }


def load_gap_enrichment(path=DATA, *, destination_ids=None, base_ids=None):
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return validate_gap_dataset(
        payload, destination_ids=destination_ids, base_ids=base_ids)


def missing_pair_report(base_ids, destination_ids, *, gaps=None,
                        existing_timed_pairs=()):
    """Read-only coverage across arbitrary selected bases and destinations.

    Do not infer missing=impossible, reverse journeys or a time from adjacency.
    """
    gaps = gaps if gaps is not None else load_gap_enrichment()
    bases = list(base_ids)
    destinations = list(destination_ids)
    if (len(set(bases)) != len(bases) or len(set(destinations)) != len(destinations)):
        raise ValueError("duplicate coverage identifiers")
    covered = set(existing_timed_pairs)
    rows = []
    for b in bases:
        for d in destinations:
            key = b, d
            if b == d:
                state = "local_not_rail"
            elif key in covered:
                state = "existing_historical"
            elif key in gaps["by_pair"]:
                state = "new_reference_only"
            else:
                state = "still_unknown"
            rows.append({"base_id": b, "destination_id": d, "state": state})
    return {
        "total": len(rows),
        "rows": rows,
        "reference_only": sum(r["state"] == "new_reference_only" for r in rows),
        "still_unknown": sum(r["state"] == "still_unknown" for r in rows),
        "no_schedule_2027_confirmed": True,
        "mutates_catalog": False,
    }
