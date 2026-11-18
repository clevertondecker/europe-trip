"""Rate-limited research probe. Produces candidates, NEVER accepted evidence.

One record must be manually checked against the cited operator page before
being added to data13_directed_connectivity_2026_11.json. This deliberately
does not infer reverse routes, times, transfers, fares or service in 2027.
"""
from __future__ import annotations
import argparse
import html
from html.parser import HTMLParser
import json
import re
import sys
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from urllib.robotparser import RobotFileParser

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.data13_research_queue import queue_candidates

SLUG = {
    "mulhouse":"mulhouse","strasbourg":"strasbourg","metz":"metz",
    "nancy":"nancy","colmar":"colmar","selestat":"selestat",
    "saint_louis":"saint-louis","belfort":"belfort","besancon":"besancon",
    "thionville":"thionville","haguenau":"haguenau","saverne":"saverne",
    "reims":"reims","lille":"lille","arras":"arras","dijon":"dijon",
    "freiburg":"fribourg-en-brisgau","offenburg":"offenbourg","kehl":"kehl",
    "karlsruhe":"karlsruhe","baden_baden":"baden-baden",
    "saarbrucken":"sarrebruck","trier":"treves","lorrach":"lorrach",
    "aachen":"aachen","arlon":"arlon","liege":"liege","namur":"namur",
    "luxembourg_city":"luxembourg","esch":"esch-sur-alzette",
    "basel":"bale","interlaken":"interlaken",
    "lauterbrunnen":"lauterbrunnen","brussels":"bruxelles",
    "bruges_be":"bruges","rotterdam":"rotterdam","ghent":"gand",
    "amsterdam":"amsterdam","cologne":"cologne","paris":"paris",
    "stuttgart":"stuttgart","beaune":"beaune","lausanne":"lausanne",
    "lyon":"lyon","epernay":"epernay",
}
# Oeschinensee is not a train station and needs separate last-mile research.
EXCLUDE_DEST = {"oeschinen"}
AGENT = "EuropeTripData13Research/1.0 (+https://github.com/clevertondecker/europe-trip)"


class PlainHTML(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
    def handle_data(self, data):
        self.parts.append(data)


def extract_minimum(page: str):
    parsed = PlainHTML()
    parsed.feed(page)
    body = re.sub(r"\s+", " ", html.unescape(" ".join(parsed.parts)))
    match = re.search(
        r"Durée du trajet le plus court\s*(?:\||:)?\s*(\d{1,2})\s*h\s*(\d{1,2})",
        body, flags=re.IGNORECASE)
    if not match:
        return None, None
    value = 60 * int(match.group(1)) + int(match.group(2))
    if not (1 <= value <= 1440):
        return None, None
    return value, body[max(0,match.start()-50):match.end()+50]


def run(limit: int, bases: set[str], delay: float):
    robots = RobotFileParser()
    robots.set_url("https://www.sncf-connect.com/robots.txt")
    try:
        robots.read()
    except (URLError, HTTPError, TimeoutError) as exc:
        print("DATA13_PROBE_SKIP_ROBOTS " + type(exc).__name__,flush=True)
        return
    count=found=0
    for pair in queue_candidates():
        if (pair["destination_id"] in EXCLUDE_DEST or
                pair["base_id"] not in SLUG or
                pair["destination_id"] not in SLUG or
                (bases and pair["base_id"] not in bases)):
            continue
        src, dest = pair["base_id"], pair["destination_id"]
        url = f'https://www.sncf-connect.com/train/trajet/{SLUG[src]}/{SLUG[dest]}'
        if not robots.can_fetch(AGENT,url):
            continue
        if count >= limit:
            break
        count += 1
        try:
            req=Request(url,headers={"User-Agent":AGENT,
                                     "Accept-Language":"fr-FR,fr;q=0.9"})
            with urlopen(req,timeout=8) as response:
                if response.status != 200:
                    continue
                data=response.read(2_000_000).decode("utf-8","replace")
                published=response.geturl()
            minimum, excerpt=extract_minimum(data)
            if minimum is not None and published.startswith("https://www.sncf-connect.com/"):
                found+=1
                print("DATA13_CANDIDATE "+json.dumps({
                    "origin_id":src,"destination_id":dest,
                    "minimum_oneway_min":minimum,"source_url":published,
                    "source_excerpt":excerpt,"research_only":True
                },ensure_ascii=False),flush=True)
        except (HTTPError,URLError,TimeoutError,ValueError) as exc:
            print("DATA13_PROBE_SKIP "+src+" "+dest+" "+type(exc).__name__,flush=True)
            if isinstance(exc,HTTPError) and exc.code==429:
                break
        time.sleep(delay)
    print(f"DATA13_PROBE_SUMMARY checked={count} candidate={found}",flush=True)


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--limit",type=int,default=60)
    p.add_argument("--bases",default="metz,nancy,colmar,dijon,reims")
    p.add_argument("--delay",type=float,default=1.5)
    args=p.parse_args()
    if not 1 <= args.limit <= 200 or args.delay < 1:
        raise SystemExit("Conservative research limits violated")
    run(args.limit,set(filter(None,args.bases.split(","))),args.delay)
