"""Discover real destinations and compare actionable profile itineraries in Streamlit."""
from __future__ import annotations
from copy import deepcopy
import streamlit as st
from destination_recommender import recommend_destinations
from travel_profile_scenarios import build_profile_scenarios
from recommended_itineraries import approve_destination,reject_destination,approve_profile_scenario
from planning_session import accept_approved_plan
from destination_labels import place_label, country_flag
from attractions_model import package_cost
from advisor_finance import advisor_projection
from scenario_board_ui import render_scenario_boards
from outing_guide_model import build_outing_guide
from outing_guide_ui import render_outing_guide

def money(value):
    return "R$ "+f"{value:,.0f}".replace(",",".")

def _financial_snapshot(plan,catalog,routes,trip_data,live,eurfx,chffx,use_city_rent):
    """Use the exact same projection settings as the workspace's budget tab."""
    ids=[a for group in plan["packages"].values() for a in group]
    costs=package_cost(catalog,routes,plan["base_city"],ids)
    projection=advisor_projection(
        trip_data,live,plan,costs,eurfx,chffx,use_city_rent)
    return {"total":float(projection["result"]["total"]),
            "margin":float(projection["result"]["margin"]),
            "known":float(projection["known_billets_brl"]),
            "pending":len(costs["missing"])}


def _go_to_my_outings():
    st.session_state["itinerary_section"]="Meus passeios"


def _render_suggestion(rec,plan,catalog,routes,trip_data,live,eurfx,chffx,use_city_rent):
    with st.container(border=True):
        header,detail=st.columns([1,2],gap="medium")
        with header:
            photo=rec.get("photo")
            if photo and photo.get("url"):
                st.image(photo["url"],use_container_width=True)
                st.caption("Imagem: "+photo.get("author","")+" · "+photo.get("license",""))
        with detail:
            st.markdown("#### "+place_label(rec["name"],rec["country"],show_country=True))
            minutes=rec["train_minutes_one_way"]
            st.caption("Partida: "+str(rec["base_city"]).capitalize()+" · "+
                       rec["trip_type"]+" · "+(
                f"Trem {minutes} min por trecho (histórico)" if minutes is not None
                else "Tempo de trem não verificado — limite escolhido não verificável"))
            fare=rec.get("fare_eur_person_oneway")
            if fare is not None:
                conditional=(" · desconto Carte Fluo condicionado" if
                             rec.get("fare_type")=="discount_carte_fluo" else "")
                st.caption(f"Tarifa histórica € {fare:.2f} por pessoa/trecho"+
                           conditional+"; não é cotação para 2027.")
            elif rec["destination_id"]!=rec["base_city"]:
                st.caption("Tarifa entre a base e este destino: não pesquisada/confirmada.")
            st.write("**O que conhecer:** "+", ".join(rec["attraction_names"]))
            with st.expander("Ver atrações recomendadas"):
                for attraction in rec["attraction_names"]:
                    st.write("• "+attraction)
                st.caption("Visitas sujeitas a horários e ingressos de 2027 ainda não verificados.")
            with st.expander("Por que foi sugerido?"):
                for reason in rec["reasons"][:2]:st.caption(reason)
            e=rec["known_costs"]["EUR"]
            ch=rec["known_costs"]["CHF"]
            st.write(f"**Bilhetes históricos conhecidos (casal):** € {e:.2f} + CHF {ch:.2f}")
            if rec["missing"]:
                st.caption("⚠ "+str(len(rec["missing"]))+
                           " pendência(s) de custo/logística. Subtotal incompleto.")
            if rec["conditional"]:
                st.caption("Tarifas com condições: "+", ".join(rec["conditional"]))
            if st.checkbox("Ver guia: trajeto, pontos e custos",
                           key="discovery_guide_toggle_"+rec["destination_id"]):
                guide=build_outing_guide(plan,catalog,routes,rec["destination_id"],
                                         rec["selected_attractions"])
                render_outing_guide(guide,key_prefix="discovery_guide_"+rec["destination_id"],
                                    eurfx=eurfx,chffx=chffx)
            with st.expander("Fontes e dados a confirmar"):
                st.markdown("[Informações oficiais do destino]("+rec["source_url"]+")")
                st.markdown("[Fonte da conexão]("+rec["route_source"]+")")
                for missing in rec["missing"]:st.caption("• "+missing)
            a,b=st.columns(2)
            with a:
                if st.button("Quero visitar",key="advisor_discover_add_"+rec["destination_id"],
                             use_container_width=True):
                    try:
                        updated=approve_destination(plan,rec,approved=True)
                        before=_financial_snapshot(plan,catalog,routes,trip_data,
                                                   live,eurfx,chffx,use_city_rent)
                        after=_financial_snapshot(updated,catalog,routes,trip_data,
                                                  live,eurfx,chffx,use_city_rent)
                        accept_approved_plan(updated)
                        st.session_state["discovery_last_added"]={
                            "name":rec["name"],"destination_id":rec["destination_id"],
                            "before":before,"after":after}
                        st.rerun()
                    except ValueError as exc:
                        st.error("Não foi possível adicionar o passeio: "+str(exc))
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
    cities={d["id"]:d["name"] for d in catalog["destinations"]}
    base_name=cities.get(plan["base_city"],plan["base_city"])
    st.info("Cidade-base: **"+base_name+"** · A pesquisa usa tarifas e tempos "
            "da matriz específica dessa base (revisão "+str(routes.get("checked_at","não informada"))+
            "). Não são preços ao vivo nem horários confirmados de 2027.")
    st.caption("Clique em **Quero visitar** para incluir imediatamente o destino em **Meus passeios**. "
               "O orçamento da sessão é recalculado automaticamente; a gravação online depende do salvamento.")
    live=sync_sources["finance"]["status"]=="live"
    current=_financial_snapshot(plan,catalog,routes,trip_data,live,eurfx,chffx,use_city_rent)
    notice=st.session_state.pop("discovery_last_added",None)
    if notice:
        st.success("✓ "+notice["name"]+" foi adicionado a Meus passeios.")
        before,after=notice["before"],notice["after"]
        delta=after["total"]-before["total"]
        st.caption("Projeção recalculada: "+money(before["total"])+" → "+
                   money(after["total"])+" · alteração "+money(delta)+
                   ". Margem atual: "+money(after["margin"])+".")
        if abs(delta)<0.005:
            st.caption("O total não mudou porque os gastos conhecidos ainda cabem na "
                       "verba de passeios já prevista, ou não há valores novos cotados.")
        st.button("Ver em Meus passeios →",key="discovery_go_my_outings",
                  on_click=_go_to_my_outings,width="stretch")
    a,b,c=st.columns(3)
    a.metric("Passeios no meu roteiro",len(plan["packages"]))
    b.metric("Projeção do casal",money(current["total"]))
    c.metric("Margem até o teto",money(current["margin"]))
    if current["pending"]:
        st.caption(f"⚠ {current['pending']} componente(s) sem preço completo: "
                   "os valores são parciais, não cotações para 2027.")
    st.caption("Os gastos conhecidos dos passeios já estão considerados na provisão "
               "de excursões; não são somados duas vezes.")
    col1,col2=st.columns(2)
    with col1:
        max_minutes=st.selectbox("Tempo máximo de trem por trecho", [70,120,180,300],
                                  index=2,key="advisor_discovery_max",
                                  format_func=lambda n:f"Até {n} minutos documentados")
    with col2:
        overnight=st.checkbox("Incluir destinos com possível pernoite",
                              value=False,key="advisor_discovery_overnight")
    include_unknown=st.checkbox(
        "Mostrar também destinos sem tempo ferroviário verificado",
        value=False,key="advisor_discovery_unverified",
        help="Esses destinos não passaram no filtro de duração: é preciso "
             "confirmar conexões e horários antes de escolhê-los.")
    places=recommend_destinations(plan,catalog,routes,profile=plan["profile"],
                                 max_travel_minutes=max_minutes,allow_overnight=overnight,
                                 include_unverified_routes=include_unknown,
                                 eur_fx=eurfx,chf_fx=chffx)
    categories_by_dest={}
    for attraction in catalog["attractions"]:
        categories_by_dest.setdefault(attraction["destination_id"],set()).add(attraction["category"])
    search_col,country_col,category_col=st.columns([2,1,1])
    with search_col:
        query=st.text_input("Buscar destino",key="workspace_destination_search",
                            placeholder="Cidade ou atração")
    with country_col:
        countries=sorted({x["country"] for x in places})
        selected_country=st.selectbox("País",["Todos"]+countries,
                                      key="workspace_destination_country")
    with category_col:
        categories=sorted({cat for x in places
                          for cat in categories_by_dest.get(x["destination_id"],set())})
        category=st.selectbox("Categoria",["Todas"]+categories,
                              key="workspace_destination_category")
    sort=st.selectbox("Ordenar por",["Relevância","Nome (A–Z)","Trem mais curto conhecido"],
                      key="workspace_discovery_sort")
    if query:
        term=query.casefold().strip()
        places=[x for x in places if term in x["name"].casefold()
                or any(term in a.casefold() for a in x["attraction_names"])]
    if selected_country!="Todos":
        places=[x for x in places if x["country"]==selected_country]
    if category!="Todas":
        places=[x for x in places
                if category in categories_by_dest.get(x["destination_id"],set())]
    if sort=="Nome (A–Z)":
        places.sort(key=lambda x:x["name"].casefold())
    elif sort=="Trem mais curto conhecido":
        places.sort(key=lambda x:(x["train_minutes_one_way"] is None,
                    x["train_minutes_one_way"] if x["train_minutes_one_way"] is not None else 0,
                    x["name"]))
    page_size=6
    filter_signature=(plan["base_city"],plan["profile"],query,selected_country,
                      category,sort,max_minutes,overnight,include_unknown)
    if st.session_state.get("workspace_discovery_filters")!=filter_signature:
        st.session_state["workspace_discovery_filters"]=filter_signature
        st.session_state["workspace_discovery_count"]=page_size
    count=st.session_state.get("workspace_discovery_count",page_size)
    if not places:
        st.info("Nenhum destino novo encontrado com esses critérios. "
                "Aumente o tempo de deslocamento ou habilite pernoites.")
    else:
        st.caption(f"{len(places)} destinos candidatos, ordenados por adequação ao perfil escolhido.")
        for rec in places[:count]:
            _render_suggestion(rec,plan,catalog,routes,trip_data,live,
                               eurfx,chffx,use_city_rent)
        if len(places)>count and st.button("Ver mais destinos",key="workspace_discovery_more"):
            st.session_state["workspace_discovery_count"]=count+page_size
            st.rerun()

    st.caption("Resultados do catálogo existente; destinos descartados não reaparecem.")
