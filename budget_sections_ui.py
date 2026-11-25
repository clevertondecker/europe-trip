"""Short, non-mutating budget summary and details for UX 3.1 tabs."""
from __future__ import annotations
import streamlit as st
from data_model import calculate_scenario, get_scenario, money_brl
from unified_budget import resolve_french_budget
from official_budget_model import official_budget_for_plan
from quote_research_ui import render_quotes_summary,render_quotes_details
from ux_shared_ui_presentation import page_header, kpi_cards, next_action, section_heading
from ux64_navigation_model import select_public_task


def render_budget_summary(data:dict,plan:dict,finance_live:bool)->None:
    st.markdown(page_header(
        "Visão financeira", "NOSSA EUROPA 2027 · ORÇAMENTO",
        "Consulte as estimativas e a margem do cenário oficial, sempre com contexto de fonte.",
        tag="Valores de referência", variant="compact",
    ),unsafe_allow_html=True)
    official=official_budget_for_plan(data,finance_live,plan)
    if not official["outings_available"]:
        st.warning("Referência da planilha, sem recálculo dos passeios do roteiro. A verba original de passeios permanece incluída; revise a seleção antiga.")
    scenario=official["scenario"]
    cards=kpi_cards([
        {"name":"Teto planejado","value":money_brl(scenario["cap_brl"]),
         "hint":"Cenário oficial · não é gasto","icon":"◎","highlight":True},
        {"name":"Total oficial estimado","value":money_brl(official["total"]),
         "hint":"Referência + excedente conhecido de passeios" if official["outings_available"] else "Planilha · sem recálculo de passeios","icon":"▤"},
        {"name":"Margem oficial","value":money_brl(official["margin"]),
         "hint":"Teto menos projeção parcial","icon":"◈"},
    ])
    with st.container(key="ux84_finance_metrics"):
        for column,markup in zip(st.columns(3,gap="small"),cards):
            column.markdown(markup,unsafe_allow_html=True)
    st.caption("Dois viajantes · Itália e França · valores de referência, "
               "não reservas nem preços finais de setembro–novembro de 2027.")
    if official["margin"] < 0:
        st.warning("A projeção parcial excede o teto.")
    if official["has_unknown_costs"]:
        st.caption("Há componentes de passeio com preço pendente; a margem não é dinheiro livre.")
    if official["planned_days"] != official["reference_days"]:
        st.caption(f'Verba de referência para {official["reference_days"]} dias; roteiro atual de {official["planned_days"]} dias.')
    if not finance_live:
        st.info("Dados financeiros em snapshot histórico. Confirme no Drive antes de reservar.")
    st.markdown(section_heading(
        "DISTRIBUIÇÃO","Principais despesas previstas",
        "Valores de referência por categoria, sem cotação definitiva.",
        variant="compact",
    ),unsafe_allow_html=True)
    rows=[{"Categoria":row["name"],"Valor (R$)":money_brl(row["amount"])}
          for row in scenario["components"]]
    if official["known_excursions_overage_brl"]:
        rows.append({"Categoria":"Excedente conhecido de passeios",
                     "Valor (R$)":money_brl(official["known_excursions_overage_brl"])})
    st.dataframe(rows,hide_index=True,width="stretch",height=265)
    render_quotes_summary(data,plan,finance_live)
    st.markdown(next_action(
        "Compare cenários sem alterar o plano",
        "Simule duração, cidade-base e gastos antes de confirmar decisões.",
        variant="compact",
    ),unsafe_allow_html=True)
    st.button("Abrir simulações",key="ux84_go_simulations",type="primary",
              on_click=select_public_task,args=(st.session_state,"Orçamento","Simulações"))
    st.caption("A referência oficial não muda ao simular alternativas.")


def render_budget_details(data:dict,plan:dict,finance_live:bool)->None:
    scenario=get_scenario(data,plan["budget_scenario"])
    baseline=calculate_scenario(scenario)
    french=resolve_french_budget(scenario,finance_live)
    st.markdown(page_header(
        "Detalhamento financeiro", "NOSSA EUROPA 2027 · ORÇAMENTO",
        "Consulte categorias, fontes e lacunas das estimativas cadastradas.",
        variant="compact",
    ),unsafe_allow_html=True)
    st.caption("Valores originais por categoria. As estimativas de uma simulação "
               "são exibidas na aba Simulações, sem sobrescrever o orçamento oficial.")
    labels={"rent":"Moradia","groceries":"Supermercado","dining":"Restaurantes e bares",
            "transport":"Transporte local","excursions":"Passeios"}
    st.dataframe([{"Categoria":labels[k],"Verba francesa (R$)":money_brl(french["amounts"][k])}
                  for k in ("rent","groceries","dining","transport","excursions")],
                 hide_index=True,width="stretch",height=240)
    st.markdown(section_heading(
        "CUSTOS POR CATEGORIA","Categorias da viagem completa",
        variant="compact",
    ),unsafe_allow_html=True)
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
    render_quotes_details(plan)
    st.link_button("Consultar planilha financeira oficial",
                   data["sources"]["spreadsheet"],width="stretch")
