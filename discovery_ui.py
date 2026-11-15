"""Discover real destinations and compare actionable profile itineraries in Streamlit."""
from __future__ import annotations
from copy import deepcopy
import streamlit as st
from destination_recommender import recommend_destinations
from travel_profile_scenarios import build_profile_scenarios
from recommended_itineraries import approve_destination,reject_destination,approve_profile_scenario
from planning_session import accept_approved_plan
from scenario_board_ui import render_scenario_boards

def money(value):
    return "R$ "+f"{value:,.0f}".replace(",",".")

def _render_suggestion(rec,plan):
    with st.container(border=True):
        header,detail=st.columns([1,2],gap="medium")
        with header:
            photo=rec.get("photo")
            if photo and photo.get("url"):
                st.image(photo["url"],use_container_width=True)
                st.caption("Imagem: "+photo.get("author","")+" · "+photo.get("license",""))
        with detail:
            st.markdown("#### "+rec["name"]+" · "+rec["country"])
            st.caption(rec["trip_type"])
            st.write("**O que conhecer:** "+", ".join(rec["attraction_names"]))
            with st.expander("Ver atrações recomendadas"):
                for attraction in rec["attraction_names"]:
                    st.write("• "+attraction)
                st.caption("Visitas sujeitas a horários e ingressos de 2027 ainda não verificados.")
            for reason in rec["reasons"][:2]:st.caption(reason)
            e=rec["known_costs"]["EUR"]
            ch=rec["known_costs"]["CHF"]
            st.write(f"**Bilhetes históricos conhecidos (casal):** € {e:.2f} + CHF {ch:.2f}")
            if rec["missing"]:
                st.warning(str(len(rec["missing"]))+" informação(ões) de custo/logística pendente(s). "
                           "O subtotal não equivale a uma cotação completa.")
            if rec["conditional"]:
                st.caption("Tarifas com condições: "+", ".join(rec["conditional"]))
            with st.expander("Fontes e dados a confirmar"):
                st.markdown("[Informações oficiais do destino]("+rec["source_url"]+")")
                st.markdown("[Fonte da conexão]("+rec["route_source"]+")")
                for missing in rec["missing"]:st.caption("• "+missing)
            a,b=st.columns(2)
            with a:
                if st.button("Quero visitar",key="advisor_discover_add_"+rec["destination_id"],
                             use_container_width=True):
                    updated=approve_destination(plan,rec,approved=True)
                    accept_approved_plan(updated)
                    st.success("Adicionado ao planejamento. Nenhuma reserva foi feita.")
                    st.rerun()
            with b:
                if st.button("Descartar",key="advisor_discover_dismiss_"+rec["destination_id"],
                             use_container_width=True):
                    updated=reject_destination(plan,rec["destination_id"],approved=True)
                    accept_approved_plan(updated)
                    st.rerun()

def render_discovery(plan,catalog,routes,trip_data,sync_sources,eurfx,chffx,use_city_rent,
                     *,view="discover"):
    """Show only the active task. Never render both catalog and heavy boards."""
    if view in ("board", "budget"):
        scenarios=build_profile_scenarios(
            plan,catalog,routes,trip_data,sync_sources["finance"]["status"]=="live",
            eurfx,chffx,use_city_rent=use_city_rent,
            allow_overnight=st.session_state.get("advisor_discovery_overnight",False))
        render_scenario_boards(
            plan,scenarios,catalog,routes,trip_data,
            sync_sources["finance"]["status"]=="live",
            eurfx,chffx,use_city_rent=use_city_rent,finance_only=view=="budget")
        return
    st.markdown("### Descobrir lugares para conhecer")
    st.caption("Sugestões do catálogo pesquisado — fotos, atrações, deslocamentos e valores "
               "de referência. Só entram no roteiro quando você escolhe.")
    col1,col2=st.columns(2)
    with col1:
        max_minutes=st.selectbox("Tempo máximo de trem por trecho", [70,120,180,300],
                                  index=2,key="advisor_discovery_max",
                                  format_func=lambda n:f"Até {n} minutos documentados")
    with col2:
        overnight=st.checkbox("Incluir destinos com possível pernoite",
                              value=False,key="advisor_discovery_overnight")
    places=recommend_destinations(plan,catalog,routes,profile=plan["profile"],
                                 max_travel_minutes=max_minutes,allow_overnight=overnight)
    query=st.text_input("Buscar destino",key="workspace_destination_search",
                        placeholder="Cidade ou atração")
    countries=sorted({x["country"] for x in places})
    selected_country=st.selectbox("País",["Todos"]+countries,
                                  key="workspace_destination_country")
    if query:
        term=query.casefold().strip()
        places=[x for x in places if term in x["name"].casefold()
                or any(term in a.casefold() for a in x["attraction_names"])]
    if selected_country!="Todos":
        places=[x for x in places if x["country"]==selected_country]
    page_size=6
    count=st.session_state.get("workspace_discovery_count",page_size)
    if not places:
        st.info("Nenhum destino novo encontrado com esses critérios. "
                "Aumente o tempo de deslocamento ou habilite pernoites.")
    else:
        st.caption(f"{len(places)} destinos candidatos, ordenados por adequação ao perfil escolhido.")
        for rec in places[:count]:_render_suggestion(rec,plan)
        if len(places)>count and st.button("Ver mais destinos",key="workspace_discovery_more"):
            st.session_state["workspace_discovery_count"]=count+page_size
            st.rerun()

    st.caption("Resultados do catálogo existente; destinos descartados não reaparecem.")
