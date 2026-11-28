"""Auditable research coverage across 30 European base-city candidates.

This is *not* a ranking model.  Historic prices, operator weekday schedules,
generic rental search URLs, and counts of links never become quality scores.
Every city is assessed against the SAME fixed 15-destination basket.
"""
from __future__ import annotations

from pathlib import Path
import json
from copy import deepcopy

from base_research_expanded_model import (
    CRITERIA,PRESETS,load_research,load_rail,observed_housing,normalized_score,
)
from base_explorer_model import load_exploration
from attractions_model import load_base_routes
from five_base_comparison_model import load_five_base_evidence

LABELS={
    "temporary_housing":"Moradia",
    "rail_connectivity":"Trens",
    "viable_destinations":"Passeios",
    "outing_cost":"Custos dos passeios",
    "daily_life_remote_work":"Vida cotidiana",
    "practical_country_diversity":"Países práticos",
}
UNRESEARCHED="Não pesquisado"
PARTIAL="Parcial"
DOCUMENTED="Pesquisado"
# These are NOT weights for final city quality; they are requirements of
# documentary coverage, disclosed individually to the traveler.
REQUIREMENTS={
    "temporary_housing":(
        "Amostra histórica de aluguel",
        "Anúncio individual com URL própria",
        "Ocupação de dois adultos confirmada",
        "Contrato para 56–60 noites confirmado",
        "Taxas e caução conhecidas",
        "Internet confirmada",
        "Distância a estação verificada",
    ),
    "rail_connectivity":(
        "Rede ou ligação ferroviária com fonte específica",
        "Tempos estação–estação para a cesta comum",
        "Frequência das ligações pesquisadas",
        "Conexões/trocas verificadas",
        "Retorno aos fins de semana verificado",
    ),
    "viable_destinations":(
        "Destinos da cesta com tempo de ida observado",
        "Retorno/última milha conhecidos",
        "Acesso real às atrações e pernoites verificados",
    ),
    "outing_cost":(
        "Tarifas de ida históricas rastreáveis",
        "Ida e volta em tarifa normal verificada",
        "Transporte urbano/ingressos/pernoites documentados",
    ),
    "daily_life_remote_work":(
        "Preços cotidianos específicos da cidade",
        "Local de trabalho com fonte",
        "Internet compatível com trabalho remoto",
        "Transporte urbano e serviços sem carro",
        "Horários de acesso compatíveis com expediente",
    ),
    "practical_country_diversity":(
        "Destinos internacionais com tempo registrado",
        "Conexões e retornos internacionais verificados",
    ),
}
# A comparable score requires a separate, exact 0–100 metric based on the
# same 15 journeys, two-adult housing, fares and daily-life basket for all 12.
# No current evidence meets that policy; keep the final score unavailable.
COMPARABLE_REQUIREMENTS={
    "temporary_housing":"3 apartamentos completos e comparáveis, dois adultos, 56–60 noites e todas as taxas",
    "rail_connectivity":"15 tempos da mesma cesta, conexões, frequência, retorno e última milha em período equivalente",
    "viable_destinations":"15 destinos com retorno e acesso à atração documentados, por categorias de interesse",
    "outing_cost":"15 percursos da mesma cesta com tarifa normal de volta, ingressos e custos locais",
    "daily_life_remote_work":"Cesta equivalente de alimentação, serviços, internet e horários compatíveis para todas as bases",
    "practical_country_diversity":"Acesso internacional com ida/volta e tempo porta a porta comparáveis",
}


def _valid_url(url):
    return isinstance(url,str) and url.startswith("https://")


def _safe_ratio(found,total):
    return round(100*found/total,1) if total else 0.


def _make_evidence(*,city_id,criterion,indicator,value,unit,source_url,
                   date_observed,scope,kind,limitation,comparable=False):
    return {
        "city":city_id,"criterion":criterion,"indicator":indicator,
        "value":value,"unit":unit,"source_url":source_url,
        "observed_at":date_observed,"scope":scope,"kind":kind,
        "limitation":limitation,"comparable_for_final_score":comparable,
        "revalidate_for_2027":True,
    }


def load_round2():
    path=Path(__file__).resolve().parent/"data"/"city_research_round2_2026.json"
    data=json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data.get("cities"),list) or len(data["cities"])<4:
        raise ValueError("Referências de vida cotidiana incompletas")
    return data


def _dataset_routes(city_id,rail,exploration,five,base_routes):
    """Precedence: same-basket rail-specific study, then exploratory,
    then expanded operator excerpts. No sum of duplicated source records."""
    basket={d["id"]:d for d in five["common_destinations"]}
    rows={}
    for item in five["verified_time_routes"]:
        if item["base_id"]!=city_id or item["destination_id"] not in basket:
            continue
        rows[item["destination_id"]]={
            "destination_id":item["destination_id"],
            "minutes":item["fastest_train_oneway_min"],
            "fare_oneway":item.get("advertised_from_eur_person_oneway"),
            "source_url":item["source_url"],"date":five["checked_at"],
            "scope":"operador / viagem de ida estação–estação",
            "frequency":None,"transfers":None,"return_verified":False,
        }
    for item in exploration["routes"]:
        dest=item["destination_id"]
        if item["base_id"]!=city_id or dest not in basket or dest in rows:
            continue
        minutes=item.get("train_minutes_oneway_min")
        if minutes is None or not _valid_url(item.get("source_url")):continue
        rows[dest]={
            "destination_id":dest,"minutes":minutes,
            "fare_oneway":item.get("fare_from_eur_person_oneway"),
            "source_url":item["source_url"],"date":item.get("retrieved_at"),
            "scope":"referência histórica de ida estação–estação",
            "frequency":None,"transfers":None,"return_verified":False,
        }
    for item in base_routes["routes"]:
        dest=item["destination_id"]
        if item["base_id"]!=city_id or dest not in basket or dest in rows:
            continue
        minutes=item.get("train_minutes_one_way")
        if minutes is None or not _valid_url(item.get("source_url")):continue
        rows[dest]={
            "destination_id":dest,"minutes":minutes,
            "fare_oneway":item.get("fare_eur_person_oneway"),
            "source_url":item["source_url"],"date":item.get("retrieved_at"),
            "scope":"referência histórica TER, estação–estação",
            "frequency":None,"transfers":item.get("transfers"),
            "return_verified":item.get("weekend_return_verified") is True,
        }
    for item in rail["segments"]:
        dest=item["to"]
        if item["from"]!=city_id or dest not in basket or dest in rows:continue
        rows[dest]={
            "destination_id":dest,"minutes":item["fastest_minutes"],
            "fare_oneway":item.get("advertised_fare_from_eur_person_oneway"),
            "source_url":item["source_url"],"date":rail["basis_date"],
            "scope":"segunda-feira de referência, estação–estação",
            "frequency":item.get("services_on_sample_day"),
            "transfers":item.get("transfers_for_fastest"),
            "return_verified":False,
        }
    return basket,rows


def _finish(key,flags):
    # Evidence-depth ratio is a checklist, not suitability and not a market
    # confidence interval. Each requirement contributes exactly one boolean.
    n=len(REQUIREMENTS[key])
    if len(flags)!=n:
        raise ValueError("Contagem documental incompatível com metodologia")
    fractions=[float(x) for x in flags]
    if any(not 0<=v<=1 for v in fractions):
        raise ValueError("Cobertura precisa estar no intervalo 0–1")
    filled=sum(v>0 for v in fractions)
    depth=sum(fractions)
    return {
        "criterion":key,"label":LABELS[key],
        "documented_count":filled,"requirements_count":n,
        "documentary_percent":_safe_ratio(depth,n),
        "status":UNRESEARCHED if filled==0 else
                 (DOCUMENTED if depth==n else PARTIAL),
        "checks":[{"requirement":r,"documented":v>0,
                   "coverage_percent":round(v*100,1)}
                  for r,v in zip(REQUIREMENTS[key],fractions)],
        "comparable_score":None,
        "scoring_status":"Dados insuficientes para nota comparável",
        "scoring_gap":COMPARABLE_REQUIREMENTS[key],
    }


def city_evidence(city,*,study=None,rail=None,exploration=None,
                  five=None,round2=None,base_routes=None):
    """Fixed requirements; never turn missing fares/listings into zero euros."""
    if study is None:study=load_research()
    if rail is None:rail=load_rail()
    if exploration is None:exploration=load_exploration()
    if five is None:five=load_five_base_evidence()
    if round2 is None:round2=load_round2()
    if base_routes is None:base_routes=load_base_routes()
    # Accept parsed round2 dict or a list of city rows (compatibility).
    round2_cities=round2.get("cities",[]) if isinstance(round2,dict) else round2
    everyday=next((row for row in round2_cities if row["id"]==city["id"]),{})
    basket,routes=_dataset_routes(city["id"],rail,exploration,five,base_routes)
    observed=observed_housing(city)
    offers=city["housing_offers"]
    observed_source=next((x for x in offers if _valid_url(x.get("catalogue_url"))),None)
    five_housing=next((x for x in five["housing"] if x["id"]==city["id"]),{})
    five_listings=five_housing.get("listings",[])
    hflags=[
        bool(observed["count"] or five_listings),
        any(_valid_url(x.get("listing_url")) for x in offers) or
          any(_valid_url(x.get("source_url")) and
              x.get("source_is_direct_listing")=="direct_listing_page"
              for x in five_listings),
        any(x.get("two_adults_confirmed") is True for x in offers),
        any(x.get("short_stay_56_to_60_nights_confirmed") is True for x in offers),
        any(x.get("all_mandatory_fees_known") is True for x in offers),
        any(x.get("internet_verified") is True for x in offers),
        any(x.get("near_station_verified") is True for x in offers),
    ]
    rows=list(routes.values())
    timed=[r for r in rows if type(r["minutes"]) is int and r["minutes"]>0]
    fares=[r for r in timed if isinstance(r.get("fare_oneway"),(int,float))
           and r["fare_oneway"]>0]
    # Some early studies have a route at all, but not the same basket.
    # Never count generic links or unrelated cities as basket coverage.
    countries={basket[r["destination_id"]]["country"] for r in timed
               if basket[r["destination_id"]]["country"]!=city["country"]}
    freq=[r for r in rows if r.get("frequency") is not None]
    turns=[r for r in rows if r.get("transfers") is not None]
    verified_returns=[r for r in rows if r.get("return_verified") is True]
    common=len(basket)
    # A criterion counts as "documented" only with a real sourced item. For
    # basket-coverage checklist flags, the actual fraction is separately shown.
    # Sourced network evidence outside the fixed basket is genuine
    # documentary research, but it cannot become a comparable time.
    rail_references=[
        note for note in study.get("research_updates",[])
        if note.get("city_id")==city["id"] and
           note.get("criterion")=="rail_connectivity" and
           note.get("kind") in (
               "official_network_reference","operator_schedule_reference",
               "regional_network_reference",
               "operator_schedule_different_sample_day",
               "official_operator_route_overview",
           ) and _valid_url(note.get("source_url"))
    ]
    rflags=[bool(timed or rail_references),
            len(timed)/common,len(freq)/common,
            len(turns)/common,len(verified_returns)/common]
    vflags=[len(timed)/common,len(verified_returns)/common,0]
    cflags=[len(fares)/common,0,0]
    cowork=everyday.get("coworking") or {}
    dailyflags=[
        everyday.get("restaurant_two_midrange_eur") is not None and
          _valid_url(everyday.get("restaurant_source_url")),
        bool(cowork.get("name")) and _valid_url(cowork.get("source_url")),
        cowork.get("internet_verified") is True,
        everyday.get("urban_transport_researched") is True,
        cowork.get("late_work_compatible") is True,
    ]
    country_choices={place["country"] for place in basket.values()
                     if place["country"]!=city["country"]}
    pflags=[len(countries)/len(country_choices) if country_choices else 0,0]
    flags=[hflags,rflags,vflags,cflags,dailyflags,pflags]
    criterion={k:_finish(k,flags[i]) for i,k in enumerate(CRITERIA)}
    evidence=[]
    if observed_source:
        evidence.append(_make_evidence(
            city_id=city["id"],criterion="temporary_housing",
            indicator="amostra de anúncios em catálogo",value=observed["count"],
            unit="observações históricas",source_url=observed_source["catalogue_url"],
            date_observed=observed_source.get("checked_at"),
            scope="preço/m²/mês do anúncio sem datas 2027",
            kind=observed_source.get("source_type","catalogue_snapshot"),
            limitation="URLs genéricas; sem evidência de imóvel inteiro, dois adultos, contrato ou taxas"))
    for listing in five_listings:
        if (listing.get("source_is_direct_listing")=="direct_listing_page"
                and _valid_url(listing.get("source_url"))):
            evidence.append(_make_evidence(
                city_id=city["id"],criterion="temporary_housing",
                indicator="anúncio individual histórico de apartamento mobiliado",
                value=listing["monthly_eur"],unit="EUR/mês (anúncio de 2026)",
                source_url=listing["source_url"],date_observed=five["checked_at"],
                scope=listing.get("title","anúncio individual"),
                kind="direct_listing_observation_2026",
                limitation="Sem confirmação de dois adultos, 56–60 noites, internet, taxas totais, caução ou disponibilidade outono/2027"))
    for r in timed:
        evidence.append(_make_evidence(
            city_id=city["id"],criterion="rail_connectivity",
            indicator="tempo mínimo observado de ida",value=r["minutes"],
            unit="minutos estação–estação",source_url=r["source_url"],
            date_observed=r["date"],scope=r["destination_id"],
            kind="historical_operator_or_route_reference",
            limitation="Não comprova retorno, tarifa normal, viagens nos fins de semana ou 2027"))
        if r in fares:
            evidence.append(_make_evidence(
                city_id=city["id"],criterion="outing_cost",
                indicator="tarifa mínima publicada por pessoa e trecho",
                value=r["fare_oneway"],unit="EUR/pessoa/ida",
                source_url=r["source_url"],date_observed=r["date"],
                scope=r["destination_id"],kind="advertised_starting_fare",
                limitation="Não é custo ida/volta para casal; sujeito a condições e estoque"))
    if dailyflags[0]:
        evidence.append(_make_evidence(
            city_id=city["id"],criterion="daily_life_remote_work",
            indicator="refeição intermediária para dois",value=everyday[
                "restaurant_two_midrange_eur"],unit="EUR/casal/refeição",
            source_url=everyday["restaurant_source_url"],date_observed=
                round2.get("checked_at") if isinstance(round2,dict) else None,
            scope="estimativa colaborativa, não preço contratual",
            kind="crowdsourced",limitation="amostra não representativa; sem internet ou supermercado"))
    updates=study.get("research_updates",[])
    for note in updates:
        if note.get("city_id") not in (city["id"],"all"):
            continue
        if not _valid_url(note.get("source_url")):continue
        evidence.append(_make_evidence(
            city_id=city["id"],criterion=note["criterion"],
            indicator=note["indicator"],value=note.get("value"),
            unit=note.get("unit"),source_url=note["source_url"],
            date_observed=note.get("observed_at"),
            scope=note.get("scope","referência estrutural"),
            kind=note.get("kind","research_update"),
            limitation=note["limitation"]))
    return {
        "id":city["id"],"name":city["name"],"country":city["country"],
        "shortlist":city["shortlist"],"housing":observed,
        "route_basket_total":common,"route_basket_with_time":len(timed),
        "route_basket_with_fare":len(fares),
        "route_time_coverage_percent":_safe_ratio(len(timed),common),
        "route_return_verified":len(verified_returns),
        "international_countries_with_time":sorted(countries),
        "criteria":criterion,"evidence":evidence,
        "status":PARTIAL if any(x["documented_count"] for x in criterion.values())
                 else UNRESEARCHED,
        "decision_ready":False,"score_0_100":None,
        "missing_for_decision":[x["scoring_gap"] for x in criterion.values()],
    }


def coverage_matrix(profile="general",study=None,rail=None,exploration=None,
                    five=None,round2=None,base_routes=None):
    """Same documentary facts, different fixed weighting; no quality ranking."""
    if profile not in PRESETS:raise ValueError("Perfil inválido")
    if study is None:study=load_research()
    if rail is None:rail=load_rail()
    if exploration is None:exploration=load_exploration()
    if five is None:five=load_five_base_evidence()
    if round2 is None:round2=load_round2()
    if base_routes is None:base_routes=load_base_routes()
    out=[]
    for city in study["cities"]:
        result=city_evidence(city,study=study,rail=rail,exploration=exploration,
                             five=five,round2=round2,base_routes=base_routes)
        weighted=sum(PRESETS[profile][i]*result["criteria"][key]["documentary_percent"]/100
                     for i,key in enumerate(CRITERIA))
        result["documentary_weighted_percent"]=round(weighted,1)
        # The scoring coverage is distinct from research activity. It is zero
        # today because none of the FULL criterion comparability tests pass.
        score=normalized_score(
            {key:result["criteria"][key]["comparable_score"] for key in CRITERIA},
            profile)
        result["scoring_weight_percent"]=score["evidence_weight"]
        result["score_0_100"]=score["score_0_100"]
        out.append(result)
    return out


def coverage_summary(rows):
    return {
        "cities":len(rows),
        "shortlist":sum(r["shortlist"] for r in rows),
        "housing_documented":sum(r["criteria"]["temporary_housing"]["documented_count"]>0 for r in rows),
        "rail_documented":sum(r["route_basket_with_time"]>0 for r in rows),
        "has_comparable_criterion":sum(r["scoring_weight_percent"]>0 for r in rows),
        "decision_ready":sum(r["decision_ready"] for r in rows),
    }
