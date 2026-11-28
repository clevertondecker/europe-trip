"""Evidence-first weekend/daily shopping and reconciled budget dashboards."""
from __future__ import annotations

from formatting import brl, _RAISE

import streamlit as st

from reconciled_trip_research import (grocery_reference,load_extended_research,
                                      reconcile_researched_itinerary)

def _money(value:float)->str:
    return brl(value, decimals=2, missing=_RAISE)


def render_grocery_and_weekend_examples()->None:
    with st.expander("Supermercado e restaurantes de fim de semana — preços pesquisados"):
        e=load_extended_research()
        st.markdown("**Preços de itens de supermercado (Carrefour França)**")
        basket=grocery_reference(e)
        for item in basket["rows"]:
            st.write("• "+item["item"]+" · "+item["quantity"]+
                     " · € "+f"{item['amount_eur']:.2f}")
            st.markdown("[Preço de referência]("+item["source_url"]+")")
        st.metric("Total desta pequena cesta ilustrativa", "€ "+
                  f"{basket['sample_basket_eur']:.2f}")
        st.warning("Esta cesta é INCOMPLETA: não cobre proteínas, vegetais, frutas, "
                   "refeições, cafés ou mês inteiro. Os preços variam conforme a loja "
                   "e a modalidade de compra. **Não** extrapolar para orçamento mensal.")
        st.markdown("**Exemplos com funcionamento publicado em fim de semana**")
        for item in e["weekend_restaurants"]:
            days="sábado e domingo" if len(item["days"])==2 else (
                "sábado" if item["days"]==["sat"] else "domingo")
            st.write("• "+item["city"].capitalize()+" · "+item["venue"]+
                     " · "+item["menu"]+" · € "+
                     f"{item['price_per_person']:.2f} / pessoa"+
                     " ("+days+")")
            st.markdown("[Cardápio e funcionamento]("+item["source_url"]+")")
        st.caption("Alguns preços representam prato único e outros menu completo. "
                   "Uma reserva ou funcionamento em 2027 não está assegurado.")


def render_reconciled_budget(plan:dict,catalog:dict,routes:dict,
                             financial_data:dict,source_live:bool,
                             eurfx:float,chffx:float,
                             use_city_rent:bool=True)->None:
    with st.expander("Conciliação: passeios, almoço e verbas já previstas"):
        model=reconcile_researched_itinerary(
            plan,catalog,routes,financial_data,source_live,
            eurfx,chffx,use_city_rent)
        st.caption("Compara despesas observadas com as rubricas já reservadas. "
                   "Não substitui preços faltantes por zero nem altera o orçamento salvo.")
        x,y=st.columns(2)
        x.metric("Verba para passeios",_money(model["excursion_allowance_brl"]))
        y.metric("Verba de restaurantes e saídas (período)",_money(model["dining_allowance_brl"]))
        if model["total_count"]==0:
            st.info("Adicione ou adote um passeio para conciliar custos da viagem.")
            return
        st.caption(str(model["priced_count"])+"/"+str(model["total_count"])+
                   " passeios com dados suficientes de trem normal e almoço "
                   "compatível com a data cadastrada.")
        for row in model["outings"]:
            day=row["day"]["date"] or "sem data definida"
            st.markdown("**"+row["destination"].capitalize()+"** · "+day)
            st.caption("Trem normal para o casal: "+
                       (_money(row["normal_rail_couple_brl"]) if
                        row["normal_rail_couple_brl"] is not None else "não cotado")+
                       " · almoço observado: "+
                       (_money(row["meal_couple_brl"]) if
                        row["meal_couple_brl"] is not None else "não cotado")+
                       " · ingressos conhecidos: "+_money(row["verified_ticket_brl"]))
            if row["meal_examples"]:
                st.caption("Exemplos do dia (não reservas): "+
                           ", ".join(m["venue"]+" "+m["menu"]+" "+
                                     str(m["price_per_person"])+" "+m["currency"]
                                     for m in row["meal_examples"]))
        st.caption("Almoços já comparados à verba existente: "+
                   _money(model["covered_lunch_brl"])+
                   " · trem/ingressos já cobertos pela provisão: "+
                   _money(model["covered_excursions_brl"]))
        if not model["can_compare_all"]:
            st.warning("Não há projeção global conciliada: faltam dados suficientes "
                       "para "+", ".join(model["unpriced_destinations"])+
                       ". Uma tarifa desconhecida NÃO é uma passagem gratuita.")
        else:
            st.metric("Projeção de referência parcialmente conciliada (2026)",
                      _money(model["partial_reference_projection_brl"]))
            st.caption("Variação indicativa versus projeção atual: "+
                       _money(model["indicated_increment_brl"])+
                       ". Esse valor não é previsão completa de 2027.")
        st.warning("Ainda fora do subtotal: "+", ".join(model["excluded_costs"])+
                   ". A projeção de referência não é aplicada automaticamente ao roteiro.")


def render_reconciled_profiles(plan:dict,scenarios:list[dict],catalog:dict,
                               routes:dict,financial_data:dict,source_live:bool,
                               eurfx:float,chffx:float,use_city_rent:bool)->None:
    with st.expander("Conciliar os três estilos com restaurantes e excursões"):
        rows=[]
        for option in scenarios:
            draft={**plan,"profile":option["profile"],
                   "packages":option["proposal_packages"],
                   "assignments":option["preview_assignments"]}
            model=reconcile_researched_itinerary(
                draft,catalog,routes,financial_data,source_live,
                eurfx,chffx,use_city_rent)
            rows.append({"Perfil":option["label"],
                         "Cobertura":str(model["priced_count"])+"/"+str(model["total_count"]),
                         "Almoços observados (R$)":model["observed_lunch_brl"],
                         "Trem+ingressos publicados (R$)":model["documented_rail_and_tickets_brl"],
                         "Projeção ilustrativa (R$)":model["partial_reference_projection_brl"]})
        st.dataframe(rows,hide_index=True,width="stretch")
        st.warning("Somatórios parciais não são comparáveis entre perfis quando "
                   "a cobertura de rotas, dias e refeições é diferente. "
                   "A comparação não altera seu orçamento oficial.")
