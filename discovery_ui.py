"""Discover real destinations and compare actionable profile itineraries in Streamlit."""
from __future__ import annotations

from formatting import brl, REQUIRED
from copy import deepcopy
import streamlit as st
from destination_recommender import recommend_destinations
from travel_profile_scenarios import build_profile_scenarios
from recommended_itineraries import approve_destination,reject_destination,approve_profile_scenario
from planning_session import accept_approved_plan,commit_outing,active_plan
from ux45_outing_contract import preview_outing
from itinerary_flow_model import period_options,FRANCE_STAGE,UNASSIGNED
from destination_labels import place_label, country_flag
from attractions_model import package_cost
from advisor_finance import advisor_projection
from scenario_board_ui import render_scenario_boards
from outing_guide_model import build_outing_guide
from outing_guide_ui import render_outing_guide

def money(value):
    return brl(value, decimals=0, missing=REQUIRED)


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
    from ux45_navigation_context import handoff
    destination=st.session_state.get("discovery_last_destination")
    if destination:
        handoff(st.session_state,area="Meu roteiro",
                section="Melhorar meu roteiro",destination_id=destination)


def _render_suggestion(rec,plan,catalog,routes,trip_data,live,eurfx,chffx,use_city_rent):
    with st.container(border=True):
        header,detail=st.columns([1,2],gap="medium")
        with header:
            photo=rec.get("photo")
            if photo and photo.get("url"):
                st.image(photo["url"],width="stretch")
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
                if st.button("Revisar inclusão no roteiro",
                             key="advisor_discover_add_"+rec["destination_id"],
                             width="stretch"):
                    st.session_state["ux45_discovery_review"]=rec["destination_id"]
                    st.session_state["ux45_discovery_revision"]=plan["revision"]
                    st.rerun()
            with b:
                if st.button("Descartar",key="advisor_discover_dismiss_"+rec["destination_id"],
                             width="stretch"):
                    updated=reject_destination(plan,rec["destination_id"],approved=True)
                    accept_approved_plan(updated)
                    st.rerun()
            if st.session_state.get("ux45_discovery_review")==rec["destination_id"]:
                st.markdown("**Revisar antes de adicionar ao roteiro**")
                if st.session_state.get("ux45_discovery_revision")!=active_plan()["revision"]:
                    st.warning("O planejamento mudou. Reabra a sugestão para revisar a versão atual.")
                else:
                    info=preview_outing(plan,catalog,rec["destination_id"])
                    options={a["id"]:a["name"] for a in catalog["attractions"]
                             if a["destination_id"]==rec["destination_id"]}
                    default=[a for a in (info["selected_attractions"] or
                                         rec["selected_attractions"]) if a in options]
                    key="ux45_discovery_attrs_"+rec["destination_id"]
                    if key not in st.session_state:
                        st.session_state[key]=default
                    picked=st.multiselect("Atrações a incluir ou atualizar",
                                           list(options),key=key,max_selections=5,
                                           format_func=lambda k:options[k], placeholder="Escolha uma ou mais opções")
                    periods=period_options(FRANCE_STAGE)
                    period=st.selectbox("Período flexível (opcional)",periods,
                                        index=periods.index(info["period"])
                                              if info["period"] in periods else 0,
                                        key="ux45_discovery_period_"+rec["destination_id"])
                    st.caption(("Atualizar destino já incluído" if info["already_exists"]
                                else "Adicionar novo destino")+" · "+
                               str(len(picked))+" atração(ões) · "+
                               ("sem data definida" if not info["dates"]
                                else str(len(info["dates"]))+" data(s) preservada(s)")+
                               " · retorno ferroviário a confirmar · alteração apenas na sessão.")
                    confirm,cancel=st.columns(2)
                    if confirm.button("Confirmar "+("atualização" if info["already_exists"]
                                                   else "inclusão"),
                                      key="ux45_discovery_confirm_"+rec["destination_id"],
                                      disabled=not picked):
                        try:
                            before=_financial_snapshot(plan,catalog,routes,trip_data,
                                                       live,eurfx,chffx,use_city_rent)
                            result=commit_outing(rec["destination_id"],picked,period,
                                                 confirmed=True)
                            after=_financial_snapshot(active_plan(),catalog,routes,trip_data,
                                                      live,eurfx,chffx,use_city_rent)
                            st.session_state["discovery_last_added"]={
                                "name":result.name,"destination_id":result.destination_id,
                                "attraction_count":result.attraction_count,
                                "period":result.period,"dates":list(result.dates),
                                "action":result.action,"before":before,"after":after}
                            st.session_state["discovery_last_destination"]=rec["destination_id"]
                            st.session_state.pop("ux45_discovery_review",None)
                            st.session_state.pop("ux45_discovery_revision",None)
                            st.rerun()
                        except (ValueError,KeyError) as exc:
                            st.error("Não foi possível confirmar a alteração: "+str(exc))
                    if cancel.button("Cancelar revisão",
                                      key="ux45_discovery_cancel_"+rec["destination_id"]):
                        st.session_state.pop("ux45_discovery_review",None)
                        st.session_state.pop("ux45_discovery_revision",None)
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
    st.caption("Revise atrações e período antes de confirmar a inclusão em Meu planejamento. "
               "A projeção financeira será atualizada apenas após sua confirmação; "
               "o salvamento remoto é separado.")
    live=sync_sources["finance"]["status"]=="live"
    current=_financial_snapshot(plan,catalog,routes,trip_data,live,eurfx,chffx,use_city_rent)
    notice=st.session_state.pop("discovery_last_added",None)
    if notice:
        st.success("✓ "+notice["name"]+(" foi atualizado" if notice.get("action")=="updated"
                   else " foi adicionado")+" em Meu planejamento.")
        st.caption(str(notice.get("attraction_count",0))+" atração(ões) · "+
                   ("sem período definido" if notice.get("period",UNASSIGNED)==UNASSIGNED
                    else "período "+notice["period"])+
                   (" · "+str(len(notice.get("dates",[])))+" data(s) preservada(s)"
                    if notice.get("dates") else " · sem data definida")+
                   " · retorno ferroviário pendente · alteração somente na sessão.")
        before,after=notice["before"],notice["after"]
        delta=after["total"]-before["total"]
        st.caption("Projeção recalculada: "+money(before["total"])+" → "+
                   money(after["total"])+" · alteração "+money(delta)+
                   ". Margem atual: "+money(after["margin"])+".")
        if abs(delta)<0.005:
            st.caption("O total não mudou porque os gastos conhecidos ainda cabem na "
                       "verba de passeios já prevista, ou não há valores novos cotados.")
        continue_col,go_col=st.columns(2)
        if continue_col.button("Continuar descobrindo",key="ux45_discovery_continue"):
            st.session_state.pop("discovery_last_added",None)
            st.rerun()
        go_col.button("Ver no meu roteiro",key="discovery_go_my_outings",
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
