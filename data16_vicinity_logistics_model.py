"""Research-only transport projection to each of three attraction hubs."""
from data16_three_base_attraction_model import load_data16
from base_scenario_model import base_options
from base_explorer_model import load_exploration
from rail_evidence_unified_model import load_rail_evidence
from evidence_query_model import get_rail_evidence
from rail_reference_projection_model import decorate_comparison
HUBS=("selestat","offenburg","dijon")

def hub_references(origin,*,rail=None,exploration=None):
    if origin not in {x["id"] for x in base_options()}:
        raise ValueError("Unknown base city")
    rail=rail if rail is not None else load_rail_evidence()
    exploration=exploration if exploration is not None else load_exploration()
    inputs=[]
    for hub in HUBS:
        legacy=get_rail_evidence(origin,hub,rail=rail,exploration=exploration)
        inputs.append({"base_id":origin,"destination_id":hub,
                       "evidence_status":legacy["status"],
                       "minimum_oneway_min":legacy["minimum_oneway_min"],
                       "source_url":legacy["source_url"],"divergent_sources":False})
    cells=decorate_comparison({"rows":inputs})["cells"]
    result={}
    for hub in HUBS:
        item=cells[(origin,hub)]
        local=origin==hub
        result[hub]={
            "origin_id":origin,"hub_id":hub,"local":local,
            "rail_to_hub_min":None if local else item["display_min"],
            "evidence_category":item["category"],"evidence_label":item["label"],
            "source_url":item.get("reference_source_url") or item.get("source_url"),
            "last_mile_min":None,"total_oneway_min":None,
            "return_verified_2027":False,
        }
    return result

def attraction_references(origin,*,data=None,rail=None,exploration=None):
    data=data or load_data16()
    hubs=hub_references(origin,rail=rail,exploration=exploration)
    return [{
        "origin_id":origin,"attraction_id":a["id"],"hub_id":a["base_id"],
        "rail_to_hub_min":hubs[a["base_id"]]["rail_to_hub_min"],
        "rail_to_hub_source":hubs[a["base_id"]]["source_url"],
        "local_hub":hubs[a["base_id"]]["local"],
        "evidence_label":hubs[a["base_id"]]["evidence_label"],
        "last_mile_hint":a["transport_hint"],
        "last_mile_status":a["transport_status"],
        "last_mile_min":None,"total_oneway_min":None,
        "return_verified_2027":False,"feasibility":"unknown"
    } for a in data["attraction_candidates"]]

def all_base_hubs():
    rail=load_rail_evidence()
    exploration=load_exploration()
    return [v for b in base_options() for v in hub_references(
        b["id"],rail=rail,exploration=exploration).values()]
