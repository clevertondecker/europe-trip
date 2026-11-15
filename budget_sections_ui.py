"""Short, non-mutating budget summary and details for UX 3.1 tabs."""
from __future__ import annotations
import streamlit as st
from data_model import calculate_scenario, get_scenario, money_brl
from unified_budget import resolve_french_budget


def render_budget_summary(data:dict,plan:dict,finance_live:bool)->None:
    st.markdown("### Orçamento da viagem")
    scenario=get_scenario(data,plan["budget_scenario"])
    baseline=calculate_scenario(scenario)
    a,b,c=st.columns(3,gap="small")
    a.metric("Teto planejado",money_brl(scenario["cap_brl"]))
    b.metric("Total da referência",money_brl(baseline["total"]))
    c.metric("Margem de referência",money_brl(baseline["balance"]))
    st.caption("Dois viajantes · Itália e França · valores de referência, "
               "não reservas nem preços finais de setembro–novembro de 2027.")
    if not finance_live:
        st.info("Dados financeiros em snapshot histórico. Confirme no Drive antes de reservar.")
    st.markdown("**Principais despesas previstas**")
    st.dataframe([{"Categoria":row["name"],"Valor (R$)":round(row["amount"],2)}
                  for row in scenario["components"]],
                 hide_index=True,width="stretch",height=265)
    st.caption("Para testar outra cidade-base, duração, aluguel ou câmbio, "
               "abra a aba **Simulações**. A referência oficial não muda ao simular.")


def render_budget_details(data:dict,plan:dict,finance_live:bool)->None:
    scenario=get_scenario(data,plan["budget_scenario"])
    baseline=calculate_scenario(scenario)
    french=resolve_french_budget(scenario,finance_live)
    st.markdown("### Detalhamento e fontes")
    st.caption("Valores originais por categoria. As estimativas de uma simulação "
               "são exibidas na aba Simulações, sem sobrescrever o orçamento oficial.")
    labels={"rent":"Moradia","groceries":"Supermercado","dining":"Restaurantes e bares",
            "transport":"Transporte local","excursions":"Passeios"}
    st.dataframe([{"Categoria":labels[k],"Verba francesa (R$)":round(french["amounts"][k],2)}
                  for k in ("rent","groceries","dining","transport","excursions")],
                 hide_index=True,width="stretch",height=240)
    st.markdown("**Categorias da viagem completa**")
    st.bar_chart([{"Categoria":r["name"],"Valor (R$)":r["amount"]}
                  for r in scenario["components"]],
                 x="Categoria",y="Valor (R$)",horizontal=True,height=325)
    st.caption("Total de referência: "+money_brl(baseline["total"])+
               " · teto: "+money_brl(scenario["cap_brl"])+
               " · margem: "+money_brl(baseline["balance"]))
    if abs(baseline["rounding_difference"])>.1:
        st.warning("Há diferença de arredondamento no orçamento. Validar planilha.")
    st.warning("Valores não incluem cotações verificadas de hospedagem mobiliada para "
               "60 noites nem todas as viagens de trem. Não classifique informação "
               "desconhecida como €0.")
    st.link_button("Consultar planilha financeira oficial",
                   data["sources"]["spreadsheet"],width="stretch")
