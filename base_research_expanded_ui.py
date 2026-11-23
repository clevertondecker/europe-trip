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
from data23_france_candidates_model import base_attractions,base_routes
from ux47_photo_ui import photo_markup,photo_credit
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


def _city_housing(city,*,profile_mode=False):
    offers=city["housing_offers"]
    with st.expander(("Moradia e bairros · "+str(len(offers))+" anúncios históricos")
                     if profile_mode else
                     "Moradia · anúncios históricos ("+str(len(offers))+")"):
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
        if profile_mode:
            pack=pack_for_city(load_city_packs(),city["id"])
            neighborhoods=pack["neighborhoods"] if pack else []
            if neighborhoods:
                st.markdown("**Bairros documentados**")
                for item in neighborhoods:
                    st.markdown("**"+item["name"]+"** · [Fonte local]("+
                                item["source_url"]+")")
            else:
                st.caption("Bairros ainda sem referências específicas pesquisadas.")


def _city_routes(city_id,five,rail,*,profile_mode=False):
    destinations={x["id"]:x for x in five["common_destinations"]}
    with st.expander("Trens, logística e passeios" if profile_mode else
                     "Trens e passeios · tempos e fontes"):
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


def _city_profile(city_id,study,*,profile_mode=False):
    profiles=load_profiles(canonical=study)
    p=profile_by_id(profiles,city_id)
    if not profile_mode:
        st.markdown("**Contexto pesquisado:** "+p["summary"])
    pack=pack_for_city(load_city_packs(),city_id)
    if profile_mode and not pack:
        with st.expander("Vida cotidiana, bairros e clima"):
            st.write(p["summary"])
            st.caption("Detalhes de custo, bairros e clima ainda não pesquisados.")
    if pack:
        with st.expander("Vida cotidiana, bairros e clima"):
            if profile_mode:
                st.write(p["summary"])
            d=pack["daily_life"]
            if d["restaurant_two_midrange_eur_2026"] is not None:
                st.caption("Restaurante para dois · referência colaborativa de 2026: "+
                           _money(d["restaurant_two_midrange_eur_2026"]))
                st.markdown("[Fonte de custo]("+d["restaurant_source_url"]+")")
            else:
                st.caption("Cesta de custo de vida equivalente: ainda não pesquisada.")
            # In the individual profile, neighborhood sources are already
            # placed under Moradia; keep the legacy independent explorer intact.
            if not profile_mode:
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
    if not profile_mode:
        _city_sources(p)


def _city_sources(profile,*,profile_mode=False):
    with st.expander("Fontes e metodologia" if profile_mode else
                     "Fontes públicas e limitações"):
        for item in profile["evidence"]:
            st.markdown("• "+item["summary"]+" · [Fonte]("+item["source_url"]+")")
        st.caption("O número de fontes não é nota de qualidade. Valores históricos "
                   "e informações faltantes permanecem identificados.")


@st.cache_data(show_spinner=False,ttl=86400,max_entries=64)
def _candidate_photo_markup(photo:dict,name:str)->str:
    """Cache Wikimedia image URL resolution to avoid network calls on every rerun."""
    return photo_markup(photo,name)


def _candidate_media_and_logistics(city_id:str)->None:
    """Pictures and outbound rail evidence for newly researched home bases."""
    attractions=base_attractions(city_id)
    if not attractions:
        return
    st.markdown("#### Atrações para conhecer")
    st.caption("Fotografias licenciadas e fontes oficiais. A visita não é uma reserva; "
               "bilhetes, acesso local e funcionamento no outono de 2027 ainda pendem de confirmação.")
    for proximity,title in (("local","Atrações na cidade"),("regional","Passeios nas redondezas")):
        group=[a for a in attractions if (a["proximity"]=="local") == (proximity=="local")]
        if not group:
            continue
        with st.expander(title+f" ({len(group)})",expanded=proximity=="local"):
            for attraction in group:
                with st.container(border=True):
                    left,right=st.columns([1,2])
                    with left:
                        st.markdown(_candidate_photo_markup(attraction["photo"],attraction["name"]),
                                    unsafe_allow_html=True)
                        credit=photo_credit(attraction["photo"])
                        if credit:
                            st.caption(credit)
                    with right:
                        st.markdown("**"+attraction["name"]+"**")
                        st.caption(attraction["place"]+" · "+
                            ("Passeio local" if attraction["proximity"]=="local"
                             else "Excursão nas redondezas"))
                        st.write(attraction["notes"])
                        st.markdown("[Fonte turística]("+attraction["source_url"]+")")
    st.markdown("#### Tempos ferroviários pesquisados a partir desta base")
    st.caption("Mínimos de ida publicados em 2026, estação a estação; não são "
               "tempos porta a porta e não confirmam retorno aos fins de semana de 2027.")
    for route in base_routes(city_id):
        mins=route["minimum_oneway_min"]
        label=route["destination_id"].replace("_"," ").title()
        st.markdown("**"+label+"** · "+f"{mins//60}h{mins%60:02d}"+
                    " · [SNCF Connect]("+route["source_url"]+")")
    st.info("As demais combinações ainda não pesquisadas permanecem sem tempo; "
            "não suponha que ausência de dados signifique ausência de trem.")


def _profile_summary_facts(city,study):
    """At most one sourced fact per evidence category, never duplicated paraphrases."""
    profile=profile_by_id(load_profiles(canonical=study),city["id"])
    facts=[]
    seen=set()
    for item in profile["evidence"]:
        category=item.get("section")
        if (category not in ("transport","quality_of_life","remote_work","climate")
                or category in seen or not item.get("summary") or
                not item.get("source_url")):
            continue
        seen.add(category)
        facts.append(item)
        if len(facts)==2:
            break
    return facts


def _render_profile_summary(city,study):
    """Two compact source-backed research facets; no quality/ranking claims."""
    evidence=_profile_summary_facts(city,study)
    st.markdown("#### Pesquisa em resumo")
    left,right=st.columns(2,gap="medium")
    with left:
        with st.container(key="ux109-facts",border=True):
            st.markdown("**Já documentado**")
            if not evidence:
                st.caption("Ainda não há evidências urbanas específicas nesta pesquisa.")
            for item in evidence:
                st.write(item["summary"])
                st.link_button("Fonte: "+item["section"].replace("_"," "),
                               item["source_url"])
    with right:
        with st.container(key="ux109-gaps",border=True):
            st.markdown("**Ainda pendente para 2027**")
            st.write("• Moradia: disponibilidade, contrato, taxas e caução.")
            st.write("• Transporte: retorno, frequência e última milha.")
    st.caption("As referências históricas descrevem o avanço da pesquisa; "
               "não são notas de qualidade da cidade ou cotações para 2027.")


def _render_ux105_profile_context(city_id):
    """Surface UX105 mobility without re-rendering DATA23 regional rail."""
    from ux105_base_city_context import context_for_base
    context=context_for_base(city_id)
    if context is None:
        return
    with st.expander("Mobilidade local e atrações complementares"):
        for item in context["mobility"]:
            st.write(item["label"]+" — "+item["detail"])
            st.markdown("[Fonte de transporte]("+item["source_url"]+")")
        known={item["name"].casefold() for item in base_attractions(city_id)}
        for item in context["attractions"]:
            if item["name"].casefold() not in known:
                st.write(item["name"]+" — "+item["detail"])
                st.markdown("[Fonte da atração]("+item["source_url"]+")")
        st.caption("Referências locais não confirmam horários, volta, tarifas ou "
                   "disponibilidade de 2027.")


def _render_profile_details(city,study,rail,five):
    """Reuse the existing renderers in decision-oriented order."""
    city_id=city["id"]
    st.markdown("### Investigue por assunto")
    _city_housing(city,profile_mode=True)
    if base_routes(city_id):
        # DATA23 has attractions with imagery and regional rail references.
        _candidate_media_and_logistics(city_id)
    else:
        _city_routes(city_id,five,rail,profile_mode=True)
    _render_ux105_profile_context(city_id)
    _city_profile(city_id,study,profile_mode=True)
    p=profile_by_id(load_profiles(canonical=study),city_id)
    _city_sources(p,profile_mode=True)
    st.caption("Limitações gerais: amostras de hospedagem não comprovam contrato para "
               "56–60 noites, taxas ou internet em 2027; tempos de ida não confirmam "
               "retorno nem última milha; dados faltantes não equivalem a zero.")


def _explore_city(study,rail,five,*,fixed_city=None)->None:
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
    h=observed_housing(city)
    if fixed_city is None:
        st.markdown("#### "+city["name"]+" · "+city["country"])
        st.caption(city["corridor"]+" · "+("Finalista" if city["shortlist"] else "Candidata"))
    documented=next(r for r in coverage_matrix("general",study=study) if r["id"]==selected)
    if fixed_city is None:
        a,b=st.columns(2)
        a.metric("Anúncios históricos de 2026",h["count"])
        b.metric("Destinos da pesquisa histórica com referência de tempo",
                 str(documented["route_basket_with_time"])+"/"+str(documented["route_basket_total"]))
    else:
        a,b=st.columns(2,gap="medium")
        with a:
            with st.container(key="ux109-kpi-housing",border=True):
                st.metric("Anúncios históricos de 2026",h["count"])
                st.caption("Amostra documental, não imóveis disponíveis")
        with b:
            with st.container(key="ux109-kpi-rail",border=True):
                st.metric("Destinos com tempo pesquisado",
                          str(documented["route_basket_with_time"])+"/"+
                          str(documented["route_basket_total"]))
                st.caption("Cesta histórica, não destinos do seu roteiro")
    additional=base_routes(selected)
    if additional:
        st.caption(f"{len(additional)} referências adicionais de ida (DATA23/2026), "
                   "fora da cesta histórica; retorno e 2027 não confirmados.")
    if fixed_city is None:
        _city_profile(selected,study)
        _candidate_media_and_logistics(selected)
        _city_housing(city)
        if not base_routes(selected):
            _city_routes(selected,five,rail)
    else:
        _render_profile_summary(city,study)
        _render_profile_details(city,study,rail,five)
    with st.expander("Pesquisa técnica · critérios, pesos e pontuação indisponível"):
        preset=st.segmented_control("Ponderação",["Geral","Econômico","Explorador"],
                                    default="Geral",key="expanded_bases_rank_preset")
        preset_id={"Geral":"general","Econômico":"economy",
                   "Explorador":"explorer"}.get(preset,"general")
        evaluation=next(r for r in coverage_matrix(preset_id,study=study) if r["id"]==selected)
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
    rail=load_rail()
    five=load_five_base_evidence()
    summary=research_overview(study)
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
        _explore_city(study,rail,five,fixed_city=fixed_city)
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
