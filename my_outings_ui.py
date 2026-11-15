"""Direct editor for actual TripPlan outings, distinct from simulated proposals."""
from __future__ import annotations

from collections import defaultdict
from html import escape

import streamlit as st

from planning_session import select_package, delete_package
from attractions_model import package_cost
from advisor_finance import advisor_projection


def _go_budget_presets()->None:
    st.session_state["itinerary_section"]="Orçamento"


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
    picked = st.multiselect(
        "Atrações deste passeio (1 a 5)",
        options=list(labels),
        default=[a for a in plan["packages"][dest_id] if a in labels],
        format_func=lambda key: labels[key],
        key="outing_edit_attractions_" + dest_id,
    )
    if st.button("Salvar alterações", key="outing_edit_save_" + dest_id,
                 width="stretch"):
        try:
            _commit_selection(dest_id, picked, set(labels))
            st.session_state["outing_edit_open"] = None
            st.success("Passeio atualizado no planejamento. Salve online para manter a alteração.")
            st.rerun()
        except ValueError as exc:
            st.error(str(exc))


def render_my_outings(plan: dict, catalog: dict, *, routes: dict | None = None,
                      trip_data: dict | None = None, finance_live: bool = False,
                      eurfx: float = 6.3, chffx: float = 7.1,
                      use_city_rent: bool = True) -> None:
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
    if routes is not None and trip_data is not None:
        chosen=[a for ids in plan["packages"].values() for a in ids]
        prices=package_cost(catalog,routes,plan["base_city"],chosen)
        financial=advisor_projection(trip_data,finance_live,plan,prices,
                                     eurfx,chffx,use_city_rent)
        allowance=float(financial["budget_excursions_allowance_brl"])
        known=float(financial["known_billets_brl"])
        st.markdown("#### Quanto dos passeios já está previsto no orçamento?")
        c1,c2,c3=st.columns(3)
        money=lambda value:"R$ "+f"{value:,.0f}".replace(",",".")
        c1.metric("Verba reservada",money(allowance))
        c2.metric("Custos conhecidos dos escolhidos",money(known))
        c3.metric("Saldo nominal da provisão",money(max(0,allowance-known)))
        if allowance>0:
            st.progress(min(1.,known/allowance))
        st.caption("Projeção global do casal: "+money(financial["result"]["total"])+
                   " · margem até o teto: "+money(financial["result"]["margin"])+".")
        if prices["missing"]:
            st.warning(f"{len(prices['missing'])} componente(s) sem preço completo. "
                       "O saldo nominal não significa dinheiro disponível.")
        st.caption("A verba já existia mesmo antes de escolher destinos; acrescentar um "
                   "passeio só aumenta a projeção quando os custos conhecidos excedem "
                   "a provisão. Alimentação, transporte urbano e outros valores "
                   "pendentes não são tratados como gratuitos.")

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
                destination = st.selectbox(
                    "Destino", list(lookup), key="outing_new_destination",
                    format_func=lambda key: lookup[key]["name"] + " · " + lookup[key]["country"])
                labels = {a["id"]: a["name"] for a in attractions[destination]
                          if plan.get("preferences", {}).get(a["id"]) != "Descartar"}
                picked = st.multiselect(
                    "Atrações (selecione de 1 a 5)",
                    options=list(labels), key="outing_new_attractions",
                    format_func=lambda key: labels[key])
                if st.button("Adicionar ao meu roteiro", type="primary",
                             key="outing_add_save", width="stretch"):
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
        st.info("Você ainda não adotou um roteiro. A verba para excursões já está "
                "prevista no orçamento, mas ainda não representa passeios escolhidos.")
        st.button("Ver roteiros prontos por estilo →",key="outing_go_budget_presets",
                  on_click=_go_budget_presets)
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
                if routes is not None:
                    one=package_cost(catalog,routes,plan["base_city"],plan["packages"][dest_id])
                    euro=one["known_by_currency"]["EUR"]
                    chf=one["known_by_currency"]["CHF"]
                    st.caption(f"Bilhetes e transporte históricos conhecidos (casal): "
                               f"€ {euro:.2f} · CHF {chf:.2f}")
                    if one["missing"]:
                        st.caption(f"⚠ {len(one['missing'])} componente(s) sem cotação completa")
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
