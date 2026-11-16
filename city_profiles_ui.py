"""Compact public city profiles. Reuses existing research, not a new planning page."""
from __future__ import annotations

import streamlit as st
from city_profiles_model import load_profiles,profile_by_id,compact_comparison

def _eur(value):
    return "Não pesquisado" if value is None else "€ "+f"{value:,.0f}".replace(",",".")

def _profile_card(profile:dict,row:dict):
    st.markdown("#### "+profile["name"]+" · "+profile["country"])
    st.caption(profile["corridor"]+" · "+("Finalista" if profile["shortlist"] else "Em observação"))
    st.write(profile["summary"])
    demographics=profile.get("demographics") or {}
    population=demographics.get("population_municipal")
    if population is not None:
        st.caption("População do município em 2023: "+
                   f"{population:,}".replace(",",".")+
                   " habitantes · não inclui a aglomeração. "+
                   "[Fonte INSEE]("+demographics["source_url"]+")")
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
    st.markdown("### Comparação prática de 2–3 cidades")
    finalists=[p["city_id"] for p in profiles["cities"] if p["shortlist"]]
    shortlist=st.multiselect("Comparar perfis cadastrados",finalists,
                             default=[i for i in ("mulhouse","strasbourg","freiburg") if i in finalists],
                             max_selections=3,key="ux_city_profile_compare",
                             format_func=lambda key:profile_by_id(profiles,key)["name"])
    if len(shortlist)>=2:
        st.dataframe(compact_comparison(profiles,shortlist),
                     hide_index=True,width="stretch")
        st.caption("Faixa de moradia é amostra histórica não comparável à reserva de 2027. "
                   "Sem ranking, economia presumida ou nota final.")
    else:
        st.info("Selecione duas ou três finalistas para comparar seus perfis.")
