"""DATA13 offline source identity, static-HTML minimum extraction and review gate.

A syntactically valid URL cannot substantiate a published journey duration.
No external network calls or inference of reverse/2027 journeys occur here.
"""
from __future__ import annotations

import csv
from datetime import date
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
import re
from urllib.parse import urlparse

SNCF = {
    "aachen":"aix-la-chapelle", "amsterdam":"amsterdam",
    "arras":"arras", "baden_baden":"baden-baden", "basel":"bale",
    "beaune":"beaune", "belfort":"belfort", "besancon":"besancon",
    "brussels":"bruxelles", "colmar":"colmar", "cologne":"cologne",
    "dijon":"dijon", "epernay":"epernay", "freiburg":"fribourg-en-brisgau",
    "haguenau":"haguenau", "karlsruhe":"karlsruhe", "kehl":"kehl",
    "liege":"liege", "lille":"lille", "luxembourg_city":"luxembourg",
    "lausanne":"lausanne", "lyon":"lyon", "metz":"metz", "mulhouse":"mulhouse", "nancy":"nancy",
    "offenburg":"offenbourg", "paris":"paris", "reims":"reims",
    "rotterdam":"rotterdam", "saarbrucken":"sarrebruck",
    "saint_louis":"saint-louis", "saverne":"saverne",
    "selestat":"selestat", "strasbourg":"strasbourg",
    "thionville":"thionville",
}
TRAINLINE = {
    "aachen":"aachen", "amsterdam":"amsterdam", "arlon":"arlon",
    "besancon":"besancon",
    "brussels":"brussels",
    "basel":"basel-sbb", "bruges_be":"bruges-brugge",
    "colmar":"colmar", "cologne":"cologne-germany", "dijon":"dijon",
    "esch":"esch-sur-alzette", "freiburg":"freiburg-breisgau-hbf",
    "ghent":"ghent", "interlaken":"interlaken-ost", "kehl":"kehl", "lausanne":"lausanne",
    "liege":"liege", "lille":"lille",
    "lorrach":"lorrach", "luxembourg_city":"luxembourg", "mulhouse":"mulhouse", "offenburg":"offenburg",
    "lyon":"lyon", "metz":"metz", "namur":"namur",
    "nancy":"nancy", "paris":"paris", "reims":"reims",
    "rotterdam":"rotterdam", "saint_louis":"st-louis", "saverne":"saverne", "strasbourg":"strasbourg",
    "stuttgart":"stuttgart", "thionville":"thionville",
    "trier":"trier-hbf",
}
class EvidenceError(ValueError):
    """Fail closed for invalid/ambiguous source evidence."""


def validate_record_url(row):
    kind = row.get("reference_kind")
    if kind == "official_operator_minimum":
        host, names = "www.sncf-connect.com", SNCF
    elif kind == "secondary_route_minimum":
        host, names = "www.thetrainline.com", TRAINLINE
    else:
        raise EvidenceError("Unsupported DATA13 source class")
    try:
        u = urlparse(row["source_url"])
        if (u.scheme != "https" or u.hostname != host or u.port is not None
                or u.username or u.password or u.query or u.fragment or u.params):
            raise EvidenceError("Unapproved source URL")
    except (TypeError, KeyError, ValueError) as exc:
        raise EvidenceError("Invalid source URL") from exc
    if kind == "official_operator_minimum":
        match = re.fullmatch(r"/train/(?:trajet|horaires)/([a-z0-9-]+)/([a-z0-9-]+)",u.path)
    else:
        match = re.fullmatch(r"/en/train-times/([a-z0-9-]+)-to-([a-z0-9-]+)",u.path)
    if not match:
        raise EvidenceError("Not a directional rail page")
    origin, destination = match.groups()
    if (origin != names.get(row.get("origin_id")) or
            destination != names.get(row.get("destination_id"))):
        raise EvidenceError("URL refers to another route or opposite direction")


class _Text(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tokens, self.ignored = [], 0
    def handle_starttag(self, tag, attrs):
        if tag in ("script","style","noscript"):
            self.ignored += 1
    def handle_endtag(self, tag):
        if tag in ("script","style","noscript") and self.ignored:
            self.ignored -= 1
        elif tag in ("p","div","tr","td","h1","h2","h3","li"):
            self.tokens.append(" ")
    def handle_data(self, value):
        if not self.ignored:
            self.tokens.append(value)


def _minutes(raw):
    value = unescape(raw).replace("\xa0"," ").lower()
    h = re.fullmatch(r"\s*(\d{1,2})\s*h\s*(\d{1,2})\s*m?\s*",value)
    m = re.fullmatch(r"\s*(\d{1,4})\s*m(?:in(?:utes?)?)?\s*",value)
    if h:
        hours, minutes = map(int,h.groups())
        result=60*hours+minutes if minutes<60 else None
    elif m:
        result=int(m.group(1))
    else:
        return None
    return result if result is not None and 1<=result<=1440 else None


def extract_minimum(html, *, provider):
    """Return only explicit shortest journey time, not an average or a fare."""
    if not isinstance(html,str):
        raise TypeError("html must be text")
    collector=_Text()
    collector.feed(html)
    text=re.sub(r"\s+"," "," ".join(collector.tokens))
    if provider=="sncf":
        pattern=r"Dur[eé]e du trajet le plus court\s*:?\s*(\d{1,2}\s*h\s*\d{1,2})"
    elif provider=="trainline":
        pattern=r"Journey time\s*:?\s*From\s*(\d{1,2}\s*h\s*\d{1,2}\s*m|\d{1,4}\s*m)"
    else:
        raise EvidenceError("Unsupported provider")
    values={_minutes(v) for v in re.findall(pattern,text,flags=re.I)}
    values.discard(None)
    return next(iter(values)) if len(values)==1 else None


def verify_observation(row, html):
    validate_record_url(row)
    kind="sncf" if row["reference_kind"]=="official_operator_minimum" else "trainline"
    observed=extract_minimum(html,provider=kind)
    if observed is None:
        return {"status":"insufficient_evidence","published_min":None}
    return {"status":"verified" if observed==row["minimum_oneway_min"] else "duration_mismatch",
            "published_min":observed}


def vetted_overlay_by_pair(records, manifest_file):
    """Return only independently reviewed DATA13 pairs for public comparisons.

    This is an offline human-review assertion, not proof of live 2027 service.
    Unreviewed JSON research is retained but cannot enter the display overlay.
    """
    with Path(manifest_file).open(newline="",encoding="utf-8") as source:
        manifest=list(csv.DictReader(source))
    if len(manifest)!=len(records):
        raise EvidenceError("DATA13 manifest must include all research rows")
    index={}
    for m in manifest:
        key=(m.get("origin_id"),m.get("destination_id"))
        if key in index:
            raise EvidenceError("Duplicate pair in evidence manifest")
        index[key]=m
    result={}
    pending=0
    for record in records:
        validate_record_url(record)
        key=(record["origin_id"],record["destination_id"])
        m=index.pop(key,None)
        if m is None:
            raise EvidenceError("Missing manifest pair: "+repr(key))
        for field,manifest_field in (("source_url","source_url"),
                                     ("reference_kind","source_kind"),
                                     ("confidence","confidence"),
                                     ("direction","direction")):
            if str(record[field])!=m.get(manifest_field):
                raise EvidenceError("Manifest provenance mismatch: "+repr(key))
        if m.get("url_direction_check")!="match" or int(m.get("minimum_dataset_min") or -1)!=record["minimum_oneway_min"]:
            raise EvidenceError("Manifest route/minimum mismatch: "+repr(key))
        if m.get("verification_status")=="verified_minimum":
            try:
                published=int(m.get("published_min_rechecked") or -1)
                checked=date.fromisoformat(m["verification_checked_at"])
            except (ValueError,TypeError) as exc:
                raise EvidenceError("Missing review date or duration: "+repr(key)) from exc
            if (published!=record["minimum_oneway_min"] or checked.year!=2026
                    or not m.get("brief_evidence","").strip()
                    or record.get("valid_for_2027") is not False):
                raise EvidenceError("Invalid reviewed evidence: "+repr(key))
            result[key]=record
        elif m.get("verification_status")=="not_independently_checked":
            if m.get("published_min_rechecked","").strip():
                raise EvidenceError("Unreviewed row claims a checked minimum")
            pending+=1
        else:
            raise EvidenceError("Unresolved provenance status: "+repr(key))
    if index:
        raise EvidenceError("Manifest has unknown pairs")
    return result,{"research_rows":len(records),"verified_displayable":len(result),
                   "pending_source_review":pending}
