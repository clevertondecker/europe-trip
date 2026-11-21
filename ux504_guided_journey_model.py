"""UX 5.0.4 — read-only projection of the real planning journey.

No additional authoritative progress state; no inference of finalized bases,
confirmed costs, bookings, or comparisons simply from visiting a page.
"""
from __future__ import annotations

from itinerary_flow_model import UNASSIGNED

STEPS = (
    ("discover", "Descobrir lugares",
     "Conhecer destinos e atrações antes de escolher onde ficar",
     "Explorar", "Passeios", "Descobrir lugares"),
    ("wishlist", "Minha lista",
     "Priorizar lugares que queremos conhecer",
     "Explorar", "Passeios", "Minha lista"),
    ("compare", "Comparar cidades-base",
     "Investigar a logística da mesma seleção em diferentes bases",
     "Explorar", "Comparar", None),
    ("itinerary", "Montar roteiro",
     "Escolher passeios e organizar períodos e datas",
     "Meu roteiro", "Meu planejamento", None),
    ("budget", "Revisar orçamento",
     "Analisar estimativas e informações ainda não confirmadas",
     "Orçamento", "Resumo financeiro", None),
)


def project_journey(plan: dict, interests: dict | None = None) -> dict:
    """Summarize existing records; does not modify either input."""
    items = (interests or {}).get("items", [])
    active = [x for x in items if x.get("priority") in
              ("must_visit", "interested", "maybe")]
    wishes = len(active)
    # Project itinerary completion by destination rather than comparing
    # unrelated counts of dates and selected outings.
    packages = plan.get("packages", {})
    flexible = plan.get("flexible_visits", [])
    destinations = set(packages) | {v["destination_id"] for v in flexible}
    assignments = set(plan.get("assignments", {}).values())
    flexible_dates = {v["destination_id"] for v in flexible if v.get("exact_date")}
    with_date = destinations & (assignments | flexible_dates)
    with_period = {v["destination_id"] for v in flexible
                   if v.get("period") and v["period"] != UNASSIGNED}
    organized = destinations & (with_date | with_period)
    pending = destinations - organized
    outing_count = len(destinations)
    dated_count = len(with_date)
    organized_count = len(organized)
    pending_count = len(pending)
    statuses = (
        "Pronto para explorar — sem decisão necessária",
        f"{wishes} destino(s) desejado(s)" if wishes else "Nenhum destino na lista",
        "Comparação disponível — base ainda em avaliação" if wishes else
        "Adicione destinos antes de comparar",
        (f"{outing_count} lugar(es) · {organized_count} organizado(s) "
         f"({dated_count} com data) · {pending_count} pendente(s)"
         if outing_count else "Nenhum passeio selecionado"),
        "Cenário de orçamento disponível — custos não confirmados",
    )
    steps = [
        {"id":step[0],"title":step[1],"description":step[2],
         "area":step[3],"section":step[4],"view":step[5],
         "status":statuses[index]}
        for index,step in enumerate(STEPS)
    ]
    remaining = {x["destination_id"] for x in active} - destinations
    if remaining:
        from attractions_model import load_attractions
        from itinerary_flow_model import destinations as canonical_destinations
        eligible_remaining=remaining & {d["id"] for d in canonical_destinations(load_attractions())}
    else:
        eligible_remaining=set()
    if not wishes and not outing_count:
        next_step = {"label":"Começar pelos destinos","id":"discover"}
        alternative_actions = []
    elif not outing_count and not eligible_remaining:
        next_step = {"label":"Revisar minha lista","id":"wishlist"}
        alternative_actions = [{"label":"Descobrir destinos compatíveis","id":"discover"}]
    elif not outing_count:
        next_step = {"label":"Montar roteiro com meus destinos","id":"itinerary"}
        alternative_actions = [{"label":"Comparar cidades-base","id":"compare"}]
    elif eligible_remaining:
        next_step = {"label":"Adicionar destinos pendentes ao roteiro","id":"itinerary"}
        alternative_actions = [{"label":"Comparar cidades-base","id":"compare"}]
    else:
        next_step = {"label":"Revisar meu roteiro","id":"itinerary"}
        alternative_actions = [{"label":"Revisar orçamento","id":"budget"}]
    return {
        "steps":steps,"next":next_step,"alternatives":alternative_actions,
        "wishes":wishes,"outings":outing_count,"dated_visits":dated_count,
        "organized_destinations":organized_count,
        "pending_destinations":pending_count,
        "base_decision_confirmed":False,
        "comparison_concluded":False,"budget_confirmed":False,
    }


def navigation_request(step_id: str) -> dict:
    """One-shot navigation intent, consumed before widget initialization."""
    step = next((x for x in STEPS if x[0] == step_id), None)
    if step is None:
        raise ValueError("Etapa de planejamento desconhecida")
    return {"area":step[3],"section":step[4],"view":step[5]}


def apply_navigation_request(state: dict) -> bool:
    """Apply a queued request *before* Streamlit renders ux_area/ux_section."""
    request = state.pop("_ux504_navigation_request", None)
    if request is None:
        return False
    valid_requests = [navigation_request(x[0]) for x in STEPS] + [
        {"area":"Meu roteiro","section":"Organizar viagem","view":None}]
    if (not isinstance(request, dict) or request not in valid_requests):
        raise ValueError("Solicitação de navegação inválida")
    from ux_navigation import set_task
    set_task(state, request["area"], request["section"])
    if request["view"] is not None:
        state["ux502_view"] = request["view"]
    return True
