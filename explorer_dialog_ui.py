"""Contextual attraction dialog; does not create a second planning state."""
from __future__ import annotations

from html import escape
from dataclasses import asdict
from ux45_outing_contract import preview_outing
import streamlit as st

from attractions_model import package_cost, route_for
from explorer_mutation_guard import (
    can_edit, save_outing, remove_outing, change_interest, SimulationWriteBlocked,
)
from planning_session import active_plan


def render_attraction_dialog(destination_id: str, base: str, catalog: dict, routes: dict,
                             by_id: dict, by_attr: dict) -> None:
    dest = by_id[destination_id]

    @st.dialog(f"Montar passeio em {dest['name']}")
    def editor() -> None:
        mode = st.session_state.get("ux_mode", "Oficial")
        editable = can_edit(base, active_plan(), mode)
        current=preview_outing(active_plan(),catalog,destination_id)
        previous = current["selected_attractions"]
        if not editable:
            st.info("Simulação: seleções temporárias não modificam seu roteiro oficial.")
        elif previous:
            st.info("Este passeio já existe. Você pode atualizar as atrações.")
        else:
            st.caption("Escolha atrações e adicione ao roteiro; não é necessário definir uma data.")
        route = route_for(routes, base, destination_id)
        minutes = route["train_minutes_one_way"]
        st.caption("Base: " + by_id[base]["name"] + " · trem: " +
                   (f"{minutes} min/trecho" if minutes is not None else "não verificado"))
        here = [a for a in catalog["attractions"] if a["destination_id"] == destination_id]
        for attraction in here:
            with st.container(border=True):
                st.markdown("**" + escape(attraction["name"]) + "**")
                st.write(attraction["summary"])
                st.caption(f"{attraction['visit_minutes']} min (estimativa) · "
                           + _label_cost(attraction))
                if attraction.get("seasonality"):
                    st.caption("Sazonalidade: " + attraction["seasonality"])
                if attraction.get("source_urls"):
                    st.markdown("[Fonte](" + attraction["source_urls"][0] + ")")
        available = [a["id"] for a in here]
        key = "explore_package_select_" + destination_id
        if key not in st.session_state:
            draft = st.session_state.get("explore_simulated_choices", {}).get(destination_id, previous or available[:3])
            st.session_state[key] = [x for x in draft if x in available][:5]
        picked = st.multiselect(
            "Atrações desejadas (até cinco)", available, key=key,
            max_selections=5, format_func=lambda x: by_attr[x]["name"], placeholder="Escolha uma ou mais opções")
        duration = sum(by_attr[x]["visit_minutes"] for x in picked)
        st.caption(f"Duração nas atrações: {duration // 60}h{duration % 60:02d}; "
                   "deslocamentos e filas não incluídos.")
        costs = package_cost(catalog, routes, base, picked)
        st.caption(f"Custos conhecidos (casal): € {costs['known_by_currency']['EUR']:.2f} "
                   f"· CHF {costs['known_by_currency']['CHF']:.2f}. "
                   "Valores incompletos e históricos, não cotações de 2027.")
        if not editable:
            st.session_state.setdefault("explore_simulated_choices", {})[destination_id] = list(picked)
            st.caption("Prévia local somente. Não será aplicada automaticamente.")
        else:
            st.caption("Resumo da alteração: "+str(len(picked))+" atração(ões) · "+
                       ("período "+current["period"] if current["period"]!="Ainda não definido" else "período ainda não definido")+
                       " · datas existentes serão preservadas · somente nesta sessão.")
            if st.button("Atualizar passeio" if previous else "Adicionar ao meu roteiro",
                         key="explore_save_" + destination_id, disabled=not picked,
                         width="stretch"):
                try:
                    result=save_outing(base, mode, destination_id, picked)
                    st.session_state["ux45_explore_result"]=asdict(result)
                    st.session_state.pop("explore_selected_destination", None)
                    st.rerun()
                except (ValueError, SimulationWriteBlocked) as exc:
                    st.error(str(exc))
            if previous and st.button("Remover passeio", key="explore_remove_" + destination_id):
                st.session_state["ux45_explore_removing"]=destination_id
                st.rerun()
            if st.session_state.get("ux45_explore_removing")==destination_id:
                assigned=current["dates"]
                st.warning("Remover "+dest["name"]+" do roteiro? "+
                           (str(len(assigned))+" data(s) associada(s) serão removidas. "
                            if assigned else "Não há datas associadas. ")+
                           "As atrações e o período flexível serão removidos.")
                yes,no=st.columns(2)
                if yes.button("Confirmar remoção",key="ux45_explore_remove_confirm_"+destination_id):
                    try:
                        result=remove_outing(base,mode,destination_id,confirmed=True)
                        st.session_state["ux45_explore_result"]=asdict(result)
                        st.session_state.pop("ux45_explore_removing",None)
                        st.session_state.pop("explore_selected_destination",None)
                        st.rerun()
                    except (ValueError,SimulationWriteBlocked) as exc:
                        st.error(str(exc))
                if no.button("Cancelar",key="ux45_explore_remove_cancel_"+destination_id):
                    st.session_state.pop("ux45_explore_removing",None)
                    st.rerun()
            with st.expander("Preferências (não adicionam ao roteiro)", expanded=False):
                st.caption("Quero visitar marca interesse exploratório; Adicionar ao roteiro é uma ação separada.")
                for attr in here:
                    k = "explore_mark_" + attr["id"]
                    marks = ["Quero visitar", "Opcional", "Descartar"]
                    current = active_plan().get("preferences", {}).get(attr["id"], "Opcional")
                    st.selectbox(attr["name"], marks, key=k,
                                 index=marks.index(current))
                    if st.button("Aplicar preferência", key="explore_mark_apply_" + attr["id"]):
                        try:
                            change_interest(base, mode, attr["id"], st.session_state[k])
                            st.success("Interesse exploratório registrado; nenhum passeio foi adicionado.")
                        except SimulationWriteBlocked as exc:
                            st.error(str(exc))
        if st.button("Fechar e continuar explorando", key="explore_close_" + destination_id):
            st.session_state.pop("explore_selected_destination", None)
            st.rerun()

    editor()


def _label_cost(entry: dict) -> str:
    ticket = entry["ticket"]
    if ticket["amount"] is not None:
        return f"{ticket['currency']} {ticket['amount']:.2f}/adulto"
    if ticket["status"] == "not_applicable":
        return "Passeio externo sem bilhete"
    return "Ingresso a verificar"
