"""Local, licensed destination imagery; no network access at app runtime."""
from __future__ import annotations

from functools import lru_cache
import json
from pathlib import Path
from hashlib import md5
from urllib.parse import quote, unquote, urlsplit

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
    return (local_destination_photo(destination["id"]) or
            destination.get("photo") or online_photo)



def display_photo_url(url: str) -> str:
    """Resolve reviewed Commons FilePath links to their canonical media CDN URL.

    Do not guess an image title: Wikimedia stores the MD5 directory from the
    exact UTF-8 file title. Leave all other URLs untouched.
    """
    parsed = urlsplit(url)
    prefix = "/wiki/Special:FilePath/"
    if (parsed.scheme != "https" or
            parsed.netloc != "commons.wikimedia.org" or
            not parsed.path.startswith(prefix)):
        return url
    title = unquote(parsed.path[len(prefix):]).replace(" ", "_")
    if (not title or "/" in title or "\\" in title or
            title.startswith(".") or "." not in title):
        return url
    digest = md5(title.encode("utf-8")).hexdigest()
    return ("https://upload.wikimedia.org/wikipedia/commons/" +
            digest[0] + "/" + digest[:2] + "/" + quote(title, safe="()_-."))
