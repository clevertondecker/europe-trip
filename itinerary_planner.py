"""Evidence-aware 2027 itinerary planning: transport samples, not bookable quotes."""
from __future__ import annotations
import json
from pathlib import Path

FILE = Path(__file__).resolve().parent / "data" / "itinerary_options_2027.json"

def validate_itinerary(data: dict) -> None:
    if data["travelers"] != 2 or data["wedding"] != "2027-09-04":
        raise ValueError("Wrong travel profile")
    places = data["places"]
    ids = [p["id"] for p in places]
    if len(ids) != len(set(ids)) or len(ids) < 15:
        raise ValueError("Destination catalog invalid")
    phases = {"italy", "france"}
    for p in places:
        if p["phase"] not in phases or not -90 <= p["lat"] <= 90 or not -180 <= p["lon"] <= 180:
            raise ValueError("Invalid place map data")
    known_bases = {"salerno", "maiori", "mulhouse", "strasbourg", "metz", "nancy"}
    outing_ids = set()
    for entry in data["outings"]:
        if entry["id"] in outing_ids or not entry["id"]:
            raise ValueError("Duplicate outing")
        outing_ids.add(entry["id"])
        if entry["phase"] not in phases or not set(entry["base_ids"]) <= known_bases:
            raise ValueError("Unknown base/phase")
        if entry["currency"] not in {"EUR", "CHF"}:
            raise ValueError("Currency cannot be inferred or mixed")
        if not entry["source_url"].startswith("https://"):
            raise ValueError("Provenance required")
        price = entry["price_eur_person_leg"]
        if price is None:
            if entry["fare_kind"] != "unknown":
                raise ValueError("Unknown fare cannot masquerade as verified")
        elif price <= 0 or entry["fare_kind"] not in {"full", "discount", "roundtrip_price"}:
            raise ValueError("Invalid fare")
        if entry["fare_kind"] == "roundtrip_price" and entry["legs"] != 1:
            raise ValueError("Round-trip price must not be doubled")
        if entry["legs"] not in {1, 2}:
            raise ValueError("Only known leg counts supported")

def load_itinerary(path: Path = FILE) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    validate_itinerary(data)
    return data

def select_outings(data: dict, phase: str, base: str) -> list[dict]:
    return [o for o in data["outings"] if o["phase"] == phase and base in o["base_ids"]]

def published_ticket_total(entry: dict, travelers: int = 2) -> float | None:
    """Only a *conditional* historical ticket subtotal; excludes everything else."""
    if travelers < 1:
        raise ValueError("Travelers must be positive")
    price = entry["price_eur_person_leg"]
    return None if price is None else round(price * entry["legs"] * travelers, 2)

def basket_totals(outings: list[dict], selected_ids: list[str], travelers: int = 2) -> dict:
    by_id = {x["id"]:x for x in outings}
    if len(selected_ids) != len(set(selected_ids)) or not set(selected_ids) <= set(by_id):
        raise ValueError("Selected outing does not belong to this base")
    subtotals = {"EUR": 0., "CHF": 0.}
    missing = []
    conditional = []
    for key in selected_ids:
        item = by_id[key]
        value = published_ticket_total(item, travelers)
        if value is None:
            missing.append(item["title"])
        else:
            subtotals[item["currency"]] = round(subtotals[item["currency"]] + value, 2)
            if item["fare_kind"] == "discount":
                conditional.append(item["title"])
    return {"known_ticket_subtotals":subtotals, "unpriced":missing,
            "discount_conditional":conditional, "selected_count":len(selected_ids),
            "complete":len(missing)==0 and len(selected_ids)>0}

def visible_map_places(data: dict, phase: str) -> list[dict]:
    return [p for p in data["places"] if p["phase"] == phase]
