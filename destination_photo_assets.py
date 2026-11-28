"""Local, licensed destination imagery; no network access at app runtime."""
from __future__ import annotations

from functools import lru_cache
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MANIFEST = ROOT / "data" / "destination_photo_assets.json"


@lru_cache(maxsize=1)
def _manifest() -> dict:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if data.get("schema_version") != 1:
        raise ValueError("Unsupported destination photo manifest version")
    return data["assets"]


def local_destination_photo(destination_id: str) -> dict | None:
    """Return a local-image photo record if its bytes exist and are safe."""
    record = _manifest().get(destination_id)
    if record is None:
        return None
    relative = Path(record["file"])
    if (relative.is_absolute() or ".." in relative.parts or
            relative.suffix.casefold() != ".webp" or
            relative.parts[:2] != ("assets", "destinations")):
        raise ValueError("Unsafe local image reference")
    path = ROOT / relative
    if not path.is_file() or path.stat().st_size < 5000:
        return None
    if not (record["source_page"].startswith("https://commons.wikimedia.org/wiki/File:") and
            record["license_url"].startswith(("https://creativecommons.org/licenses/",
                                              "https://creativecommons.org/publicdomain/")) and
            record["author"] and record["license"] and record["alt"]):
        raise ValueError("Destination photo without valid attribution")
    return {
        "local_path": str(path),
        "author": record["author"],
        "license": record["license"],
        "license_url": record["license_url"],
        "source_page": record["source_page"],
        "alt": record["alt"],
        "origin": "bundled_open_license",
        "edited": True,
    }


def preferred_destination_photo(destination: dict, online_photo: dict | None = None) -> dict | None:
    """Prefer bundled verified bytes over hotlinked editorial images."""
    local = local_destination_photo(destination["id"])
    if local:
        return local
    photo = destination.get("photo")
    if destination["id"] == "metz" and photo:
        # Verified Wikimedia Commons source (not a guessed CDN hash).
        # Keep this as an editorial fallback until a licensed local WEBP
        # can be bundled through the photo manifest.
        return {
            **photo,
            "url": "https://upload.wikimedia.org/wikipedia/commons/3/36/Metz_centre_ville_crop.jpg",
            "source_page": "https://commons.wikimedia.org/wiki/File:Metz_centre_ville_crop.jpg",
            "author": "Philippe Gisselbrecht / Ville de Metz",
            "license": "CC BY-SA 4.0",
            "license_url": "https://creativecommons.org/licenses/by-sa/4.0/",
        }
    return photo or online_photo



from collections import OrderedDict
from time import monotonic
from commons_client import NEGATIVE_TTL, file_path_title, fetch_photo

_resolution_cache = OrderedDict()


def display_photo_url(url: str) -> str:
    """Direct URLs bypass lookup; failed lookups retry after a short TTL."""
    title = file_path_title(url)
    if not title:
        return url
    now = monotonic()
    cached = _resolution_cache.get(title)
    if cached is not None:
        result, expires = cached
        if now < expires:
            _resolution_cache.move_to_end(title)
            return result or url
    photo = fetch_photo(title)
    result = photo["url"] if photo else None
    _resolution_cache[title] = (result, float("inf") if result else monotonic() + NEGATIVE_TTL)
    _resolution_cache.move_to_end(title)
    while len(_resolution_cache) > 256:
        _resolution_cache.popitem(last=False)
    return result or url
