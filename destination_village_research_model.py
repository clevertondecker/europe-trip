"""Read-only evidence for Wengen and Riquewihr; no inferred schedules or fares."""
from pathlib import Path
import json

DATA = Path(__file__).resolve().parent / "data" / "wengen_riquewihr_research_2026_11.json"
BASE_IDS = ("mulhouse", "strasbourg", "metz", "nancy", "lille")
DESTINATION_IDS = ("wengen", "riquewihr")

def load_village_research(path=DATA):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    rows = data["connections"]
    pairs = {(r["base_id"], r["destination_id"]) for r in rows}
    if len(rows) != len(pairs) or pairs != {(b, d) for b in BASE_IDS for d in DESTINATION_IDS}:
        raise ValueError("Incomplete village research matrix")
    for r in rows:
        if r["valid_for_2027"] is not False or r["weekend_return_verified"] is not False or r["full_route_fare_couple"] is not None:
            raise ValueError("Unverified future journey or fare")
        if r["kind"] == "separate_segments_not_timetable":
            if r["minimum_oneway_min"] is not None or r["typical_oneway_min"] is not None or r["segment_sum_min"] != sum(s["minimum_min"] for s in r["segments"]):
                raise ValueError("Segment sum is not an end-to-end timetable")
        elif r["kind"] != "published_full_route" or r["mode"] != "rail" or r["segment_sum_min"] is not None or not r["minimum_oneway_min"]:
            raise ValueError("Invalid full journey reference")
        if not all(s["source_url"].startswith("https://") for s in r["segments"]):
            raise ValueError("Missing source")
    return data
