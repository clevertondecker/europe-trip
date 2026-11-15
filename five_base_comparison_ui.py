"""Focused five-base evidence panel, strictly isolated from the approved TripPlan."""
from __future__ import annotations

import streamlit as st

from five_base_comparison_model import (
    BASE_IDS,COUNTRY_FLAGS,base_comparison,housing_sample,
    illustrative_cashflow,load_five_base_evidence,route_observation,
)

LABELS={"housing":"Moradia mobiliada, total 60 noites (€)",
        "groceries":"Compras de supermercado, casal (€)",
        "restaurants":"Restaurantes e cafés, casal (€)",
        "urban":"Transporte urbano, casal (€)",
        "excursions":"Trens, ingressos e passeios, casal (€)",
        "extras":"Taxas não incluídas e reserva de imprevistos (€)"}


def _label(base:dict)->str:
    return COUNTRY_FLAGS.get(base["country"],"")+" "+base["name"]


def _eur(v)->str:
    return "Não cotado" if v is None else "€ "+f"{v:,.2f}".replace(",","_").replace(".",",").replace("_",".")


def render_five_base_study()->None:
    data=load_five_base_evidence()
    bases={b["id"]:b for b in data["housing"]}
    destinations={d["id"]:d for d in data["common_destinations"]}
    window=data["research_window"]
    st.markdown("### Cinco bases prioritárias · mesmas 15 cidades de interesse")
    st.caption("Janela **hipotética**: "+window["arrival_2027_assumption"]+" → "+
               window["departure_2027_assumption"]+" (60 noites). O roteiro oficial "
               "não fixou essa data. A lista de 15 destinos é idêntica para as "
               "cinco bases, mas **NÃO** significa 15 passeios viáveis em cada uma.")
    chosen=st.multiselect("Destinos geográficos a incluir na comparação",
                          list(destinations),default=list(destinations),
                          format_func=lambda id:COUNTRY_FLAGS.get(destinations[id]["country"],"")+
                          " "+destinations[id]["name"],key="five_base_destinations")
    if not chosen:
        st.info("Selecione ao menos um destino para comparar.")
        return
    compared=base_comparison(data,chosen)
    st.markdown("**Tempos ferroviários conhecidos (estação a estação, só ida)**")
    tab=[]
    for summary in compared:
        h=summary["housing"]
        tab.append({
            "Base":_label(bases[summary["base_id"]]),
            "Com duração documentada":str(summary["with_station_times"])+"/"+
                                      str(summary["destinations_count"]),
            "Com tarifa anunciada":summary["with_fare_samples"],
            "Até 60 min, trecho":summary["within_60_station"],
            "Até 90 min, trecho":summary["within_90_station"],
            "Países nos trajetos documentados":summary["country_count_lower_bound"],
            "Anúncios de 30–60 m²":str(h["size_30_to_60_count"])+"/"+
                                      str(h["sample_count"]),
            "Total 60 noites": "Pendente"
        })
    st.dataframe(tab,hide_index=True,width="stretch")
    st.warning("As contagens representam apenas trajetos **com horário observado** e "
               "não comprovam ida e volta em fim de semana de 2027. "
               "Uma base com menos dados NÃO é pior ou mais barata. "
               "Os países são destinos de trajetos publicados, não países "
               "já visitáveis de modo prático para a data de viagem.")

    selected=st.selectbox("Explorar uma das cinco bases",list(BASE_IDS),
                         format_func=lambda id:_label(bases[id]),
                         key="five_base_detail")
    b=bases[selected];h=housing_sample(b)
    st.markdown("#### "+_label(b)+" — referências de aluguel mobiliado")
    st.caption("Três referências diferentes de anúncios publicados em 2026. "
               "Preço por mês observado, não total para duas pessoas por 60 noites; "
               "limpeza, contas, internet, duração mínima e disponibilidade em 2027 "
               "precisam ser confirmadas individualmente.")
    st.caption("Intervalo observado: "+_eur(h["min_eur_month"])+
               " a "+_eur(h["max_eur_month"])+
               "/mês · tamanhos comparáveis 30–60 m²: "+
               str(h["size_30_to_60_count"])+"/3.")
    if h["size_30_to_60_count"]<2:
        st.warning("A amostra contém imóveis de tamanhos pouco comparáveis com "
                   "um apartamento compacto para duas pessoas. A mediana não "
                   "serve para declarar esta base mais cara ou barata.")
    for row in b["listings"]:
        with st.container(border=True):
            st.markdown("**"+row["title"]+"** · "+_eur(row["monthly_eur"])+
                        "/mês · "+str(row["size_m2"])+" m²")
            st.caption("Ocupação para dois: "+
                       ("declarada no catálogo, mas a data não foi checada" if
                        row["two_adults_confirmed"] is True else
                        "não verificada individualmente")+
                       " · Despesas incluídas: "+row["utilities"]+
                       " · Janela de 2027: não confirmada")
            st.markdown("[Consultar fonte do anúncio]("+row["source_url"]+")")

    st.markdown("#### Os mesmos destinos vistos desta base")
    show_unknown=st.checkbox("Mostrar também trajetos ainda sem horários",
                             value=True,key="five_base_show_unknown")
    for dest_id in chosen:
        row=route_observation(data,selected,dest_id)
        if row["status"]=="unresearched" and not show_unknown:
            continue
        where=destinations[dest_id]
        title=COUNTRY_FLAGS.get(where["country"],"")+" "+where["name"]
        if row["status"]=="local_no_intercity_train":
            status="Na própria cidade · transporte até atrações pendente"
        elif row["train_min"] is None:
            status="Trem: não pesquisado · preço desconhecido"
        else:
            status=("Trem mais rápido observado: "+str(row["train_min"])+" min"+
                    (" · regional observado: "+str(row["regional_min"])+" min"
                     if row["regional_min"] is not None else "")+
                    " · tarifa desde: "+_eur(row["fare_from_eur_person_oneway"]))
        st.markdown("**"+title+"** — "+status)
        if row["source_url"]:
            st.markdown("[Fonte de horário ou tarifa]("+row["source_url"]+")")
        if row["status"]!="unresearched":
            st.caption(row["notes"]+" · Retorno em 2027: não verificado")

    st.markdown("#### Cenário financeiro manual (não altera o orçamento oficial)")
    st.caption("Você informa os valores **totais para duas pessoas e 60 noites**. "
               "Não importamos preços de anúncios antigos como se fossem cotações. "
               "Campos em €0 são tratados como **não informados**, não como gastos gratuitos.")
    fx=st.number_input("Câmbio hipotético R$/€",min_value=0.01,max_value=30.0,
                       value=6.3,step=0.1,key="five_base_fx")
    vals={}
    cols=st.columns(2)
    for idx,(key,title) in enumerate(LABELS.items()):
        with cols[idx%2]:
            entered=st.number_input(title,min_value=0.0,max_value=100000.,
                                    value=0.,step=50.,key="five_base_manual_"+key)
        vals[key]=None if entered==0 else entered
    deposit=st.number_input("Caução reembolsável, caixa comprometido (€)",
                            min_value=0.0,max_value=20000.,value=0.,step=100.,
                            key="five_base_deposit")
    vals["refundable_deposit"]=deposit
    scenario=illustrative_cashflow(vals,fx)
    if scenario["missing_categories"]:
        st.warning("Sem orçamento completo: ainda faltam "+", ".join(
            LABELS[k] for k in scenario["missing_categories"])+
            ". O subtotal de categorias preenchidas é parcial.")
        if scenario["known_input_subtotal_eur"] is not None:
            st.metric("Subtotal de hipóteses preenchidas",_eur(
                      scenario["known_input_subtotal_eur"]))
    else:
        st.metric("Soma das seis categorias, apenas hipótese do casal",
                  _eur(scenario["full_six_category_hypothesis_eur"]))
        st.caption("Conversão ilustrativa: R$ "+
                   f"{scenario['full_six_category_hypothesis_brl']:,.2f}"+
                   ". Não inclui Itália/voos, taxas não cadastradas e outras "
                   "obrigações da viagem; não substitui a previsão oficial.")
    st.caption("Caução reembolsável fora das despesas: "+_eur(
               scenario["deposit_cash_eur"])+
               ". Nenhuma opção acima salva roteiro, reserva ou orçamento no GitHub.")
