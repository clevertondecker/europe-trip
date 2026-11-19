"""DATA16: reviewed regional attraction candidates, not trip viability."""

from __future__ import annotations
import json
from pathlib import Path
from urllib.parse import urlparse

DEFAULT=Path(__file__).resolve().parent/"data"/"data16_three_base_attraction_research_2026_11.json"
BASES={"selestat","offenburg","dijon"}
CATEGORIES={"castle","nature","heritage","wildlife","gastronomy","museum"}


def validate_data16(data):
    if data.get("schema_version")!=1 or data.get("scope")!="DATA16_research_candidates_not_canonical_tripplan":
        raise ValueError("DATA16 scope/version")
    bases=data.get("base_profiles",{})
    if set(bases)!=BASES or set(data.get("base_ids",[]))!=BASES:
        raise ValueError("DATA16 only approved three base cities")
    for base in bases.values():
        if base.get("lodging_state") not in {
            "no_qualified_two_adult_55_to_65_night_quote",
            "examples_only_not_autumn_2027_eligible",
            "historical_rent_index_only"
        } or not base.get("housing_source","").startswith("https://"):
            raise ValueError("Unreviewed lodging claim")
    rows=data.get("attraction_candidates",[])
    if len(rows)!=15 or len({x["id"] for x in rows})!=len(rows):
        raise ValueError("DATA16 expected 15 distinct candidates")
    if {r["base_id"] for r in rows}!=BASES:
        raise ValueError("Missing city candidates")
    if any(sum(r["base_id"]==b for r in rows)!=5 for b in BASES):
        raise ValueError("Expected five candidates per base")
    for x in rows:
        if not x["id"].startswith("data16_"+x["base_id"]+"_") or x["category"] not in CATEGORIES:
            raise ValueError("Invalid candidate identity")
        u=urlparse(x.get("source_url",""))
        if u.scheme!="https" or not u.hostname or not x.get("name") or not x.get("location"):
            raise ValueError("Candidate lacks individual official source")
        if x["source_kind"]!="official_tourism_or_operator":
            raise ValueError("Non-official source")
        photo=x.get("photo")
        if (not isinstance(photo,dict) or not photo.get("file_title")
                or not photo.get("source_page","").startswith(
                    "https://commons.wikimedia.org/wiki/File:")
                or not photo.get("alt")
                or photo.get("license_verified_for_reuse") is not False
                or type(photo.get("contextual")) is not bool):
            raise ValueError("DATA16 image identity/credit missing or fabricated")
        if x["id"]=="data16_dijon_cassissium" and not photo["contextual"]:
            raise ValueError("Contextual photo must remain labeled")
        if (x["minimum_oneway_min"] is not None or x["door_to_door_min"] is not None or
            x["return_verified_2027"] is not False or x["open_2027_verified"] is not False or
            x["ticket_eur"] is not None or x["existing_local_attraction"] is not False):
            raise ValueError("Unverified itinerary/price or duplicate attraction")
    return {"bases":len(BASES),"candidates":len(rows)}


def load_data16(path=DEFAULT):
    result=json.loads(Path(path).read_text(encoding="utf-8"))
    validate_data16(result)
    return result
