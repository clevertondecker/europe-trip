"""UX124: read-only city dossier assembled from existing evidence contracts."""
from __future__ import annotations
from collections import Counter
from copy import deepcopy
from base_research_expanded_model import load_research,observed_housing
from city_profiles_model import load_profiles,profile_by_id
from city_research_packs_model import load_city_packs,pack_for_city
from city_research_round2 import load_round2
from city_market import load_market
from city_compare import load_cities
from city_research import load_audit
from trip01_supplemental_discovery import build_exploration_discovery
from ux502_destination_interests_model import empty_interests,ordered_interests,PRIORITIES
from base_recommendation_evidence_model import _wishlist_matrix_builder
from routes7_comparison_projection import decorate_comparison
from base_scenario_model import expanded_rail_routes
from rail_evidence_unified_model import canonical_place
from data23_france_candidates_model import base_attractions
from ux105_base_city_context import context_for_base
from attractions_model import load_attractions
from dq30_mobility_evidence_model import load_mobility_pilot
from attraction_last_mile_model import load_access_pilot

TOPICS=("Visão geral","Moradia","Logística","Vida cotidiana","Trabalho remoto","Atrações")

ACTIVE_PRIORITIES=PRIORITIES[:3]
ROUTE_SCOPES=("Minha lista","Todos os destinos","Com tempo pesquisado")
TIMED=("historical","reference_only")

def personalize_routes(routes,priorities):
    """One canonical order for both full and filtered views; no input mutation."""
    rows=[{**r,"priority":priorities.get(r["destination_id"])} for r in routes]
    return sorted(rows,key=lambda r:(PRIORITIES.index(r["priority"])
                    if r["priority"] in PRIORITIES else len(PRIORITIES),r["name"]))

def route_scope(routes,scope):
    if scope not in ROUTE_SCOPES:
        raise ValueError("Escopo ferroviário inválido")
    if scope==ROUTE_SCOPES[0]:
        rows=[r for r in routes if r["priority"] in ACTIVE_PRIORITIES]
    elif scope==ROUTE_SCOPES[2]:
        rows=[r for r in routes if r["cell"]["category"] in TIMED]
    else:
        rows=list(routes)
    counts=Counter(r["cell"]["category"] for r in rows)
    return {"rows":rows,"total":len(rows),"eligible":len(rows)-counts["local"],
            "timed":sum(counts[c] for c in TIMED),"local":counts["local"],
            "historical":counts["historical"],"indicative":counts["reference_only"],
            "missing":counts["no_time"]}

def profile_summary_facts(profile):
    facts=[]
    for category in ("transport","housing","remote_work","daily_costs","climate","quality_of_life"):
        for item in profile["evidence"]:
            summary=item.get("summary","")
            if (item.get("section")!=category or not summary or not item.get("source_url")
                    or any(word in summary.casefold() for word in ("população","densidade","recenseamento"))):
                continue
            facts.append(item)
            break
        if len(facts)==2:
            break
    return facts

def city_profile(base_id,*,research=None,discovery=None,interests=None):
    """The catalog-wide route projection is separate from the user's wishlist.
    
    Uses exactly the same pair evidence and precedence as UX87, with no write,
    no ranking, no assumed return, and no change to either catalog or wishlist.
    """
    research=load_research(include_candidates=True) if research is None else research
    discovery=build_exploration_discovery() if discovery is None else discovery
    city=next((c for c in research["cities"] if c["id"]==base_id),None)
    if city is None:
        raise ValueError("Cidade-base desconhecida")
    profile=profile_by_id(load_profiles(canonical=research),base_id)
    pack=pack_for_city(load_city_packs(),base_id) or {}
    round2=load_round2()
    cost=next((c for c in round2["cities"] if c["id"]==base_id),None)
    market=load_market()
    observed_market=next((c for c in market["cities"] if c["id"]==base_id),None)
    historical=load_cities()
    editorial=next((c for c in historical["cities"] if c["id"]==base_id),None)
    audit=next((c for c in load_audit()["cities"] if c["id"]==base_id),None)
    names={d["id"]:d for d in discovery["destinations"]}
    priorities={i["destination_id"]:i["priority"] for i in ordered_interests(
        empty_interests() if interests is None else interests,discovery)}
    # Private interests are never overwritten. This temporary document is only
    # a request to the existing read-only matrix to enumerate the full catalog.
    basket=empty_interests()
    basket["items"]=[{"destination_id":k,"priority":"interested"} for k in names]
    raw=_wishlist_matrix_builder()(basket,[base_id],discovery=discovery,research=research)
    projected=decorate_comparison(raw)
    routes=[]
    for row in raw["rows"]:
        dest=row["destination_id"]
        cell=projected["cells"][(base_id,dest)]
        fares=[]
        for item in row["observations"]:
            value=item.get("fare_from_eur_person_oneway")
            if value is not None and item.get("source_url"):
                entry={"amount":value,"source_url":item["source_url"],
                       "conditions":item.get("fare_conditions"),
                       "observed_at":item.get("evidence_date")}
                if entry not in fares:
                    fares.append(entry)
        routes.append({"destination_id":dest,"name":names[dest]["name"],
                       "priority":None,"cell":cell,"fares":fares,
                       "observations":deepcopy(row["observations"]),
                       "historical_typical":row["typical_oneway_min"],
                       "source_date":row["source_date"],"source_dataset":row["source_dataset"],
                       "research_gaps":row["research_gaps"]})
    routes=personalize_routes(routes,priorities)
    counts=dict(Counter(r["cell"]["category"] for r in routes))
    extra=[r for r in expanded_rail_routes(base_id)
           if canonical_place(r["destination_id"]) not in names]
    canonical={a["id"]:a for a in load_attractions()["attractions"]}
    candidates=base_attractions(base_id)
    candidate_by_id={a["id"]:a for a in candidates}
    local=[]
    for item in names.get(base_id,{}).get("attractions",[]):
        original=canonical.get(item["id"],{})
        candidate=candidate_by_id.get(item["id"],{})
        local.append({**item,"summary":original.get("summary") or candidate.get("notes"),
                      "photo":original.get("photo") or candidate.get("photo"),
                      "visit_minutes":original.get("visit_minutes"),
                      "visit_minutes_status":original.get("visit_minutes_status"),
                      "ticket":original.get("ticket")})
    context=context_for_base(base_id) or {"mobility":[],"attractions":[],"gaps":[]}
    # DATA23 attraction IDs are authoritative. Local records are not rendered
    # a second time as regional or complementary recommendations.
    local_ids={a["id"] for a in local}
    local_names={a["name"].casefold() for a in local}
    extra_attractions=[a for a in candidates if a["id"] not in local_ids]
    local_names.update(a["name"].casefold() for a in extra_attractions)
    complementary=[a for a in context["attractions"] if a["name"].casefold() not in local_names]
    pilot=load_mobility_pilot()
    access=load_access_pilot(discovery=discovery)
    access_notes=[r for r in pilot.get("access_reference_not_canonical_attraction",[])
                  if r["destination_id"]==base_id]
    access_observations=[r for r in access["observations"] if r["destination_id"]==base_id]
    # Destination suggestions are based on documented one-way minima, not
    # invented proximity, feasibility or a new ranking of the bases.
    excursions=[{"destination_id":r["destination_id"],"name":r["name"],
                 "cell":r["cell"],"attraction_count":names[r["destination_id"]]["attraction_count"],
                 "source_url":names[r["destination_id"]].get("source_url")}
                for r in routes if r["cell"]["category"] in ("historical","reference_only")
                and names[r["destination_id"]]["attraction_count"]>0]
    excursions.sort(key=lambda r:(r["cell"]["display_min"],r["name"]))
    return deepcopy({"city":city,"profile":profile,"pack":pack,"cost":cost,
            "market":observed_market,"market_common":market["common_costs"],
            "round2_sources":round2["common_sources"],"editorial":editorial,
            "editorial_source":historical["source"]["url"],"audit":audit,
            "housing":observed_housing(city),"routes":routes,"counts":counts,
            "extra_routes":extra,"local_attractions":local,"extra_attractions":extra_attractions,
            "excursions":excursions,
            "complementary_attractions":complementary,"mobility":context["mobility"],
            "context_gaps":context["gaps"],"access_notes":access_notes,
            "access_observations":access_observations,
            "catalog_destination_count":len(names),"official_plan_modified":False})
