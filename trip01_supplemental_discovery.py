"""Read-only supplemental trip candidates, isolated from frozen 30x46 rail research."""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

DATA = Path(__file__).resolve().parent / "data" / "trip01_supplemental_destinations_2027.json"


def append_trip01_candidates(discovery: dict, path: Path = DATA) -> dict:
    """Add sourced trip candidates to browse/wishlist, without editing TripPlan.

    Deliberately NOT added to canonical attractions, historical rail projection
    or the four-base outing matrix: there is no validated 2027 return/cost.
    """
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if payload.get("schema_version") != 1:
        raise ValueError("Supplemental trip candidate schema not supported")
    output = deepcopy(discovery)
    by_id = {item["id"]: item for item in output["destinations"]}
    for entry in payload["destinations"]:
        if entry["id"] in by_id or not entry["source_url"].startswith("https://"):
            raise ValueError("Supplemental destination duplicated or missing source")
        if not (-90 <= entry["lat"] <= 90 and -180 <= entry["lon"] <= 180):
            raise ValueError("Supplemental destination has invalid coordinates")
        photo = entry.get("photo")
        if photo and (not photo.get("url", "").startswith("https://commons.wikimedia.org/")
                      or not photo.get("source_page", "").startswith("https://commons.wikimedia.org/")
                      or not photo.get("author") or not photo.get("license")
                      or not photo.get("license_url", "").startswith("https://")):
            raise ValueError("Supplemental destination photo lacks Commons source or license")
        attrs = entry.get("attractions", [])
        if not attrs or any(not a["source_url"].startswith("https://") for a in attrs):
            raise ValueError("Supplemental attraction missing source")
        if len({a["id"] for a in attrs}) != len(attrs):
            raise ValueError("Supplemental attraction IDs duplicated")
        selected = [
            {"id": a["id"], "name": a["name"], "category": a["category"],
             "source_url": a["source_url"], "kind": "supplemental_exploratory",
             "reconciled_source_ids": [], "additional_sources": [],
             "alias_names": []}
            for a in attrs
        ]
        by_id[entry["id"]] = {
            "id": entry["id"], "name": entry["name"], "country": entry["country"],
            "sources": ["trip01_supplemental_2027"], "attractions": selected,
            "attraction_count": len(selected),
            "categories": sorted({a["category"] for a in attrs}),
            "photo": entry.get("photo"), "source_url": entry["source_url"],
            "research_status": "supplemental_attractions_documented",
            "feasible_from_base": None, "verified_weekend_return": False,
            "officially_selected": False,
        }
    output["destinations"] = sorted(
        by_id.values(), key=lambda item: (item["country"], item["name"], item["id"])
    )
    output["destination_count"] = len(output["destinations"])
    output["unique_attractions_count"] = sum(
        d["attraction_count"] for d in output["destinations"]
    )
    output["countries"] = sorted({d["country"] for d in output["destinations"]})
    output["categories"] = sorted({
        category for d in output["destinations"] for category in d["categories"]
    })
    return output
