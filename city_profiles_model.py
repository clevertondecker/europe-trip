"""Public city profiles and provenance; never writes to TripPlan or GCS.

The profile dataset supplements existing 30-city coverage; it does not replace
rail, housing or financial contracts and must not publish invented scores.
"""
from __future__ import annotations

import json
from pathlib import Path
from copy import deepcopy
from base_research_expanded_model import load_research

PATH=Path(__file__).resolve().parent/"data"/"city_profiles_enriched.json"
SECTIONS=frozenset({"transport","quality_of_life","housing","remote_work",
                    "daily_costs","climate"})


def validate_profiles(data:dict,canonical:dict|None=None)->dict:
    canonical=load_research() if canonical is None else canonical
    if not isinstance(data,dict) or data.get("schema_version")!=1:
        raise ValueError("Versão das fichas incompatível")
    rows=data.get("cities")
    if not isinstance(rows,list):
        raise ValueError("Fichas ausentes")
    originals={c["id"]:c for c in canonical["cities"]}
    if len(rows)!=len(originals):
        raise ValueError("Fichas devem representar cada cidade cadastrada")
    seen=set()
    for row in rows:
        if not isinstance(row,dict):
            raise ValueError("Ficha inválida")
        key=row.get("city_id")
        if key in seen or key not in originals:
            raise ValueError("Identificador ausente ou repetido")
        seen.add(key)
        source=originals[key]
        for attr,val in (("name",source["name"]),("country",source["country"]),
                         ("shortlist",source["shortlist"]),("corridor",source["corridor"])):
            if row.get(attr)!=val:
                raise ValueError("Ficha não corresponde ao cadastro canônico")
        if not isinstance(row.get("summary"),str) or not row["summary"]:
            raise ValueError("Resumo inválido")
        stat=row.get("official_statistics_source")
        if not isinstance(stat,dict) or not str(stat.get("url","")).startswith("https://"):
            raise ValueError("Fonte estatística ausente")
        if row.get("quality_of_life",{}).get("numeric_score") is not None:
            raise ValueError("Sem score numérico sem métricas comparáveis")
        if row.get("housing",{}).get("availability_2027_verified") is not False:
            raise ValueError("Disponibilidade de 2027 não comprovada")
        for field in ("advantages","limitations","research_gaps","evidence"):
            if not isinstance(row.get(field),list):
                raise ValueError("Lista de pesquisa inválida")
        for ev in row["evidence"]:
            if ev.get("section") not in SECTIONS or not ev.get("summary") or not str(ev.get("source_url","")).startswith("https://"):
                raise ValueError("Evidência sem fonte ou categoria")
            if not ev.get("observed_at") or not ev.get("limitations"):
                raise ValueError("Evidência sem data e ressalva")
        if len(row["evidence"])>30:
            raise ValueError("Ficha excessiva")
    return deepcopy(data)


def load_profiles(path:Path=PATH,canonical:dict|None=None)->dict:
    return validate_profiles(json.loads(path.read_text(encoding="utf-8")),canonical)


def profile_by_id(data:dict,city_id:str)->dict:
    for item in data["cities"]:
        if item["city_id"]==city_id:return deepcopy(item)
    raise ValueError("Cidade não encontrada")


def compact_comparison(data:dict,city_ids:list[str])->list[dict]:
    if not 2<=len(city_ids)<=3 or len(set(city_ids))!=len(city_ids):
        raise ValueError("Selecione 2 ou 3 cidades diferentes")
    result=[]
    for key in city_ids:
        row=profile_by_id(data,key)
        house=row["housing"]
        result.append({
            "Cidade":row["name"],
            "País":row["country"],
            "Corredor":row["corridor"],
            "Moradia: amostras 2026":house["historical_offer_count"],
            "Faixa observada EUR/mês":
                (str(house["historical_observed_min_eur_month"])+"–"+
                 str(house["historical_observed_max_eur_month"]))
                if house["historical_observed_min_eur_month"] is not None else "Não pesquisado",
            "Notas locais com fonte":len(row["evidence"]),
            "Estadia 2027":"Não confirmada",
            "Custo cotidiano":"Não comparável",
            "Clima setembro–novembro":"Não documentado em base comum",
        })
    return result
