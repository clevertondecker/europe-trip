"""DQ 2.1 A — weekend service evidence, without invented returns.

Separate date-specific train observations from recurring operator service
patterns. Only source-backed paired services with verified last mile can
support a time-window test. A 2026 pairing NEVER confirms a 2027 trip.
"""
from __future__ import annotations
from datetime import date,datetime,timedelta
from pathlib import Path
from copy import deepcopy
import json
from dq20_weekend_routes_model import BASES,DESTINATIONS,route_matrix,illustrative_weekends

FILE=Path(__file__).resolve().parent/"data"/"dq21_weekend_evidence_2026_11.json"

def load_weekend_details(path:Path=FILE)->dict:
    value=json.loads(path.read_text(encoding="utf-8"))
    if value.get("schema_version")!=1:
        raise ValueError("Schema DQ21 incompatível")
    records=value["dated_services"]
    seen=set()
    for leg in records:
        key=(leg["origin_id"],leg["destination_id"],leg["travel_date"],leg["depart_local"])
        if key in seen: raise ValueError("Viagem repetida")
        seen.add(key)
        day=date.fromisoformat(leg["travel_date"])
        start=datetime.fromisoformat(leg["travel_date"]+"T"+leg["depart_local"])
        end=datetime.fromisoformat(leg["travel_date"]+"T"+leg["arrive_local"])
        if end<=start:end+=timedelta(days=1)
        if (end-start)>timedelta(days=1) or not leg["source_url"].startswith("https://"):
            raise ValueError("Horário ou fonte inválidos")
        if type(leg["changes"]) is not int or leg["changes"]<0:
            raise ValueError("Conexões inválidas")
        if day.year>=2027:raise ValueError("Datas futuras não comprovadas")
    for pattern in value["patterns"]:
        if (pattern.get("kind")!="weekend_pattern_not_date_specific" or
            pattern["valid_for_2027"] is not False or
            not pattern["source_url"].startswith("https://")):
            raise ValueError("Padrão sem validade comprovada")
    return value

def paired_day_trip(origin:str,destination:str,travel_date:str, *,
                    evidence:dict|None=None,minimum_hours:float=4,
                    last_mile_minutes_each_way:int|None=None)->dict:
    """Pairs EXACT dated services on the same local day, not source averages.

    Even with historical full timings this remains an illustration; a 2027
    classification requires 2027 source observations, unavailable here.
    """
    if minimum_hours<=0 or minimum_hours>24:raise ValueError("Tempo útil inválido")
    if last_mile_minutes_each_way is not None and (
        type(last_mile_minutes_each_way) is not int or last_mile_minutes_each_way<0):
        raise ValueError("Última milha inválida")
    day=date.fromisoformat(travel_date)
    evidence=load_weekend_details() if evidence is None else evidence
    outgoing=[r for r in evidence["dated_services"] if
              (r["origin_id"],r["destination_id"],r["travel_date"])==
              (origin,destination,travel_date)]
    returning=[r for r in evidence["dated_services"] if
               (r["origin_id"],r["destination_id"],r["travel_date"])==
               (destination,origin,travel_date)]
    result={"origin_id":origin,"destination_id":destination,"travel_date":travel_date,
            "outbound_count":len(outgoing),"return_count":len(returning),
            "source_records":deepcopy(outgoing+returning),
            "visit_hours":None,"status":"dados_insuficientes",
            "confirmed_2027":False,"door_to_door_verified":False}
    if day.weekday() not in (5,6):
        result["status"]="dia_util_nao_comprova_fim_de_semana"
        return result
    if not outgoing or not returning:
        result["status"]="falta_retorno" if outgoing else "faltam_ambas_direcoes"
        return result
    valid=[]
    for a in outgoing:
        arrival=datetime.fromisoformat(travel_date+"T"+a["arrive_local"])
        for b in returning:
            dep=datetime.fromisoformat(travel_date+"T"+b["depart_local"])
            if dep<=arrival:continue
            duration=(dep-arrival).total_seconds()/3600
            if last_mile_minutes_each_way is not None:
                duration-=last_mile_minutes_each_way*2/60
            valid.append(duration)
    if not valid:
        result["status"]="horarios_incompativeis"
        return result
    result["visit_hours"]=round(max(valid),2)
    if last_mile_minutes_each_way is None:
        result["status"]="ultima_milha_pendente"
    elif result["visit_hours"]>=minimum_hours:
        result["status"]="bate_volta_historico_amostrado"
        result["door_to_door_verified"]=True
    else:result["status"]="tempo_util_insuficiente"
    return result

def weekend_research_matrix(details:dict|None=None)->list[dict]:
    details=load_weekend_details() if details is None else details
    existing=route_matrix()
    rows=[]
    for old in existing:
        origin,dest=old["base_id"],old["destination_id"]
        dated=[r for r in details["dated_services"] if
               (r["origin_id"],r["destination_id"])==(origin,dest) and
               date.fromisoformat(r["travel_date"]).weekday() in (5,6)]
        returns=[r for r in details["dated_services"] if
                 (r["origin_id"],r["destination_id"])==(dest,origin) and
                 date.fromisoformat(r["travel_date"]).weekday() in (5,6)]
        rows.append({"base_id":origin,"destination_id":dest,
                     "minimum_rail_minutes_2026":old["station_to_station_fastest_min"],
                     "representative_minutes_2026":old["representative_min"],
                     "dated_weekend_departures":deepcopy(dated),
                     "dated_weekend_returns":deepcopy(returns),
                     "intra_brussels_bruges_weekend_pattern":dest in ("brussels","bruges_be"),
                     "same_weekend_full_itinerary_verified":False,
                     "bookable_2027":False,
                     "overnight_required":None,
                     "status":"roteiro_longo_pede_pernoite_a_estudar"
                         if old["station_to_station_fastest_min"] is not None and
                            old["station_to_station_fastest_min"]>=240
                         else "horarios_de_volta_pendentes"})
    return rows

def combined_belgian_weekend()->dict:
    evidence=load_weekend_details()
    service=evidence["patterns"]
    return {"route":["brussels","bruges_be"],"weekend_segment_pattern":True,
            "direct_service_avg_min":service[0]["mean_rail_minutes"],
            "weekend_early_service_brussels":service[0]["weekend_first"],
            "weekend_late_return_from_bruges":service[1]["weekend_last"],
            "source_url":service[0]["source_url"],
            "from_each_base_verified":{base:False for base in BASES},
            "overnight_hotel_verified":False,
            "total_travel_minutes":None,"2027_confirmed":False,
            "status":"trecho_interno_documentado_viagem_completa_pendente"}

def weekend_hypotheses(n:int=8)->list[dict]:
    return [dict(row,source_status="editorial_sem_reserva")
            for row in illustrative_weekends(n)]
