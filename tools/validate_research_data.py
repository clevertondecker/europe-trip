"""ARCH 1.3 — deterministic structural checks for versioned research data.

No network, secrets or Streamlit required. This validates records, not
tourism claims or the real-time validity of historical train observations.
"""
from __future__ import annotations
import json
import sys
from pathlib import Path


ROOT=Path(__file__).resolve().parents[1]/"data"
# Executable as python tools/validate_research_data.py from the repository root.
sys.path.insert(0,str(ROOT.parent))


def validate_research_contracts(canonical: dict, expanded: dict,
                                cities: dict, exploration: dict) -> dict:
    destinations=canonical["destinations"]
    attractions=canonical["attractions"]
    local=expanded["attractions"]
    bases=cities["cities"]
    if not bases or len({x["id"] for x in bases})!=len(bases):
        raise ValueError("Missing or duplicate city IDs")
    if not destinations or not attractions:
        raise ValueError("Empty canonical destination or attraction catalog")
    if any(not isinstance(x.get("id"),str) or not x["id"].strip() for x in destinations+bases):
        raise ValueError("Missing destination or base ID")
    if len({x["id"] for x in destinations})!=len(destinations):
        raise ValueError("Duplicate canonical destination ID")
    canonical_ids={x["id"] for x in attractions}
    if any(not isinstance(x.get("id"),str) or not x["id"].strip() for x in attractions):
        raise ValueError("Missing attraction ID")
    if len(canonical_ids)!=len(attractions):
        raise ValueError("Duplicate canonical attraction ID")
    allowed_destinations={x["id"] for x in destinations}
    if any(x["destination_id"] not in allowed_destinations or not x.get("name")
           or not x.get("source_urls") or not all(
               isinstance(url,str) and url.startswith("https://")
               for url in x["source_urls"]) for x in attractions):
        raise ValueError("Canonical attraction has no destination")
    base_ids={x["id"] for x in bases}
    if not local or len({x["id"] for x in local})!=len(local):
        raise ValueError("Duplicate or empty DQ3.2 attractions")
    if any(x["city_id"] not in base_ids or not
           x.get("source_url","").startswith("https://") for x in local):
        raise ValueError("DQ3.2 local attraction without a base/source")
    from rail_evidence_unified_model import canonical_place
    canonical_cities={x["id"]:canonical_place(x["destination_id"]) for x in attractions}
    if any(x.get("canonical_attraction_id") is not None and
           (x["canonical_attraction_id"] not in canonical_ids or
            canonical_cities[x["canonical_attraction_id"]] != canonical_place(x["city_id"]))
           for x in local):
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


def verify_snapshot_baseline(observed: dict, baseline: dict) -> None:
    """Governance checkpoint independent of data structural validity."""
    expected=baseline.get("expected_counts")
    if not isinstance(expected,dict) or not expected:
        raise ValueError("Missing reviewed snapshot expectations")
    if set(expected)!=set(observed):
        raise ValueError("Snapshot metric keys changed; review baseline")
    changed={key:{"reviewed":value,"observed":observed[key]}
             for key,value in expected.items() if observed[key]!=value}
    if changed:
        raise ValueError("Dataset snapshot changed; review expected_counts: "+str(changed))


def main():
    def load(name):
        return json.loads((ROOT/name).read_text(encoding="utf-8"))
    result=validate_research_contracts(
        load("attractions_2027.json"),
        load("dq32_macro_tourism_2026_11.json"),
        load("base_city_research_expanded_2026_11.json"),
        load("exploration_bases_2027.json"))
    print("Research data structure valid:",result)
    baseline=json.loads((ROOT/"research_snapshot_baseline.json").read_text(encoding="utf-8"))
    verify_snapshot_baseline(result,baseline)
    print("Reviewed research snapshot baseline matches:",baseline["baseline_id"])
    # DATA10 is a strictly additive route-reference dataset; do not alter the
    # historical snapshot's review counts or transform research into schedules.
    from data10_connectivity_model import load_connectivity_references
    data10=load_connectivity_references()
    print("DATA10 sourced directed one-way references:",len(data10["records"]),
          "across",len({r["origin_id"] for r in data10["records"]}),"base cities")
    from data11_priority_connectivity_model import load_priority_connectivity
    data11 = load_priority_connectivity()
    print("DATA11 additional sourced route references:", len(data11["records"]),
          "across", len({row["origin_id"] for row in data11["records"]}), "priority bases")
    from data12_lille_connectivity_model import load_lille_connectivity
    data12 = load_lille_connectivity()
    print("DATA12 Lille directed one-way references:", len(data12["records"]))
    from data13_directed_connectivity_model import load_data13
    data13 = load_data13()
    print("DATA13 additional directed one-way references:",len(data13["records"]))



if __name__=="__main__":
    main()
