"""One-time Commons File namespace searches for the remaining photo QA exceptions."""
from pathlib import Path
import requests
from html.parser import HTMLParser

S = requests.Session()
HEADERS={"User-Agent":"NossaEuropa2027/1.0 (https://github.com/clevertondecker/europe-trip; media curation)"}
API="https://commons.wikimedia.org/w/api.php"
QUERIES=[
    "Saint-Louis Haut-Rhin mairie",
    "Saint Louis Haut Rhin centre ville",
    "Amsterdam canals skyline",
    "Amsterdam Prinsengracht panorama",
    "Lyon Fourvière Saone skyline",
    "Offenburg Rathaus Altstadt",
]
for q in QUERIES:
    x=S.get(API,params={"action":"query","format":"json","list":"search",
                        "srsearch":q,"srnamespace":6,"srlimit":12},
            headers=HEADERS,timeout=25).json()
    rows=[r["title"] for r in x.get("query",{}).get("search",[])]
    print("QUERY",q,flush=True)
    for i,t in enumerate(rows):
        print("CANDIDATE",i,t,flush=True)
    if not rows:
        continue
    y=S.get(API,params={"action":"query","format":"json","formatversion":2,
                        "prop":"imageinfo","iiprop":"size|extmetadata|url",
                        "iiurlwidth":960,"titles":"|".join(rows)},
            headers=HEADERS,timeout=25).json()
    for p in y.get("query",{}).get("pages",[]):
        ii=(p.get("imageinfo") or [{}])[0]
        em=ii.get("extmetadata",{})
        license=em.get("LicenseShortName",{}).get("value","")
        author=em.get("Artist",{}).get("value","")
        print("CANDIDATE_META",p["title"],f"{ii.get('width',0)}x{ii.get('height',0)}",
              license[:45],"author",author[:80],flush=True)
