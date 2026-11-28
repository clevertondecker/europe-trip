"""Display source-backed price observations without converting them into fake quotes."""
from __future__ import annotations

from formatting import brl, _RAISE

import streamlit as st
from research_cost_model import outing_research_snapshot,selected_trip_research,compare_city_bases


def money(v:float)->str:
    return brl(v, decimals=2, missing=_RAISE)


def render_researched_outing(guide:dict,eurfx:float,chffx:float,
                            *,prefix:str)->None:
    band={"economy":"low","balanced":"median","experience":"high"}.get(
        guide.get("profile","balanced"),"median")
    data=outing_research_snapshot(guide,eurfx,chffx,meal_band=band)
    with st.expander("Pesquisa de preços: refeições, transporte e cenários (nov/2026)"):
        st.caption("Dados publicados consultados em "+data["checked_at"]+
                   ". Amostra pequena de restaurantes, não média da cidade. "
                   "Valores não confirmados para 2027.")
        meals=data["meal"]
        st.markdown("**Almoço em restaurantes reais**")
        if not meals["items"]:
            st.warning("Não localizei preços recentes suficientes de restaurantes "
                       "para esta cidade. Alimentação continua sem estimativa.")
        else:
            currency="€" if meals["currency"]=="EUR" else "CHF"
            st.caption(str(meals["count"])+" cardápio(s) independentes · "+
                       "menor "+currency+" "+f"{meals['low']:.2f}"+
                       " · mediana da amostra "+currency+" "+f"{meals['median']:.2f}"+
                       " · maior "+currency+" "+f"{meals['high']:.2f}"+
                       " por pessoa; sem inferir uma média da cidade.")
            for row in meals["items"]:
                st.markdown("• **"+row["venue"]+"** · "+
                            currency+" "+f"{row['price_per_person']:.2f}"+
                            " · "+row["menu"])
                st.caption("Quando: "+row["availability"]+
                           (" · "+row["notes"] if row["notes"] else ""))
                st.markdown("[Ver cardápio original]("+row["source_url"]+")")
            a,b,c=st.columns(3)
            a.metric("Almoço mínimo observado (casal)",
                     money(data["meal_bands_brl"]["low"]))
            b.metric("Mediana observada (casal)",
                     money(data["meal_bands_brl"]["median"]))
            c.metric("Almoço mais caro observado (casal)",
                     money(data["meal_bands_brl"]["high"]))
            st.caption("Conversão ilustrativa R$/€ "+str(eurfx)+
                       " e R$/CHF "+str(chffx)+
                       ". Uma única refeição para o casal: bebidas, café e jantar "
                       "podem não estar incluídos.")

        st.markdown("**Trem: comparação sem desconto e com Carte Fluo**")
        rail=data["rail"]
        if guide["local"]:
            st.caption("Este passeio é na própria cidade-base: não há trem intermunicipal.")
        elif rail["route"] is None:
            st.warning("Sem tarifa normal ou promocional verificada nesta combinação de cidades.")
        else:
            route=rail["route"]
            st.caption("Tarifa promocional observada: € "+
                       f"{route['discounted_eur_person_oneway']:.2f}"+
                       " por pessoa e trecho · "+route["discount_condition"])
            st.markdown("[Fonte ferroviária]("+route["source_url"]+")")
            if rail["regular_roundtrip_eur"] is None:
                st.warning("Tarifa normal do casal não confirmada: não "
                           "converter automaticamente o desconto em preço cheio.")
            else:
                st.write("**Ida e volta do casal sem cartão, referência:** € "+
                         f"{rail['regular_roundtrip_eur']:.2f}")
            if rail["weekend_with_new_card_eur"] is not None:
                st.caption("Exemplo condicionado a fim de semana/feriado e um "
                           "cartão Fluo novo: € "+
                           f"{rail['weekend_with_new_card_eur']:.2f}"+
                           " (bilhetes + cartão de €30). Se já houver cartão "
                           "válido, não comprá-lo novamente.")
        st.markdown("**Transporte urbano: referências opcionais**")
        if data["transit"]:
            for fare in data["transit"]:
                unit="por pessoa/viagem" if fare["unit"]=="person_trip" else "por pessoa/dia"
                cur="€" if fare["currency"]=="EUR" else "CHF"
                st.caption("• "+fare["name"]+" · "+cur+" "+f"{fare['amount']:.2f}"+
                           " "+unit+" · "+fare["notes"])
                st.markdown("[Tarifa oficial]("+fare["source_url"]+")")
        else:
            st.caption("Não há tarifa de transporte urbano pesquisada para este destino.")

        st.markdown("**Quanto daria um passeio com um almoço?**")
        st.caption("Referência escolhida do cardápio observado: "+
                   {"low":"menor preço (Econômico)",
                    "median":"mediana da amostra (Equilibrado)",
                    "high":"maior preço (Aproveitar ao máximo)"}[band]+
                   ". O perfil define qual exemplo usar, não um multiplicador.")
        example=data["lunch_plus_rail_and_known_tickets_brl"]
        if example is None:
            st.warning("Sem subtotal combinável confiável: falta a tarifa normal "
                       "do casal, o almoço publicado ou ambos. Não usar zero.")
        else:
            st.metric("Exemplo parcial: trem normal + ingressos conhecidos + almoço",
                      money(example))
            contingency=st.slider("Reserva adicional de prudência (hipótese, %)",
                                  min_value=0,max_value=30,value=10,step=5,
                                  key=prefix+"_researched_contingency")
            st.caption("Com reserva gerencial de "+str(contingency)+
                       "% sobre o subtotal parcial: "+money(example*(1+contingency/100))+
                       ". NÃO é previsão estatística nem substitui custos desconhecidos.")
        st.warning("Não somar este subtotal diretamente à projeção global: "
                   "alimentação e excursões já possuem rubricas próprias no orçamento. "
                   "Reconciliar o gasto incremental antes de atualizar o teto.")
        st.caption("Não incluídos/completamente verificados: horário real de retorno, "
                   "transporte estação→atrações, bebidas, jantar, possíveis ingressos "
                   "pendentes, pernoite e custos de imprevistos.")


def render_research_summary(plan:dict,catalog:dict,routes:dict,
                            eurfx:float,chffx:float)->None:
    result=selected_trip_research(plan,catalog,routes,eurfx,chffx)
    with st.expander("Ver custos pesquisados de alimentação e transporte dos meus passeios"):
        if not result["parts"]:
            st.caption("Selecione passeios para consultar os preços observados de alimentação.")
            return
        st.caption("Um único almoço por casal e bilhetes/transportes verificados "
                   "quando disponíveis. NÃO é o orçamento completo da viagem.")
        st.metric("Soma parcial de passeios com referências combináveis",
                  money(result["priced_subtotal_brl"]))
        st.caption(str(result["priced_count"])+" de "+str(result["total_count"])+
                   " passeios com trem normal e almoço suficientes para esse subtotal.")
        if result["unpriced_destinations"]:
            st.warning("Sem subtotal combinável: "+
                       ", ".join(result["unpriced_destinations"])+
                       ". Não são passeios gratuitos.")
        st.caption("A projeção global já tem rubricas de alimentação/excursões: "
                   "esta soma não é acrescentada automaticamente para evitar dupla cobrança.")


def render_research_profiles(plan:dict,scenarios:list[dict],catalog:dict,
                             routes:dict,eurfx:float,chffx:float)->None:
    with st.expander("Comparar preços de alimentação pesquisados entre estilos"):
        st.caption("Comparação apenas ilustrativa: cada total inclui uma referência "
                   "de almoço para duas pessoas, ingresso conhecido e trem normal "
                   "quando pesquisado. NÃO incorpora automaticamente à projeção.")
        table=[]
        for option in scenarios:
            pseudo={**plan,"profile":option["profile"],
                    "packages":option["proposal_packages"]}
            result=selected_trip_research(pseudo,catalog,routes,eurfx,chffx)
            table.append({"Estilo":option["label"],
                          "Almoço observado usado":{"economy":"menor",
                            "balanced":"mediana","experience":"maior"}[option["profile"]],
                          "Passeios":result["total_count"],
                          "Com referências combináveis":result["priced_count"],
                          "Soma parcial em R$":result["priced_subtotal_brl"],
                          "Passeios sem total":len(result["unpriced_destinations"])})
        st.dataframe(table,hide_index=True,width="stretch")
        st.warning("As somas são parciais e têm coberturas diferentes. "
                   "Não é correto concluir que o estilo com menor subtotal "
                   "é o mais barato quando há trajetos e refeições sem cotação.")
        st.caption("Refeições em casa já estão contempladas em rubricas do "
                   "orçamento geral: não somar refeições turísticas duas vezes.")


def render_city_base_research(plan:dict,catalog:dict,routes:dict,
                              eurfx:float,chffx:float)->None:
    with st.expander("Comparar cidade-base: mesmo roteiro, custos e horas pesquisados"):
        if not plan["packages"]:
            st.caption("Confirme ao menos um passeio para comparar as quatro bases.")
            return
        names={d["id"]:d["name"] for d in catalog["destinations"]}
        rows=compare_city_bases(plan,catalog,routes,eurfx,chffx)
        display=[]
        for r in rows:
            display.append({
                "Cidade-base":names.get(r["base"],r["base"]),
                "Tempo ferroviário conhecido ida+volta (min)":r["known_train_roundtrip_minutes"],
                "Trajetos sem tempo":len(r["unknown_duration_destinations"]),
                "Passeios com referência de preço":str(r["priced_outings"])+"/"+str(r["total_outings"]),
                "Soma pesquisada parcial (R$)":r["researched_partial_brl"]
            })
        st.dataframe(display,hide_index=True,width="stretch")
        st.warning("Bases com mais trajetos sem horário/tarifa podem parecer "
                   "mais baratas. Comparação NÃO é uma classificação de melhor base; "
                   "as somas têm cobertura diferente.")
        st.caption("Minutos de trem são estação a estação (ida+volta), sem deslocamento "
                   "ao alojamento, conexões, espera ou atrações. Alimentação representa "
                   "um almoço observado, não alimentação completa. Câmbio hipotético.")
