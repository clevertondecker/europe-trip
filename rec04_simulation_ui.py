"""Small REC04 context panel inside existing budget and recommendation screens."""
from __future__ import annotations
import streamlit as st
from rec04_simulation_handoff import ERROR,valid_context,return_to_source,return_to_official
from rec04_candidate_capabilities import capability_for


def render_simulation_context(plan):
    state=st.session_state
    message=state.pop(ERROR,None)
    if message:
        st.warning(message)
    ctx=valid_context(state)
    if ctx is None:
        return
    cap=capability_for(ctx["city_id"])
    with st.container(border=True):
        st.markdown("#### Simulação exploratória · "+cap["name"])
        st.caption("Base oficial continua "+plan["base_city"].title()+
                   ". Nenhuma escolha aqui altera TripPlan, reservas ou dados privados.")
        if not cap["detailed_budget_supported"]:
            st.warning("Orçamento específico da cidade ainda indisponível. "
                       "A simulação abaixo usa provisões gerais, não preço local.")
        else:
            st.info("Matriz de passeios disponível, mas moradia e transporte em 2027 "
                    "ainda não estão confirmados.")
        st.caption("Pendências: "+"; ".join(cap["missing"]))
        left,right=st.columns(2)
        left.button("Voltar à pesquisa anterior",key="rec04_return_to_source",
                    on_click=return_to_source,args=(state,))
        right.button("Ver orçamento oficial",key="rec04_return_to_official",
                     on_click=return_to_official,args=(state,))
