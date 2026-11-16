"""Data Quality 2.1 B: reproducible remote-work and climate evidence.

No quality/safety rank. Uses actual date and IANA time zones for 2027 DST;
source discrepancies remain visible rather than silently reconciled.
"""
from __future__ import annotations
import json
from pathlib import Path
from datetime import date,datetime
from zoneinfo import ZoneInfo
from copy import deepcopy
from dq20_urban_life_model import compare_urban_life,BASES

FILE=Path(__file__).resolve().parent/"data"/"dq21_living_evidence_2026_11.json"
BRAZIL="America/Sao_Paulo"
EUROPE="Europe/Berlin"

def load_living_evidence(path:Path=FILE)->dict:
    source=json.loads(path.read_text(encoding="utf-8"))
    if source.get("schema_version")!=1 or {x["city_id"] for x in source.get("city_review_scope",[])}!=set(BASES):
        raise ValueError("Evidências urbanas incompatíveis")
    climate=source["freiburg_climate"]
    if (climate["station_id"]!="01443" or climate["normal_period"]!="1991-2020" or
        climate["official_station_series_independently_extracted"] is not False or
        climate["methodological_equivalence_to_french_stations"] is not False):
        raise ValueError("Clima não validado na fonte primária")
    if any(not str(r["urban_provider_url"]).startswith("https://")
           for r in source["city_review_scope"]):
        raise ValueError("Rede sem fonte")
    return source

def brazil_to_europe_hours(on_date:str, *, start_hour:int,end_hour:int)->dict:
    if not (type(start_hour)==type(end_hour)==int and 0<=start_hour<end_hour<=24):
        raise ValueError("Expediente brasileiro inválido")
    day=date.fromisoformat(on_date)
    if day.year!=2027 or day<=date(2027,9,4):
        raise ValueError("Simulação restrita à temporada posterior ao casamento de 2027")
    start=datetime(day.year,day.month,day.day,start_hour,tzinfo=ZoneInfo(BRAZIL))
    end=datetime(day.year,day.month,day.day,tzinfo=ZoneInfo(BRAZIL))
    end=end.replace(hour=end_hour if end_hour<24 else 0)
    if end_hour==24:
        from datetime import timedelta
        end+=timedelta(days=1)
    converted_start=start.astimezone(ZoneInfo(EUROPE))
    converted_end=end.astimezone(ZoneInfo(EUROPE))
    return {"date_brazil":on_date,"brazil_hours":[start_hour,end_hour],
            "europe_start":converted_start.isoformat(),
            "europe_end":converted_end.isoformat(),
            "europe_hours":[converted_start.hour,converted_end.hour],
            "time_zone":"Europe/Berlin",
            "offset_hours":int(converted_start.utcoffset().total_seconds()/3600-
                               start.utcoffset().total_seconds()/3600),
            "verified_coworking_open_at_shift_end":False}

def compare_living_depth(*,study_dates:tuple[str,str]|None=None,
                         brazil_hours:tuple[int,int]|None=None)->dict:
    source=load_living_evidence()
    base=compare_urban_life()
    if (study_dates is None)!=(brazil_hours is None):
        raise ValueError("Expediente só com datas explícitas")
    work_scenarios=[]
    if study_dates is not None:
        if len(study_dates)!=2 or len(brazil_hours)!=2:
            raise ValueError("Datas/horários insuficientes")
        work_scenarios=[brazil_to_europe_hours(d,start_hour=brazil_hours[0],
                                            end_hour=brazil_hours[1])
                        for d in study_dates]
    supplemental={row["city_id"]:row for row in source["city_review_scope"]}
    result=[]
    for original in base["cities"]:
        city=original["city_id"]
        data=deepcopy(original["dimensions"])
        original_climate=data["clima_set_nov"]
        if city=="freiburg":
            record=source["freiburg_climate"]
            original_climate["months_9_10_11"]={
                m:{"tmean_c":value,"precip_mm":None}
                for m,value in record["monthly_mean_temperature_c"].items()}
            original_climate.update({"station":"Freiburg 01443",
                "source_url":record["temperature_source_url"],
                "climate_status":"secondary_dwd_report_reconciliation_needed",
                "precipitation_verified":False,
                "primary_series_extracted":False})
        else:
            original_climate.update({"climate_status":"existing_french_station_normals",
                                    "precipitation_verified":True,
                                    "primary_series_extracted":None})
        result.append({"city_id":city,"dimensions":data,
                       "work_scenarios":deepcopy(work_scenarios),
                       "property_internet_confirmed":False,
                       "property_last_mile_confirmed":False,
                       "late_transit_service":supplemental[city]["urban_provider_url"],
                       "grocery_gym_pharmacy_walk_verified":False,
                       "comparable_crime_rate":None,
                       "night_safety_for_property":None,
                       "city_score":None})
    return {"cities":result,"source_issues":[
                "DWD 01443 temperature republications differ; verify against primary station file",
                "Shared 1991–2020 climate period does not prove equal station exposure",
                "City transport service does not prove specific rental access or night safety"],
            "no_official_trip_changes":True,"work_hours_selected":brazil_hours is not None,
            "ranked":False}
