"""REC05: deterministic research *worklist*, not a city ranking or trip planner.

Uses only REC02's confirmed scope, raw REC01 provenance and optional UX506 /
REC04 capability projections. Unknown never means impossible or zero.
"""
from __future__ import annotations
from copy import deepcopy
from datetime import date
import json
from urllib.parse import urlparse

POLICY_VERSION="rec05-prioritized-evidence-v1"
STATES=frozenset(("comparable","partial_evidence","insufficient_evidence"))
CATEGORIES=frozenset(("historical","reference_only","local","no_time"))
LEVELS={"must_visit":0,"housing":1,"interested":2,"maybe":3}
KINDS={
    "outbound_minimum":(0,"Operador ferroviário, trecho dirigido e data",
                        "Mínimo de ida e identidade de estações ainda não documentados"),
    "urban_access":(1,"Transporte urbano e acesso local oficial",
                    "Deslocamento urbano e acesso ao passeio não confirmados"),
    "comparable_service":(2,"Serviço ferroviário com estações/dia definidos",
                          "Há apenas referência indicativa, não trajeto historicamente comparável"),
    "weekend_return":(3,"Operador ferroviário, serviço de volta na data pretendida",
                      "Ida documentada não confirma volta nem janela horária"),
    "last_mile":(4,"Fonte oficial de acesso à atração e retorno à estação",
                 "Última milha de ida e volta não confirmada"),
    "fare_2027":(5,"Operador, tarifa e condições para os dois viajantes",
                 "Tarifa total para o casal em 2027 não confirmada"),
    "frequency_2027":(6,"Operador e frequência do serviço na data pretendida",
                      "Frequência e composição de serviços para 2027 desconhecidas"),
    "source_trace":(7,"Fonte oficial datada e identidade do par",
                    "Falta URL verificável para a observação"),
    "housing_quote":(8,"Hospedagem mobiliada nas datas e condições iguais",
                     "Aluguel, internet, taxas e caução da estadia de 2027 não cotados"),
    "housing_internet":(9,"Anúncio/contrato mobiliado e internet para trabalho remoto",
                        "Internet, posto de trabalho e acesso à estação não confirmados"),
}


def _source(value):
    if not isinstance(value,str):
        return None
    url=urlparse(value)
    return value if url.scheme=="https" and url.netloc else None


def _housing_status(readiness,base_id):
    if not isinstance(readiness,dict):
        return None
    return next((r for r in readiness.get("base_housing",[])
                 if r.get("base_id")==base_id),None)


def _journey_status(readiness,base_id,destination_id):
    if not isinstance(readiness,dict):
        return None
    return next((r for r in readiness.get("journeys",[])
                 if r.get("base_id")==base_id and
                    r.get("destination_id")==destination_id),None)


def prioritize_research(recommendation, *, base_ids=None, capabilities=None,
                        readiness=None, limit=None):
    """Pure O(B*D) worklist, bounded by explicit selected bases.

    limit affects presentation only; total_count is the entire selected scope.
    No network requests, geocoding, guessed fares or mutable session state.
    """
    if limit is not None and (type(limit) is not int or limit<1):
        raise ValueError("Limite inválido")
    if not isinstance(recommendation,dict) or recommendation.get("state") not in STATES:
        return {"policy_version":POLICY_VERSION,"state":"scope_required","tasks":[],
                "total_count":0,"base_ids":[],"destination_ids":[],"read_only":True}
    if not str(recommendation.get("policy_version","")).startswith("rec02-"):
        raise ValueError("Política REC02 incompatível")
    destinations=recommendation["destinations"]
    candidates=recommendation["candidates"]
    ids={d["id"] for d in destinations}
    bases={c["base_id"]:c for c in candidates}
    if (not ids or len(ids)!=len(destinations) or
            len(bases)!=len(candidates) or not bases or
            any(d.get("priority") not in ("must_visit","interested","maybe")
                for d in destinations)):
        raise ValueError("Escopo ou candidatas inconsistentes")
    if base_ids is None:
        highlights=sorted(b for b in recommendation.get("highlight_ids",[])
                          if b in bases)
        chosen=highlights[:5] if highlights else sorted(bases)[:3]
    else:
        if (not isinstance(base_ids,list) or not base_ids
                or len(set(base_ids))!=len(base_ids)
                or any(b not in bases for b in base_ids)):
            raise ValueError("Cidades selecionadas inválidas")
        chosen=sorted(base_ids)
    by_id={d["id"]:d for d in destinations}
    incomplete=not bool(recommendation.get("complete_groups"))
    queue={}

    def append(base,dest,kind,priority,*,source_url=None,checked_at=None,blocking=False):
        key=(base,dest,kind)
        if key in queue:
            return
        reason=KINDS[kind][2]
        if priority=="must_visit" and blocking:
            reason+=" · Destino imperdível impede uma comparação de escopo completo"
        queue[key]={
            "base_id":base,"destination_id":dest,
            "evidence_type":kind,
            "priority":priority,
            "blocks_complete_comparison":bool(blocking),
            "reason":reason,
            "expected_source":KINDS[kind][1],
            "source_url":_source(source_url),
            "source_checked_at":checked_at if isinstance(checked_at,str) and checked_at else None,
            "direction":base+" → "+(dest or "moradia local"),
            "status":"pending_research",
        }

    for base in chosen:
        c=bases[base]
        cells=c["evidence"]
        if set(cells)!=ids:
            raise ValueError("Matriz de evidências incompleta")
        raw_rows=c.get("raw_rail_evidence",{})
        if not isinstance(raw_rows,dict):
            raise ValueError("Proveniência inválida")
        housing=_housing_status(readiness,base)
        cap=(capabilities or {}).get(base,{})
        if (cap.get("rental_quote_2027_available") is not True and
                not (housing and housing.get("verified_56_to_60_night_quotes_2027",0)>0)):
            append(base,None,"housing_quote","housing")
        if not housing or not housing.get("work_space_verified",False) or not housing.get("station_access_verified",False):
            append(base,None,"housing_internet","housing")
        for dest in sorted(ids):
            d=by_id[dest]
            cell=cells[dest]
            category=cell.get("category")
            if category not in CATEGORIES:
                raise ValueError("Categoria REC01 inválida")
            raw=raw_rows.get(dest,{})
            source_url=cell.get("source_url") or raw.get("source_url")
            checked_at=(cell.get("gap_checked_at") or cell.get("source_date") or
                        raw.get("evidence_date") or raw.get("retrieved_at"))
            priority=d["priority"]
            blocking=bool(incomplete and priority=="must_visit" and category=="no_time")
            if category=="no_time":
                append(base,dest,"outbound_minimum",priority,source_url=source_url,
                       checked_at=checked_at,blocking=blocking)
                continue
            if category=="local":
                append(base,dest,"urban_access",priority,source_url=source_url,
                       checked_at=checked_at)
                continue
            if category=="reference_only":
                append(base,dest,"comparable_service",priority,source_url=source_url,
                       checked_at=checked_at)
            journey=_journey_status(readiness,base,dest)
            if not journey or journey.get("weekend_return_verified") is not True:
                append(base,dest,"weekend_return",priority,source_url=source_url,
                       checked_at=checked_at)
            if not journey or journey.get("last_mile_verified") is not True:
                append(base,dest,"last_mile",priority,source_url=source_url,
                       checked_at=checked_at)
            append(base,dest,"fare_2027",priority,source_url=source_url,
                   checked_at=checked_at)
            append(base,dest,"frequency_2027",priority,source_url=source_url,
                   checked_at=checked_at)
            if not _source(source_url):
                append(base,dest,"source_trace",priority)
    ordered=sorted(queue.values(),key=lambda t:(
        LEVELS[t["priority"]],0 if t["blocks_complete_comparison"] else 1,
        KINDS[t["evidence_type"]][0],t["base_id"],t["destination_id"] or ""))
    return {"policy_version":POLICY_VERSION,"state":"ready",
            "base_ids":chosen,"destination_ids":sorted(ids),
            "tasks":deepcopy(ordered if limit is None else ordered[:limit]),
            "total_count":len(ordered),"read_only":True,
            "claims_feasibility_2027":False,
            "method":"Urgência editorial por prioridade declarada, lacuna e tipo; "
                     "não estima probabilidades, qualidade ou custo das cidades."}


def export_research_plan(queue, *, exported_at=None):
    """Manual export contains public IDs, evidence type, sources and conditions only."""
    if queue.get("state")!="ready":
        raise ValueError("A pesquisa precisa de escopo válido")
    when=exported_at or date.today().isoformat()
    date.fromisoformat(when)
    safe=("base_id","destination_id","evidence_type","priority",
          "blocks_complete_comparison","reason","expected_source",
          "source_url","source_checked_at","direction","status")
    result={
        "policy_version":POLICY_VERSION,"exported_at":when,
        "research_state":"not_performed",
        "base_ids":list(queue["base_ids"]),
        "destination_ids":list(queue["destination_ids"]),
        "items":[{k:row.get(k) for k in safe} for row in queue["tasks"]],
        "limitations":"Lista editorial de pendências; nenhuma fonte revisitada ou "
                      "reserva para 2027 é confirmada.",
    }
    return (json.dumps(result,sort_keys=True,ensure_ascii=False,indent=2)+"\n").encode("utf-8")
