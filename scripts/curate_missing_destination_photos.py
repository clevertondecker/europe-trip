#!/usr/bin/env python3
"""Prepare fixed, licensed WebP photos for every as-yet-unillustrated destination.

Curation runs in GitHub Actions, not when a visitor opens Streamlit.
Wikipedia article identity is explicit; only Commons images with verifiable
open licenses and authors are accepted. Failures remain in an auditable report.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date
from html import unescape
from html.parser import HTMLParser
import io
import json
from pathlib import Path
import re
import time

import requests
from PIL import Image, ImageOps, UnidentifiedImageError

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data" / "destination_photo_assets.json"
REPORT = ROOT / "docs" / "UX_ALL_DESTINATION_PHOTOS_AUDIT.json"
WIKIPEDIA = "https://en.wikipedia.org/w/api.php"
COMMONS = "https://commons.wikimedia.org/w/api.php"
HEADERS = {"User-Agent": "NossaEuropa2027/1.0 (https://github.com/clevertondecker/europe-trip; contact: GitHub issues)"}
TITLES = {
    "lorrach": "Lörrach",
    "offenburg": "Offenburg",
    "saarbrucken": "Saarbrücken",
    "stuttgart": "Stuttgart",
    "trier": "Trier",
    "arlon": "Arlon",
    "bruges_be": "Bruges",
    "brussels": "Brussels",
    "ghent": "Ghent",
    "liege": "Liège",
    "namur": "Namur",
    "arras": "Arras",
    "beaune": "Beaune",
    "belfort": "Belfort",
    "besancon": "Besançon",
    "dijon": "Dijon",
    "haguenau": "Haguenau",
    "lille": "Lille",
    "lyon": "Lyon",
    "paris": "Paris",
    "reims": "Reims",
    "saint_louis": "Saint-Louis, Haut-Rhin",
    "saverne": "Saverne",
    "selestat": "Sélestat",
    "thionville": "Thionville",
    "epernay": "Épernay",
    "esch": "Esch-sur-Alzette",
    "amsterdam": "Amsterdam",
    "rotterdam": "Rotterdam",
    "lausanne": "Lausanne",
    "lauterbrunnen": "Lauterbrunnen",
}
COUNTRY = {
    "Alemanha": "Germany", "Bélgica": "Belgium", "França": "France",
    "Luxemburgo": "Luxembourg", "Países Baixos": "Netherlands",
    "Suíça": "Switzerland",
}
MAX_BYTES = 16_000_000


class _Plain(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_data(self, data):
        self.parts.append(data)


def plain(html: str) -> str:
    parser = _Plain()
    parser.feed(html or "")
    return " ".join(unescape("".join(parser.parts)).split())[:180]


def get_json(api: str, params: dict):
    for attempt in range(3):
        try:
            res = requests.get(api, params=params, headers=HEADERS, timeout=35)
            res.raise_for_status()
            return res.json()
        except (requests.RequestException, ValueError):
            if attempt == 2:
                raise
            time.sleep((attempt + 1) * 2)
    raise AssertionError("unreachable")


def key(s):
    return s.replace("_", " ").strip().casefold()


def audit_inventory():
    from ux501_destination_discovery_model import build_destination_discovery
    inventory = build_destination_discovery()["destinations"]
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    already = set(manifest["assets"])
    missing = [d for d in inventory if not d.get("photo") and d["id"] not in already]
    unknown = set(TITLES) - {d["id"] for d in inventory}
    uncovered = {d["id"] for d in missing} - set(TITLES)
    if unknown or uncovered:
        raise RuntimeError(f"Title mapping mismatch: unknown={unknown}; unmapped={uncovered}")
    return inventory, manifest, missing


def get_wikipedia_leads(missing: list[dict]):
    titles = [TITLES[d["id"]] for d in missing]
    data = get_json(WIKIPEDIA, {
        "action": "query", "format": "json", "formatversion": 2,
        "redirects": 1, "prop": "pageimages", "piprop": "name",
        "titles": "|".join(titles),
    })["query"]
    redirects = {key(r["from"]): key(r["to"]) for r in data.get("redirects", [])}
    normalized = {key(r["from"]): key(r["to"]) for r in data.get("normalized", [])}
    pages = {key(p["title"]): p for p in data["pages"] if not p.get("missing")}
    found, failures = {}, {}
    for dest in missing:
        desired = key(TITLES[dest["id"]])
        page = pages.get(redirects.get(normalized.get(desired, desired),
                                       normalized.get(desired, desired)))
        if not page or not page.get("pageimage"):
            failures[dest["id"]] = "Wikipedia article has no identified lead image"
            continue
        filename = page["pageimage"]
        if not filename.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
            failures[dest["id"]] = "Lead image is not a photograph: " + filename
            continue
        found[dest["id"]] = "File:" + filename.removeprefix("File:")
    return found, failures


def licensed_commons_info(files: dict[str, str]):
    if not files:
        return {}, {}
    payload = get_json(COMMONS, {
        "action": "query", "format": "json", "formatversion": 2,
        "prop": "imageinfo", "iiprop": "url|size|extmetadata",
        "iiurlwidth": 960, "titles": "|".join(dict.fromkeys(files.values())),
    })
    pages = {key(p["title"]): p for p in payload["query"]["pages"]}
    chosen, failures = {}, {}
    for destination_id, filename in files.items():
        page = pages.get(key(filename), {})
        info = (page.get("imageinfo") or [{}])[0]
        meta = info.get("extmetadata", {})
        license_name = plain(meta.get("LicenseShortName", {}).get("value", ""))
        author = plain(meta.get("Artist", {}).get("value", ""))
        license_link = meta.get("LicenseUrl", {}).get("value", "")
        is_open = (bool(re.match(r"(?i)^CC BY(?:-SA)? \d", license_name)) or
                   license_name.startswith(("CC0", "Public domain", "PD-")))
        # Skip ambiguous/unattributed/non-commercial media.
        if not (author and license_name and is_open):
            failures[destination_id] = f"Unusable license/artist: {license_name!r}, {author[:45]!r}"
            continue
        if not license_link.startswith("https://"):
            if "CC BY-SA" in license_name:
                license_link = "https://creativecommons.org/licenses/by-sa/" + license_name.split()[-1] + "/"
            elif "CC BY " in license_name:
                license_link = "https://creativecommons.org/licenses/by/" + license_name.split()[-1] + "/"
            elif license_name.startswith("CC0"):
                license_link = "https://creativecommons.org/publicdomain/zero/1.0/"
            elif license_name.startswith(("Public domain", "PD-")):
                license_link = "https://creativecommons.org/publicdomain/mark/1.0/"
            else:
                failures[destination_id] = "Open license lacks verifiable URL"
                continue
        url = info.get("thumburl") or info.get("url")
        if not url or not url.startswith(("https://upload.wikimedia.org/",
                                              "https://thumb.wikimedia.org/")):
            failures[destination_id] = "Commons did not supply a direct photo URL"
            continue
        width, height = info.get("width", 0), info.get("height", 0)
        if width < 600 or height < 350:
            failures[destination_id] = f"Source image too small: {width}x{height}"
            continue
        source = "https://commons.wikimedia.org/wiki/" + filename.replace(" ", "_")
        chosen[destination_id] = {
            "filename": filename.removeprefix("File:"),
            "url": url, "source_page": source, "author": author,
            "license": license_name, "license_url": license_link,
            "source_width": width, "source_height": height,
        }
    return chosen, failures


def create_webp(destination_id, meta):
    path = ROOT / "assets" / "destinations" / f"{destination_id}.webp"
    if path.exists():
        with Image.open(path) as img:
            if img.format == "WEBP" and img.size == (800, 450):
                return path.stat().st_size
    res = requests.get(meta["url"], headers=HEADERS, timeout=45)
    res.raise_for_status()
    if len(res.content) > MAX_BYTES or len(res.content) < 2500:
        raise ValueError("Unexpected Commons response size")
    img = Image.open(io.BytesIO(res.content))
    img.load()
    if img.width < 500 or img.height < 320:
        raise ValueError("Downloaded thumbnail too small")
    photo = ImageOps.fit(ImageOps.exif_transpose(img).convert("RGB"),
                         (800, 450), method=Image.Resampling.LANCZOS)
    path.parent.mkdir(parents=True, exist_ok=True)
    photo.save(path, "WEBP", quality=77, method=6)
    with Image.open(path) as checked:
        checked.verify()
    byte_count = path.stat().st_size
    if not 5000 <= byte_count <= 250000:
        path.unlink(missing_ok=True)
        raise ValueError(f"Invalid WebP output size: {byte_count}")
    return byte_count


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--discover-only", action="store_true")
    args = parser.parse_args()
    inventory, manifest, missing = audit_inventory()
    leads, failures = get_wikipedia_leads(missing)
    verified, license_failures = licensed_commons_info(leads)
    failures.update(license_failures)
    print("INVENTORY",len(inventory),"NEED",len(missing),
          "LEADS",len(leads),"LICENSED",len(verified),flush=True)
    for d in missing:
        pid = d["id"]
        print("PHOTO_CANDIDATE",pid,
              verified.get(pid, {}).get("filename", "MISSING"),
              verified.get(pid, {}).get("license", ""),flush=True)
    if args.discover_only:
        return
    results = {}
    with ThreadPoolExecutor(max_workers=4) as pool:
        tasks = {pool.submit(create_webp, city_id, info): city_id
                 for city_id, info in verified.items()}
        for future in as_completed(tasks):
            city_id = tasks[future]
            try:
                size = future.result()
                results[city_id] = size
                print("PHOTO_SAVED",city_id,size,flush=True)
            except (requests.RequestException, OSError,
                    ValueError, UnidentifiedImageError) as exc:
                failures[city_id] = "Download/optimization failed: " + str(exc)[:150]
    names = {d["id"]: d for d in missing}
    for city_id in sorted(results):
        info = verified[city_id]
        d = names[city_id]
        manifest["assets"][city_id] = {
            "filename": info["filename"],
            "file": f"assets/destinations/{city_id}.webp",
            "author": info["author"],
            "license": info["license"],
            "license_url": info["license_url"],
            "source_page": info["source_page"],
            "alt": f"Fotografia ilustrativa de {d['name']}, {d['country']}",
        }
    manifest["assets"] = dict(sorted(manifest["assets"].items()))
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+"\n",
                        encoding="utf-8")
    report = {
        "checked_at": str(date.today()),
        "total_destinations": len(inventory),
        "editorial_photo_count": sum(bool(d.get("photo")) for d in inventory),
        "previously_local_count": len(inventory) - len(missing) -
                                  sum(bool(d.get("photo")) for d in inventory),
        "initial_missing": len(missing),
        "newly_bundled": len(results),
        "remaining_missing": len(missing) - len(results),
        "new_assets": [
            {"destination_id": k, "name": names[k]["name"],
             "filename": verified[k]["filename"],
             "license": verified[k]["license"],
             "source": verified[k]["source_page"],
             "bytes": results[k]}
            for k in sorted(results)
        ],
        "unresolved": [{"destination_id": k, "name": names[k]["name"],
                        "reason": failures.get(k, "No verified photo")}
                       for k in sorted(names) if k not in results],
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2)+"\n",
                      encoding="utf-8")
    print("PHOTO_REPORT",json.dumps({
        k: report[k] for k in (
            "total_destinations", "initial_missing", "newly_bundled",
            "remaining_missing", "unresolved")},ensure_ascii=False),flush=True)


if __name__ == "__main__":
    main()
