"""Fail-closed Wikimedia Commons photo metadata used only for DATA16 cards."""
import json
import re
from html import unescape
from urllib.parse import urlencode
from urllib.request import Request,urlopen

def _plain(value):
    return unescape(re.sub(r"<[^>]+>","",str(value or ""))).strip()

def parse_metadata(payload,file_title):
    pages=payload.get("query",{}).get("pages",{})
    if isinstance(pages,list):
        pages={str(i):v for i,v in enumerate(pages)}
    for page in pages.values():
        if page.get("title")!="File:"+file_title:
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
        from urllib.parse import urlsplit
        p=urlsplit(license_url)
        name=license_name.casefold().strip()
        free_by=bool(re.fullmatch(r"cc by(?:-sa)? [1-9]\\.\\d",name))
        url_free=(p.scheme=="https" and p.hostname=="creativecommons.org"
                  and p.path.startswith(("/licenses/by/","/licenses/by-sa/")))
        public_domain=(name in ("cc0","cc-zero","public domain","pd-old","pd-us")
                       and (not license_url or (p.scheme=="https"
                           and p.hostname=="creativecommons.org"
                           and p.path.startswith("/publicdomain/"))))
        permitted=(free_by and url_free) or public_domain
        if (not author or not permitted or not image_url
                or not image_url.startswith("https://upload.wikimedia.org/")):
            return None
        return {"url":image_url,"author":author[:200],
                "license":license_name,"license_url":license_url}
    return None

def fetch_photo(file_title,timeout=6):
    q=urlencode({"action":"query","prop":"imageinfo","titles":"File:"+file_title,
                 "iiprop":"url|extmetadata","iiurlwidth":720,"format":"json"})
    req=Request("https://commons.wikimedia.org/w/api.php?"+q,
                headers={"User-Agent":"EuropeTrip-Research/1.0 (source credits)",
                         "Accept":"application/json"})
    try:
        with urlopen(req,timeout=timeout) as response:
            return parse_metadata(json.load(response),file_title)
    except (OSError,ValueError,TypeError,KeyError):
        return None
