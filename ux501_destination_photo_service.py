"""Wikimedia Commons photo lookup for destination discovery.

The canonical catalog remains read-only. No geolocation or city matching by
distance. Only use the lead image of an explicitly selected Wikipedia city page
when Commons exposes reusable license and author metadata.
"""
from __future__ import annotations

from html import unescape
from html.parser import HTMLParser
import re
import json
from urllib.parse import urlencode, quote
from urllib.request import Request, urlopen

WIKIPEDIA_API = "https://en.wikipedia.org/w/api.php"
COMMONS_API = "https://commons.wikimedia.org/w/api.php"
USER_AGENT = ("NossaEuropa2027/1.0 "
              "(https://github.com/clevertondecker/europe-trip; contact via GitHub issues)")

# Article titles are identifiers, not an image search query: this prevents
# displaying pictures of unrelated places with similar names.
ARTICLE_TITLES = {
    "brussels": "Brussels",
    "bruxelles": "Brussels",
    "cologne": "Cologne",
    "koln": "Cologne",
    "koeln": "Cologne",
    "baden_baden": "Baden-Baden",
    "saint_louis": "Saint-Louis, Haut-Rhin",
    "luxembourg": "Luxembourg City",
    "luxembourg_city": "Luxembourg City",
    "oeschinen": "Oeschinen Lake",
    "freiburg": "Freiburg im Breisgau",
    "bruges_be": "Bruges",
    "basel": "Basel",
    "esch": "Esch-sur-Alzette",
    "liege": "Liège",
    "saarbrucken": "Saarbrücken",
    "lorrach": "Lörrach",
    "selestat": "Sélestat",
}
# Human-reviewed city-specific photos. Entries are verified against their
# Wikimedia Commons file pages (artist/license), and never depend on a
# live Wikipedia/Commons Action API call at render time. FilePath performs
# the redirect to the actual hosted image; no local redistribution.
CURATED_COMMONS_FILES = {
    "aachen": ("Cathedral in Aachen.jpg", "Vitold Muratov", "CC BY-SA 4.0"),
    "baden_baden": ("Baden Baden - Lichtentaler Allee - View SE.jpg",
                   "Txllxt TxllxT", "CC BY-SA 4.0"),
    "cologne": ("Köln Cathedral, Germany.jpg", "AtmikaPaul", "CC BY-SA 4.0"),
    "karlsruhe": ("MKa 0553 Schloss Karlsruhe.jpg", "Martin Kraft",
                  "CC BY-SA 3.0"),
    "kehl": ("Passerelle des Deux Rives Kehl.jpg", "H.Helmlechner",
             "CC BY-SA 4.0"),
}


def curated_destination_photo(destination_id: str) -> dict | None:
    """Reviewed file/author/license triple, no speculative image mapping."""
    spec = CURATED_COMMONS_FILES.get(destination_id)
    if not spec:
        return None
    filename, author, license_name = spec
    safe_filename = quote(filename.replace(" ", "_"), safe="()_-")
    return {
        "url":"https://commons.wikimedia.org/wiki/Special:FilePath/" + safe_filename,
        "source_page":"https://commons.wikimedia.org/wiki/File:" + safe_filename,
        "author":author,
        "license":license_name,
        "license_url":("https://creativecommons.org/licenses/by-sa/" +
                       license_name.rsplit(" ",1)[-1] + "/"),
        "origin":"reviewed_commons_file",
    }


TRANSLATED_TITLES = {
    "Bruxelas": "Brussels",
    "Colônia": "Cologne",
    "Luxemburgo": "Luxembourg City",
    "Basileia": "Basel",
}


class _PlainText(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_data(self, data):
        self.parts.append(data)


def _plain(value: str) -> str:
    parser = _PlainText()
    parser.feed(value or "")
    return " ".join(unescape("".join(parser.parts)).split())[:140]


def _request_json(url: str, params: dict) -> dict:
    """Bounded Wikimedia Action API request; never download original images."""
    request = Request(url + "?" + urlencode(params),
                      headers={"User-Agent": USER_AGENT,
                               "Accept": "application/json"})
    with urlopen(request, timeout=6) as response:
        return json.load(response)


def _key(title: str) -> str:
    return title.replace("_", " ").strip().casefold()


def _license_allowed(name: str) -> bool:
    value = name.strip().casefold().replace("-", " ")
    return bool(re.match(r"^cc by(?: sa)? \d", value) or
                value.startswith(("cc0", "public domain", "pd ")))


def _image_metadata(page: dict) -> dict | None:
    info = (page.get("imageinfo") or [None])[0]
    if not info:
        return None
    meta = info.get("extmetadata") or {}
    license_name = _plain(meta.get("LicenseShortName", {}).get("value", ""))
    author = _plain(meta.get("Artist", {}).get("value", ""))
    license_url = meta.get("LicenseUrl", {}).get("value", "")
    url = info.get("thumburl") or info.get("url", "")
    title = page.get("title", "")
    if (not _license_allowed(license_name) or not author or
            not title.startswith("File:") or
            not url.startswith("https://upload.wikimedia.org/")):
        return None
    return {
        "url": url,
        "author": author,
        "license": license_name,
        "license_url": license_url if license_url.startswith("https://") else None,
        "source_page": "https://commons.wikimedia.org/wiki/" +
                       quote(title.replace(" ", "_"), safe=":()_-"),
        "origin": "wikimedia_commons",
    }


def lookup_destination_photos(destinations: list[dict], fetch_json=None) -> dict[str, dict]:
    """Find licensed photos for visible destinations, with exact article identity.

    Network errors return an empty mapping; no false substitutions or writes.
    The caller caches this result with Streamlit to avoid repeated requests.
    """
    fetch = fetch_json or _request_json
    requested = {}
    known = {}
    for destination in destinations:
        if destination.get("photo"):
            continue
        reviewed = curated_destination_photo(destination["id"])
        if reviewed:
            known[destination["id"]] = reviewed
            continue
        article = (ARTICLE_TITLES.get(destination["id"]) or
                   TRANSLATED_TITLES.get(destination["name"]) or destination["name"])
        if article:
            requested[destination["id"]] = article
    if not requested:
        return known
    try:
        response = fetch(WIKIPEDIA_API, {
            "action": "query", "format": "json", "formatversion": 2,
            "redirects": 1, "prop": "pageimages",
            "piprop": "thumbnail|name", "pithumbsize": 720,
            "titles": "|".join(dict.fromkeys(requested.values())),
        })
        query = response.get("query", {})
        redirects = {_key(r["from"]):_key(r["to"])
                     for r in query.get("redirects", [])}
        pages = {_key(p["title"]):p for p in query.get("pages", [])
                 if not p.get("missing")}
        chosen = {}
        filenames = {}
        for destination_id, article in requested.items():
            page = pages.get(redirects.get(_key(article),_key(article)))
            if not page or not page.get("pageimage"):
                continue
            filename = "File:" + page["pageimage"].removeprefix("File:")
            chosen[destination_id] = filename
            filenames[filename] = True
        if not filenames:
            return known
        metadata = fetch(COMMONS_API, {
            "action":"query","format":"json","formatversion":2,
            "prop":"imageinfo","iiprop":"url|extmetadata",
            "iiurlwidth":720,"titles":"|".join(filenames),
        })
        licensed = {_key(p["title"]):_image_metadata(p) for p in
                    metadata.get("query", {}).get("pages", [])}
        found = {key: licensed[_key(title)] for key,title in chosen.items()
                 if licensed.get(_key(title)) is not None}
        return {**known, **found}
    except (OSError, ValueError, KeyError, TypeError):
        # Network failure must not hide verified editorial photos.
        return known
