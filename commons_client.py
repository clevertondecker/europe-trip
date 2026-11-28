"""Shared fail-closed Wikimedia Commons imageinfo client."""
import json
import re
from html import unescape
from urllib.parse import urlencode, unquote, urlsplit
from urllib.request import Request
import urllib.request

def urlopen(*args, **kwargs):
    return urllib.request.urlopen(*args, **kwargs)

IMAGE_HOSTS = frozenset({"upload.wikimedia.org", "thumb.wikimedia.org"})
NEGATIVE_TTL = 300


def is_image_url(value):
    try:
        p = urlsplit(value or "")
        return (p.scheme == "https" and p.hostname in IMAGE_HOSTS and
                p.username is None and p.password is None and p.port in (None, 443))
    except (ValueError, TypeError):
        return False


def _plain(value):
    return " ".join(unescape(re.sub(r"<[^>]+>","",str(value or ""))).split())

def parse_metadata(payload,file_title):
    pages=payload.get("query",{}).get("pages",{})
    if isinstance(pages,list):
        pages={str(i):v for i,v in enumerate(pages)}
    for page in pages.values():
        if page.get("title")!="File:"+file_title or "missing" in page:
            continue
        infos=page.get("imageinfo") or []
        if not infos:
            return None
        info=infos[0]
        meta=info.get("extmetadata",{})
        author=_plain(meta.get("Artist",{}).get("value"))
        license_name=_plain(meta.get("LicenseShortName",{}).get("value"))
        license_url=meta.get("LicenseUrl",{}).get("value","")
        image_url=info.get("thumburl") or info.get("url")
        p=urlsplit(license_url)
        name=license_name.casefold().strip()
        free_by=bool(re.fullmatch(r"cc by(?:-sa)? [1-9]\.\d",name))
        url_free=(p.scheme=="https" and p.hostname=="creativecommons.org"
                  and p.path.startswith(("/licenses/by/","/licenses/by-sa/")))
        public_domain=(name in ("cc0","cc-zero","public domain","pd-old","pd-us")
                       and (not license_url or (p.scheme=="https"
                           and p.hostname=="creativecommons.org"
                           and p.path.startswith("/publicdomain/"))))
        permitted=(free_by and url_free) or public_domain
        if (not author or not permitted or not image_url
                or not is_image_url(image_url)):
            return None
        return {"url":image_url,"author":author[:140],
                "license":license_name,"license_url":license_url}
    return None

WIDTH = 720
TIMEOUT = 6
USER_AGENT = "NossaEuropa2027/1.0 (https://github.com/clevertondecker/europe-trip; contact via GitHub issues)"

COMMONS_API = "https://commons.wikimedia.org/w/api.php"

def file_path_title(url):
    p = urlsplit(url)
    prefix = "/wiki/Special:FilePath/"
    if p.scheme == "https" and p.netloc == "commons.wikimedia.org" and p.path.startswith(prefix):
        title = unquote(p.path[len(prefix):]).replace("_", " ")
        if title and "/" not in title and chr(92) not in title and title.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
            return title
    return None

def request_json(url, params, timeout=TIMEOUT):
    req = Request(url + "?" + urlencode(params), headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    with urlopen(req, timeout=timeout) as response:
        return json.load(response)

def query_imageinfo(titles, fetch_json=None, timeout=TIMEOUT):
    params = {"action":"query", "prop":"imageinfo", "titles":"|".join(titles),
              "iiprop":"url|extmetadata", "iiurlwidth":WIDTH, "format":"json", "formatversion":2}
    return fetch_json(COMMONS_API, params) if fetch_json else request_json(COMMONS_API, params, timeout)

def fetch_photo(file_title,timeout=TIMEOUT):
    try:
        return parse_metadata(query_imageinfo(["File:"+file_title], timeout=timeout),file_title)
    except (OSError,ValueError,TypeError,KeyError):
        return None
