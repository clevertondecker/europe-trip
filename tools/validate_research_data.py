"""ARCH 1.3 — deterministic structural checks for versioned research data.

No network, secrets or Streamlit required. This validates records, not
tourism claims or the real-time validity of historical train observations.
"""
from __future__ import annotations
import json
from pathlib import Path


ROOT=Path(__file__).resolve().parents[1]/"data"


def validate_research_contracts(canonical: dict, expanded: dict,
                                cities: dict, exploration: dict) -> dict:
    destinations=canonical["destinations"]
    attractions=canonical["attractions"]
    local=expanded["attractions"]
    bases=cities["cities"]
    if len(bases)!=30 or len({x["id"] for x in bases})!=30:
        raise ValueError("Expected 30 distinct research city IDs")
    if len(destinations)!=14 or len(attractions)!=65:
        raise ValueError("Canonical attraction catalog unexpectedly changed")
    if len({x["id"] for x in destinations})!=len(destinations):
        raise ValueError("Duplicate canonical destination ID")
    canonical_ids={x["id"] for x in attractions}
    if len(canonical_ids)!=len(attractions):
        raise ValueError("Duplicate canonical attraction ID")
    allowed_destinations={x["id"] for x in destinations}
    if any(x["destination_id"] not in allowed_destinations for x in attractions):
        raise ValueError("Canonical attraction has no destination")
    base_ids={x["id"] for x in bases}
    if not local or len({x["id"] for x in local})!=len(local):
        raise ValueError("Duplicate or empty DQ3.2 attractions")
    if any(x["city_id"] not in base_ids or not
           x.get("source_url","").startswith("https://") for x in local):
        raise ValueError("DQ3.2 local attraction without a base/source")
    if any(x.get("canonical_attraction_id") is not None and
           x["canonical_attraction_id"] not in canonical_ids for x in local):
        raise ValueError("DQ3.2 semantic alias points outside canonical catalog")
    routes=exploration["routes"]
    pairs=[(x["base_id"],x["destination_id"]) for x in routes]
    if len(pairs)!=len(set(pairs)):
        raise ValueError("Duplicate exploratory route")
    if any(type(x.get("train_minutes_oneway_min")) not in (int,type(None))
           or (type(x.get("train_minutes_oneway_min")) is int and
               x["train_minutes_oneway_min"]<=0)
           for x in routes):
        raise ValueError("Exploratory train duration must be positive integer or null")
    if any(x.get("return_verified_2027") is not False for x in routes):
        raise ValueError("Unverified 2027 route cannot be marked confirmed")
    return {"bases":len(bases),"canonical_destinations":len(destinations),
            "canonical_attractions":len(attractions),
            "dq32_source_records":len(local),
            "dq32_cities":len({x["city_id"] for x in local}),
            "historical_exploration_routes":len(routes)}


def main():
    def load(name):
        return json.loads((ROOT/name).read_text(encoding="utf-8"))
    result=validate_research_contracts(
        load("attractions_2027.json"),
        load("dq32_macro_tourism_2026_11.json"),
        load("base_city_research_expanded_2026_11.json"),
        load("exploration_bases_2027.json"))
    print("Research data contracts valid:",result)


if __name__=="__main__":
    main()
