"""DATA 8.1: read-only attraction enrichment and field-level provenance.

Canonical attraction identity belongs to build_destination_discovery().
This module never mutates that catalog, a wishlist, or TripPlan. 2027 access
and booking availability cannot be inferred from historical/source rules.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import date
from pathlib import Path
from urllib.parse import urlparse
import json


ADMISSION = {"unknown", "free_general_entry", "published_price", "external_no_ticket"}
OPENING = {"unknown", "published_general_rule"}
LOCATION = {"unknown", "published_address"}
SEASON = {"unknown", "published_note"}
DURATION = {"unknown", "editorial_estimate", "operator_guidance"}


def _official_url(url):
    parsed = urlparse(url or "")
    return parsed.scheme == "https" and bool(parsed.hostname)


def _checked(value):
    if not isinstance(value, str):
        raise ValueError("source check date missing")
    return date.fromisoformat(value)


def _source_field(field, *, required=False):
    if not isinstance(field, dict):
        raise ValueError("evidence field is not an object")
    url, checked = field.get("source_url"), field.get("checked_at")
    if required and (not _official_url(url) or not checked):
        raise ValueError("published fact requires HTTPS source and checked date")
    if url is not None or checked is not None:
        if not _official_url(url) or checked is None:
            raise ValueError("source url/date must be supplied together")
        _checked(checked)


def _duration(row):
    if not isinstance(row, dict) or row.get("state") not in DURATION:
        raise ValueError("duration state invalid")
    lo, hi = row.get("min_minutes"), row.get("max_minutes")
    if row["state"] == "unknown":
        if lo is not None or hi is not None:
            raise ValueError("unknown duration cannot have numbers")
    elif (type(lo) is not int or type(hi) is not int or
          lo <= 0 or hi < lo or hi > 600):
        raise ValueError("duration must be a plausible positive range")
    if row["state"] == "editorial_estimate":
        if not row.get("method"):
            raise ValueError("editorial range needs explicit method")
    if row["state"] == "operator_guidance":
        _source_field(row, required=True)


def _admission(row):
    if not isinstance(row, dict) or row.get("state") not in ADMISSION:
        raise ValueError("ticket state invalid")
    if row.get("valid_for_2027") is not False:
        raise ValueError("price cannot claim 2027 booking")
    amount = row.get("amount")
    if row["state"] in {"unknown", "external_no_ticket"}:
        if amount is not None:
            raise ValueError("unknown/external ticket is not numeric")
    elif row["state"] == "free_general_entry":
        if amount != 0:
            raise ValueError("free entry requires explicit zero")
        _source_field(row, required=True)
    else:
        if type(amount) not in (int, float) or amount <= 0 or row.get("currency") not in ("EUR", "CHF"):
            raise ValueError("published ticket must be positive EUR/CHF")
        if row.get("unit") not in ("adult", "person", "couple"):
            raise ValueError("ticket denomination missing")
        _source_field(row, required=True)


def validate_entry(entry, *, identity_map, seen=None):
    """Validate an attraction record against *existing* canonical IDs."""
    if not isinstance(entry, dict):
        raise ValueError("attraction entry invalid")
    x = deepcopy(entry)
    aid, dest = x.get("attraction_id"), x.get("destination_id")
    if not aid or identity_map.get(aid) != dest:
        raise ValueError("unreconciled or mismatched attraction identity")
    if seen is not None:
        if aid in seen:
            raise ValueError("duplicate canonical attraction")
        seen.add(aid)
    if x.get("valid_for_2027") is not False:
        raise ValueError("entire research entry is historical/planning only")
    experience = x.get("experience")
    if not isinstance(experience, dict) or not experience.get("why_visit"):
        raise ValueError("why visit is required")
    _source_field(experience, required=True)
    _duration(x.get("duration"))
    _admission(x.get("admission"))
    opening = x.get("opening")
    if not isinstance(opening, dict) or opening.get("state") not in OPENING:
        raise ValueError("opening state invalid")
    if opening["state"] == "published_general_rule":
        if not opening.get("rule"):
            raise ValueError("published opening needs rule")
        _source_field(opening, required=True)
    elif opening.get("rule") is not None:
        raise ValueError("unknown opening cannot have rule")
    if opening.get("valid_for_2027") is not False:
        raise ValueError("opening never confirms 2027")
    season = x.get("seasonality")
    if not isinstance(season, dict) or season.get("state") not in SEASON:
        raise ValueError("seasonality state invalid")
    if season["state"] == "published_note":
        if not season.get("note"):
            raise ValueError("source seasonality note missing")
        _source_field(season, required=True)
    elif season.get("note") is not None:
        raise ValueError("unknown seasonality cannot have claim")
    location = x.get("location")
    if not isinstance(location, dict) or location.get("state") not in LOCATION:
        raise ValueError("location state invalid")
    if location["state"] == "published_address":
        if not location.get("address"):
            raise ValueError("published address missing")
        _source_field(location, required=True)
    elif location.get("address") is not None:
        raise ValueError("unknown location cannot contain address")
    # Access is its own versioned entity (DATA 8.3), not an inferred distance.
    if x.get("travel_time_from_station") is not None:
        raise ValueError("station time belongs in independent access evidence")
    return x


def build_identity_map(discovery):
    return {a["id"]: dest["id"] for dest in discovery["destinations"]
            for a in dest["attractions"]}


def validate_dataset(data, *, discovery):
    if (not isinstance(data, dict) or data.get("schema_version") != 1 or
            data.get("scope") != "tourism_planning_overlay"):
        raise ValueError("invalid tourism overlay version/scope")
    _checked(data.get("checked_at"))
    ids = build_identity_map(discovery)
    seen = set()
    rows = [validate_entry(x, identity_map=ids, seen=seen)
            for x in data.get("entries", [])]
    for x in rows:
        for field in ("experience", "opening", "admission", "seasonality", "location"):
            checked = x[field].get("checked_at")
            if checked and checked > data["checked_at"]:
                raise ValueError("source checked after dataset snapshot")
    candidates = data.get("unreconciled_candidates", [])
    for x in candidates:
        if (x.get("canonical_attraction_id") is not None or
                not x.get("destination_id") or not x.get("name") or
                not _official_url(x.get("source_url"))):
            raise ValueError("candidate may not invent a canonical ID")
    return {"schema_version": 1, "checked_at": data["checked_at"],
            "entries": rows, "by_id": {x["attraction_id"]: x for x in rows},
            "unreconciled_candidates": deepcopy(candidates),
            "mutates_catalog": False, "verified_2027_visits": 0}


def load_dataset(path, *, discovery=None):
    from ux501_destination_discovery_model import build_destination_discovery
    discovery = discovery if discovery is not None else build_destination_discovery()
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return validate_dataset(data, discovery=discovery)


def coverage_report(research, *, destination_ids=None):
    selected = set(destination_ids) if destination_ids is not None else None
    rows = [r for r in research["entries"]
            if selected is None or r["destination_id"] in selected]
    return {"selected_attractions": len(rows),
            "experience_sourced": sum(bool(r["experience"]["why_visit"]) for r in rows),
            "duration_range": sum(r["duration"]["state"] != "unknown" for r in rows),
            "general_entry_known": sum(r["admission"]["state"] not in ("unknown",) for r in rows),
            "general_hours_documented": sum(r["opening"]["state"] != "unknown" for r in rows),
            "seasonality_documented": sum(r["seasonality"]["state"] != "unknown" for r in rows),
            "address_documented": sum(r["location"]["state"] != "unknown" for r in rows),
            "2027_verified": 0}


def card_projection(attraction, *, research):
    """Read-only view; don't replace canonical description/alias/IDs."""
    item = research["by_id"].get(attraction["id"])
    return {**deepcopy(attraction), "data8": deepcopy(item),
            "data8_researched": item is not None, "2027_confirmed": False}
