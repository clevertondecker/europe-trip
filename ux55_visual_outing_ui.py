"""UX 5.5 read-only destination and attraction discovery.

Canonical planning remains in itinerary_flow_ui/commit_outing. Unknown 2027
availability and prices are never inferred from historical source records.
"""
from __future__ import annotations

from html import escape
from math import isfinite

import streamlit as st
from itinerary_flow_model import FRANCE_STAGE
from ux47_photo_ui import photo_markup, photo_credit

TICKET_UNITS = {
    "adult": "por adulto (entrada)",
    "adult_return": "por adulto (ida e volta incluídas)",
}


def ticket_presentation(ticket: dict | None) -> dict[str, str | None]:
    """Preserve denomination, currency, validity and operator caveats."""
    ticket = ticket if isinstance(ticket, dict) else {}
    status, amount = ticket.get("status"), ticket.get("amount")
    unit, currency = ticket.get("per"), ticket.get("currency")
    validity, notes = ticket.get("validity"), ticket.get("notes")
    if status == "not_applicable":
        label = "Passeio externo sem bilhete cadastrado (acessos internos podem ser pagos)"
    elif (status == "operator_published" and type(amount) in (int, float)
          and isfinite(amount) and amount >= 0 and currency in ("EUR", "CHF")
          and unit in TICKET_UNITS):
        label = f"{currency} {amount:.2f} {TICKET_UNITS[unit]} · tarifa publicada (histórica)"
    else:
        label = "Preço ou modalidade de ingresso a verificar"
    return {
        "price": label,
        "validity": str(validity).strip() if validity else None,
        "notes": str(notes).strip() if notes else None,
    }


def destination_preview(dest: dict, catalog: dict) -> dict:
    """Read canonical destination/attraction details; never modify user selections."""
    canonical = (next((d for d in catalog["destinations"] if d["id"] == dest["id"]), None)
                 if dest["stage"] == FRANCE_STAGE else None)
    source = canonical or {}
    attractions = ({a["id"]: a for a in catalog["attractions"]}
                   if canonical else {})
    details = []
    for choice in dest["attractions"]:
        item = attractions.get(choice["id"], {})
        ticket = ticket_presentation(item.get("ticket"))
        details.append({
            "id": choice["id"], "name": choice["name"],
            "summary": item.get("summary") or "Descrição detalhada ainda não cadastrada.",
            "minutes": item.get("visit_minutes"),
            "price": ticket["price"],
            "ticket_validity": ticket["validity"],
            "ticket_notes": ticket["notes"],
            "source": (item.get("source_urls") or [None])[0],
        })
    return {
        "name": dest["name"],
        "country": source.get("country") or ("Itália" if canonical is None else ""),
        "photo": source.get("photo"),
        "source": source.get("source_url"),
        "details": details,
    }


def render_destination_preview(dest: dict, catalog: dict,
                               picked: list[str] | None = None) -> None:
    """Render facts before existing multiselect/confirmation widgets."""
    view = destination_preview(dest, catalog)
    picked_ids = set(picked or [])
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
            st.write("Conheça o destino e as atrações antes de escolher. "
                     "Dados que ainda não foram pesquisados ficam sinalizados.")
            if view["source"]:
                st.link_button("Fonte turística do destino", view["source"])
            st.caption("Foto da cidade, não necessariamente de cada atração.")
    st.markdown("##### Conheça as atrações")
    if not view["details"]:
        st.info("Ainda não há atrações cadastradas para este destino.")
        return
    st.caption("Expanda qualquer atração para consultar informações e fontes; "
               "a inclusão no roteiro é confirmada separadamente abaixo.")
    for item in view["details"]:
        with st.expander(("✓ " if item["id"] in picked_ids else "") + item["name"],
                         expanded=item["id"] in picked_ids):
            st.write(item["summary"])
            duration = (str(item["minutes"]) + " min de visita (estimativa editorial)"
                        if item["minutes"] is not None else "Duração a verificar")
            st.caption(duration)
            st.caption(item["price"])
            if item["ticket_validity"]:
                st.caption("Vigência da fonte: " + item["ticket_validity"])
            if item["ticket_notes"]:
                st.caption("Observação: " + item["ticket_notes"])
            if item["source"]:
                st.link_button("Consultar fonte oficial", item["source"])
    st.caption("Preços e descrições são referências de pesquisa: não confirmam "
               "tarifas, funcionamento, reservas ou serviços de retorno em 2027.")
