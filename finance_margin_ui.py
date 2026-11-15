"""Read-only Streamlit view for finance margin diagnostics."""
import streamlit as st
def render_finance_margin_summary(metrics:dict,*,profile:str)->None:
    st.markdown("#### Orçamento de passeios · "+profile)
    a,b,c=st.columns(3)
    a.metric("Margem geral",f"R$ {metrics['budget_margin_brl']:,.0f}")
    b.metric("Custos conhecidos",f"R$ {metrics['known_spend_brl']:,.0f}")
    c.metric("Saldo nominal de excursões",f"R$ {metrics['known_allowance_remaining_brl']:,.0f}")
    st.progress(min(1.0,metrics["utilization_pct"]/100),
                text=f"{metrics['utilization_pct']:.1f}% da provisão utilizada por gastos conhecidos")
    st.caption(metrics["coverage_caveat"])
    if metrics["pending_count"]:
        st.warning(f"{metrics['pending_count']} itens sem cotação completa.")
