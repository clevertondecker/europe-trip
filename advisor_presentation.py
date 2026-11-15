"""Human-readable, source-backed advice. Presentation only, no LLM."""
from __future__ import annotations
from collections import OrderedDict

SEVERITY_ORDER={"BLOCKER":0,"CRITICAL":1,"WARNING":2,"INFO":3}
CATEGORY={
    "OVER_BUDGET":"Orçamento","LOW_MARGIN":"Orçamento","MISSING_PRICES":"Orçamento",
    "ROUTE_UNKNOWN":"Transporte","RETURN_UNVERIFIED":"Transporte",
    "LONG_TRAVEL":"Conforto","MODERATE_TRAVEL":"Conforto","OVERNIGHT":"Conforto",
    "DISCOUNT_CONDITIONAL":"Bilhetes"}
TITLES={
    "OVER_BUDGET":"O planejamento ultrapassou o orçamento",
    "LOW_MARGIN":"A margem financeira está apertada",
    "MISSING_PRICES":"Alguns valores ainda precisam de pesquisa",
    "ROUTE_UNKNOWN":"Ainda não sabemos o trajeto completo",
    "RETURN_UNVERIFIED":"Confira como voltar no fim do passeio",
    "LONG_TRAVEL":"Talvez valha a pena pernoitar",
    "MODERATE_TRAVEL":"Reserve um dia inteiro para este passeio",
    "OVERNIGHT":"Uma noite fora pode tornar a viagem mais confortável",
    "DISCOUNT_CONDITIONAL":"Confirme as condições do desconto"}
INTRO={
    "OVER_BUDGET":"O valor projetado supera o teto escolhido.",
    "LOW_MARGIN":"Há pouca margem para despesas inesperadas.",
    "MISSING_PRICES":"Faltam tarifas ou ingressos; o total conhecido não é o custo completo.",
    "ROUTE_UNKNOWN":"Sem os horários completos, ainda não é seguro encaixar este passeio.",
    "RETURN_UNVERIFIED":"Ainda falta confirmar o último retorno para a cidade-base.",
    "LONG_TRAVEL":"O tempo conhecido no trem já é longo, sem contar acesso às estações.",
    "MODERATE_TRAVEL":"O deslocamento requer mais tempo do que um passeio local.",
    "OVERNIGHT":"A logística dos Alpes pode precisar de hospedagem adicional.",
    "DISCOUNT_CONDITIONAL":"A tarifa observada depende de condições que precisam ser confirmadas."}

def present_risks(risks:list[dict],names:dict[str,str]|None=None)->list[dict]:
    """Group exact duplicates; never hide unique destination-specific warnings."""
    names=names or {}
    unique=OrderedDict()
    for r in risks:
        code=r["code"]
        item=r.get("affected","")
        identity=(code,item)
        if identity in unique:continue
        destination=names.get(item,item if item!="budget" else "Planejamento geral")
        unique[identity]={
            "id":code+":"+item,
            "category":CATEGORY.get(code,"Planejamento"),
            "severity":r["severity"],
            "title":TITLES.get(code,r["message"]),
            "summary":INTRO.get(code,r["message"]),
            "destination":destination,
            "suggestion":r.get("resolution") or "Consulte as informações faltantes",
            "source":r.get("source",""),
            "known_impact":None,
            "confidence":"parcial" if r["code"] in {
                "MISSING_PRICES","ROUTE_UNKNOWN","RETURN_UNVERIFIED","OVERNIGHT"} else "condicional"
        }
    return sorted(unique.values(),key=lambda x:(
        SEVERITY_ORDER.get(x["severity"],9),x["category"],x["destination"]))

def proposal_comparison(plan:dict,proposal:dict,cost_before:dict|None=None)->dict:
    """A calendar-only rearrangement has no demonstrated cash savings."""
    old=plan.get("assignments",{})
    new=proposal.get("assignments",{})
    changed=[{"date":day,"destination":dest} for day,dest in sorted(new.items())
             if old.get(day)!=dest]
    unresolved=list(proposal.get("unresolved",[]))
    return {"existing_count":len(old),"proposed_count":len(new),
            "added":changed,
            "unresolved":unresolved,
            "unresolved_count":len(unresolved),
            "known_cost_before":None if cost_before is None else cost_before.get("known_by_currency"),
            "known_cost_after":None if cost_before is None else cost_before.get("known_by_currency"),
            "cost_difference_verified":None,
            "claim":"Mudamos apenas datas. Não há economia confirmada por esta simulação.",
            "can_apply":bool(changed)}

def simple_next_step(plan:dict,risk_cards:list[dict])->str:
    if not plan.get("packages"):
        return "Comece escolhendo atrações em Explorar atrações."
    if not plan.get("assignments"):
        return "Monte seu calendário e compare sugestões antes de aceitar."
    if risk_cards:
        return "Confira os alertas importantes antes de reservar."
    return "Revise as fontes e confirme datas e preços antes de reservar."
