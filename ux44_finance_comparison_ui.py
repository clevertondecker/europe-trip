"""UX 4.4: optional manual hypotheses alongside existing housing observations."""
from __future__ import annotations
import streamlit as st
from ux44_finance_comparison_model import (
    CATEGORIES,LABELS,compare_city_costs,differences
)

def render_partial_finance(matrix:dict)->None:
    cities=matrix["cities"]
    if len(cities)<2:
        return
    with st.expander("Moradia e custos · simulação parcial para 60 noites"):
        st.caption("Valores em euros para o período completo de 60 noites e duas "
                   "pessoas. Campos vazios significam desconhecido, nunca zero. "
                   "Nenhuma hipótese modifica o orçamento oficial.")
        fx_str=st.text_input("Câmbio de referência (R$/€), opcional",
                             value="",key="ux44_fx",placeholder="Ex.: 6.30")
        entries={}
        for city in cities:
            st.markdown("**"+city["name"]+"**")
            housing=city["housing"]
            if housing["min_eur_month"] is not None:
                st.caption("Amostra histórica de anúncios (€/mês): "+
                           str(housing["min_eur_month"])+" a "+
                           str(housing["max_eur_month"])+
                           ". Não é cotação para 60 noites.")
            else:
                st.caption("Sem referência de moradia documentada.")
            with st.container(border=True):
                inputs={}
                for category in CATEGORIES:
                    value=st.text_input(LABELS[category]+" (€ total)",
                        key="ux44_"+city["id"]+"_"+category,
                        placeholder="Desconhecido · informar hipótese")
                    if value.strip():
                        inputs[category]={"amount":value.strip(),
                                          "basis":"manual_hypothesis"}
                deposit=st.text_input("Caução temporariamente comprometida (€)",
                            key="ux44_"+city["id"]+"_deposit",
                            placeholder="Desconhecido")
                if deposit.strip():
                    inputs["deposit"]=deposit.strip()
                entries[city["id"]]=inputs
        try:
            comparison=compare_city_costs(entries,eur_fx=fx_str or None)
        except ValueError as exc:
            st.error(str(exc))
            return
        rows=[]
        for city in cities:
            c=comparison["cities"][city["id"]]
            rows.append({"Cidade":city["name"],
                         "Subtotal das hipóteses (€)":c["known_subtotal_eur"],
                         "Categorias faltantes":len(c["missing_categories"]),
                         "Custo completo":"Não calculável"})
        st.dataframe(rows,hide_index=True,width="stretch")
        shared=differences(comparison)
        if shared:
            st.caption(str(len(shared))+" categorias com hipóteses fornecidas "
                       "para todas as favoritas. Comparações dependem das mesmas premissas.")
        st.caption("Caução é imobilização temporária de caixa, não despesa. "
                   "As hipóteses não são adicionadas ao orçamento geral, "
                   "que já reserva rubricas de moradia e passeios.")
        st.info("Conclusão: há apenas subtotais hipotéticos. Faltam contratos "
                "comparáveis, tarifas completas e confirmação de retorno para 2027.")
