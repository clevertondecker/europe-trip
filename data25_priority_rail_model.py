"""DATA25: additive operator references for the approved French research scope."""
from pathlib import Path
import json

from rail_gap_enrichment_model import validate_gap_dataset

DATA = Path(__file__).resolve().parent / "data" / "data25_priority_rail_2026_11.json"
RESEARCH_BASE_IDS = ("lille", "metz", "mulhouse", "nancy", "strasbourg")
RESEARCH_SCOPE_APPROVED_AT = "2026-11-25"
RESEARCH_DESTINATIONS = ("annecy", "angers", "rennes", "selestat")


def load_data25(path=DATA):
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    result = validate_gap_dataset(payload, base_ids=RESEARCH_BASE_IDS,
                                  destination_ids=RESEARCH_DESTINATIONS)
    for row in result["records"]:
        if (row["evidence_type"] != "official_route_minimum" or
                row["source_url"] != "https://www.sncf-connect.com/train/trajet/"
                + row["origin_id"] + "/" + row["destination_id"]):
            raise ValueError("DATA25: source must match directed operator route")
    return result
