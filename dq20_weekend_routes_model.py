"""Data Quality 2.0 (A): conservative weekend itinerary feasibility pilot.

The existing rail evidence adapter is authoritative for original observations.
This module enriches only evidence absent from that adapter; it never adds two
legs together to assert a connection, or turns a weekday journey into a
verified Saturday/Sunday return. Pure/read-only.
"""
from __future__ import annotations
import json
from pathlib import Path
from rail_evidence_unified_model import canonical_place,load_rail_evidence,route_evidence

FILE=Path(__file__).resolve().parent/"data"/"dq20_route_evidence_delta_2026_11.json"
BASES=("mulhouse","strasbourg","freiburg")
DESTINATIONS=("luxembourg_city","interlaken","brussels","bruges_be","rotterdam")
LABELS={"mulhouse":"Mulhouse","strasbourg":"Strasbourg","freiburg":"Freiburg im Breisgau",
        "luxembourg_city":"Luxemburgo","interlaken":"Interlaken",
        "brussels":"Bruxelas","bruges_be":"Bruges","rotterdam":"Rotterdam"}
STATUSES=("bate_volta_comprovado","fim_semana_com_pernoite_comprovado",
          "viagem_longa_ou_exigente_indicativa","dados_insuficientes")

def load_pilot(path:Path=FILE)->dict:
    value=json.loads(path.read_text(encoding="utf-8"))
    if (value.get("schema_version")!=1 or
        tuple(value.get("pilot_bases",()))!=BASES or
        tuple(value.get("pilot_destinations",()))!=DESTINATIONS):
        raise ValueError("Piloto 3×5 incompatível")
    seen=set()
    for r in value["observations"]:
        pair=(r["origin_id"],r["destination_id"])
        if pair in seen or r["origin_id"] not in BASES or r["destination_id"] not in DESTINATIONS:
            raise ValueError("Observações duplicadas ou fora da cesta")
        seen.add(pair)
        if (r["observed_minutes"] is not None and
            (type(r["observed_minutes"]) is not int or r["observed_minutes"]<=0)):
            raise ValueError("Duração histórica inválida")
        if not r["source_url"].startswith("https://"):
            raise ValueError("Evidência sem fonte")
        if r["weekend_return_verified"] or r["verified_for_2027"]:
            raise ValueError("Retorno/data futuros não documentados")
    return value

def classify_feasibility(*,oneway_min:int|None,weekend_outbound:bool=False,
                         weekend_return:bool=False,visit_hours:float|None=None,
                         overnight_confirmed:bool=False)->str:
    """Conservative and explicit policy, no train timetable invented.

    A true weekend day-trip requires actual outbound AND return observations
    plus at least four usable destination hours (including local transport
    verified separately). Otherwise long journeys (>=4h one way) are
    *indicatively* demanding, never declared impossible.
    """
    if oneway_min is not None and (type(oneway_min) is not int or oneway_min<=0):
        raise ValueError("Duração inválida")
    if visit_hours is not None and not 0<=visit_hours<=24:
        raise ValueError("Tempo de visita inválido")
    if weekend_outbound and weekend_return and visit_hours is not None and visit_hours>=4:
        return STATUSES[0]
    if weekend_outbound and weekend_return and overnight_confirmed:
        return STATUSES[1]
    if oneway_min is not None and oneway_min>=240:
        return STATUSES[2]
    return STATUSES[3]

def route_matrix(pilot:dict|None=None,rail:dict|None=None)->list[dict]:
    pilot=load_pilot() if pilot is None else pilot
    rail=load_rail_evidence() if rail is None else rail
    delta={(x["origin_id"],x["destination_id"]):x
           for x in pilot["observations"]}
    results=[]
    for base in BASES:
        for dest in DESTINATIONS:
            original=route_evidence(rail,base,dest)
            complementary=delta.get((base,dest))
            # Prefer original published observation; a new sample is a
            # separately dated piece of evidence, not a competing minimum.
            known=original["minimum_oneway_min"]
            if known is None and complementary:
                known=complementary["observed_minutes"]
            sources=[dict(source_dataset=o["source_dataset"],source_url=o["source_url"],
                          evidence_date=o["evidence_date"],minimum_oneway_min=o["minimum_oneway_min"])
                     for o in original["observations"] if o["source_url"]]
            if complementary:
                sources.append({"source_dataset":"dq20_operator_addendum" if complementary["source_kind"]=="operator" else "dq20_secondary_addendum",
                                "source_url":complementary["source_url"],
                                "evidence_date":pilot["checked_at"],
                                "minimum_oneway_min":complementary["observed_minutes"]})
            fastest_source=(original["source_url"] if original["minimum_oneway_min"] is not None else
                            complementary["source_url"] if complementary else None)
            result={"base_id":base,"destination_id":dest,"base_name":LABELS[base],
                    "destination_name":LABELS[dest],"station_to_station_fastest_min":known,
                    "representative_min":(complementary["average_minutes"] if complementary else
                                          original["typical_oneway_min"]),
                    "representative_basis":"different_dated_sample" if complementary else "canonical_only",
                    "transfers_in_example":complementary["example_transfers"] if complementary else original["transfers"],
                    "fare_eur_person_oneway":None,
                    "source_url":fastest_source,"source_records":sources,
                    "weekend_outbound_verified":False,"weekend_return_verified":False,
                    "last_mile_verified":False,"door_to_door_min":None,
                    "destination_visit_hours":None,"overnight_confirmed":False,
                    "reference_period":"2026 samples; not a 2027 timetable",
                    "missing":["weekend_outbound","weekend_return","first_last_mile",
                               "door_to_door","date_specific_2027","fare_condition"],
                    "feasibility":classify_feasibility(oneway_min=known)}
            results.append(result)
    return results

def combined_brussels_bruges(pilot:dict|None=None)->dict:
    pilot=load_pilot() if pilot is None else pilot
    bridge=pilot["links_between_destinations"][0]
    if (canonical_place(bridge["origin_id"]),canonical_place(bridge["destination_id"]))!=("brussels","bruges_be"):
        raise ValueError("Trecho de conexão inválido")
    return {"itinerary":["brussels","bruges_be"],"between_cities_min":bridge["typical_minutes"],
            "between_cities_verified_on_weekends":True,"source_url":bridge["source_url"],
            "full_weekend_verified_from_base":False,"return_to_base_verified":False,
            "overnight_required":None,
            "missing":["base_to_brussels_weekend","bruges_to_base_return",
                       "local_transport","accommodation_if_overnight"],
            "conclusion":"Ligação Bruxelas–Bruges comprovada; roteiro completo ainda não comprovado."}

def illustrative_weekends(count:int=8)->list[dict]:
    if count not in (8,9):raise ValueError("Comparação ilustrativa para oito ou nove fins de semana")
    themes=[
        ("Descanso e reconhecimento da base",[],"descanso"),
        ("Luxemburgo — investigar retorno",["luxembourg_city"],"a_verificar"),
        ("Interlaken — possível pernoite",["interlaken"],"a_verificar"),
        ("Rotina local e descanso",[],"descanso"),
        ("Bruxelas + Bruges — investigar pernoite",["brussels","bruges_be"],"a_verificar"),
        ("Passeios curtos próximos à base",[],"livre"),
        ("Rotterdam — investigar viagem longa",["rotterdam"],"a_verificar"),
        ("Fim de semana livre",[],"descanso")]
    if count==9:themes.append(("Reserva para imprevistos",[],"reserva"))
    return [{"index":i+1,"theme":t,"destinations":places,"status":status,
             "dates_assigned":False,"travel_total_minutes":None,
             "overnight_confirmed":False}
            for i,(t,places,status) in enumerate(themes)]
