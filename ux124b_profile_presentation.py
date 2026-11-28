"""UX124B: small read-only presentation helpers; not a new decision model."""
from __future__ import annotations

from formatting import eur
from html import escape
import re
from ux124_city_profile_model import TIMED,profile_summary_facts,route_scope,ROUTE_SCOPES
from ux502_destination_interests_model import LABELS
from routes7_comparison_projection import format_minutes
from five_base_comparison_model import COUNTRY_FLAGS

def city_intro(profile):
    """Remove only the known administrative prefix; keep sourced statements."""
    text=profile["summary"].strip()
    text=re.sub(r"^Cidade cadastrada no corredor [^.]+\.\s*","",text,count=1)
    if text.startswith("Pesquisa inicial:"):
        return "Características locais ainda pouco pesquisadas."
    # Exact paraphrases of existing source sentences; do not infer amenities.
    return {
        "O turismo municipal documenta uma rede de bondes e conexão entre a estação e museus, incluindo o Cité du Train.":
            "Rede de bondes e ligações entre a estação e museus, como o Cité du Train, documentadas pelo turismo municipal.",
        "A ligação ferroviária Metz–Luxembourg inclui exemplos de TER diretos de aproximadamente 53–54 minutos em horários pesquisados de 2026.":
            "Trens TER diretos para Luxemburgo em cerca de 53–54 minutos nos horários pesquisados de 2026.",
        "O escritório de turismo descreve os bairros Grande Île, Petite France, Krutenau e Neustadt como áreas distintas.":
            "Grande Île, Petite France, Krutenau e Neustadt são bairros com características distintas segundo o turismo local.",
    }.get(text,text)

def editorial_risk_text(risk):
    # Historical editorial impressions are not current measured conditions.
    return {
        "Menor vida urbana na matriz editorial":"A avaliação histórica indicava uma vida urbana menos intensa que outras opções estudadas.",
        "Maior custo de aluguel estimado":"A avaliação histórica estimava aluguel mais caro que outras opções estudadas.",
        "Acesso às áreas alpinas menos conveniente":"A avaliação histórica indicava acesso menos conveniente às regiões alpinas.",
        "Menor pontuação editorial de natureza":"A avaliação histórica favorecia outras cidades quanto às opções de natureza.",
    }.get(risk,risk)

def destination_name(row):
    flag=COUNTRY_FLAGS.get(row.get("country"),"")
    return (flag+" " if flag else "")+row["name"]

def logistics_table(rows):
    """Hide a wholly unavailable column only; retain canonical divergences."""
    typical=[typical_time_label(row) for row in rows]
    has_typical=any(value!="Tempo médio não documentado" for value in typical)
    result=[]
    for row,value in zip(rows,typical):
        entry={"Destino":destination_name(row),"Prioridade":LABELS.get(row["priority"],"—"),
               "Tempo de ida":row["cell"]["label"]}
        if has_typical:
            entry["Tempo médio/típico"]=value if value!="Tempo médio não documentado" else "—"
        result.append(entry)
    return result,has_typical

def practical_facts(profile):
    """Conservative editorial selection: no second tourism/transport summary.

    The existing advantages are elaborations of the same introductory
    narrative. Keep them in documentation; surface only sourced independent
    subjects, not a text-similarity heuristic or inferred advantage.
    """
    intro=city_intro(profile)
    lead=[e for e in profile["evidence"] if city_intro({"summary":e["summary"]}).rstrip(".")==intro.rstrip(".")
          or e["summary"]==profile["summary"]]
    occupied={e["section"] for e in lead}
    urls={e.get("source_url") for e in lead}
    # Only complementary practical subjects. Do not relabel an unverified
    # rent/remote-work observation as a benefit, since those have own blocks.
    facts=[]
    for e in profile_summary_facts(profile):
        if (e["section"] not in ("daily_costs","climate") or e["section"] in occupied
                or e.get("source_url") in urls or e["summary"] in (intro,profile["summary"])):
            continue
        if e["summary"] not in facts:
            facts.append(e["summary"])
    return facts[:2]

def typical_time_label(route):
    """Preserve the shared presentation, including reconsulted divergences."""
    label=route["cell"]["typical_label"]
    if label=="Tempo médio não documentado" and route["historical_typical"] is not None:
        return format_minutes(route["historical_typical"])+" · típico histórico"
    return label

def simulation_note(capability):
    if not capability["scenario_selectable"]:
        return "Simulação indisponível para esta cidade."
    return capability["budget_note"]+". Aluguel e caução de 2027 não cotados."

def compact_money(value):
    return eur(value, decimals=2, missing="Não pesquisado", trim_zeros=True)


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
        amount,qualifier="Local",label.removeprefix("Local — ")
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
        flag=COUNTRY_FLAGS.get(row.get("country"),"")
        flag_html=('<span class="ux124c-flag" role="img" aria-label="'+safe(row["country"])+'">'+safe(flag)+'</span> ') if flag else ""
        parts.append('<li><div><strong>'+flag_html+safe(r["name"])+'</strong>'+priority+
                     '</div><div class="ux124b-route-value"><strong>'+safe(r["time"])+
                     '</strong><small>'+safe(r["qualifier"])+'</small></div></li>')
    return '<ul class="ux124b-routes" aria-label="Referências de ida">'+''.join(parts)+'</ul>'

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
