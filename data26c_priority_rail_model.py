"""Additional directed operator summaries; no dated itinerary or fare claim."""
from pathlib import Path
import json

from data25_priority_rail_model import RESEARCH_BASE_IDS
from rail_gap_enrichment_model import validate_gap_dataset

DATA = Path(__file__).resolve().parent / "data" / "data26c_priority_rail_2026_11.json"
INITIAL_SLUGS = {"saumur": "saumur", "dinan": "dinan", "le_mans": "le-mans", "saint_malo": "saint-malo"}
SLUGS = {**INITIAL_SLUGS, "beaune": "beaune", "besancon": "besancon",
         "freiburg": "fribourg-en-brisgau", "saarbrucken": "sarrebruck"}
ADDITIONAL_PAIRS = {("lille", "beaune"), ("lille", "besancon"),
                    ("metz", "freiburg"), ("nancy", "saarbrucken")}
EXPECTED_PAIRS = {(b, d) for b in RESEARCH_BASE_IDS for d in INITIAL_SLUGS} | ADDITIONAL_PAIRS

def load_data26c_rail(path=DATA):
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    result = validate_gap_dataset(payload, base_ids=RESEARCH_BASE_IDS, destination_ids=SLUGS)
    seen = set()
    for row in result["records"] + payload["unresolved"]:
        origin, dest = row["origin_id"], row["destination_id"]
        key = origin, dest
        if (key in seen or origin not in RESEARCH_BASE_IDS or dest not in SLUGS
                or row["source_url"] != "https://www.sncf-connect.com/train/trajet/" + origin + "/" + SLUGS[dest]
                or row["source_checked_at"] != payload["checked_at"]):
            raise ValueError("DATA26C: invalid directed source or duplicated consultation")
        seen.add(key)
        if key in result["by_pair"]:
            if (row["evidence_type"] != "official_route_minimum"
                    or type(row["published_average_min"]) is not int
                    or not row["oneway_min"] <= row["published_average_min"] <= 1440
                    or row["source_capture_date"] is not None
                    or not row["index_recency"]):
                raise ValueError("DATA26C: unsupported summary evidence")
        elif row["reason"] != "technical_failure":
            raise ValueError("DATA26C: unsupported unresolved consultation")
    if seen != EXPECTED_PAIRS:
        raise ValueError("DATA26C: incomplete consultation batch")
    result["unresolved"] = payload["unresolved"]
    return result
