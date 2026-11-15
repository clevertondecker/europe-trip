"""Consistent exploratory impact explanation across Streamlit tabs."""
from __future__ import annotations
import streamlit as st
from base_scenario_model import base_options
from base_scenario_impact import scenario_impact


def sync_city_widget(widget_key:str,choices:list[str])->None:
    """Reflect the global candidate without overwriting real widget changes.

    Call before creating the local widget. An on_change handler updates the
    canonical selection at callback time, prior to the next script rerun.
    """
    selected=st.session_state.get("scenario_base_selected")
    if selected in choices and st.session_state.get(widget_key)!=selected:
        st.session_state[widget_key]=selected


def set_city_from_widget(widget_key:str)->None:
    """Propagate local city selections to the shared global context."""
    from base_scenario_model import choose_exploratory_base
    options=base_options()
    selected=choose_exploratory_base(st.session_state[widget_key],options)
    st.session_state["scenario_base_selected"]=selected
    st.session_state["scenario_sidebar"]=selected
    st.session_state["ux_last_candidate"]=selected
    st.session_state["ux_mode"]="Simulação"


def render_scenario_impact(plan:dict,trip_data:dict,finance_live:bool)->None:
    selected=st.session_state.get("scenario_base_selected")
    if not selected or selected==plan["base_city"]:
        return
    labels={x["id"]:x["name"] for x in base_options()}
    with st.expander("Impacto hipotético · "+labels.get(selected,selected),expanded=False):
        result=scenario_impact(plan,trip_data,finance_live,selected,
             st.session_state.get("advisor_eurfx",6.3),
             st.session_state.get("advisor_chffx",7.1),
             french_days=st.session_state.get("ux_days") if
             st.session_state.get("ux_mode")=="Simulação" else None)
        st.caption("Roteiro oficial: "+labels.get(plan["base_city"],plan["base_city"])+
                   ". Esta simulação não altera datas, atrações, calendário ou reservas.")
        if result["total_brl"] is None:
            st.info("Orçamento específico desta cidade: não cotado. "
                    "A provisão geral continua no orçamento oficial, "
                    "mas não representa o custo local desta candidata.")
        else:
            a,b=st.columns(2)
            a.metric("Projeção histórica e parcial (R$)",
                     f"{result['total_brl']:,.0f}")
            b.metric("Bilhetes conhecidos (R$)",
                     f"{result['known_tickets_brl']:,.0f}")
            st.warning("Projeção baseada nas premissas atuais e em preços de 2026. "
                       "Não significa que o custo total de 2027 esteja confirmado.")
        if result["missing"]:
            st.caption("Informações pendentes: "+"; ".join(result["missing"][:6]))
        st.caption("Consulte Explorar bases e Pesquisa ampliada para fontes e rotas.")
