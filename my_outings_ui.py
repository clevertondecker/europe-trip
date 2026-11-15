"""Direct editor for actual TripPlan outings, distinct from simulated proposals."""
from __future__ import annotations

from collections import defaultdict
from html import escape

import streamlit as st

from planning_session import select_package, delete_package


def catalog_options(catalog: dict, plan: dict) -> tuple[dict, dict]:
    destinations = {d["id"]: d for d in catalog["destinations"]}
    attractions = defaultdict(list)
    for attraction in catalog["attractions"]:
        attractions[attraction["destination_id"]].append(attraction)
    return destinations, attractions


def selected_cards(plan: dict, catalog: dict) -> list[dict]:
    """Only canonical approved packages, never proposed scenario destinations."""
    destinations, attractions = catalog_options(catalog, plan)
    by_id = {a["id"]: a for a in catalog["attractions"]}
    result = []
    for dest_id, selected in plan["packages"].items():
        if dest_id not in destinations:
            continue
        dest = destinations[dest_id]
        result.append({
            "id": dest_id, "name": dest["name"], "country": dest["country"],
            "photo": dest.get("photo"), "attractions": [
                by_id[key]["name"] for key in selected if key in by_id],
            "dates": sorted(day for day, value in plan["assignments"].items()
                            if value == dest_id),
        })
    return result


def _commit_selection(dest_id: str, selected: list[str], valid: set[str]) -> None:
    if not selected or len(selected) > 5 or len(selected) != len(set(selected)):
        raise ValueError("Selecione de uma a cinco atrações diferentes.")
    if not set(selected) <= valid:
        raise ValueError("Atração não pertence ao destino.")
    select_package(dest_id, selected)


def _photo(dest: dict) -> None:
    photo = dest.get("photo")
    if photo and photo.get("url"):
        st.image(photo["url"], width="stretch")
        st.caption("Foto: " + photo["author"] + " · " + photo["license"])


def _edit_card(dest_id: str, plan: dict, attractions: dict) -> None:
    available = attractions.get(dest_id, [])
    labels = {item["id"]: item["name"] for item in available}
    with st.form("outing_edit_form_" + dest_id):
        picked = st.multiselect(
            "Atrações deste passeio (1 a 5)",
            options=list(labels),
            default=[a for a in plan["packages"][dest_id] if a in labels],
            format_func=lambda key: labels[key],
            key="outing_edit_attractions_" + dest_id,
        )
        submitted = st.form_submit_button("Salvar alterações", width="stretch")
        if submitted:
            try:
                _commit_selection(dest_id, picked, set(labels))
                st.session_state["outing_edit_open"] = None
                st.success("Passeio atualizado no planejamento. Salve online para manter a alteração.")
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))


def render_my_outings(plan: dict, catalog: dict) -> None:
    """Add, edit and remove directly from the canonical itinerary in-session.

    Remote persistence remains the owner's explicit action in save panel.
    """
    destinations, attractions = catalog_options(catalog, plan)
    cards = selected_cards(plan, catalog)
    st.markdown("### Meus passeios")
    st.caption("Aqui aparecem **somente os passeios que você escolheu**. "
               "As sugestões do consultor ficam na aba Simular roteiros.")
    a, b = st.columns(2, gap="small")
    a.metric("Passeios escolhidos", len(cards))
    b.metric("Atrações escolhidas", sum(len(p) for p in plan["packages"].values()))

    if st.button("＋ Adicionar passeio", type="primary",
                 key="outing_add_open", width="stretch"):
        st.session_state["outing_adding"] = not st.session_state.get("outing_adding", False)
        st.session_state["outing_edit_open"] = None
        st.session_state["outing_remove_pending"] = None

    if st.session_state.get("outing_adding", False):
        with st.container(border=True):
            st.markdown("#### Novo passeio")
            remaining = [d for d in catalog["destinations"]
                         if d["id"] not in plan["packages"]
                         and d["id"] not in plan.get("excluded_destinations", [])]
            if not remaining:
                st.info("Todos os destinos disponíveis já estão incluídos ou descartados.")
            else:
                lookup = {d["id"]: d for d in remaining}
                with st.form("outing_add_form"):
                    destination = st.selectbox(
                        "Destino", list(lookup), key="outing_new_destination",
                        format_func=lambda key: lookup[key]["name"] + " · " + lookup[key]["country"])
                    labels = {a["id"]: a["name"] for a in attractions[destination]
                              if plan.get("preferences", {}).get(a["id"]) != "Descartar"}
                    picked = st.multiselect(
                        "Atrações (selecione de 1 a 5)",
                        options=list(labels), key="outing_new_attractions",
                        format_func=lambda key: labels[key])
                    confirm = st.form_submit_button("Adicionar ao meu roteiro", type="primary",
                                                    width="stretch")
                    if confirm:
                        try:
                            _commit_selection(destination, picked, set(labels))
                            st.session_state["outing_adding"] = False
                            st.success("Passeio adicionado ao seu roteiro. Salve online para manter a alteração.")
                            st.rerun()
                        except ValueError as exc:
                            st.error(str(exc))
            if st.button("Cancelar", key="outing_add_cancel"):
                st.session_state["outing_adding"] = False
                st.rerun()

    if not cards:
        st.info("Você ainda não adicionou passeios ao planejamento. "
                "Clique em **Adicionar passeio** para começar.")
        return

    for card in cards:
        dest_id = card["id"]
        with st.container(border=True):
            photo_col, info_col = st.columns([1, 2], gap="medium")
            with photo_col:
                _photo(destinations[dest_id])
            with info_col:
                st.markdown("#### " + escape(card["name"]) + " · " + escape(card["country"]))
                st.caption("✓ No meu roteiro · " + str(len(card["attractions"])) +
                           " atração(ões) · " +
                           (", ".join(card["dates"]) if card["dates"] else "Sem data definida"))
                st.write(" · ".join(card["attractions"]))
                edit_col, remove_col = st.columns(2, gap="small")
                with edit_col:
                    if st.button("✎ Editar", key="outing_edit_" + dest_id,
                                 width="stretch"):
                        st.session_state["outing_edit_open"] = (
                            None if st.session_state.get("outing_edit_open") == dest_id else dest_id)
                        st.session_state["outing_remove_pending"] = None
                        st.rerun()
                with remove_col:
                    if st.button("Remover", key="outing_remove_" + dest_id,
                                 width="stretch"):
                        st.session_state["outing_remove_pending"] = dest_id
                        st.session_state["outing_edit_open"] = None
                        st.rerun()
            if st.session_state.get("outing_edit_open") == dest_id:
                _edit_card(dest_id, plan, attractions)
            if st.session_state.get("outing_remove_pending") == dest_id:
                st.warning("Remover " + card["name"] +
                           " do seu roteiro? As datas associadas também serão removidas.")
                yes, no = st.columns(2)
                with yes:
                    if st.button("Confirmar remoção", type="primary",
                                 key="outing_confirm_remove_" + dest_id,
                                 width="stretch"):
                        delete_package(dest_id)
                        st.session_state["outing_remove_pending"] = None
                        st.success("Passeio removido do planejamento. Salve online para manter a alteração.")
                        st.rerun()
                with no:
                    if st.button("Cancelar", key="outing_cancel_remove_" + dest_id,
                                 width="stretch"):
                        st.session_state["outing_remove_pending"] = None
                        st.rerun()
    st.caption("Alterações aparecem imediatamente no mapa e no orçamento da sessão. "
               "Para recuperá-las em outro dispositivo, use Salvar planejamento, "
               "se a autenticação do proprietário estiver configurada.")
