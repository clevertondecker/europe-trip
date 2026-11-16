"""Evidence-led screening UI; no changes to TripPlan, official scores or budget."""
from __future__ import annotations

import streamlit as st
from five_base_comparison_ui import render_five_base_study
from base_coverage_model import coverage_matrix
from exploratory_selection import sync_city_widget, set_city_from_widget

from base_research_expanded_model import (
    COUNTRY_FLAGS,PRESETS,load_research,load_rail,
    decision_readiness,find_city,normalized_score,observed_housing,research_overview,
)


def _money(amount:float|None)->str:
    if amount is None:return "Não cotado"
    return "€ "+f"{amount:,.0f}".replace(",",".")


def render_expanded_research()->None:
    study=load_research()
    rail=load_rail()
    summary=research_overview(study)
    st.markdown("### Pesquisa ampliada: onde morar por 56 a 60 noites?")
    st.caption("Pesquisa em 15/11/2026 · França, Alemanha, Bélgica e Luxemburgo. "
               "Isto é uma **triagem de alternativas**, não um ranking definitivo, "
               "simulação de reserva ou alteração da cidade-base aprovada.")
    left,mid,right=st.columns(3)
    left.metric("Cidades candidatas",summary["candidate_count"])
    mid.metric("Finalistas em investigação",summary["shortlist_count"])
    right.metric("Cotações elegíveis para 2027",summary["three_eligible_2027_quotes"])
    st.warning("Nenhuma cidade dispõe ainda de três hospedagens privativas "
               "confirmadas para 56–60 noites em setembro–novembro de 2027. "
               "Por isso, não atribuí pontuações definitivas de 0 a 100 nem "
               "declarei uma cidade vencedora. Anúncios de 2026 são só amostras.")
    with st.expander("Aprofundamento · Offenburg, Trier, Mulhouse, Strasbourg e Lille",
                     expanded=True):
        render_five_base_study()

    country=st.selectbox("Filtrar país",["Todos"]+
                         sorted(summary["country_counts"]),
                         key="expanded_bases_country_filter")
    only_finalists=st.checkbox("Mostrar somente as 12 finalistas de pesquisa",
                               value=True,key="expanded_bases_only_shortlisted")
    cities=[c for c in study["cities"]
            if (country=="Todos" or c["country"]==country)
            and (not only_finalists or c["shortlist"])]
    rows=[]
    for c in cities:
        h=observed_housing(c)
        rows.append({
            "Cidade":COUNTRY_FLAGS.get(c["country"],"")+" "+c["name"],
            "País":c["country"],
            "Corredor":c["corridor"],
            "Anúncios observados":h["count"],
            "Menor aluguel anunciado/mês":_money(h["minimum_eur_month"]),
            "Mediana da pequena amostra/mês":_money(h["median_eur_month"]),
            "Preço final 56–60 noites":"Não cotado",
            "Ranking confiável":"Pendente"
        })
    st.dataframe(rows,hide_index=True,width="stretch")
    st.caption("Não foram estimados total de 60 noites, caução, limpeza, taxa turística, "
               "internet, elegibilidade contratual e custos do transporte ao alojamento. "
               "A amostra é heterogênea e não representa uma mediana do mercado local.")

    candidates={c["id"]:COUNTRY_FLAGS.get(c["country"],"")+" "+c["name"]
                for c in cities}
    if not candidates:
        st.info("Não há cidade nesta seleção.")
        return
    selected_ids=list(candidates)
    suggested=st.session_state.get("scenario_base_selected")
    if suggested in candidates:
        sync_city_widget("expanded_bases_detail_city",selected_ids)
    selected=st.selectbox("Examinar evidências de uma cidade",selected_ids,
                          index=selected_ids.index(suggested) if suggested in candidates else 0,
                          format_func=lambda id:candidates[id],
                          key="expanded_bases_detail_city",
                          on_change=set_city_from_widget,
                          args=("expanded_bases_detail_city",))
    if suggested in candidates:
        st.session_state["scenario_base_selected"]=selected
    st.caption("Cidade-base hipotética compartilhada com Comparar cidades e Orçamento. "
               "Examinar uma candidata não muda o roteiro oficial.")
    c=find_city(study,selected)
    h=observed_housing(c)
    st.markdown("#### "+candidates[selected]+" · "+c["corridor"])
    if h["count"]<3:
        st.warning("Encontramos menos de três anúncios individuais adequados para "
                   "a triagem inicial. Não completar a amostra com quartos para "
                   "uma pessoa ou municípios vizinhos.")
    if h["count"]:
        for quote in c["housing_offers"]:
            with st.container(border=True):
                st.markdown("**"+quote["observed_title_or_address"]+"** · "+
                            _money(quote["monthly_eur"])+"/mês · "+
                            str(quote["size_m2"])+" m²")
                st.caption("Anúncio de 2026, "
                           +("até 2 adultos declarado" if quote["two_adults_confirmed"]
                             else "ocupação de 2 adultos não comprovada")
                           +". 56–60 noites, taxas e disponibilidade 2027 "
                           "NÃO verificadas; internet e distância até estação pendentes.")
                st.markdown("[Consultar anúncio ou catálogo]("+
                            (quote["listing_url"] or quote["catalogue_url"])+")")
    else:
        st.caption("Ainda não há ofertas de hospedagem comparáveis cadastradas.")
    readiness=decision_readiness(c)
    st.markdown("**O que impede decisão agora**")
    for reason in readiness["reasons"]:
        st.caption("• "+reason)
    if c.get("screening_notes"):
        st.info(c["screening_notes"])

    st.markdown("#### Ranking de 0–100: fórmulas prontas, dados insuficientes")
    preset=st.segmented_control("Ponderação",
                                ["Geral","Econômico","Explorador"],
                                default="Geral",key="expanded_bases_rank_preset")
    preset_id={"Geral":"general","Econômico":"economy",
               "Explorador":"explorer"}.get(preset,"general")
    evaluated=next(row for row in coverage_matrix(preset_id)
                   if row["id"]==selected)
    info=normalized_score(
        {key:evaluated["criteria"][key]["comparable_score"]
         for key in evaluated["criteria"]},preset_id)
    weights=dict(zip(("Moradia temporária","Trens e conexões",
                      "Passeios viáveis","Custo dos passeios",
                      "Vida cotidiana/remoto","Países práticos"),PRESETS[preset_id]))
    st.caption("Pesos (%) · "+", ".join(k+": "+str(v) for k,v in weights.items()))
    st.caption("Pontuação final: **ainda não calculável**. "
               "A fórmula não redistribui o peso de uma categoria ausente "
               "para outra; assim, uma cidade com pouca pesquisa não é "
               "beneficiada artificialmente.")
    st.caption("**Documentação pesquisada:** "+
               f'{evaluated["documentary_weighted_percent"]:.1f}%'+
               " dos requisitos ponderados deste perfil. O valor mede pesquisa "
               "existente, não qualidade de vida ou nota de cidade.")
    st.caption("**Cobertura elegível para pontuação:** "+
               str(info["evidence_weight"])+"%. O critério só entra na "
               "nota quando todos os seus indicadores são suficientemente "
               "completos e comparáveis.")
    st.caption("Na aba Explorar → Comparar → Pesos das 30 cidades, compare "
               "os 15 destinos comuns, os requisitos restantes e as fontes "
               "detalhadas sem modificar a base oficial.")

    st.markdown("#### Amostra ferroviária de operadores")
    st.caption("Dados publicados para **segunda, 16/11/2026**; não representam "
               "horários de sábado nem de 2027, e o último trem de partida "
               "não comprova retorno da atração.")
    rail_rows=[]
    for line in rail["segments"]:
        rail_rows.append({
            "Rota":line["origin"]+" → "+line["destination"],
            "Mais rápido (min)":line["fastest_minutes"],
            "TER regional típico (min)":line["representative_regional_minutes"]
                    if line["representative_regional_minutes"] is not None else "Não verificado",
            "Média do operador (min)":line["average_minutes"],
            "Serviços no dia consultado":line["services_on_sample_day"],
        })
    st.dataframe(rail_rows,hide_index=True,width="stretch")
    for route in rail["segments"]:
        st.markdown("[Horários da operadora · "+route["origin"]+" → "+
                    route["destination"]+"]("+route["source_url"]+")")
    st.caption("Mesmo onde existe frequência alta, o tempo real porta a porta, "
               "as conexões de volta, os custos para duas pessoas e a "
               "sazonalidade continuam a ser verificados para 2027.")
