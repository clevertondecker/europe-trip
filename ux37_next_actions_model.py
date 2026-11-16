"""UX 3.7: factual, read-only next actions derived from the canonical TripPlan.

No new persistence, hidden scoring, or extra financial totals. Missing
research is not evidence that a route is impossible or a cost is zero.
"""
from __future__ import annotations

from itinerary_flow_model import selected_rows, UNASSIGNED

ACTIONS = {
    "housing": ("Comparar hospedagem para a estadia", "Explorar", "Comparar"),
    "return": ("Verificar trem de volta", "Explorar", "Passeios"),
    "cost": ("Conferir custos pendentes", "Orçamento", "Detalhamento"),
    "organize": ("Organizar passeio sem data", "Meu roteiro", "Organizar viagem"),
    "start": ("Escolher os primeiros passeios", "Explorar", "Passeios"),
}


def next_actions(plan: dict, catalog: dict, evidence: dict, *, limit: int = 4) -> list[dict]:
    """Return up to four contextual actions, without mutating input data.

    Evidence must be a validated load_outing_evidence() dataset.
    An item with amount=None is an unresolved source, not a numeric zero.
    """
    if limit < 1:
        return []
    selected = selected_rows(plan, catalog)
    names = {d["id"]: d["name"] for d in catalog["destinations"]}
    selected_ids = [row["id"] for row in selected if row["stage"] == "França"]
    rows = []
    if plan["base_city"] in {"mulhouse", "strasbourg", "metz", "nancy"}:
        rows.append({
            "id": "housing:" + plan["base_city"],
            "title": ACTIONS["housing"][0],
            "detail": "Comparar anúncios mobiliados para duas pessoas e a janela completa; "
                      "pesquisas históricas não confirmam disponibilidade em 2027.",
            "why": "A cidade-base determina grande parte do custo e da logística.",
            "area": ACTIONS["housing"][1], "section": ACTIONS["housing"][2],
            "destination_id": plan["base_city"], "source": None,
            "status": "Verificação atual necessária",
        })
    if not selected:
        rows.append({
            "id": "start", "title": ACTIONS["start"][0],
            "detail": "Escolha até cinco atrações por passeio; a data pode ficar indefinida.",
            "why": "Ainda não há passeios selecionados no roteiro.",
            "area": "Explorar", "section": "Passeios",
            "destination_id": None, "source": None, "status": "Decisão do viajante",
        })
    # Dedupe by destination and decision: multiple attractions never multiply a
    # single return-leg research requirement.
    for destination in selected_ids:
        if destination not in names:
            continue
        items = [x for x in evidence["items"]
                 if x.get("destination_id") == destination and x.get("amount") is None]
        returning = next((x for x in items if x["category"] == "intercity_return"), None)
        if returning and destination != plan["base_city"]:
            rows.append({
                "id": "return:" + destination,
                "title": ACTIONS["return"][0] + " — " + names[destination],
                "detail": "Conferir horários de retorno, conexões e último trecho para a data escolhida. "
                          "A ausência de pesquisa não significa que o trajeto é inviável.",
                "why": "O retorno é necessário para avaliar um bate-volta.",
                "area": "Explorar", "section": "Passeios",
                "destination_id": destination, "source": returning.get("source_url"),
                "status": "Pesquisa incompleta",
            })
        cost_items = [x for x in items if x["category"] in ("ticket", "local_transport", "extra_hotel")]
        if cost_items:
            rows.append({
                "id": "cost:" + destination,
                "title": ACTIONS["cost"][0] + " — " + names[destination],
                "detail": "Há despesas sem valor completo para o casal. "
                          "Não tratá-las como gratuitas ou como cotação de 2027.",
                "why": "O orçamento da visita pode estar incompleto.",
                "area": "Orçamento", "section": "Detalhamento",
                "destination_id": destination,
                "source": next((x.get("source_url") for x in cost_items if x.get("source_url")), None),
                "status": "Pesquisa incompleta",
            })
    for row in selected:
        if row["period"] == UNASSIGNED and not row["exact_dates"]:
            rows.append({
                "id": "organize:" + row["id"],
                "title": ACTIONS["organize"][0] + " — " + row["name"],
                "detail": "Escolha um período quando fizer sentido; não é necessário reservar uma data.",
                "why": "O passeio já está no roteiro, mas ainda não foi organizado.",
                "area": "Meu roteiro", "section": "Organizar viagem",
                "destination_id": row["id"], "source": None,
                "status": "Decisão do viajante",
            })
    # Stable explicit decision order; no quality score or arbitrary weight.
    return rows[:limit]
