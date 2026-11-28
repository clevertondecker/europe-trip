"""Source-backed tourism research overlays, never a second attraction catalog."""
from __future__ import annotations

from evidence_validation import is_https_url

from copy import deepcopy
from datetime import date, datetime, timedelta, time, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from pathlib import Path
import json

from ux501_destination_discovery_model import build_destination_discovery

DATA = Path(__file__).resolve().parent / "data/tourism_visit_evidence_pilot_2026_11.json"


def _mins(clock):
    if clock == "24:00":
        return 1440
    if not isinstance(clock,str):
        raise ValueError("HH:MM esperado")
    try:
        t = datetime.strptime(clock,"%H:%M")
    except ValueError as exc:
        raise ValueError("HH:MM inválido") from exc
    return t.hour*60+t.minute


def validate_opening_schedule(schedule: dict):
    """Structured, explicitly dated research; source text stays untouched."""
    if not isinstance(schedule,dict):
        raise ValueError("Horário estruturado inválido")
    x=deepcopy(schedule)
    if x.get("state") not in ("unknown","partial","historical","verified_current_rule"):
        raise ValueError("Estado de horário inválido")
    if not is_https_url(x.get("source_url")):
        raise ValueError("Horário sem fonte")
    date.fromisoformat(x["checked_at"])
    try:
        ZoneInfo(x["timezone"])
    except (KeyError,TypeError,ZoneInfoNotFoundError) as exc:
        raise ValueError("Fuso IANA obrigatório") from exc
    weekly=x.get("weekly_intervals",{})
    if not isinstance(weekly,dict) or any(k not in {str(i) for i in range(7)} for k in weekly):
        raise ValueError("Dia da semana inválido")
    def verify(spans):
        if not isinstance(spans,list):
            raise ValueError("Janelas devem ser lista")
        pairs=[]
        for span in spans:
            a,b=_mins(span["open"]),_mins(span["close"])
            if not 0<=a<b<=1440:
                raise ValueError("Intervalo inválido")
            pairs.append((a,b))
        pairs.sort()
        if any(pairs[i][0]<pairs[i-1][1] for i in range(1,len(pairs))):
            raise ValueError("Janelas sobrepostas")
    for spans in weekly.values():
        verify(spans)
    seen=set()
    for e in x.get("exceptions",[]):
        day=date.fromisoformat(e["date"])
        if day in seen or e.get("state") not in ("closed","open","unknown"):
            raise ValueError("Exceção duplicada ou inválida")
        seen.add(day)
        verify(e.get("intervals",[]))
        if e["state"]=="closed" and e.get("intervals"):
            raise ValueError("Fechamento não pode conter horários de abertura")
    validity=x.get("validity",{})
    for key in ("from","until"):
        if validity.get(key):
            date.fromisoformat(validity[key])
    if validity.get("from") and validity.get("until") and validity["from"]>validity["until"]:
        raise ValueError("Validade invertida")
    for season in x.get("seasons",[]):
        date.fromisoformat("2028-"+season["from_month_day"])
        date.fromisoformat("2028-"+season["until_month_day"])
    return x


def evaluate_visit_window(schedule, *, earliest_start, latest_end, duration_min):
    """Historical clock fit, NEVER proof that the attraction opens in 2027."""
    s=validate_opening_schedule(schedule)
    if (not isinstance(earliest_start,datetime) or
        not isinstance(latest_end,datetime) or
        earliest_start.tzinfo is None or latest_end.tzinfo is None or
        type(duration_min) is not int or duration_min<=0):
        raise ValueError("Visita exige instantes UTC-aware e minutos positivos")
    start=earliest_start.astimezone(timezone.utc)
    finish=latest_end.astimezone(timezone.utc)
    def result(state,**extra):
        return {"status":state,"start":None,"end":None,
                "verified_for_date":False,**extra}
    if start+timedelta(minutes=duration_min)>finish:
        return result("insufficient_visit_time")
    zone=ZoneInfo(s["timezone"])
    first=start.astimezone(zone).date()
    last=finish.astimezone(zone).date()
    if (last-first).days>3:
        return result("window_too_broad")
    uncertain=False
    closed=False
    for k in range((last-first).days+1):
        d=first+timedelta(days=k)
        iso=d.isoformat()
        valid=s.get("validity",{})
        if (valid.get("from") and iso<valid["from"] or
            valid.get("until") and iso>valid["until"]):
            uncertain=True
            continue
        mmdd=d.strftime("%m-%d")
        seasons=s.get("seasons",[])
        if any(not ((t["from_month_day"]<=mmdd<=t["until_month_day"])
                     if t["from_month_day"]<=t["until_month_day"]
                     else (mmdd>=t["from_month_day"] or mmdd<=t["until_month_day"]))
               for t in seasons):
            uncertain=True
            continue
        e=next((x for x in s.get("exceptions",[]) if x["date"]==iso),None)
        if e and e["state"]=="closed":
            closed=True
            continue
        if e and e["state"]=="unknown":
            uncertain=True
            continue
        spans=e.get("intervals",[]) if e else s.get("weekly_intervals",{}).get(str(d.weekday()))
        if spans is None:
            uncertain=True
            continue
        if not spans:
            closed=True
            continue
        midnight=datetime.combine(d,time.min,tzinfo=zone)
        tomorrow=datetime.combine(d+timedelta(days=1),time.min,tzinfo=zone)
        for interval in spans:
            a,b=_mins(interval["open"]),_mins(interval["close"])
            open_at=(midnight+timedelta(minutes=a)).astimezone(timezone.utc)
            close_at=(tomorrow if b==1440 else midnight+timedelta(minutes=b)).astimezone(timezone.utc)
            begin=max(start,open_at)
            end=begin+timedelta(minutes=duration_min)
            if end<=min(close_at,finish):
                return {"status":"historical_window_compatible",
                        "start":begin,"end":end,
                        "verified_for_date":False,"temporal_scope":s["state"]}
    return result("opening_not_fully_documented" if uncertain else
                  "closed_on_date" if closed else "closed_or_insufficient_window")


def load_visit_evidence(path=DATA, *, discovery=None):
    doc = json.loads(Path(path).read_text(encoding="utf-8"))
    if doc.get("schema_version") != 1 or doc.get("scope") != (
        "historical_operator_read_only_2027_not_guaranteed"):
        raise ValueError("Escopo do overlay incompatível")
    date.fromisoformat(doc["checked_at"])
    discovery = discovery if discovery is not None else build_destination_discovery()
    lookup = {x["id"]: d["id"] for d in discovery["destinations"]
              for x in d["attractions"]}
    seen = set()
    for row in doc.get("entries", []):
        aid = row["attraction_id"]
        if aid in seen or aid not in lookup or lookup[aid] != row["destination_id"]:
            raise ValueError("Atração duplicada ou identidade de destino inválida")
        seen.add(aid)
        date.fromisoformat(row["checked_at"])
        if not (is_https_url(row.get("source_url")) and
                is_https_url(row.get("address_source_url"))):
            raise ValueError("Pesquisa sem fonte oficial URL HTTPS")
        if not row.get("experience_reason") or not row.get("address"):
            raise ValueError("Identidade/experiência insuficiente")
        if row.get("opening_state") != "verified_current_rule" or not row.get("opening_rule"):
            raise ValueError("Horário genérico não fundamentado")
        if row.get("opening_schedule") is not None:
            validate_opening_schedule(row["opening_schedule"])
        ticket = row["entry_ticket"]
        if ticket["status"] == "free_public_entry":
            if ticket.get("amount") != 0:
                raise ValueError("Ingresso externo gratuito exige valor zero")
        elif ticket["status"] == "unknown":
            if ticket.get("amount") is not None:
                raise ValueError("Ingresso não verificado não pode ter preço")
        else:
            raise ValueError("Estado do ingresso inválido")
        if row.get("additional_activity"):
            additional = row["additional_activity"]
            if (type(additional["amount"]) not in (int, float)
                    or additional["amount"] <= 0 or
                    not is_https_url(additional["source_url"])):
                raise ValueError("Atividade adicional sem fonte/preço positivo")
            if additional.get("valid_for_2027") is not False:
                raise ValueError("Tarifa adicional futura não pesquisada")
        if (row.get("valid_for_2027") is not False or
                row.get("station_to_attraction_min") is not None or
                ticket.get("valid_for_2027") is not False):
            raise ValueError("Horários/tarifas atuais não garantem 2027/última milha")
    return deepcopy(doc)


def visit_decision_overview(*, discovery=None):
    data = load_visit_evidence(discovery=discovery)
    return {
        "entries": data["entries"], "pilot_count": len(data["entries"]),
        "2027_date_specific_opening_confirmed": 0,
        "door_to_door_verified": 0,
        "catalog_mutated": False, "wishlist_mutated": False,
    }
