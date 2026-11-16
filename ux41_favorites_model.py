"""UX 4.1 — reusable, strictly exploratory comparisons for up to three cities.

The same fifteen destinations and the same city identifiers are used throughout.
An unresearched route is UNKNOWN, never unreachable, zero, or a city penalty.
"""
from __future__ import annotations
from copy import deepcopy
import json

from base_research_expanded_model import observed_housing
from base_coverage_model import coverage_matrix
from five_base_comparison_model import BASE_IDS,route_observation

MAX_FAVORITES=3
FAVORITES_KIND="nossa-europa-exploratory-city-favorites"
FAVORITES_SCHEMA=1
MAX_FAVORITES_BYTES=16_384


def validate_favorites(ids:list[str],study:dict)->list[str]:
    valid={r["id"] for r in study["cities"]}
    if (not isinstance(ids,list) or len(ids)>MAX_FAVORITES or
        any(not isinstance(x,str) or x not in valid for x in ids) or
        len(set(ids))!=len(ids)):
        raise ValueError("Escolha até três cidades cadastradas, sem repetição")
    return list(ids)


def set_favorites(previous:list[str],chosen:list[str],study:dict)->list[str]:
    validate_favorites(previous,study)
    return validate_favorites(chosen,study)


def export_favorites(ids:list[str],study:dict)->bytes:
    content={"kind":FAVORITES_KIND,"schema_version":FAVORITES_SCHEMA,
             "city_ids":validate_favorites(ids,study),"status":"exploratory_only"}
    return (json.dumps(content,ensure_ascii=False,sort_keys=True)+"\n").encode("utf-8")


def import_favorites(raw:bytes,study:dict)->list[str]:
    if not isinstance(raw,bytes) or not 0<len(raw)<=MAX_FAVORITES_BYTES:
        raise ValueError("Arquivo de favoritas inválido ou grande demais")
    try: document=json.loads(raw.decode("utf-8"))
    except (ValueError,UnicodeError) as e:
        raise ValueError("Favoritas: JSON inválido") from e
    if (not isinstance(document,dict) or
        set(document)!={"kind","schema_version","city_ids","status"} or
        document["kind"]!=FAVORITES_KIND or
        document["schema_version"]!=FAVORITES_SCHEMA or
        document["status"]!="exploratory_only"):
        raise ValueError("Arquivo de favoritas de outra versão")
    return validate_favorites(document["city_ids"],study)


def comparative_matrix(study:dict, five:dict,profiles:dict,packs:dict,
                       ids:list[str],dest_ids:list[str])->dict:
    """Only use equivalent definitions; no winner, fabricated price or trip change."""
    ids=validate_favorites(ids,study)
    candidates={c["id"]:c for c in study["cities"]}
    profile_map={c["city_id"]:c for c in profiles["cities"]}
    pack_map={c["city_id"]:c for c in packs["cities"]}
    destinations={d["id"]:d for d in five["common_destinations"]}
    if (not isinstance(dest_ids,list) or len(set(dest_ids))!=len(dest_ids) or
        any(not isinstance(i,str) or i not in destinations for i in dest_ids)):
        raise ValueError("Cesta de passeios inválida")
    known=coverage_matrix("general",study=study)
    coverage={row["id"]:row for row in known}
    views=[]
    for key in ids:
        c=candidates[key]
        h=observed_housing(c)
        p=profile_map.get(key,{})
        pack=pack_map.get(key,{})
        offer_sizes=[x["size_m2"] for x in c["housing_offers"]]
        sizes_comparable=sum(30<=x<=60 for x in offer_sizes)
        two_adults=sum(x.get("two_adults_confirmed") is True for x in c["housing_offers"])
        routes=[]
        for dest in dest_ids:
            if key in BASE_IDS:
                route=route_observation(five,key,dest)
                duration=route["train_min"]
                regional=route["regional_min"]
                note=route["notes"]
                source=route["source_url"]
                if route["status"]=="local_no_intercity_train":
                    status="local"
                elif duration is not None:
                    status="documented_oneway"
                else:status="not_researched"
            else:
                # The other 25 cities have scattered legacy rail observations;
                # none is a same-basket verified route in this exact five-base matrix.
                duration=regional=source=None
                status="not_compared_on_shared_basket"
                note="A rota não foi validada na mesma matriz de 15 destinos"
            routes.append({"destination_id":dest,"destination_name":destinations[dest]["name"],
                           "duration_min_oneway":duration,"regional_min_oneway":regional,
                           "source_url":source,"status":status,"note":note,
                           "return_2027_verified":False,"last_mile_verified":False})
        documented=sum(x["status"]=="documented_oneway" for x in routes)
        daily=pack.get("daily_life") or {}
        remote=pack.get("remote_work") or {}
        climates=pack.get("climate") or {}
        lodging=pack.get("housing") or {}
        views.append({
            "id":key,"name":c["name"],"country":c["country"],
            "shortlist":c["shortlist"],"corridor":c["corridor"],
            "housing":{"observations_2026":h["count"],"min_eur_month":h["minimum_eur_month"],
                       "max_eur_month":h["maximum_eur_month"],
                       "size_30_to_60":sizes_comparable,"two_adults_documented":two_adults,
                       "available_2027_count":0,
                       "source_type":"small_heterogeneous_historical_sample"},
            "routes":routes,"documented_shared_basket":documented,
            "selected_destinations_count":len(dest_ids),
            "other_rail_evidence_count":coverage[key]["route_basket_with_time"],
            "daily":{"restaurant_two_eur_2026":daily.get("restaurant_two_midrange_eur_2026"),
                     "restaurant_source_url":daily.get("restaurant_source_url"),
                     "coworking_reference":remote.get("coworking_reference"),
                     "neighborhoods":pack.get("neighborhoods",[]),
                     "climate_months":climates.get("months_9_10_11"),
                     "climate_station":climates.get("station_name"),
                     "climate_url":climates.get("source_url")},
            "summary":p.get("summary","Ainda não há descrição municipal específica."),
            "research_gaps":p.get("research_gaps",[]),
            "data_missing": (
                ["Hospedagem completa para 2027"]+
                (["Custo cotidiano comparável"] if daily.get("complete_comparable_basket_eur") is None else [])+
                (["Clima set–nov"] if climates.get("months_9_10_11") is None else [])+
                (["Retorno e última milha dos passeios"] if dest_ids else [])),
        })
    return {"cities":views,"destinations":deepcopy(dest_ids),"status":"exploratory_only",
            "final_winner":None,"complete_budget":None}


def comparison_insights(matrix:dict)->list[str]:
    cities=matrix["cities"]
    if len(cities)<2:return []
    lines=[]
    counts=[(c["name"],c["documented_shared_basket"]) for c in cities]
    if len({x[1] for x in counts})>1:
        top=max(counts,key=lambda x:x[1])
        lines.append(top[0]+" tem mais **tempos de ida pesquisados nesta cesta** ("+
                     str(top[1])+"/"+str(len(matrix["destinations"]))+
                     "); isto não demonstra mobilidade melhor.")
    else:
        lines.append("A cobertura documentada na mesma cesta não diferencia estas cidades.")
    if all(c["housing"]["observations_2026"] for c in cities):
        lines.append("Há amostras históricas de moradia, mas tamanhos e condições "
                     "não permitem comparar custos finais de 60 noites.")
    else:
        lines.append("A moradia ainda não pode ser comparada para todas as selecionadas.")
    if all(c["documented_shared_basket"]==0 for c in cities):
        lines.append("Ainda não é possível comparar os deslocamentos nesta cesta.")
    lines.append("Nenhuma volta de fim de semana ou reserva de 2027 foi confirmada.")
    return lines
