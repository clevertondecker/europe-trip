"""Evidence-first 30-city research comparison (not an invented score table)."""
from __future__ import annotations

import streamlit as st

from base_research_expanded_model import PRESETS,load_research
from base_coverage_model import (
    LABELS,REQUIREMENTS,coverage_matrix,coverage_summary,UNRESEARCHED,PARTIAL,
)
from five_base_comparison_model import load_five_base_evidence
from city_profiles_ui import render_enriched_city_profiles

from dq31_logistics_evaluation_model import (
    DEFAULT_WEIGHTS, FALLBACK_BASKET, logistics_comparison,
)
from planning_session import active_plan

PROFILE_IDS={"Geral":"general","Economia":"economy","Explorador":"explorer"}

LOGISTICS_WEIGHT_CHOICES = {
    "Logística prioritária · 65/30/5": {"logistics":65,"living_cost":30,"daily_practicality":5},
    "Mais passeios · 75/20/5": {"logistics":75,"living_cost":20,"daily_practicality":5},
    "Mais economia · 50/45/5": {"logistics":50,"living_cost":45,"daily_practicality":5},
}


def _render_dq32_macro_coverage(rows):
    """Opportunity discovery counts, not a quality or reachability ranking."""
    from arch14_macro_coverage_cache import cached_macro_coverage_rows

    st.markdown("### DQ 3.2 · Cobertura ampliada de oportunidades")
    st.caption(
        "Atrações locais identificadas e conexões ferroviárias históricas, "
        "independentemente do nível de detalhamento pedestre. "
        "Contagens medem pesquisa, NÃO qualidade nem passeios viáveis.")
    data=cached_macro_coverage_rows(tuple(row["id"] for row in rows))
    st.dataframe(data,hide_index=True,width="stretch")
    st.caption(
        "Atrações canônicas e novas são contadas separadamente; equivalências "
        "semânticas são reconciliadas sem perder IDs e fontes. "
        "O mesmo universo de destinos é considerado para todas as bases. "
        "Ausência de tempo não é ausência de conexão. "
        "Preservados os pesos exploratórios de logística/custo/praticidade "
        "e as exigências estritas da decisão definitiva.")


def _render_dq31_logistics(rows):
    """Same-basket exploratory facts, without inventing a maturity score."""
    from five_base_comparison_model import load_five_base_evidence

    st.markdown("### Comparação exploratória · logística e custo de vida")
    st.caption(
        "A documentação completa continua necessária para a decisão final, "
        "não para explorar alternativas. Prioridade sugerida: 65% logística, "
        "30% custo de vida e deslocamentos, 5% praticidade cotidiana. "
        "Os pesos orientam a pesquisa; NÃO viram uma nota sem dados comparáveis.")
    preset=st.selectbox("Prioridades da comparação",list(LOGISTICS_WEIGHT_CHOICES),
                        key="ux_dq31_logistics_weights")
    all_destinations=load_five_base_evidence()["common_destinations"]
    names={d["id"]:d["name"] for d in all_destinations}
    selected_from_plan=[key for key in active_plan().get("packages",{})
                        if key in names]
    default=selected_from_plan or [x for x in FALLBACK_BASKET if x in names]
    chosen=st.multiselect(
        "Mesmos destinos para comparar as cidades-base",
        options=list(names),default=default,
        format_func=lambda key:names[key],key="ux_dq31_basket",
        help="Se não houver passeios oficiais nesta cesta, usamos uma seleção "
             "exploratória, sem alterar o planejamento.")
    if not chosen:
        st.info("Selecione ao menos um destino para a comparação.")
        return
    comparison=logistics_comparison(
        [x["id"] for x in rows],
        selected_destinations=chosen,
        weights=LOGISTICS_WEIGHT_CHOICES[preset],
        coverage=rows)
    st.caption("Mesma cesta para todas as cidades: "+
               ", ".join(names[x] for x in comparison["basket"]["ids"])+
               ". Sem retorno de 2027 comprovado, não declaramos bate-volta garantido.")

    summaries=[]
    for row in comparison["rows"]:
        maturity=row["maturity"]["current"]
        stage={"pesquisa_inicial":"Pesquisa inicial",
               "triagem_exploratoria":"Triagem com evidências",
               "comparacao_fundamentada":"Cobertura de triagem ampliada",
               "decisao_definitiva":"Pronta para decisão"}[maturity]
        rent=row["housing_historical_median_eur_month"]
        summaries.append({
            "Cidade-base":row["name"],
            "Maturidade":stage,
            "Trens conhecidos":str(row["train_time_coverage"])+"/"+str(row["basket_size"]),
            "Rotas completas":str(row["complete_itineraries"])+"/"+str(row["basket_size"]),
            "Aluguel histórico (€ / mês)":round(rent) if rent is not None else None,
            "Amostras moradia":row["housing_sample_count"],
            "Vida cotidiana":"Parcial" if row["daily_researched"] else "Pendente",
            "Documentação":f'{row["documentary_weighted_percent"]:.1f}%',
            "Próxima pesquisa":row["missing"][0] if row["missing"] else "Revisão final",
        })
    st.dataframe(summaries,hide_index=True,width="stretch",height=360)
    st.caption("Aluguel: mediana de anúncios históricos não comparáveis, "
               "não cotação de 2027. Uma cidade com 0 rotas conhecidas não "
               "significa que não há trem. 'Rotas completas' exige retorno e "
               "última milha; nenhum tempo de ida foi duplicado.")
    keyed={x["id"]:x for x in comparison["rows"]}
    inspect=st.selectbox("Examinar logística e lacunas da cidade",
                         list(keyed),format_func=lambda i:keyed[i]["name"],
                         key="ux_dq31_city_detail")
    if inspect:
        city=keyed[inspect]
        destrows=[]
        for item in city["routes"]:
            walks=item["station_to_attraction_evidence"]
            destrows.append({
                "Destino":names[item["destination_id"]],
                "Trem (ida histórica, min)":item["oneway_train_min"],
                "Estação → atração": (
                    str(walks[0]["minutes"])+" min · publicado"
                    if walks else "Não pesquisado"),
                "Retorno":"Não verificado",
                "Tempo porta a porta":"Não disponível",
            })
        st.dataframe(destrows,hide_index=True,width="stretch")
        st.caption("Duração publicada de uma caminhada é informação do DESTINO "
                   "e não cria vantagem para uma base. São trajetos incompletos: "
                   "faltam acesso inicial, retorno e conexões.")
        with st.expander("Consultar fontes ferroviárias e bloqueios"):
            for item in city["routes"]:
                if item["train_source_url"]:
                    st.markdown("**"+names[item["destination_id"]]+"** · "+
                                str(item["oneway_train_min"])+" min (ida) · "+
                                "[Fonte]("+item["train_source_url"]+")")
            st.write("**Próximas verificações:** "+"; ".join(city["missing"]))
    st.caption("Não há ranking final neste estágio. O nível C continua exigindo "
               "dados específicos da viagem e hospedagem confirmada.")

CRITERIA_KEYS=list(LABELS)


def _status(row,key):
    entry=row["criteria"][key]
    if entry["documented_count"]==0:return "Não pesquisado"
    return "Parcial" if entry["documented_count"]<entry["requirements_count"] else "Pesquisado"


def _currency(value):
    return "Não documentado" if value is None else "€ "+f"{value:,.0f}".replace(",",".")


def _evidence_table(rows,*,long=False):
    items=[]
    for r in rows:
        housing=r["housing"]
        items.append({
            "Cidade":r["name"],
            "Moradia":_status(r,"temporary_housing"),
            "Trens":str(r["route_basket_with_time"])+"/15 tempos" if
                        r["route_basket_with_time"] else
                        ("Rede pesquisada · tempos pendentes" if
                         r["criteria"]["rail_connectivity"]["documented_count"]
                         else "Não pesquisado"),
            "Passeios":_status(r,"viable_destinations"),
            "Custos":_status(r,"outing_cost"),
            "Vida cotidiana":_status(r,"daily_life_remote_work"),
            "Documentação ponderada":f'{r["documentary_weighted_percent"]:.1f}%',
            "Nota final":"Indisponível",
            "Situação":"Pesquisa parcial" if r["status"]==PARTIAL
                       else "Sem pesquisa",
        })
    return items


def _city_detail(row):
    st.markdown("#### "+row["name"]+" · evidências e pendências")
    a,b,c=st.columns(3)
    a.metric("Moradia histórica",str(row["housing"]["count"])+" observações")
    b.metric("Tempos da mesma cesta",f'{row["route_basket_with_time"]}/15')
    c.metric("Tarifas de ida documentadas",f'{row["route_basket_with_fare"]}/15')
    if row["housing"]["count"]:
        h=row["housing"]
        st.caption("Amostra não representativa do mercado (€/mês): "+
                   _currency(h["minimum_eur_month"])+" a "+
                   _currency(h["maximum_eur_month"])+
                   "; mediana apenas dos registros consultados "+
                   _currency(h["median_eur_month"])+
                   ". Nenhuma hospedagem para 2027 foi cotada integralmente.")
    st.caption("Países com ao menos uma referência de tempo ferroviário: "+
               (", ".join(row["international_countries_with_time"])
                if row["international_countries_with_time"] else
                "nenhum comprovado pela amostra atual")+
               ". Isso NÃO significa retorno viável, nem que os demais países "
               "sejam inacessíveis.")
    for key,item in row["criteria"].items():
        with st.expander(item["label"]+" · "+str(item["documented_count"])+"/"+
                         str(item["requirements_count"])+" requisitos documentais"):
            for check in item["checks"]:
                st.caption(("✓ " if check["documented"] else "○ ")+
                           check["requirement"])
            st.warning("Para pontuar: "+item["scoring_gap"]+
                       ". Dados faltantes não foram considerados zero.")
    with st.expander("Abrir fontes e dados históricos",expanded=False):
        if not row["evidence"]:
            st.info("Ainda não há fonte catalogada para os requisitos desta cidade.")
        else:
            for item in row["evidence"]:
                with st.container(border=True):
                    st.markdown("**"+item["indicator"]+"** · "+LABELS[
                        item["criterion"]])
                    st.caption(("Valor: "+str(item["value"])+" "+
                                str(item["unit"] or "")) if
                               item["value"] is not None else
                               "Referência contextual sem valor numérico")
                    st.caption("Observação: "+str(item["observed_at"] or
                               "data não identificada")+" · Escopo: "+
                               str(item["scope"])+" · Tipo: "+item["kind"])
                    st.markdown("[Ver fonte]("+item["source_url"]+")")
                    st.caption("Limite: "+item["limitation"])
    st.caption("**Por que não há nota final?** Nenhuma das seis métricas de "
               "qualidade está completa e padronizada para comparar os mesmos "
               "indicadores. Amostras de aluguel e horários de ida de 2026 são "
               "pesquisa útil, não ofertas ou itinerários verificados para 2027.")


def _side_by_side(rows):
    choices={r["id"]:r for r in rows}
    shortlist=[r["id"] for r in rows if r["shortlist"]]
    st.markdown("### Comparar duas ou três finalistas")
    picked=st.multiselect("Cidades para comparar",shortlist,
                          default=[x for x in ("mulhouse","strasbourg","offenburg")
                                   if x in choices],
                          max_selections=3,key="ux_30_shortlist_compare",
                          format_func=lambda key:choices[key]["name"])
    if len(picked)<2:
        st.info("Selecione ao menos duas finalistas para comparação.")
        return
    cols=st.columns(len(picked))
    for col,key in zip(cols,picked):
        r=choices[key]
        with col:
            with st.container(border=True):
                st.markdown("**"+r["name"]+"**")
                st.caption("Pesquisa documental ponderada: "+
                           f'{r["documentary_weighted_percent"]:.1f}%'+
                           " · não é nota de qualidade")
                st.caption("Aluguel observado: "+
                           _currency(r["housing"]["median_eur_month"])+
                           "/mês (mediana de amostra histórica)")
                st.caption("Tempos de trem documentados: "+
                           str(r["route_basket_with_time"])+"/15")
                st.caption("Tarifas de ida: "+
                           str(r["route_basket_with_fare"])+"/15")
                st.caption("Países com tempo observado: "+
                           (", ".join(r["international_countries_with_time"])
                            or "Não pesquisado"))
                st.caption("Vida cotidiana: "+
                           _status(r,"daily_life_remote_work"))
                st.caption("Cotações elegíveis para 2027: **nenhuma confirmada**")
    st.caption("As contagens mostram onde há pesquisa, não quantos passeios são "
               "viáveis. Moradia com maior número de anúncios não recebe "
               "automaticamente nota melhor. Preços não comparáveis não são "
               "somados, nem usados para declarar economia.")


def render_weight_coverage()->None:
    st.markdown("### Comparar 30 cidades-base · o que já sabemos")
    st.caption("Casal sem carro, cerca de dois meses de temporada europeia. "
               "Pesquisa e pontuação são indicadores **diferentes**; selecionar "
               "uma cidade aqui não altera o plano oficial.")
    profile=st.segmented_control("O que priorizar?",
                                 list(PROFILE_IDS),key="ux_30_weight_profile",
                                 selection_mode="single")
    profile_id=PROFILE_IDS.get(profile,"general")
    rows=coverage_matrix(profile_id)
    summary=coverage_summary(rows)
    a,b,c,d,e=st.columns(5)
    a.metric("Cidades",summary["cities"])
    b.metric("Com moradia pesquisada",summary["housing_documented"])
    c.metric("Com tempos ferroviários",summary["rail_documented"])
    d.metric("Com critério pontuável",summary["has_comparable_criterion"])
    e.metric("Prontas para decisão",summary["decision_ready"])

    st.info("**Atenção:** o percentual agora mede **progresso documental por "
            "requisito**, não a qualidade da cidade. O antigo 0% vinha da "
            "avaliação de um dicionário vazio para todas as cidades. "
            "A cobertura para pontuação e a nota final continuam indisponíveis "
            "até existirem métricas completas e comparáveis.")
    only=st.checkbox("Priorizar as 12 finalistas",value=True,
                     key="ux_30_only_finalists")
    filtered=[r for r in rows if r["shortlist"]] if only else rows
    _render_dq32_macro_coverage(filtered)
    _render_dq31_logistics(filtered)

    with st.expander("Entenda os seis critérios e seus pesos",expanded=False):
        st.dataframe([{"Critério":LABELS[key],
                       "Peso no perfil (%)":weight,
                       "O que precisamos documentar":len(REQUIREMENTS[key])}
                      for key,weight in zip(CRITERIA_KEYS,PRESETS[profile_id])],
                     hide_index=True,width="stretch")
        st.caption("A ponderação da **documentação** usa os seis pesos originais "
                   "sobre a fração de itens verificados de cada categoria. "
                   "Não redistribui peso de pesquisa faltante. "
                   "Esse indicador não é uma nota de adequação.")
        st.caption("Trens = informações do conjunto fixo de 15 destinos e "
                   "atributos das ligações. Passeios = acesso às atrações e "
                   "necessidade real de retorno ou pernoite. Países = diversidade "
                   "internacional demonstrada, sem repetir a mesma vantagem "
                   "como nota ferroviária.")

    render_enriched_city_profiles(rows,only_finalists=only)
    st.markdown("### Matriz documental detalhada")
    st.markdown("**Matriz de evidências**")
    st.dataframe(_evidence_table(filtered),hide_index=True,width="stretch",
                 height=405)
    st.caption("Cada linha reflete as mesmas regras documentais. Uma cidade sem "
               "ligação pesquisada está como 'Não pesquisado', não como "
               "'Sem ligação'. O índice de documentação não compara a qualidade "
               "dos anúncios ou destinos.")
    lookup={r["id"]:r for r in filtered}
    selected=st.selectbox("Analisar uma cidade",list(lookup),
                          key="ux_30_city_detail",
                          format_func=lambda key:lookup[key]["name"])
    if selected:
        _city_detail(lookup[selected])
    _side_by_side(rows)
    st.markdown("#### Próximos dados que farão diferença")
    st.caption("Prioridade: confirmar, na mesma cesta de 15 destinos, horários "
               "de ida e volta, conexões/última milha, tarifas normais para "
               "duas pessoas; e apartamentos inteiros para 56–60 noites com "
               "internet, taxas, caução e distância à estação. "
               "Coberturas dos outros 18 municípios permanecem visíveis quando "
               "o filtro de finalistas é desativado.")
    st.caption("Fontes legadas: GitHub (JSONs versionados); governança histórica: "
               "Drive Living Europe. Nenhuma decisão de cidade-base foi aplicada.")
