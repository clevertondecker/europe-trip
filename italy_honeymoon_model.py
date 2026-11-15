"""Italy honeymoon candidates: pure, audited and read-only relative to TripPlan.

No booking, no official itinerary modification and no 2027 availability claims.
"""
from __future__ import annotations

from decimal import Decimal,InvalidOperation
from pathlib import Path
import json

FILE=Path(__file__).resolve().parent/"data"/"italy_honeymoon_research_2027.json"
UNITS={"person_oneway":1,"person_each_way":2,"person_roundtrip":1,
       "person_ticket":1}


def load_honeymoon(path:Path=FILE)->dict:
    payload=json.loads(path.read_text(encoding="utf-8"))
    if payload["schema_version"]!=1 or payload["wedding_date"]!="2027-09-04":
        raise ValueError("Roteiro italiano incompatível")
    ids=[x["id"] for x in payload["prices"]]
    if len(ids)!=len(set(ids)):raise ValueError("Referência duplicada")
    for price in payload["prices"]:
        if (price["unit"] not in UNITS or price["eur_per_person"]<=0 or
                price["valid_for_2027"] is not False or
                not price["source_url"].startswith("https://")):
            raise ValueError("Tarifa histórica inválida ou sem fonte")
    scenarios=payload["scenarios"]
    if {x["id"] for x in scenarios}!={"balanced","economy","experience"}:
        raise ValueError("Três propostas obrigatórias")
    for s in scenarios:
        if (s["days"]!=10 or s["nights"]!=9 or
                s["rome_nights"]+s["coast_nights"]+s["naples_nights"]!=9 or
                len(s["days_detail"])!=10 or not 1<=s["coast_nights"]<=6):
            raise ValueError("Dias e noites não conciliados")
        if len(s["key_paid_refs"])!=len(set(s["key_paid_refs"])) or not set(s["key_paid_refs"])<=set(ids):
            raise ValueError("Referências de custos inválidas")
    if len({b["id"] for b in payload["coast_bases"]})!=len(payload["coast_bases"]):
        raise ValueError("Bases duplicadas")
    if any(b["hotel_five_nights_eur"] is not None for b in payload["coast_bases"]):
        raise ValueError("Não cotar hotel sem preço válido para a data")
    return payload


def preview_nights(scenario:dict,extra_night:bool=False)->dict:
    """Nine nights means 10 calendar days, ten nights means 11 in this proposal."""
    return {"rome":scenario["rome_nights"],
            "coast":scenario["coast_nights"]+int(extra_night),
            "naples":scenario["naples_nights"],
            "nights":scenario["nights"]+int(extra_night),
            "calendar_days":scenario["days"]+int(extra_night),
            "requires_official_italy_days_change":bool(extra_night)}


def ticket_sample(payload:dict,scenario_id:str,travelers:int=2)->dict:
    """Selected distinct *2026 ticket samples*, not all costs of the holiday."""
    if type(travelers) is not int or travelers<1:raise ValueError("Invalid party size")
    s=next((x for x in payload["scenarios"] if x["id"]==scenario_id),None)
    if s is None:raise ValueError("Cenário desconhecido")
    prices={x["id"]:x for x in payload["prices"]}
    items=[]
    for key in s["key_paid_refs"]:
        p=prices[key]
        subtotal=Decimal(str(p["eur_per_person"]))*UNITS[p["unit"]]*travelers
        items.append({"id":p["id"],"name":p["name"],
                      "couple_sample_eur":float(subtotal),
                      "status":p["status"],"url":p["source_url"],
                      "notes":p["notes"],"unit":p["unit"]})
    total=sum(Decimal(str(x["couple_sample_eur"])) for x in items)
    return {"scenario_id":scenario_id,"known_sample_subtotal_eur":float(total),
            "items":items,"is_complete_cost":False,
            "ticket_prices_valid_for_2027":False,
            "missing":[
                "Hospedagem Roma e costa", "Todas as refeições e cafés",
                "Transporte urbano, bagagens e acesso ao hotel",
                "Transporte terrestre alternativo a ferries",
                "Transfer até aeroporto de Nápoles",
                "Voos Itália–França e internacional já em verba aérea",
                "Ferry e ingressos opcionais, previsões e taxas não cotadas"
            ]}


def optional_comparison(payload:dict)->list[dict]:
    p={r["id"]:r for r in payload["prices"]}
    def total(x:str,legs:int=1)->float:
        row=p[x]
        return float(Decimal(str(row["eur_per_person"]))*2*UNITS[row["unit"]]*legs)
    return [
        {"id":"capri_from_amalfi","title":"Capri via Amalfi, NLG, ida+volta",
         "known_ticket_reference_eur":total("amalfi_capri_rt")+total("capri_landing"),
         "extra_needed":"Transfer até Amalfi, passeio terrestre em Capri, alimentação, mar calmo, último retorno e 2027"},
        {"id":"capri_from_maiori","title":"Capri via Maiori, NLG, ida+volta",
         "known_ticket_reference_eur":total("maiori_capri_rt")+total("capri_landing"),
         "extra_needed":"Viagem de 2026 até 30/09; troca em Amalfi, passeio terrestre, 2027 e clima"},
        {"id":"pompeii","title":"Pompeia Express para dois",
         "known_ticket_reference_eur":total("pompeii_express"),
         "extra_needed":"Trem/ônibus, último horário, guia, bagagens e tempo do passeio"},
    ]


def manual_italy_cost(payload:dict,scenario_id:str,values:dict,
                      eurfx:float,extra_night:bool=False)->dict:
    """Only for a user-supplied Italian-period sensitivity; not global total."""
    try:
        rate=Decimal(str(eurfx))
        if not rate.is_finite() or rate<=0:raise ValueError()
    except (InvalidOperation,TypeError,ValueError):
        raise ValueError("Câmbio inválido")
    scenario=next((x for x in payload["scenarios"] if x["id"]==scenario_id),None)
    if not scenario:raise ValueError("Cenário inválido")
    sample=ticket_sample(payload,scenario_id)
    categories=("rome_hotel_night","coast_hotel_night",
                "naples_hotel_night","food_couple_per_day",
                "extra_local_transport","additional_admissions")
    user={}
    missing=[]
    for key in categories:
        if key=="naples_hotel_night" and scenario["naples_nights"]==0:
            continue
        v=values.get(key)
        if v is None:
            missing.append(key)
            user[key]=None
            continue
        try:amt=Decimal(str(v))
        except (InvalidOperation,TypeError,ValueError) as exc:
            raise ValueError("Despesa manual inválida") from exc
        if not amt.is_finite() or amt<0:raise ValueError("Despesa manual inválida")
        user[key]=amt
    # Explicitly entered zero is a real value; None means unknown.
    weights={"rome_hotel_night":scenario["rome_nights"],
             "coast_hotel_night":scenario["coast_nights"]+int(extra_night),
             "naples_hotel_night":scenario["naples_nights"],
             "food_couple_per_day":scenario["days"]+int(extra_night),
             "extra_local_transport":1,"additional_admissions":1}
    other=sum((amount*weights[key] for key,amount in user.items()
               if amount is not None),Decimal(0))
    subtotal=other+Decimal(str(sample["known_sample_subtotal_eur"]))
    return {"status":"complete_user_inputs_not_full_trip" if not missing else "partial",
            "missing_manual_inputs":missing,
            "known_tickets_eur":sample["known_sample_subtotal_eur"],
            "manual_plus_known_reference_eur":round(float(subtotal),2),
            "illustrative_italy_total_eur":round(float(subtotal),2) if not missing else None,
            "illustrative_italy_total_brl":round(float(subtotal*rate),2) if not missing else None,
            "global_budget_unchanged":True,
            "flight_double_count_prevented":True,
            "complete_2027_quote":False,
            "extra_night_included":bool(extra_night),
            "other_missing":sample["missing"]}
