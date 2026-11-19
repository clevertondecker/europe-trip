"""UX 5.5: read-only visual context for the existing canonical outing editor.

No alternative selection store, booking action, or inferred 2027 travel time.
The visual card consumes the same destination/attraction IDs as commit_outing.
"""
from __future__ import annotations

from html import escape

import streamlit as st

from itinerary_flow_model import FRANCE_STAGE
from ux47_photo_ui import photo_markup, photo_credit


def destination_preview(dest: dict, catalog: dict) -> dict:
    """Produce a safe, catalog-backed preview without altering TripPlan."""
    canonical = next((d for d in catalog["destinations"]
                      if d["id"] == dest["id"]), None) if dest["stage"] == FRANCE_STAGE else None
    source = canonical or {}
    attractions = {a["id"]: a for a in catalog["attractions"]} if canonical else {}
    details = []
    for choice in dest["attractions"]:
        item = attractions.get(choice["id"], {})
        ticket = item.get("ticket") or {}
        amount = ticket.get("amount")
        if ticket.get("status") == "operator_published" and amount is not None:
            price = f'{ticket.get("currency", "EUR")} {amount:.2f} por adulto (referência histórica)'
        elif ticket.get("status") == "not_applicable":
            price = "Visita externa sem bilhete cadastrado"
        else:
            price = "Ingresso a verificar"
        details.append({
            "id": choice["id"], "name": choice["name"],
            "summary": item.get("summary") or "Descrição detalhada ainda não cadastrada.",
            "minutes": item.get("visit_minutes"),
            "price": price,
            "source": (item.get("source_urls") or [None])[0],
        })
    return {
        "name": dest["name"],
        "country": source.get("country") or ("Itália" if canonical is None else ""),
        "photo": source.get("photo"),
        "source": source.get("source_url"),
        "details": details,
    }


def render_destination_preview(dest: dict, catalog: dict, picked: list[str]) -> None:
    """Visual discovery is informational; only the existing confirm button writes."""
    view = destination_preview(dest, catalog)
    with st.container(border=True):
        visual, facts = st.columns([1, 2], gap="medium", vertical_alignment="top")
        with visual:
            st.html(photo_markup(view["photo"], view["name"]))
            credit = photo_credit(view["photo"])
            if credit:
                st.caption(credit)
        with facts:
            st.markdown("##### " + escape(view["name"]) + " · " + escape(view["country"]))
            st.caption(str(len(view["details"])) + " atrações no catálogo atual")
            st.write("Conheça o destino antes de selecionar as atrações. "
                     "Informações incompletas permanecem marcadas como pendentes.")
            if view["source"]:
                st.link_button("Fonte turística do destino", view["source"])
            st.caption("A fotografia representa o destino, não necessariamente a atração.")
    st.markdown("##### Conheça as atrações")
    if not view["details"]:
        st.info("Ainda não há atrações cadastradas para este destino.")
        return
    for item in view["details"]:
        selected = item["id"] in picked
        with st.expander(("✓ " if selected else "") + item["name"],
                         expanded=selected):
            st.write(item["summary"])
            duration = (str(item["minutes"]) + " min de visita (estimativa editorial)"
                        if item["minutes"] is not None else "Duração de visita a verificar")
            st.caption(duration + " · " + item["price"])
            if item["source"]:
                st.link_button("Consultar fonte oficial", item["source"])
    st.caption("As descrições e custos são referências de pesquisa, "
               "não disponibilidade, horários ou preços confirmados para 2027.")
