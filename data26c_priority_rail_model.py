"""Additional directed operator and distributor summaries; no dated itinerary or fare claim."""
from pathlib import Path
from datetime import date
import json

from data25_priority_rail_model import RESEARCH_BASE_IDS
from rail_gap_enrichment_model import validate_gap_dataset

DATA = Path(__file__).resolve().parent / "data" / "data26c_priority_rail_2026_11.json"
INITIAL_SLUGS = {"saumur": "saumur", "dinan": "dinan", "le_mans": "le-mans", "saint_malo": "saint-malo"}
SLUGS = {**INITIAL_SLUGS, "beaune": "beaune", "besancon": "besancon",
         "freiburg": "fribourg-en-brisgau", "saarbrucken": "sarrebruck",
         "stuttgart": "stuttgart", "arlon": "arlon",
         "trier": "treves", "offenburg": "offenburg",
         "aachen": "aix-la-chapelle", "baden_baden": "baden-baden", "kehl": "kehl",
         "interlaken": "interlaken", "liege": "liege", "namur": "namur"}
ADDITIONAL_PAIRS = {("lille", "beaune"), ("lille", "besancon"),
                    ("metz", "freiburg"), ("nancy", "saarbrucken"),
                    ("metz", "stuttgart"), ("nancy", "stuttgart"),
                    ("metz", "arlon"), ("nancy", "arlon"),
                    ("metz", "trier"), ("nancy", "trier"), ("strasbourg", "trier"),
                    ("metz", "offenburg"), ("nancy", "offenburg"),
                    ("metz", "aachen"), ("nancy", "aachen"),
                    ("metz", "baden_baden"), ("nancy", "baden_baden"),
                    ("lille", "baden_baden"), ("metz", "kehl"),
                    ("nancy", "interlaken"), ("metz", "interlaken"),
                    ("metz", "liege"), ("strasbourg", "arlon"),
                    ("metz", "namur"), ("strasbourg", "namur")}
EXPECTED_PAIRS = {(b, d) for b in RESEARCH_BASE_IDS for d in INITIAL_SLUGS} | ADDITIONAL_PAIRS

def _valid_source(row):
    origin, dest = row["origin_id"], row["destination_id"]
    kind = row.get("evidence_type")
    if kind == "secondary_sample":
        station_destinations = {"trier": ("trier-hbf", "Trier Hbf"),
                                "aachen": ("aachen-hbf", "Aachen Hbf"),
                                "interlaken": ("interlaken-ost", "Interlaken Ost"),
                                "liege": ("liege-guillemins", "Liège-Guillemins")}
        slug = dest.replace("_", "-")
        if dest in station_destinations:
            slug, station = station_destinations[dest]
            if row.get("published_arrival_station") != station:
                return False
        origin_slug = origin
        if (origin, dest) == ("lille", "baden_baden"):
            if row.get("published_origin_station") != "Lille-Europe":
                return False
            origin_slug = "lille-europe"
        return row["source_url"] in (
            f"https://www.thetrainline.com/en/train-times/{origin_slug}-to-{slug}",
            f"https://www.thetrainline.com/train-times/{origin_slug}-to-{slug}",
            f"https://www.thetrainline.com/fr/horaires-train/{origin_slug}-a-{slug}",
        )
    return row["source_url"] == f"https://www.sncf-connect.com/train/trajet/{origin}/{SLUGS[dest]}"

DESTINATION_COUNTRIES = {
    "saumur": "FR", "dinan": "FR", "le_mans": "FR", "saint_malo": "FR",
    "beaune": "FR", "besancon": "FR", "freiburg": "DE", "saarbrucken": "DE",
    "stuttgart": "DE", "arlon": "BE", "trier": "DE", "offenburg": "DE",
    "aachen": "DE", "baden_baden": "DE", "kehl": "DE",
    "interlaken": "CH", "liege": "BE", "namur": "BE",
}

def _validate_quality_review(row, snapshot):
    review = row.get("quality_review")
    if review is None:
        return
    if (review["source_url"] != row["source_url"]
            or not date.fromisoformat(row["source_checked_at"]) <= date.fromisoformat(review["checked_at"]) <= snapshot
            or review["direction"] != "outbound_only"
            or review["origin_country"] != "FR"
            or review["destination_country"] != DESTINATION_COUNTRIES[row["destination_id"]]
            or review["service_legs_verified"] is not False
            or review["valid_for_2027"] is not False
            or not review["note"] or not review["samples"]):
        raise ValueError("DATA26C: invalid quality review provenance")
    for sample in review["samples"]:
        if (type(sample["minimum_min"]) is not int or type(sample["average_min"]) is not int
                or not 1 <= sample["minimum_min"] <= sample["average_min"] <= 1440
                or not sample["index_recency"] or not sample["mode_basis"]
                or any(not isinstance(s, str) or not s.strip() for k in (
                    "origin_station_labels", "arrival_station_labels") for s in sample[k])):
            raise ValueError("DATA26C: invalid reviewed summary")
    reproduced = any(s["minimum_min"] == row["oneway_min"]
                     and s["average_min"] == row["published_average_min"]
                     for s in review["samples"])
    if review["selected_summary_reproduced"] is not reproduced:
        raise ValueError("DATA26C: reviewed summary reproduction mismatch")

def load_data26c_rail(path=DATA):
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    result = validate_gap_dataset(payload, base_ids=RESEARCH_BASE_IDS, destination_ids=SLUGS)
    snapshot = date.fromisoformat(payload["checked_at"])
    seen = set()
    for row in result["records"] + payload["unresolved"]:
        origin, dest = row["origin_id"], row["destination_id"]
        key = origin, dest
        if (key in seen or origin not in RESEARCH_BASE_IDS or dest not in SLUGS
                or not _valid_source(row)
                or date.fromisoformat(row["source_checked_at"]) > snapshot):
            raise ValueError("DATA26C: invalid directed source or duplicated consultation")
        seen.add(key)
        if key in result["by_pair"]:
            if (row["evidence_type"] not in ("official_route_minimum", "secondary_sample")
                    or row["service_date"] is not None
                    or type(row["published_average_min"]) is not int
                    or not row["oneway_min"] <= row["published_average_min"] <= 1440
                    or row["source_capture_date"] is not None
                    or not row["index_recency"]):
                raise ValueError("DATA26C: unsupported summary evidence")
            _validate_quality_review(row, snapshot)
        elif row["reason"] != "technical_failure":
            raise ValueError("DATA26C: unsupported unresolved consultation")
    if seen != EXPECTED_PAIRS:
        raise ValueError("DATA26C: incomplete consultation batch")
    result["unresolved"] = payload["unresolved"]
    return result
