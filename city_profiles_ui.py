"""Compact public city profiles. Reuses existing research, not a new planning page."""
from __future__ import annotations

import streamlit as st
from city_profiles_model import load_profiles,profile_by_id
from city_research_packs_model import load_city_packs,pack_for_city

def _eur(value):
    return "Não pesquisado" if value is None else "€ "+f"{value:,.0f}".replace(",",".")


def _pack_details(pack:dict)->None:
    """Research context is readonly, not a rental search or booking promise."""
    with st.expander("Vida cotidiana, custos e trabalho remoto",expanded=True):
        d=pack["daily_life"]
        if d["restaurant_two_midrange_eur_2026"] is not None:
            st.markdown("**Restaurante intermediário para dois (amostra de 2026):** "+
                        _eur(d["restaurant_two_midrange_eur_2026"]))
            st.markdown("[Referência colaborativa histórica]("+d["restaurant_source_url"]+")")
            st.caption("Índice colaborativo: não representa a cesta completa de vida cotidiana nem preço de 2027.")
        else:
            st.caption("Custo de restaurante para dois: sem referência local reutilizável.")
        cowork=pack["remote_work"]["coworking_reference"]
        if cowork:
            st.markdown("**Coworking pesquisado:** "+cowork["name"]+
                        " · "+_eur(cowork["price_eur_2026"])+
                        " / "+cowork["price_basis"])
            st.markdown("[Ver fonte do coworking]("+cowork["source_url"]+")")
            st.caption("Condições: "+cowork["limitations"])
        else:
            st.caption("Coworking: sem oferta concreta pesquisada para esta cidade.")
        st.caption("Internet do imóvel, cesta de supermercado, transporte mensal e horários de trabalho: ainda não validados.")
        climate=pack["climate"]
        months=climate["months_9_10_11"]
        if months:
            st.markdown("**Clima histórico de setembro a novembro (estação próxima)**")
            st.dataframe([{
                "Mês":label,
                "Temperatura média (°C)":months[str(number)]["tmean_c"],
                "Chuva média (mm/mês)":months[str(number)]["precip_mm"]
            } for number,label in ((9,"Setembro"),(10,"Outubro"),(11,"Novembro"))],
                hide_index=True,width="stretch")
            st.caption("Estação "+climate["station_name"]+" · normais 1991–2020, "
                       "não previsão de 2027 nem medição do endereço do imóvel.")
            st.markdown("[Fonte das normais da estação]("+climate["source_url"]+")")
        else:
            st.caption("Clima de setembro a novembro: normais 1991–2020 ainda não extraídas para estação próxima. "
                       "Ausência de dados não equivale a temperatura ou chuva zero.")
    with st.expander("Moradia de 56–60 noites e bairros",expanded=False):
        h=pack["housing"]
        st.caption("Observações históricas de apartamentos: "+
                   str(len(h["historical_listings"]))+
                   " · links de anúncios individuais: "+str(h["individual_listing_urls_count"])+
                   " · estadias verificadas para 2027: 0.")
        for n in pack["neighborhoods"]:
            st.markdown("**"+n["name"]+"** · [Fonte municipal]("+n["source_url"]+")")
            st.caption(n["reason_to_investigate"])
        if not pack["neighborhoods"]:
            st.caption("Bairros para alugar: ainda sem referência municipal específica registrada.")
        st.markdown("**Amostras históricas de imóveis (não cotadas para 2027)**")
        for listing in h["historical_listings"]:
            st.markdown("**"+listing["observed_title_or_address"]+"** — "+
                        _eur(listing["monthly_eur_2026"])+"/mês histórico · "+
                        str(listing["size_m2"])+" m² · "+
                        "[Fonte]("+listing["source_url"]+")")
            st.caption("Anúncio individual rastreável" if listing["source_is_direct_listing"]
                       else "Referência de catálogo, anúncio individual não identificado")
        st.warning("Nenhum anúncio tem confirmados 56–60 noites, ocupação, taxas completas, internet e disponibilidade em 2027.")
    with st.expander("Trem e viagens de fim de semana",expanded=False):
        if not pack["weekend_rail_references"]:
            st.caption("Novas referências de horário não pesquisadas nesta rodada; consulte a matriz ferroviária histórica existente.")
        for rail in pack["weekend_rail_references"]:
            st.markdown("**"+rail["destination_id"].replace("_"," ").title()+"** · "+
                        str(rail["duration_minutes_oneway"])+" min de ida estação–estação")
            st.caption(rail["frequency_description"])
            if rail["fare_eur_oneway_with_condition"] is not None:
                st.caption("Tarifa de ida condicionada: "+
                           _eur(rail["fare_eur_oneway_with_condition"])+
                           " · "+rail["fare_condition"])
            st.markdown("[Conferir operador]("+rail["source_url"]+")")
            st.caption("Retorno de fim de semana, última milha e data de 2027 não confirmados. "
                       "Isto NÃO é uma viagem de bate-volta garantida.")
    with st.expander("Pendências de pesquisa desta cidade"):
        for item in pack["missing"]:
            st.caption("• "+item)

def _profile_card(profile:dict,row:dict):
    st.markdown("#### "+profile["name"]+" · "+profile["country"])
    st.caption(profile["corridor"]+" · "+("Finalista" if profile["shortlist"] else "Em observação"))
    st.write(profile["summary"])
    demographics=profile.get("demographics") or {}
    population=demographics.get("population_municipal")
    if population is not None:
        st.caption("População do município ("+str(demographics["reference_year"])+"): "+
                   f"{population:,}".replace(",",".")+
                   " habitantes · não inclui a aglomeração. "+
                   "[Fonte estatística municipal]("+demographics["source_url"]+")")
    with st.container(border=True):
        st.markdown("**Vida prática durante dois meses**")
        housing=profile["housing"]
        a,b,c=st.columns(3)
        a.metric("Amostras de aluguel (2026)",housing["historical_offer_count"])
        b.metric("Faixa observada / mês",(
            _eur(housing["historical_observed_min_eur_month"])+"–"+
            _eur(housing["historical_observed_max_eur_month"]))
                 if housing["historical_observed_min_eur_month"] is not None else "Pendente")
        c.metric("Tempos ferroviários",str(row["route_basket_with_time"])+"/15")
        st.caption("Anúncios históricos, **não** cotação de apartamento mobiliado para "
                   "56–60 noites em 2027. Amostra pequena e não representativa.")
        st.caption("Tarifas ferroviárias e retorno do fim de semana não estão "
                   "necessariamente validados. Consulte as evidências ferroviárias abaixo.")
    pack=pack_for_city(load_city_packs(),profile["city_id"])
    if pack:
        _pack_details(pack)
    if profile["evidence"]:
        st.markdown("**O que já sabemos com fonte pública**")
        for ev in profile["evidence"]:
            st.write("• "+ev["summary"])
            st.markdown("[Consultar fonte da informação]("+ev["source_url"]+")")
            st.caption("Consulta "+ev["observed_at"]+" · "+ev["limitations"])
    else:
        st.info("Ainda não há descrição municipal específica confirmada nesta rodada; "
                "a cidade continua cadastrada para a próxima pesquisa.")
    st.markdown("**O que falta verificar para decidir**")
    for gap in profile["research_gaps"]:
        st.caption("• "+gap)
    with st.expander("Fonte estatística e contexto de pesquisa"):
        stat=profile["official_statistics_source"]
        st.markdown("Fonte oficial do país para futura consulta municipal: "+
                    "["+stat["name"]+"]("+stat["url"]+")")
        st.caption("O link aponta para a base estatística, **não** comprova que "
                   "um valor específico deste município já foi extraído.")
        st.caption("As notas e indicadores financeiros continuam sendo estimativas "
                   "históricas. A seleção não altera o planejamento oficial.")


def render_enriched_city_profiles(rows:list[dict],*,only_finalists:bool)->None:
    profiles=load_profiles()
    current={r["id"]:r for r in rows}
    ids=[p["city_id"] for p in profiles["cities"] if
         p["city_id"] in current and (p["shortlist"] or not only_finalists)]
    st.markdown("### Conheça as cidades-base")
    st.caption("Perfil para uma estadia aproximada de dois meses, dois adultos, trabalho "
               "remoto e viagens sem carro. A matriz documental fica disponível abaixo.")
    selected=st.selectbox("Cidade para conhecer",ids,
                          key="ux_city_profile_detail",
                          format_func=lambda key:profile_by_id(profiles,key)["name"])
    if selected:
        _profile_card(profile_by_id(profiles,selected),current[selected])
