"""UX 4.0 phase 1: choose an action before seeing research reports.

Only presentation changes. Research data, TripPlan, quotes, finance, and scores
are all owned by existing unchanged modules.
"""
from __future__ import annotations

import streamlit as st

from base_research_expanded_model import (
    COUNTRY_FLAGS,PRESETS,load_research,load_rail,find_city,observed_housing,
    decision_readiness,research_overview,normalized_score,
)
from five_base_comparison_model import (
    BASE_IDS,COUNTRY_FLAGS as FIVE_FLAGS,load_five_base_evidence,route_observation,
)
from five_base_comparison_ui import render_five_base_study
from base_coverage_model import coverage_matrix
from city_profiles_model import load_profiles,profile_by_id
from city_research_packs_model import load_city_packs,pack_for_city
from ux41_favorites_ui import render_favorite_comparison
from ux40_research_model import (
    ACTIVITIES,five_base_cards,filter_candidates,evidence_state,
)


def _money(amount):
    return "Não pesquisado" if amount is None else "€ "+f"{amount:,.0f}".replace(",",".")


def _restore_widget(widget_key:str,saved_key:str,default):
    if widget_key not in st.session_state:
        st.session_state[widget_key]=st.session_state.get(saved_key,default)


def _save_widget(widget_key:str,saved_key:str):
    st.session_state[saved_key]=st.session_state[widget_key]


def _open_city(city_id:str)->None:
    """Only UX local widgets; never set scenario_base_selected or TripPlan."""
    st.session_state["ux40_research_activity"]="Explorar uma cidade"
    st.session_state["ux42_city_activity"]="Explorar cidades"
    st.session_state["ux40_selected_city"]=city_id
    st.session_state["expanded_bases_detail_city"]=city_id


def _five_city_comparison(study, five)->None:
    st.markdown("#### Cinco bases aprofundadas")
    st.caption("Mesmos 15 destinos de referência; mais rotas pesquisadas não significa cidade melhor.")
    cards=five_base_cards(study,five)
    for start in (0,2,4):
        group=cards[start:start+2]
        cols=st.columns(2)
        for col,card in zip(cols,group):
            with col:
                with st.container(border=True):
                    st.markdown("**"+FIVE_FLAGS.get(card["country"],"")+" "+card["name"]+"**")
                    st.caption(card["country"]+" · "+card["status"])
                    st.markdown("**"+str(card["with_station_times"])+"/"+
                                str(card["total_destinations"])+
                                "** rotas com tempo de ida documentado")
                    st.caption(str(card["housing_count"])+
                               " anúncios de 2026 · "+
                               str(card["size_comparable_count"])+"/"+
                               str(card["housing_count"])+
                               " na faixa de 30–60 m²")
                    st.caption("Hospedagem 2027: não confirmada")
                    st.button("Abrir detalhes · "+card["name"],
                              key="ux40_open_"+card["id"],
                              on_click=_open_city,args=(card["id"],),
                              use_container_width=True)
    st.caption("As amostras são pequenas; a quantidade de evidências indica "
               "andamento da pesquisa, não preço, segurança ou adequação.")
    with st.expander("Comparação ferroviária completa, 15 destinos e simulação manual"):
        st.caption("Relatório original preservado, incluindo filtros dos 15 destinos, "
                   "referências de imóveis, fontes e simulação financeira apenas hipotética.")
        render_five_base_study()


def _city_housing(city):
    offers=city["housing_offers"]
    with st.expander("Moradia · anúncios históricos ("+str(len(offers))+")"):
        if not offers:
            st.info("Ainda não há anúncios individuais pesquisados.")
        for item in offers:
            st.markdown("**"+item["observed_title_or_address"]+"** · "+
                        _money(item["monthly_eur"])+"/mês · "+
                        str(item["size_m2"])+" m²")
            st.markdown("[Fonte do anúncio ou catálogo]("+
                        (item.get("listing_url") or item["catalogue_url"])+")")
            st.caption("Referência de 2026, sem confirmação de imóvel para "
                       "dois adultos por 56–60 noites em 2027.")


def _city_routes(city_id,five,rail):
    destinations={x["id"]:x for x in five["common_destinations"]}
    with st.expander("Trens e passeios · tempos e fontes"):
        if city_id in BASE_IDS:
            for key,place in destinations.items():
                route=route_observation(five,city_id,key)
                if route["status"]=="unresearched":
                    continue
                name=place["name"]
                duration=route["train_min"]
                st.markdown("**"+name+"** · "+(
                    str(duration)+" min de ida estação–estação" if duration not in (None,0)
                    else "Destino local; última milha ainda não verificada"))
                if route["source_url"]:
                    st.markdown("[Fonte de rota]("+route["source_url"]+")")
            st.caption("A cesta completa de 15 destinos e os filtros originais "
                       "continuam disponíveis na atividade Comparar cidades.")
        else:
            found=False
            for item in rail["segments"]:
                if city_id in (str(item.get("base_id","")),str(item.get("from",""))):
                    found=True
                    st.markdown("**"+str(item["origin"])+" → "+
                                str(item["destination"])+"** · "+
                                str(item["fastest_minutes"])+" min de ida")
                    st.markdown("[Operador]("+item["source_url"]+")")
            if not found:
                st.caption("Para esta cidade, ainda não há trajetos detalhados "
                           "na amostra ferroviária apresentada aqui.")
        st.caption("Datas e horários de retorno aos fins de semana de 2027 "
                   "não foram comprovados; ida não implica bate-volta.")


def _city_profile(city_id):
    profiles=load_profiles()
    p=profile_by_id(profiles,city_id)
    st.markdown("**Contexto pesquisado:** "+p["summary"])
    pack=pack_for_city(load_city_packs(),city_id)
    if pack:
        with st.expander("Vida cotidiana, bairros e clima"):
            d=pack["daily_life"]
            if d["restaurant_two_midrange_eur_2026"] is not None:
                st.caption("Restaurante para dois · referência colaborativa de 2026: "+
                           _money(d["restaurant_two_midrange_eur_2026"]))
                st.markdown("[Fonte de custo]("+d["restaurant_source_url"]+")")
            else:
                st.caption("Cesta de custo de vida equivalente: ainda não pesquisada.")
            for n in pack["neighborhoods"]:
                st.markdown("**"+n["name"]+"** · [Fonte local]("+n["source_url"]+")")
            if not pack["neighborhoods"]:
                st.caption("Sem bairro documentado nesta etapa.")
            climate=pack["climate"]
            months=climate["months_9_10_11"]
            if months:
                st.caption("Clima 1991–2020: estação "+climate["station_name"]+
                           ", não previsão para 2027.")
                st.dataframe([{
                    "Mês":name,"Temperatura média (°C)":months[str(month)]["tmean_c"],
                    "Chuva (mm/mês)":months[str(month)]["precip_mm"]
                } for month,name in ((9,"Setembro"),(10,"Outubro"),(11,"Novembro"))],
                hide_index=True,width="stretch")
                st.markdown("[Fonte climatológica]("+climate["source_url"]+")")
            else:
                st.caption("Normais climáticas comparáveis: pendentes.")
    with st.expander("Fontes públicas e limitações"):
        for item in p["evidence"]:
            st.markdown("• "+item["summary"]+" · [Fonte]("+item["source_url"]+")")
        st.caption("O número de fontes não é nota de qualidade. Valores históricos "
                   "e informações faltantes permanecem identificados.")


def _explore_city(study,rail,five)->None:
    st.markdown("#### Explore uma cidade")
    options={c["id"]:c for c in study["cities"]}
    _restore_widget("expanded_bases_detail_city","ux40_selected_city",next(iter(options)))
    st.selectbox("Cidade para examinar",list(options),
                 key="expanded_bases_detail_city",
                 on_change=_save_widget,
                 args=("expanded_bases_detail_city","ux40_selected_city"),
                 format_func=lambda key:COUNTRY_FLAGS.get(options[key]["country"],"")+
                                        " "+options[key]["name"])
    selected=st.session_state["expanded_bases_detail_city"]
    st.session_state["ux40_selected_city"]=selected
    city=find_city(study,selected)
    h=observed_housing(city)
    st.markdown("#### "+city["name"]+" · "+city["country"])
    st.caption(city["corridor"]+" · "+("Finalista" if city["shortlist"] else "Candidata"))
    a,b=st.columns(2)
    a.metric("Anúncios de 2026",h["count"])
    documented=next(r for r in coverage_matrix("general") if r["id"]==selected)
    b.metric("Tempos ferroviários pesquisados",
             str(documented["route_basket_with_time"])+"/15")
    _city_profile(selected)
    _city_housing(city)
    _city_routes(selected,five,rail)
    with st.expander("Pesquisa técnica · critérios, pesos e pontuação indisponível"):
        preset=st.segmented_control("Ponderação",["Geral","Econômico","Explorador"],
                                    default="Geral",key="expanded_bases_rank_preset")
        preset_id={"Geral":"general","Econômico":"economy",
                   "Explorador":"explorer"}.get(preset,"general")
        evaluation=next(r for r in coverage_matrix(preset_id) if r["id"]==selected)
        weights=dict(zip(("Moradia temporária","Trens e conexões","Passeios viáveis",
                          "Custo dos passeios","Vida cotidiana/remoto",
                          "Países práticos"),PRESETS[preset_id]))
        st.caption("Pesos (%): "+", ".join(k+": "+str(v) for k,v in weights.items()))
        info=normalized_score({k:v["comparable_score"]
                               for k,v in evaluation["criteria"].items()},preset_id)
        st.caption("Documentação ponderada: "+
                   f'{evaluation["documentary_weighted_percent"]:.1f}%'+
                   " · progresso de pesquisa, não qualidade da cidade.")
        st.caption("Cobertura para nota: "+str(info["evidence_weight"])+
                   "%. Nota final indisponível até indicadores comparáveis.")
        for item in decision_readiness(city)["reasons"]:
            st.caption("• "+item)
        if city.get("screening_notes"):
            st.info(city["screening_notes"])
    st.button("Voltar à comparação de favoritas",
              key="ux40_back_compare",on_click=lambda:
              st.session_state.update({"ux40_research_activity":"Comparar cidades",
                                       "ux42_city_activity":"Comparar favoritas"}))


def _all_candidates(study)->None:
    st.markdown("#### Todas as candidatas")
    st.caption("Lista de investigação. A ausência de registros não indica "
               "qualidade inferior nem impossibilidade de moradia.")
    countries=["Todos"]+sorted({c["country"] for c in study["cities"]})
    corridors=["Todos"]+sorted({c["corridor"] for c in study["cities"]})
    col1,col2=st.columns(2)
    with col1:
        _restore_widget("expanded_bases_country_filter","ux40_saved_country","Todos")
        country=st.selectbox("País",countries,key="expanded_bases_country_filter",
                             on_change=_save_widget,
                             args=("expanded_bases_country_filter","ux40_saved_country"))
        _restore_widget("ux40_corridor_filter","ux40_saved_corridor","Todos")
        corridor=st.selectbox("Corredor geográfico",corridors,key="ux40_corridor_filter",
                              on_change=_save_widget,
                              args=("ux40_corridor_filter","ux40_saved_corridor"))
    with col2:
        _restore_widget("expanded_bases_only_shortlisted","ux40_saved_finalists",False)
        finalists=st.checkbox("Mostrar somente as 12 finalistas",
                              key="expanded_bases_only_shortlisted",
                              on_change=_save_widget,
                              args=("expanded_bases_only_shortlisted","ux40_saved_finalists"))
        _restore_widget("ux40_evidence_filter","ux40_saved_evidence","Todas")
        evidence=st.selectbox("Evidências de moradia",
                             ["Todas","Com amostras de moradia","Sem amostras de moradia"],
                             key="ux40_evidence_filter",
                             on_change=_save_widget,
                             args=("ux40_evidence_filter","ux40_saved_evidence"))
    filtered=filter_candidates(study,country=country,only_finalists=finalists,
                               corridor=corridor,evidence=evidence)
    st.caption(str(len(filtered))+" cidades encontradas nas 30 candidatas.")
    st.dataframe([{
        "Cidade":COUNTRY_FLAGS.get(c["country"],"")+" "+c["name"],
        "País":c["country"],"Corredor":c["corridor"],
        "Finalista":"Sim" if c["shortlist"] else "Não",
        "Anúncios históricos":observed_housing(c)["count"],
        "Menor aluguel histórico/mês":_money(observed_housing(c)["minimum_eur_month"]),
        "Mediana da amostra/mês":_money(observed_housing(c)["median_eur_month"]),
        "Preço final 56–60 noites":"Não cotado",
        "Pesquisa de moradia":evidence_state(c),
    } for c in filtered],hide_index=True,width="stretch")
    if filtered:
        key=st.selectbox("Abrir ficha desta lista",[c["id"] for c in filtered],
                         key="ux40_list_selected",
                         format_func=lambda k:next(c["name"] for c in filtered if c["id"]==k))
        st.button("Explorar cidade selecionada",key="ux40_list_open",
                  on_click=_open_city,args=(key,))


def render_expanded_research(*,activity_override:str|None=None,compact:bool=False)->None:
    study=load_research()
    rail=load_rail()
    five=load_five_base_evidence()
    summary=research_overview(study)
    if compact:
        activity=activity_override or "Explorar uma cidade"
        if activity=="Explorar uma cidade":
            st.markdown("### Explorar cidades")
            with st.expander("Ver todas as candidatas e filtrar por país ou região"):
                _all_candidates(study)
        else:
            st.markdown("### Comparar favoritas")
    else:
        st.markdown("### Onde vale mais a pena morar?")
        st.caption("Compare cidades pelo custo de moradia, conexões ferroviárias "
                   "e acesso aos passeios que vocês desejam realizar.")
        a,b,c=st.columns(3)
        a.metric("Candidatas",summary["candidate_count"])
        b.metric("Finalistas",summary["shortlist_count"])
        c.metric("Aprofundadas",len(BASE_IDS))
        st.caption("Pesquisa preliminar baseada em referências históricas. "
                   "Hospedagens e tarifas de 2027 ainda não confirmadas.")
        st.segmented_control("O que você deseja fazer?",ACTIVITIES,
                             default=ACTIVITIES[0],key="ux40_research_activity")
        activity=st.session_state["ux40_research_activity"]
    if activity=="Comparar cidades":
        render_favorite_comparison(study,five)
        with st.expander("Referência: as cinco bases aprofundadas"):
            _five_city_comparison(study,five)
    elif activity=="Explorar uma cidade":
        _explore_city(study,rail,five)
    else:
        _all_candidates(study)
    with st.expander("O que ainda não podemos confirmar · fontes e metodologia"):
        st.markdown("- **Hospedagem:** amostras não validam contrato para "
                    "dois adultos, 56–60 noites, caução, taxas ou internet em 2027.\n"
                    "- **Trens:** duração de ida não confirma volta, última milha "
                    "nem preço total do casal em fim de semana.\n"
                    "- **Comparação:** dados faltantes não equivalem a zero; "
                    "não há nota de cidade ou vencedora definitiva.")
        st.caption("O relatório original e seus filtros de 15 destinos permanecem "
                   "sob detalhes da atividade Comparar cidades. "
                   "Esta página apenas explora alternativas e não modifica o roteiro.")
