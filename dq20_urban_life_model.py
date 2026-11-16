"""Data Quality 2.0 (B): source-aware temporary-residence profiles.

Extends the existing research packs without duplicating 12-city canonical data.
No scores, unsafe-city labels, inferred rental internet, or work schedule.
"""
from __future__ import annotations
import json
from pathlib import Path
from city_research_packs_model import load_city_packs

FILE=Path(__file__).resolve().parent/"data"/"dq20_urban_evidence_delta_2026_11.json"
BASES=("mulhouse","strasbourg","freiburg")
DIMENSIONS=("mobilidade_sem_carro","servicos_e_rotina","trabalho_remoto",
            "seguranca_comprovada","clima_set_nov","lazer_e_cultura")

def load_urban_delta(path:Path=FILE)->dict:
    delta=json.loads(path.read_text(encoding="utf-8"))
    rows=delta.get("cities",[])
    if delta.get("schema_version")!=1 or {x["city_id"] for x in rows}!=set(BASES):
        raise ValueError("Pesquisa de rotina incompleta")
    if len(rows)!=len(BASES):
        raise ValueError("Cidade duplicada")
    for x in rows:
        for field in ("network_url","evening_url"):
            if not x["transport"][field].startswith("https://"):
                raise ValueError("Fonte de mobilidade inválida")
        if x["transport"]["late_access_verified_for_address"]:
            raise ValueError("Não há horários noturnos comprovados para endereço de imóvel")
    return delta

def compare_urban_life(packs:dict|None=None,delta:dict|None=None,
                       brazil_work_window:tuple[int,int]|None=None)->dict:
    packs=load_city_packs() if packs is None else packs
    delta=load_urban_delta() if delta is None else delta
    by_pack={c["city_id"]:c for c in packs["cities"]}
    by_delta={c["city_id"]:c for c in delta["cities"]}
    if brazil_work_window is not None:
        if (not isinstance(brazil_work_window,tuple) or len(brazil_work_window)!=2 or
            not all(type(h)==int for h in brazil_work_window) or
            not 0<=brazil_work_window[0]<=23 or
            not brazil_work_window[0]<brazil_work_window[1]<=24):
            raise ValueError("Horário hipotético do Brasil inválido")
    cities=[]
    for city in BASES:
        original=by_pack[city]
        supplement=by_delta[city]
        cowork=original["remote_work"]["coworking_reference"]
        if not cowork and supplement["remote_work"]["supplemental_coworking_url"]:
            cowork={"name":"Coworkings indicados pelo turismo municipal",
                    "source_url":supplement["remote_work"]["supplemental_coworking_url"],
                    "hours":None,"price_eur_2026":None}
        months=original["climate"]["months_9_10_11"]
        climate={"months_9_10_11":months,
                 "source_url":original["climate"].get("source_url"),
                 "normal_period":original["climate"].get("normal_period"),
                 "station":original["climate"].get("station_name"),
                 "is_2027_weather_forecast":False}
        work=None
        if brazil_work_window:
            start,end=brazil_work_window
            work={"brazil_hours":[start,end],
                  "europe_summer_hours":[start+5,end+5],
                  "europe_winter_hours":[start+4,end+4],
                  "scenario_only":True,"office_use_verified":False}
        dimensions={
            "mobilidade_sem_carro":{"network":supplement["transport"]["network"],
                                   "source_url":supplement["transport"]["network_url"],
                                   "evening_reference":supplement["transport"]["evening_reference"],
                                   "evening_url":supplement["transport"]["evening_url"],
                                   "late_access_to_actual_rental_verified":False},
            "servicos_e_rotina":{"neighborhoods_to_evaluate":[n["name"] for n in original["neighborhoods"]],
                                "grocery_pharmacy_gym_proximity_verified":False,
                                "walking_time_from_rental_min":None},
            "trabalho_remoto":{"coworking_reference":cowork,
                              "coworking_covers_scenario_evening":supplement["remote_work"]["suitable_for_brazil_9_to_18"] if brazil_work_window==(9,18) else None,
                              "internet_in_rental_verified":original["remote_work"]["internet_in_rental_verified"],
                              "work_window":work},
            "seguranca_comprovada":{"comparable_official_rate":None,
                                    "night_safety_by_neighborhood":None,
                                    "no_generic_safe_city_conclusion":True},
            "clima_set_nov":climate,
            "lazer_e_cultura":{"existing_summary":original.get("summary",""),
                               "verified_near_specific_rental":False},
        }
        gaps=[]
        if months is None:gaps.append("Normais climáticas locais comparáveis set–nov")
        gaps.extend(["Transporte noturno até endereço da moradia",
                     "Velocidade de internet do imóvel",
                     "Acesso real a serviços a pé",
                     "Dados públicos de segurança comparáveis"])
        cities.append({"city_id":city,"dimensions":dimensions,
                       "evidence_gaps":gaps,"quality_score":None,
                       "rank":None,"housing_bookability_verified":False})
    return {"cities":cities,"dimension_names":DIMENSIONS,"comparison_is_factual":True,
            "score_allowed":False,"reference_period":"existing 1991–2020 climate and 2026 services"}

def _by_city(comparison:dict,city_id:str)->dict:
    return next(c for c in comparison["cities"] if c["city_id"]==city_id)
