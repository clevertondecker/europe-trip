"""DATA23: additive, source-verified candidates, attraction photos and rail references.

Never alter the frozen November 2026 thirty-city source snapshot. A new
candidate is an opt-in research item; it is NOT a saved official TripPlan base.
"""
from __future__ import annotations
from copy import deepcopy
from functools import lru_cache
from pathlib import Path
from urllib.parse import urlsplit,unquote
import json

DATA=Path(__file__).resolve().parent/"data"/"data23_france_base_candidates_2026_11.json"
REQUIRED_IDS=frozenset({"angers","le_mans","annecy","rennes"})
WIKIMEDIA_HOSTS=frozenset({"commons.wikimedia.org"})
SOURCE_HOSTS=frozenset({"www.sncf-connect.com"})
SLUGS={"angers":"angers","saumur":"saumur","nantes":"nantes",
       "tours":"tours","le_mans":"le-mans","chartres":"chartres",
       "paris":"paris","annecy":"annecy","aix_les_bains":"aix-les-bains",
       "geneva":"geneve","chamonix":"chamonix",
       "rennes":"rennes","saint_malo":"saint-malo","dinan":"dinan"}

def _safe_url(value, hosts):
    if not isinstance(value,str):return False
    try:
        url=urlsplit(value)
        return (url.scheme=="https" and url.hostname in hosts
                and not url.username and not url.password and url.port in (None,443)
                and not url.fragment)
    except ValueError:
        return False

def validate_data23(data:dict)->dict:
    if (not isinstance(data,dict) or data.get("schema_version")!=1
            or data.get("checked_at")!="2026-11-21"):
        raise ValueError("Contrato DATA23 inválido")
    bases=data.get("cities",[])
    attractions=data.get("attractions",[])
    routes=data.get("routes",[])
    if (not isinstance(bases,list) or
            {r.get("id") for r in bases if isinstance(r,dict)}!=REQUIRED_IDS or
            len(bases)!=len(REQUIRED_IDS)):
        raise ValueError("Conjunto de candidatas inesperado")
    for b in bases:
        if (b.get("country")!="França" or b.get("shortlist") is not False
                or b.get("original_base") is not False
                or b.get("ranking_status")!="not_decision_ready"
                or b.get("eligible_2027_quotes")!=0
                or b.get("housing_offers")!=[]
                or not _safe_url(b.get("source_url"),{"www.destination-angers.com",
                      "www.lemans-tourisme.com","www.ville-annecy.fr","www.tourisme-rennes.com"})
                or not isinstance(b.get("summary"),str) or not b["summary"]
                or not -90<=b.get("lat",1000)<=90
                or not -180<=b.get("lon",1000)<=180):
            raise ValueError("Dados de base não verificáveis")
    if not isinstance(attractions,list) or len(attractions)<2*len(bases):
        raise ValueError("Atrações com fotos insuficientes")
    seen=set()
    for a in attractions:
        photo=a.get("photo",{})
        if (not isinstance(a,dict) or not a.get("id") or a["id"] in seen
                or a.get("base_id") not in REQUIRED_IDS
                or a.get("proximity") not in ("local","regional")
                or not a.get("name") or not a.get("place")
                or not _safe_url(a.get("source_url"),{
                    "www.destination-angers.com","www.anjou-tourisme.com",
                    "www.lemans-tourisme.com","www.ville-annecy.fr",
                    "www.tourisme-rennes.com","www.saint-malo-tourisme.com"})
                or not isinstance(photo,dict)
                or not _safe_url(photo.get("url"),WIKIMEDIA_HOSTS)
                or not _safe_url(photo.get("source_page"),WIKIMEDIA_HOSTS)
                or "/wiki/Special:FilePath/" not in photo["url"]
                or "/wiki/File:" not in photo["source_page"]
                or unquote(photo["url"].split("/wiki/Special:FilePath/",1)[1])!=
                   unquote(photo["source_page"].split("/wiki/File:",1)[1])
                or not photo.get("author")
                or photo.get("license") not in ("CC BY-SA 3.0","CC BY-SA 4.0")
                or photo.get("license_url")!=("https://creativecommons.org/licenses/by-sa/"+
                    photo.get("license","").rsplit(" ",1)[-1]+"/")
                or photo.get("verified_2026_11_21") is not True
                or a.get("price_eur") is not None
                or a.get("editorial_duration_min") is not None
                or a.get("last_mile_min") is not None
                or a.get("availability_autumn_2027_verified") is not False
                or a.get("seasonality_2027_verified") is not False):
            raise ValueError("Atração sem fonte/foto válida ou com dados inventados")
        seen.add(a["id"])
    pairs=set()
    for r in routes:
        key=r.get("base_id"),r.get("destination_id")
        url=r.get("source_url")
        if (key in pairs or key[0] not in REQUIRED_IDS or key[1] not in SLUGS
                or not _safe_url(url,SOURCE_HOSTS)
                or not urlsplit(url).path.endswith("/"+SLUGS[key[0]]+"/"+SLUGS[key[1]])
                or type(r.get("minimum_oneway_min")) is not int
                or not 1<=r["minimum_oneway_min"]<=720
                or r.get("reference_kind")!="official_operator_minimum"
                or r.get("checked_at")!="2026-11-21"
                or r.get("confidence")!="medium"
                or r.get("fare_eur") is not None
                or r.get("valid_for_2027") is not False
                or r.get("return_2027_verified") is not False
                or r.get("door_to_door_verified") is not False):
            raise ValueError("Rota DATA23 sem evidência direcional admissível")
        pairs.add(key)
    return deepcopy(data)

@lru_cache(maxsize=1)
def load_data23()->dict:
    return validate_data23(json.loads(DATA.read_text(encoding="utf-8")))

def candidate_bases():
    return deepcopy(load_data23()["cities"])

def base_attractions(city_id):
    return deepcopy([x for x in load_data23()["attractions"] if x["base_id"]==city_id])

def base_routes(city_id):
    return deepcopy([x for x in load_data23()["routes"] if x["base_id"]==city_id])

def base_profiles():
    """Minimal honest profiles to preserve the existing strict card contract."""
    output=[]
    for b in candidate_bases():
        output.append({
            "city_id":b["id"],"name":b["name"],"country":b["country"],
            "shortlist":False,"corridor":b["corridor"],"summary":b["summary"],
            "urban_profile":[b["summary"]],
            "housing":{"historical_offer_count":0,
                       "historical_observed_min_eur_month":None,
                       "historical_observed_max_eur_month":None,
                       "period":"Não pesquisado",
                       "availability_2027_verified":False},
            "remote_work":{"internet_in_property_verified":False,
                           "coworking_verified":False},
            "daily_costs":{"comparable_basket_eur":None},
            "climate":{"sep_oct_nov_normals":None,"period":None},
            "quality_of_life":{"numeric_score":None},
            "official_statistics_source":{"name":"INSEE comparateur",
                 "url":"https://www.insee.fr/fr/statistiques/2521169"},
            "evidence":[{"id":b["id"]+"-tourism-20261121","section":"quality_of_life",
                "summary":b["summary"],"source_url":b["source_url"],
                "observed_at":"2026-11-21",
                "reference_period":"fontes institucionais de turismo em 2026",
                "scope":"cidade candidata","kind":"primary_public_context",
                "limitations":"Fonte turística não é ranking validado, preço ou disponibilidade para 2027"}],
            "advantages":[b["summary"]],
            "limitations":["Moradia, internet e custos para 60 noites não pesquisados"],
            "research_gaps":["Confirmar moradia, última milha, logística de volta e sazonalidade"],
            "last_reviewed_at":"2026-11-21","demographics":None,
        })
    return output
