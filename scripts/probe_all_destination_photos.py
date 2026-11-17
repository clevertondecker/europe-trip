"""One-off inventory and Wikimedia API probe for destination photo curation."""
import requests
from ux501_destination_discovery_model import build_destination_discovery
from destination_photo_assets import _manifest

destinations=build_destination_discovery()["destinations"]
covered=set(_manifest())
missing=[x for x in destinations if not x.get("photo") and x["id"] not in covered]
print("PHOTO_AUDIT total",len(destinations),"editorial",
      sum(bool(x.get("photo")) for x in destinations),
      "local",len(covered),"missing",len(missing),flush=True)
for d in missing:
    print("MISSING",d["id"],"|",d["name"],"|",d["country"],flush=True)
urls=[
 "https://en.wikipedia.org/w/api.php?action=query&format=json&titles=Trier&prop=pageimages&piprop=name",
 "https://commons.wikimedia.org/w/api.php?action=query&format=json&titles=File:Cathedral_in_Aachen.jpg&prop=imageinfo&iiprop=extmetadata",
 "https://en.wikipedia.org/api/rest_v1/page/summary/Trier",
 "https://commons.wikimedia.org/wiki/Special:FilePath/Cathedral_in_Aachen.jpg",
]
for url in urls:
    try:
        res=requests.get(url,timeout=15,headers={"User-Agent":"NossaEuropa2027/1.0 (https://github.com/clevertondecker/europe-trip; Wikimedia licensed photo curation)"},stream=True)
        print("PROBE",res.status_code,res.headers.get("content-type"),res.url[:120],flush=True)
    except Exception as e:
        print("PROBE_ERROR",type(e).__name__,str(e)[:180],flush=True)
