"""Source-aware supplemental outing costs; unknown is never interpreted as zero.

Existing fare/attraction prices are owned by attractions_model and not repeated.
"""
from __future__ import annotations
import json
from decimal import Decimal
from pathlib import Path
CATEGORIES={"local_transport","dining","extra_hotel","ticket","intercity_return","other"}
STATUS={"unknown","historical_observed","official_published","conditional"}
CURRENCIES={"EUR","CHF","BRL"}
UNITS={"couple","person","night","visit"}
FILE=Path(__file__).resolve().parent/"data"/"outing_cost_evidence_2027.json"

def validate_evidence(data:dict,catalog:dict|None=None)->dict:
    if data.get("schema_version")!=1 or not isinstance(data.get("items"),list):
        raise ValueError("Evidence schema invalid")
    destinations=None if catalog is None else {d["id"] for d in catalog["destinations"]}
    attraction_ids=None if catalog is None else {a["id"] for a in catalog["attractions"]}
    for item in data["items"]:
        if item["category"] not in CATEGORIES or item["status"] not in STATUS:
            raise ValueError("Unsupported cost item")
        if item.get("currency") not in CURRENCIES or item.get("unit") not in UNITS:
            raise ValueError("Invalid currency/unit")
        if destinations is not None and item.get("destination_id") not in destinations:
            raise ValueError("Unknown destination")
        if item.get("attraction_id") is not None and attraction_ids is not None and item["attraction_id"] not in attraction_ids:
            raise ValueError("Unknown attraction")
        value=item.get("amount")
        if value is None:
            if item["status"]!="unknown":raise ValueError("Known status without price")
        else:
            amount=Decimal(str(value))
            if not amount.is_finite() or amount<0:raise ValueError("Invalid amount")
            if item["status"]=="unknown":raise ValueError("Unverified numeric price")
            if not (isinstance(item.get("source_url"),str)
                    and item["source_url"].startswith("https://")
                    and item.get("verified_at") and item.get("validity_period")):
                raise ValueError("Price without dated verifiable source")
    return data

def load_outing_evidence(path:Path=FILE,catalog:dict|None=None)->dict:
    return validate_evidence(json.loads(path.read_text(encoding="utf-8")),catalog)

def evidence_for_outing(destination_id:str,attraction_ids:list[str],
                        data:dict|None=None)->dict:
    data=validate_evidence(data or load_outing_evidence())
    selected=set(attraction_ids)
    items=[x for x in data["items"] if x["destination_id"]==destination_id
           and (x.get("attraction_id") is None or x["attraction_id"] in selected)]
    amounts={cur:Decimal("0") for cur in CURRENCIES}
    pending=[]
    for item in items:
        if item["amount"] is None:pending.append(item)
        else:
            # No automatic multiplication of per-night/per-person costs without
            # nights and number of visitors explicitly modeled.
            if item["unit"] in ("couple","visit"):
                amounts[item["currency"]]+=Decimal(str(item["amount"]))
            else:pending.append(item)
    return {"items":items,"pending":pending,
            "known_by_currency":{k:float(v) for k,v in amounts.items()},
            "source_metadata":[{"category":x["category"],"source":x.get("source_url"),
                                "validity_period":x.get("validity_period")}
                               for x in items if x.get("source_url")]}
