"""Small REC04 context panel inside existing budget and recommendation screens."""
from __future__ import annotations
import streamlit as st
from rec04_simulation_handoff import ERROR,valid_context,return_to_source,return_to_official
from rec04_candidate_capabilities import capability_for


def render_simulation_context(plan):
    state=st.session_state
    message=state.pop(ERROR,None)
    if message:
        st.warning(message)
    ctx=valid_context(state)
    if ctx is None:
        return
    cap=capability_for(ctx["city_id"])
    with st.container(border=True):
        st.markdown("#### Simulação exploratória · "+cap["name"])
        st.caption("Base oficial continua "+plan["base_city"].title()+
                   ". Nenhuma escolha aqui altera TripPlan, reservas ou dados privados.")
        if not cap["detailed_budget_supported"]:
            st.warning("Orçamento específico da cidade ainda indisponível. "
                       "A simulação abaixo usa provisões gerais, não preço local.")
        else:
            st.info("Matriz de passeios disponível, mas moradia e transporte em 2027 "
                    "ainda não estão confirmados.")
        st.caption("Pendências: "+"; ".join(cap["missing"]))
        left,right=st.columns(2)
        left.button("Voltar à pesquisa anterior",key="rec04_return_to_source",
                    on_click=return_to_source,args=(state,))
        right.button("Ver orçamento oficial",key="rec04_return_to_official",
                     on_click=return_to_official,args=(state,))
        from rec05_priority_research_ui import render_research_from_session
        render_research_from_session(key="rec05_budget",base_ids=[ctx["city_id"]])


def render_optional_housing_commitments(fx,city_id,*,disabled=False):
    """Opt-in, city-scoped and hypothetical; None means not provided."""
    from rec04_housing_costs import housing_cashflow
    with st.expander("Caução reembolsável e taxas separadas (opcional)"):
        st.caption("Informe somente valores conhecidos ou hipóteses explícitas para "
                   "o casal. O desconhecido permanece não informado; nenhuma "
                   "caução é considerada despesa.")
        checked=st.checkbox("Simular caução e taxas desta cidade",
                            key="rec04_housing_terms_"+city_id,disabled=disabled)
        fee=deposit=None
        if checked and not disabled:
            fee=st.number_input("Taxas únicas não reembolsáveis (€)",
                                min_value=0.,max_value=10000.,value=0.,step=50.,
                                key="rec04_fees_"+city_id)
            deposit=st.number_input("Caução reembolsável (€)",
                                    min_value=0.,max_value=15000.,value=0.,step=50.,
                                    key="rec04_deposit_"+city_id)
            st.caption("Taxas são somadas uma vez ao custo total; caução somente "
                       "ao desembolso inicial, antes do eventual reembolso.")
    return housing_cashflow(fx_brl_per_eur=fx,fees_eur=fee,
                            refundable_deposit_eur=deposit)


def render_housing_cashflow_note(result, terms):
    from rec04_housing_costs import housing_cashflow
    if terms["refundable_deposit_brl"] is None:
        st.caption("Caução reembolsável e taxas não informadas: o total não "
                   "representa o caixa necessário ao entrar na moradia.")
        return
    gross=round(result["total"]+terms["refundable_deposit_brl"],2)
    st.caption("Taxa não reembolsável hipotética incluída UMA vez no total: R$ "+
               f'{terms["one_time_fee_expense_brl"]:,.2f}'+
               " · caução reembolsável fora do custo: R$ "+
               f'{terms["refundable_deposit_brl"]:,.2f}')
    st.info("Desembolso bruto de referência incluindo caução: R$ "+
            f'{gross:,.2f}'+
            ". Valor não é cotação final; a caução poderá ser devolvida conforme contrato.")
