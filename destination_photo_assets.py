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
    if destination["id"] == "metz" and photo and (
            photo.get("source_page") ==
            "https://commons.wikimedia.org/wiki/File:Centre_Pompidou_%C3%A0_Metz.jpg"):
        # Use Wikimedia's original media endpoint, preserving the source
        # page and license. Avoid the browser's failed FilePath redirect.
        return {
            **photo,
            "url": "https://upload.wikimedia.org/wikipedia/commons/0/00/Centre_Pompidou_%C3%A0_Metz.jpg",
        }
    return photo or online_photo



@lru_cache(maxsize=256)
def display_photo_url(url: str) -> str:
    """Use Wikimedia API imageinfo URLs, never synthesize the Commons CDN hash.

    The original Wikimedia FilePath URL is returned if Commons is unavailable;
    callers render it as a CSS background with a stable no-image fallback.
    """
    from urllib.parse import unquote, urlsplit, urlencode
    from urllib.request import urlopen, Request
    p=urlsplit(url)
    prefix="/wiki/Special:FilePath/"
    if not (p.scheme=="https" and p.netloc=="commons.wikimedia.org"
            and p.path.startswith(prefix)):
        return url
    title=unquote(p.path[len(prefix):]).replace("_"," ")
    if not title or "/" in title or "\\" in title or not title.lower().endswith(
            (".jpg",".jpeg",".png",".webp")):
        return url
    endpoint="https://commons.wikimedia.org/w/api.php?"+urlencode({
        "action":"query","titles":"File:"+title,"prop":"imageinfo",
        "iiprop":"url","iiurlwidth":"800","format":"json"})
    try:
        req=Request(endpoint,headers={"User-Agent":"EuropeTrip-Research/1.0",
                                      "Accept":"application/json"})
        with urlopen(req,timeout=4) as response:
            payload=json.load(response)
        for page in payload.get("query",{}).get("pages",{}).values():
            for info in page.get("imageinfo",[]):
                result=info.get("thumburl") or info.get("url")
                parsed=urlsplit(result or "")
                if parsed.scheme=="https" and parsed.netloc=="upload.wikimedia.org":
                    return result
    except (OSError,ValueError,TypeError,KeyError):
        pass
    return url
