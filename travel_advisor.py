"""Deterministic risk analysis and evidence-aware advice, no AI provider."""
from __future__ import annotations
from decimal import Decimal
from attractions_model import package_cost,route_for

def _risk(code,severity,message,affected,source="",resolution=""):
    return {"code":code,"severity":severity,"message":message,
            "affected":affected,"source":source,"resolution":resolution}

def assess_plan(plan,attractions,routes,budget=None):
    """Return actionable, deduplicated risks with provenance."""
    entries=[]
    base=plan["base_city"]
    dest_index={d["id"]:d for d in attractions["destinations"]}
    for dest,ids in plan["packages"].items():
        r=route_for(routes,base,dest)
        source=r["source_url"]
        if r["train_minutes_one_way"] is None and dest!=base:
            entries.append(_risk("ROUTE_UNKNOWN","WARNING",
                "Tempo e trajeto ferroviário não verificados",dest,source,
                "Pesquisar conexões, bilhetes e último retorno"))
        elif r["train_minutes_one_way"] is not None:
            if r["train_minutes_one_way"]>150:
                entries.append(_risk("LONG_TRAVEL","WARNING",
                    "Trecho ferroviário superior a 2h30; avaliar pernoite",dest,source,
                    "Comparar uma noite na região"))
            elif r["train_minutes_one_way"]>60:
                entries.append(_risk("MODERATE_TRAVEL","INFO",
                    "Deslocamento exige planejamento de dia inteiro",dest,source,
                    "Verificar tempos porta a porta"))
        if dest!=base and not r["weekend_return_verified"]:
            entries.append(_risk("RETURN_UNVERIFIED","WARNING",
                "Último retorno e serviço de fim de semana não confirmados",dest,source,
                "Consultar grade para data específica"))
        if r["fare_type"]=="discount_carte_fluo":
            entries.append(_risk("DISCOUNT_CONDITIONAL","INFO",
                "Tarifa depende de condições Carte Fluo ainda não comprovadas",dest,source,
                "Verificar elegibilidade e preço regular"))
        if dest_index[dest]["kind"]=="overnight":
            entries.append(_risk("OVERNIGHT","WARNING",
                "Região alpina: pernoite pode ser necessário",dest,dest_index[dest]["source_url"],
                "Comparar hotel e trem completo antes de aprovar"))
    known=package_cost(attractions,routes,base,
       [x for ids in plan["packages"].values() for x in ids])
    if known["missing"]:
        entries.append(_risk("MISSING_PRICES","WARNING",
            f"{len(known['missing'])} componentes sem preço completo","budget","",
            "Não considerar subtotal conhecido como custo completo"))
    if budget and budget["margin"]<0:
        entries.append(_risk("OVER_BUDGET","CRITICAL",
            "Cenário financeiro ultrapassa o teto","budget","",
            "Reduzir gastos ou rever escolhas"))
    elif budget and budget["margin"]<budget["cap"]*Decimal("0.05"):
        entries.append(_risk("LOW_MARGIN","WARNING",
            "Margem adicional inferior a 5%","budget","",
            "Manter reserva de contingência protegida"))
    return entries

def recommendations(plan,attractions,routes,risks):
    """Explanations are templates grounded in concrete rule firings."""
    output=[]
    for r in risks:
        key=r["code"]+":"+r["affected"]
        output.append({"id":key,"severity":r["severity"],
            "title":r["message"],"reason":r["resolution"],
            "evidence":r["source"],"destination":r["affected"],
            "status":"proposed","auto_apply":False})
    # Long unknown Alpine excursions can be compared with published nearby rail.
    if any(x["code"]=="OVERNIGHT" for x in risks):
        nearby=[]
        for dest in ("colmar","strasbourg","nancy","metz","basel"):
            if dest==plan["base_city"] or dest in plan.get("excluded_destinations",[]):continue
            rr=route_for(routes,plan["base_city"],dest)
            if rr["train_minutes_one_way"] is not None and rr["train_minutes_one_way"]<=70:
                nearby.append(dest)
        if nearby:
            output.append({"id":"ALTERNATIVES:NEARBY","severity":"INFO",
                "title":"Há passeios próximos com trem pesquisado: "+", ".join(nearby),
                "reason":"Alternativas não substituem automaticamente atrações prioritárias; custos completos ainda não confirmados",
                "evidence":"data/base_destination_routes_2027.json",
                "destination":nearby[0],"status":"proposed","auto_apply":False})
    return output

def objective_weights(profile):
    if profile=="balanced":return {"interest":35,"cost":25,"comfort":25,"schedule":15}
    if profile=="economy":return {"interest":20,"cost":45,"comfort":20,"schedule":15}
    if profile=="experience":return {"interest":50,"cost":15,"comfort":15,"schedule":20}
    raise ValueError("Unknown profile")
