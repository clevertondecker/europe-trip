"""Discover real destinations and compare actionable profile itineraries in Streamlit."""
from __future__ import annotations
from copy import deepcopy
import streamlit as st
from destination_recommender import recommend_destinations
from travel_profile_scenarios import build_profile_scenarios
from recommended_itineraries import approve_destination,reject_destination,approve_profile_scenario
from planning_session import accept_approved_plan

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

def render_discovery(plan,catalog,routes,trip_data,sync_sources,eurfx,chffx,use_city_rent):
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
    if not places:
        st.info("Nenhum destino novo encontrado com esses critérios. "
                "Aumente o tempo de deslocamento ou habilite pernoites.")
    else:
        st.caption(f"{len(places)} destinos candidatos, ordenados por adequação ao perfil escolhido.")
        for rec in places[:6]:_render_suggestion(rec,plan)
        if len(places)>6:
            with st.expander("Ver mais destinos recomendados"):
                for rec in places[6:]:_render_suggestion(rec,plan)
    st.divider()
    st.markdown("### Comparar estilos de viagem")
    st.caption("Os perfis selecionam **passeios concretos** do catálogo; valores históricos "
               "não são preços garantidos para 2027. Nenhuma proposta é salva sem sua aprovação.")
    scenarios=build_profile_scenarios(
        plan,catalog,routes,trip_data,sync_sources["finance"]["status"]=="live",
        eurfx,chffx,use_city_rent=use_city_rent,allow_overnight=overnight)
    for scenario in scenarios:
        with st.container(border=True):
            st.markdown("#### "+scenario["label"])
            st.caption(str(len(scenario["new_destinations"]))+" destinos sugeridos além dos já escolhidos")
            known=scenario["known_cost_by_currency"]
            total=scenario["financial"]["result"]
            a,b,c=st.columns(3)
            with a:st.metric("Projeção do cenário",money(total["total"]))
            with b:st.metric("Margem até o teto",money(total["margin"]))
            with c:st.metric("Dias no calendário",str(scenario["scheduled_count"]))
            if scenario["new_recommendations"]:
                st.write("**Destinos sugeridos:** "+", ".join(r["name"] for r in scenario["new_recommendations"]))
            else:st.info("Sem novos destinos que caibam nos critérios deste perfil.")
            st.caption(f"Passagens e ingressos historicamente conhecidos: € {known['EUR']:.2f} "
                       f"+ CHF {known['CHF']:.2f} para duas pessoas.")
            if scenario["missing_costs"]:
                st.warning(str(len(scenario["missing_costs"]))+
                           " custos sem valor completo. A projeção não é preço final.")
            if scenario["unresolved"]:
                st.caption(str(len(scenario["unresolved"]))+
                           " passeios ainda sem data devido a lacunas ou restrições.")
            st.caption("Não removemos atrações escolhidas nem comprometemos a reserva financeira.")
            with st.expander("Ver detalhes da proposta e logística"):
                for r in scenario["new_recommendations"]:
                    st.write("• "+r["name"]+" — "+r["trip_type"])
                for issue in scenario["unresolved"]:
                    st.caption(issue["destination"]+": "+issue["reason"])
                st.caption(scenario["assumptions"])
            if st.button("Aceitar este roteiro sugerido",key="advisor_scenario_accept_"+scenario["profile"],
                         use_container_width=True,disabled=not scenario["new_destinations"]):
                updated=approve_profile_scenario(plan,scenario,approved=True)
                accept_approved_plan(updated)
                st.success("Proposta aprovada no planejamento. Salve para manter as escolhas.")
                st.rerun()
