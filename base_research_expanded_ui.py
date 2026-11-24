"""UX 4.0 phase 1: choose an action before seeing research reports.

Only presentation changes. Research data, TripPlan, quotes, finance, and scores
are all owned by existing unchanged modules.
"""
from __future__ import annotations

import streamlit as st

from base_research_expanded_model import (
    COUNTRY_FLAGS,load_research,find_city,observed_housing,research_overview,
)
from five_base_comparison_model import (
    BASE_IDS,COUNTRY_FLAGS as FIVE_FLAGS,load_five_base_evidence,
)
from five_base_comparison_ui import render_five_base_study
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
        with st.container(key=f"ux53_row_bases_{start}"):
            group=cards[start:start+2]
            cols=st.columns(2, border=True)
            for col,card in zip(cols,group):
                with col:
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
                    with st.container(key=f'ux53_footer_base_{card["id"]}'):
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


def _profile_summary_facts(city,study):
    """Compatibility helper for the existing source-curation contract."""
    from ux124_city_profile_model import profile_summary_facts
    from city_profiles_model import load_profiles,profile_by_id
    return profile_summary_facts(profile_by_id(load_profiles(canonical=study),city["id"]))


def _explore_city(study,*,fixed_city=None)->None:
    if fixed_city is None:
        st.markdown("#### Explore uma cidade")
    options={c["id"]:c for c in study["cities"]}
    if fixed_city is not None:
        if fixed_city not in options:
            st.warning("Cidade não disponível para pesquisa.")
            return
        selected=fixed_city
    else:
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
    if fixed_city is None:
        st.markdown("#### "+city["name"]+" · "+city["country"])
        st.caption(city["corridor"]+" · "+("Finalista" if city["shortlist"] else "Candidata"))
    from ux124_city_profile_ui import render_city_profile
    render_city_profile(selected,research=study)
    if fixed_city is None:
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
        finalists=st.checkbox("Mostrar somente as "+str(sum(c["shortlist"] for c in study["cities"]))+" finalistas",
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
    st.caption(str(len(filtered))+" cidades encontradas nas "+str(len(study["cities"]))+" candidatas.")
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


def render_expanded_research(*,activity_override:str|None=None,compact:bool=False,fixed_city:str|None=None)->None:
    study=load_research(include_candidates=True)
    if compact:
        activity=activity_override or "Explorar uma cidade"
        if activity=="Explorar uma cidade":
            if fixed_city is None:
                st.markdown("### Explorar cidades")
                with st.expander("Ver todas as candidatas e filtrar por país ou região"):
                    _all_candidates(study)
        else:
            st.markdown("### Comparar favoritas")
    else:
        summary=research_overview(study)
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
        five=load_five_base_evidence()
        render_favorite_comparison(study,five)
        with st.expander("Referência: as cinco bases aprofundadas"):
            _five_city_comparison(study,five)
    elif activity=="Explorar uma cidade":
        _explore_city(study,fixed_city=fixed_city)
    else:
        _all_candidates(study)
    if fixed_city is None:
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
