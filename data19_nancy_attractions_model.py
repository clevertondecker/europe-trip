"""Validated Nancy research candidates; unknown trip facts remain unknown."""
import json
import unicodedata
from pathlib import Path
from urllib.parse import unquote, urlsplit

DATA = Path(__file__).resolve().parent / "data" / "data19_nancy_attractions_2026_11.json"
ZONES = {"cidade": 5, "metro": 1, "regional": 5}
PRIORITIES = {"alta", "media_alta", "media"}
UNKNOWN_FIELDS = ("rail_minutes", "last_mile_minutes", "door_to_door_minutes", "ticket_eur")


def _identity(value: str) -> str:
    """Stable comparison for names and municipalities, including accents."""
    return " ".join(
        "".join(char for char in unicodedata.normalize("NFKD", value.casefold())
                if not unicodedata.combining(char)).split()
    )


def validate_data19(payload):
    if not isinstance(payload, dict):
        raise ValueError("Invalid DATA19 payload")
    if (payload.get("schema_version") != 1
            or payload.get("scope") != "DATA19_NANCY_RESEARCH_ONLY"
            or payload.get("base_id") != "nancy"):
        raise ValueError("Invalid DATA19 scope")
    if payload.get("existing_canonical_nancy_count") != 6:
        raise ValueError("Canonical Nancy reconciliation")
    records = payload.get("attraction_candidates")
    if not isinstance(records, list) or len(records) != 11:
        raise ValueError("Expected 11 Nancy candidates")
    ids, places, photos = set(), set(), set()
    counts = {zone: 0 for zone in ZONES}
    for r in records:
        if not isinstance(r, dict):
            raise ValueError("Invalid DATA19 record")
        record_id = r.get("id")
        name, municipality = r.get("name"), r.get("municipality")
        zone = r.get("zone")
        priority = r.get("priority")
        if (not isinstance(record_id, str)
                or not record_id.startswith("data19_nancy_")
                or record_id in ids
                or not isinstance(name, str) or not name.strip()
                or not isinstance(municipality, str) or not municipality.strip()
                or zone not in ZONES or priority not in PRIORITIES
                or not isinstance(r.get("description"), str) or not r["description"].strip()
                or not isinstance(r.get("visit_tip"), str) or not r["visit_tip"].strip()
                or r.get("base_id") != "nancy"):
            raise ValueError("Missing or duplicate Nancy candidate")
        ids.add(record_id)
        place = (_identity(name), _identity(municipality))
        if place in places:
            raise ValueError("Duplicate attraction identity")
        places.add(place)
        counts[zone] += 1

        source = urlsplit(r.get("source_url", ""))
        if source.scheme != "https" or not source.hostname or source.username or source.password:
            raise ValueError("Missing valid official source")
        photo = r.get("photo")
        if not isinstance(photo, dict):
            raise ValueError("Missing Wikimedia photo metadata")
        file_title = photo.get("file_title")
        source_page = photo.get("source_page", "")
        if not isinstance(file_title, str) or not file_title.strip() or not isinstance(source_page, str):
            raise ValueError("Missing Wikimedia file title")
        page = urlsplit(source_page)
        path_prefix = "/wiki/File:"
        if (page.scheme != "https" or page.netloc != "commons.wikimedia.org"
                or not page.path.startswith(path_prefix)
                or unquote(page.path[len(path_prefix):]).replace("_", " ") != file_title
                or not photo.get("alt")
                or photo.get("license_verified_for_reuse") is not False):
            raise ValueError("Wikimedia file reference mismatch or unverified license")
        if file_title in photos:
            raise ValueError("Duplicated photo in distinct attraction cards")
        photos.add(file_title)
        if (any(r.get(k, object()) is not None for k in UNKNOWN_FIELDS)
                or r.get("open_2027_verified") is not False
                or r.get("return_2027_verified") is not False
                or r.get("feasibility") != "unknown"):
            raise ValueError("Unverified travel, opening, or fares")
    if counts != ZONES:
        raise ValueError("Incorrect Nancy zone distribution")
    return {"total": len(records), "city": counts["cidade"],
            "metro": counts["metro"], "regional": counts["regional"]}


def load_data19(path=DATA):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    validate_data19(data)
    return data
