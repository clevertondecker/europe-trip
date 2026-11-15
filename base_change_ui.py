"""Task-first comparison of an official home base with one hypothetical city."""
from __future__ import annotations
import streamlit as st

from base_change_model import (destination_catalog,destination_impact,
                               impact_summary,planned_destinations,
                               comparable_rent_whatif)
from base_scenario_model import base_options
from base_explorer_model import load_exploration
from base_explorer_ui import _choose_base


def render_base_change(plan:dict,trip_data:dict,finance_live:bool,
                       french_days:int)->None:
    catalog={x["id"]:x["name"] for x in base_options()}
    official=plan["base_city"]
    candidate=st.session_state.get("scenario_base_selected",official)
    if candidate not in catalog:
        candidate=official
    st.markdown("### O que muda ao trocar a cidade-base?")
    a,b,c=st.columns([1,1,1],gap="small")
    a.metric("Base do roteiro",catalog[official])
    b.metric("Cidade em estudo",catalog[candidate])
    c.metric("Período comparado",str(french_days)+" dias · 2 pessoas")
    st.caption("Nenhuma cidade é automaticamente aprovada. "
               "Dados de 2026 são referências históricas, não reservas para 2027.")
    if candidate==official:
        st.info("Escolha outra cidade em **Configurar simulação** no topo "
                "(ative Simulação). Depois compare os impactos aqui.")
    places=destination_catalog()
    defaults=planned_destinations(plan)
    chosen=st.multiselect("Destinos que vocês desejam manter acessíveis",
                          list(places),default=defaults,
                          format_func=lambda k:places[k],
                          key="ux_compare_destinations",max_selections=8)
    if not chosen:
        st.info("Selecione ao menos um destino para avaliar os deslocamentos.")
        return
    rows=destination_impact(plan,candidate,chosen)
    counter=impact_summary(rows)
    a,b,c,d=st.columns(4,gap="small")
    a.metric("Mais fáceis",counter["Melhorou"])
    b.metric("Mais demorados",counter["Piorou"])
    c.metric("Semelhantes",counter["Semelhante"])
    d.metric("Sem pesquisa comparável",counter["Não pesquisado"])
    st.caption("Comparação provisória de tempo mínimo estação a estação; "
               "uma cidade sem rota pesquisada **não** significa destino perdido.")
    st.dataframe([{
        "Destino":r["destination"],
        "Situação":r["status"],
        "Da base oficial (min)":r["official_minutes"] if r["official_minutes"] is not None else "Não pesquisado",
        "Da candidata (min)":r["candidate_minutes"] if r["candidate_minutes"] is not None else "Não pesquisado",
        "Diferença só ida (min)":r["delta_minutes"] if r["delta_minutes"] is not None else "—",
    } for r in rows],hide_index=True,width="stretch",height=300)
    with st.expander("Tarifas, evidências e limitações de cada destino"):
        st.caption("Tarifas históricas 'desde' ou com descontos condicionais. "
                   "Não somamos preços sem condições iguais, nem inferimos valores para o retorno.")
        for r in rows:
            st.markdown("**"+r["destination"]+" · "+r["status"]+"**")
            for label,side in (("Base oficial","official"),("Candidata","candidate")):
                fare=r[side+"_fare"]
                text=(f"€ {fare:.2f} / pessoa / trecho, referência histórica"
                      if fare is not None else "Tarifa não cotada")
                st.caption(label+": "+text+" · "+
                           str(r[side+"_fare_condition"] or "Sem modalidade definida")+
                           " · "+str(r[side+"_basis"] or "Sem data de pesquisa"))
                link=r[side+"_source"]
                if link:
                    st.markdown("[Fonte de "+label.lower()+"]("+link+")")
    st.markdown("### Diferença financeira")
    st.caption("Uma redução no aluguel pode ser anulada por transporte ou passeios. "
               "Sem cotações equivalentes, o total da troca permanece **não calculável**.")
    with st.expander("Simular dois aluguéis informados por vocês",expanded=False):
        st.caption("Preencha os dois valores mensais hipotéticos para o casal. "
                   "São provisões, não anúncios de 2027; outros custos permanecem iguais.")
        first,second=st.columns(2)
        with first:
            official_rent=st.number_input("Aluguel hipotético em "+catalog[official]+" (€ / mês)",
                                         min_value=0.,max_value=10000.,step=50.,
                                         value=0.,key="ux_compare_rent_official")
        with second:
            candidate_rent=st.number_input("Aluguel hipotético em "+catalog[candidate]+" (€ / mês)",
                                          min_value=0.,max_value=10000.,step=50.,
                                          value=0.,key="ux_compare_rent_"+candidate)
        fx=st.number_input("Câmbio de referência (R$/€)",
                           min_value=4.,max_value=10.,value=6.3,
                           step=.05,key="ux_compare_fx")
        result=comparable_rent_whatif(
            plan,trip_data,finance_live,
            official_rent if official_rent>0 else None,
            candidate_rent if candidate_rent>0 else None,
            int(french_days),float(fx))
        if not result["known"]:
            st.info("Informe ambos os aluguéis. Valores desconhecidos não são €0.")
        else:
            st.metric("Variação da moradia (R$) no total parcial",
                      f"{result['delta_brl']:+,.0f}")
            st.caption("Total condicionado às mesmas despesas atuais: "
                       f"R$ {result['official_total_brl']:,.0f} vs. "
                       f"R$ {result['candidate_total_brl']:,.0f}. "
                       "Não inclui novos trajetos, diferenças de alimentação ou reservas.")
            st.warning("Não é economia final calculada: "+
                       "; ".join(result["missing"])+".")
    st.caption("**Decisão oficial:** calendário, transporte Itália → França, hospedagem "
               "e retornos exigem revisão independente dos indicadores acima.")
    _choose_base(load_exploration(),plan,candidate)
