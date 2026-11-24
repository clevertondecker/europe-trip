"""UX124B: small read-only presentation helpers; not a new decision model."""
from __future__ import annotations
from html import escape
import re
from ux124_city_profile_model import TIMED,profile_summary_facts,route_scope,ROUTE_SCOPES
from ux502_destination_interests_model import LABELS
from routes7_comparison_projection import format_minutes

def city_intro(profile):
    """Remove only the known administrative prefix; keep sourced statements."""
    text=profile["summary"].strip()
    text=re.sub(r"^Cidade cadastrada no corredor [^.]+\.\s*","",text,count=1)
    if text.startswith("Pesquisa inicial:"):
        return "Características locais ainda pouco pesquisadas."
    return text

def practical_facts(profile):
    # Put a sourced statement in the strengths block only once. Avoid the
    # administrative lead (and its exact factual suffix), not fuzzy inference.
    intro=city_intro(profile)
    values=[e["summary"] for e in profile_summary_facts(profile)]+profile["advantages"]
    distinct=[]
    for value in values:
        if value==profile["summary"] or value.rstrip(".")==intro.rstrip(".") or value in distinct:
            continue
        distinct.append(value)
    return distinct[:2]

def compact_money(value):
    if value is None:
        return "Não pesquisado"
    text=f"{value:,.2f}".replace(",","_").replace(".",",").replace("_",".")
    return "€ "+(text[:-3] if text.endswith(",00") else text)

def route_display(row):
    """Use canonical label and minutes unchanged; split for visual hierarchy."""
    cell=row["cell"]
    label=cell["label"]
    if cell["category"] in TIMED:
        amount=format_minutes(cell["display_min"])
        if label.startswith("~"):
            amount="~"+amount
        qualifier=label[len(amount):].lstrip(" ·") if label.startswith(amount) else label
    elif cell["category"]=="local":
        amount,qualifier="Local",label
    else:
        amount,qualifier="Sem tempo",label
    return {"name":row["name"],"priority":LABELS.get(row.get("priority"),""),
            "time":amount,"qualifier":qualifier}

def route_preview(routes,limit=5):
    """First desired rows in canonical order, including unknown and local."""
    return route_scope(routes,ROUTE_SCOPES[0])["rows"][:limit]

def route_list_html(rows):
    """Read-only, accessible responsive list. No fake interactive links."""
    def safe(value):
        return escape(str(value),quote=True)
    parts=[]
    for row in rows:
        r=route_display(row)
        priority=f'<small>{safe(r["priority"])}</small>' if r["priority"] else ""
        parts.append('<li><div><strong>'+safe(r["name"])+'</strong>'+priority+
                     '</div><div class="ux124b-route-value"><strong>'+safe(r["time"])+
                     '</strong><small>'+safe(r["qualifier"])+'</small></div></li>')
    return '<ul class="ux124b-routes" aria-label="Referências de ida">'+''.join(parts)+'</ul>'

def observed_label(value):
    return "Não pesquisado" if value is None else str(value)

def ticket_text(ticket):
    if not ticket:
        return "Ingresso não pesquisado"
    amount=ticket.get("amount")
    if amount is None:
        return "Preço não pesquisado" if ticket.get("status")!="not_applicable" else "Ingresso não aplicável à referência"
    units={"adult":"por adulto","person":"por pessoa","adult_return":"por adulto · ida e volta",
           "person_return":"por pessoa · ida e volta","couple":"por casal","group":"por grupo"}
    unit=units.get(ticket.get("per"),str(ticket.get("per") or "modalidade a verificar"))
    return f'{amount:g} {ticket.get("currency") or "moeda a verificar"} · {unit} · {ticket.get("validity") or "validade a verificar"}'
