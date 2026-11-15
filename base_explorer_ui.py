"""User-controlled exploration of new French home bases, separate from TripPlan.

No new base is implicitly approved. Existing four bases may be adopted with a
separate explicit confirmation; new bases stay as session-only shortlists.
"""
from __future__ import annotations

import pydeck as pdk
import streamlit as st

from base_explorer_model import (base_opportunities,compare_bases,
                                 load_exploration,route_detail,stay_projection)
from destination_labels import place_label
from base_research_expanded_ui import render_expanded_research
from planning_session import update_fields
from base_scenario_model import base_options, choose_exploratory_base

EXISTING_BASES=frozenset({"mulhouse","strasbourg","metz","nancy"})


def _format_eur(value:float)->str:
    return "€ "+f"{value:,.2f}".replace(",","_").replace(".",",").replace("_",".")


def _format_brl(value:float)->str:
    return "R$ "+f"{value:,.0f}".replace(",",".")


def _base_name(data:dict,base_id:str)->str:
    b=next(x for x in data["bases"] if x["id"]==base_id)
    return place_label(b["name"],b["country"])


def _map_base(data:dict,base_id:str,dest_ids:list[str])->None:
    bases={b["id"]:b for b in data["bases"]}
    destinations={d["id"]:d for d in data["destinations"]}
    origin=bases[base_id]
    pins=[{"name":origin["name"],"lat":origin["lat"],"lon":origin["lon"],
           "type":"Base candidata","color":[42,117,108]}]
    pins += [{"name":destinations[k]["name"],"lat":destinations[k]["lat"],
              "lon":destinations[k]["lon"],"type":"Destino em pesquisa",
              "color":[196,130,61]}
             for k in dest_ids if k in destinations and k!=base_id]
    layer=pdk.Layer("ScatterplotLayer",data=pins,get_position="[lon,lat]",
                    get_fill_color="color",get_radius=10000,
                    radius_min_pixels=7,radius_max_pixels=13,pickable=True)
    deck=pdk.Deck(map_style="https://basemaps.cartocdn.com/gl/positron-gl-style/style.json",
                  initial_view_state=pdk.ViewState(latitude=origin["lat"],
                                                   longitude=origin["lon"],zoom=5.2),
                  layers=[layer],tooltip={"html":"<b>{name}</b><br/>{type}"})
    st.pydeck_chart(deck,height=360,width="stretch")
    st.caption("Marcadores dos centros urbanos, não rotas ferroviárias nem coordenadas "
               "exatas de atrações. Nenhuma conexão é desenhada ou calculada por linha reta.")


def _nearby(data:dict,base_id:str)->None:
    base=next(b for b in data["bases"] if b["id"]==base_id)
    st.markdown("### "+_base_name(data,base_id)+" · "+base["corridor"])
    if base["rent_market_eur_m2"] is None:
        st.caption("Aluguel do mercado residencial comum: sem referência comparável.")
    else:
        st.caption("Aluguel residencial comum de 2026: "+
                   _format_eur(base["rent_market_eur_m2"])+"/m²/mês. "
                   "**Não** é preço de apartamento mobiliado por 2 meses.")
        if base["rent_source_url"]:
            st.markdown("[Fonte do aluguel residencial]("+base["rent_source_url"]+")")
    if not base["official_base"]:
        st.info("Base nova em exploração. Não está habilitada no TripPlan oficial, "
                "pois faltam modelos de custo, atrações e rotas completos.")
    routes=base_opportunities(data,base_id)
    if not routes:
        st.warning("Nenhum trajeto pesquisado para esta base.")
        return
    a,b,c=st.columns(3)
    a.metric("Destinos em pesquisa",len(routes))
    b.metric("Tempo de trem conhecido",str(sum(x["minutes"] is not None for x in routes))+
             "/"+str(len(routes)))
    c.metric("Tarifa de referência disponível",str(sum(x["fare_from"] is not None for x in routes))+
             "/"+str(len(routes)))
    for route in routes:
        dest=route["destination"]
        with st.container(border=True):
            st.markdown("**"+place_label(dest["name"],dest["country"],show_country=True)+"**")
            left,right=st.columns(2)
            left.caption("Trem mais rápido, só ida")
            left.markdown("**"+(str(route["minutes"])+" min" if route["minutes"] is not None
                              else "Não pesquisado")+"**")
            right.caption("Preço anunciado por pessoa/trecho")
            right.markdown("**"+(_format_eur(route["fare_from"])+ " · desde" if
                                route["fare_from"] is not None else "Não cotado")+"**")
            st.caption(route["classification"]+
                       " · Volta em 2027 não verificada · "+route["notes"])
            if route["source_url"]:
                st.markdown("[Fonte do trajeto]("+route["source_url"]+")")
    if st.checkbox("Mostrar mapa dos destinos próximos",key="base_explore_map"):
        _map_base(data,base_id,[r["destination_id"] for r in routes])


def _comparison(data:dict)->None:
    names={b["id"]:_base_name(data,b["id"]) for b in data["bases"]}
    places={d["id"]:place_label(d["name"],d["country"]) for d in data["destinations"]}
    bases=st.multiselect("Quais bases comparar?",
                         list(names),default=["lille","strasbourg","metz","dijon"],
                         format_func=lambda x:names[x],key="base_compare_bases")
    dest=st.multiselect("Manter os mesmos destinos nas comparações",
                        list(places),default=["amsterdam","brussels","colmar","basel"],
                        format_func=lambda x:places[x],key="base_compare_destinations")
    if not bases or not dest:
        st.info("Selecione ao menos uma cidade-base e um destino.")
        return
    st.caption("A mesma lista de destinos é avaliada para cada base. Uma combinação "
               "sem pesquisa não é gratuita nem deve ser classificada como mais rápida.")
    outcomes=compare_bases(data,bases,dest)
    table=[]
    for result in outcomes:
        table.append({
            "Base":names[result["base_id"]],
            "Rotas com tempo":str(result["time_coverage"])+"/"+str(result["destination_count"]),
            "Trem ida+volta conhecido (min)":(result["known_time_minutes"]
                if result["known_time_minutes"] is not None else "Não pesquisado"),
            "Rotas com tarifa":str(result["fare_coverage"])+"/"+str(result["destination_count"]),
            "Somatório condicional 'desde' (€)":(result["illustrative_fare_if_all_min_eur"]
                if result["illustrative_fare_if_all_min_eur"] is not None else "Não cotado"),
            "Todos os trechos com tarifas":("Sim" if result["fully_priced"] else "Não"),
        })
    st.dataframe(table,hide_index=True,width="stretch")
    st.warning("Somas parciais não são comparáveis entre bases com cobertura desigual. "
               "Preços 'desde' consideram hipoteticamente que os quatro bilhetes do casal "
               "custem a tarifa mínima anunciada; não são cotações de ida/volta em 2027. "
               "Tempos são mínimos estação a estação, sem espera nem conexões adicionais.")
    for result in outcomes:
        with st.expander("Detalhes e fontes · "+names[result["base_id"]]):
            for row in result["routes"]:
                st.markdown("**"+places[row["destination_id"]]+"** · "+
                            (str(row["minutes"])+" min só ida" if row["minutes"] is not None
                             else "tempo desconhecido"))
                st.caption(("Se os quatro trechos custassem o mínimo anunciado: "+
                            _format_eur(row["all_legs_at_from_fare_eur"])
                            if row["all_legs_at_from_fare_eur"] is not None
                            else "Preço para o casal não cotado")+
                           " · "+row["classification"]+" · "+row["notes"])
                if row["source_url"]:
                    st.markdown("[Fonte]("+row["source_url"]+")")


def _choose_base(data:dict,plan:dict,base_id:str)->None:
    name=_base_name(data,base_id)
    with st.expander("Guardar preferência / aprovar uma base já suportada"):
        st.caption("Favoritos são salvos **somente nesta sessão**. "
                   "Não alteram o TripPlan nem escrevem no GitHub.")
        if st.button("Guardar "+name+" como base favorita em estudo",
                     key="base_explore_favorite"):
            st.session_state["base_explorer_favorite"]={"base":base_id,
                       "name":name,"status":"research_only",
                       "plan_revision":plan["revision"]}
            st.success("Base favorita registrada nesta sessão, sem alterar o roteiro.")
        favorite=st.session_state.get("base_explorer_favorite")
        if favorite:
            st.info("Em estudo nesta sessão: "+favorite["name"])
        if base_id not in EXISTING_BASES:
            st.warning("Esta cidade ainda não pode ser aplicada ao roteiro oficial "
                       "sem cadastrar hospedagem, atrações e trajetos de todas as telas. "
                       "Você pode guardá-la como favorita para uma futura proposta.")
        elif base_id==plan["base_city"]:
            st.caption("Esta já é a cidade-base do seu roteiro.")
        else:
            approved=st.checkbox("Confirmo que quero trocar a cidade-base "
                                "do meu roteiro oficial para "+name,
                                value=False,key="base_explore_apply_confirmation_"+base_id)
            if st.button("Aplicar base suportada ao roteiro oficial",
                         key="base_explore_apply",disabled=not approved):
                update_fields(base_city=base_id)
                st.success("Base alterada no planejamento desta sessão. "
                           "Revise os transportes e salve explicitamente se desejar.")
                st.rerun()


def _split_stay(data:dict,plan:dict,trip_data:dict,finance_live:bool,
                eurfx:float)->None:
    names={b["id"]:_base_name(data,b["id"]) for b in data["bases"]}
    days=plan["total_days"]-plan["italy_days"]
    st.markdown("### Uma base ou duas?")
    st.caption("Compare o mesmo período francês e as mesmas verbas restantes, "
               "mudando apenas o aluguel **hipotético** e a despesa de transferência. "
               "Não inclui novos bilhetes de passeios nem custos variáveis locais.")
    a,b=st.columns(2)
    with a:
        first=st.selectbox("Primeira base",list(names),
                           index=list(names).index("lille"),
                           format_func=lambda x:names[x],key="base_stay_first")
    with b:
        second=st.selectbox("Segunda base",list(names),
                            index=list(names).index("strasbourg"),
                            format_func=lambda x:names[x],key="base_stay_second")
    split=st.slider("Dias na primeira cidade",min_value=7,max_value=days-7,
                    value=min(20,days-7),step=1,key="base_stay_days_first")
    st.caption(str(split)+" dias em "+names[first]+" + "+str(days-split)+
               " dias em "+names[second]+". O período da França permanece "+str(days)+" dias.")
    col1,col2=st.columns(2)
    with col1:
        rent1=st.number_input("Aluguel mobiliado hipotético da 1ª base (€ / 30 dias)",
                              min_value=0.,max_value=10000.,value=0.,step=50.,
                              key="base_stay_rent_first")
    with col2:
        rent2=st.number_input("Aluguel mobiliado hipotético da 2ª base (€ / 30 dias)",
                              min_value=0.,max_value=10000.,value=0.,step=50.,
                              key="base_stay_rent_second")
    moving=st.number_input("Mudança entre as cidades (€ / casal, uma vez)",
                           min_value=0.,max_value=2500.,value=0.,step=25.,
                           key="base_stay_move")
    with st.expander("Caução e caixa temporariamente comprometido"):
        dep1=st.number_input("Caução da primeira moradia (€)",min_value=0.,
                             value=0.,step=100.,key="base_stay_deposit_first")
        dep2=st.number_input("Caução da segunda moradia (€)",min_value=0.,
                             value=0.,step=100.,key="base_stay_deposit_second")
        st.caption("Caução potencialmente reembolsável é necessidade de caixa, "
                   "não despesa definitiva; não entra no total.")
    if first==second:
        st.warning("Para comparar uma ou duas bases, escolha duas cidades distintas.")
        return
    move_without_cost=st.checkbox("Mudança sem custo financeiro confirmado",
                                  value=False,key="base_stay_move_free") if moving==0 else False
    if rent1<=0 or rent2<=0 or (moving==0 and not move_without_cost):
        st.info("Informe **os dois aluguéis mobiliados** e o custo de mudança. "
                "Sem esses valores, nenhum total será mostrado como estimativa de hospedagem. "
                "Não usamos o aluguel residencial médio como cotação de curta estadia.")
        return
    projection=stay_projection(plan,trip_data,finance_live,eurfx,
                               first,second,split,rent1,rent2,moving,dep1,dep2)
    table=[
        {"Cenário":"Somente "+names[first],"Dias":days,
         "Hospedagem (€)":projection["housing_single_a_eur"],
         "Mudança (€)":0.0,"Projeção parcial (R$)":projection["single_a_total_brl"]},
        {"Cenário":"Somente "+names[second],"Dias":days,
         "Hospedagem (€)":projection["housing_single_b_eur"],
         "Mudança (€)":0.0,"Projeção parcial (R$)":projection["single_b_total_brl"]},
        {"Cenário":names[first]+" + "+names[second],"Dias":str(split)+"+"+
         str(days-split),"Hospedagem (€)":projection["housing_split_eur"],
         "Mudança (€)":projection["move_eur"],
         "Projeção parcial (R$)":projection["split_total_brl"]},
    ]
    st.dataframe(table,hide_index=True,width="stretch")
    x,y=st.columns(2)
    x.metric("Diferença duas bases × apenas 1ª",
             _format_brl(projection["split_delta_vs_a_brl"]))
    y.metric("Cauções no cenário de 2 bases, fora do custo",
             _format_eur(projection["cash_deposit_split_eur"]))
    st.warning("A projeção **não** é custo final da viagem: passagens para os destinos, "
               "taxas de aluguel, serviços, limpeza, eventuais diárias mínimas, "
               "segunda caução, hospedagem para passeios e horários de 2027 "
               "ainda precisam ser cotados. As rubricas antigas de alimentação e "
               "excursões permanecem iguais nos três cenários.")
    if st.button("Guardar esta divisão como proposta em estudo",
                 key="base_stay_save"):
        st.session_state["base_explorer_split_favorite"]={
            "first":first,"second":second,"days_first":split,
            "days_second":days-split,"rent_first":rent1,"rent_second":rent2,
            "moving_eur":moving,"plan_revision":plan["revision"],
            "status":"research_only"}
        st.success("Divisão guardada somente nesta sessão; o roteiro aprovado não mudou.")
    saved=st.session_state.get("base_explorer_split_favorite")
    if saved:
        st.caption("Divisão em estudo nesta sessão: "+
                   names.get(saved["first"],saved["first"])+" + "+
                   names.get(saved["second"],saved["second"]))


def render_base_explorer(plan:dict,trip_data:dict,finance_live:bool,
                         eurfx:float=6.3)->None:
    data=load_exploration()
    st.markdown("## Explorar cidades-base")
    st.caption("Compare corredores de viagem e cidades francesas antes de decidir. "
               "Todas as tarifas/tempos são referências de 2026; nenhuma passagem "
               "ou aluguel mobiliado foi confirmado para setembro–novembro de 2027.")
    names={b["id"]:_base_name(data,b["id"]) for b in data["bases"]}
    options=base_options(data)
    active=plan["base_city"]
    st.caption("**Base oficial atual:** "+names[active]+
               " · **Novas candidatas:** Lille, Arras, Dijon e Reims. "
               "A exploração não altera suas escolhas.")
    mode=st.segmented_control("Modo de exploração",
            ["Destinos próximos","Comparar mesmas viagens","Uma ou duas bases","Pesquisa ampliada"],
            default="Destinos próximos",key="base_explorer_mode")
    if mode=="Destinos próximos" or mode is None:
        candidate=st.session_state.get("scenario_base_selected",active)
        if candidate not in names:
            candidate=active
        selected=st.selectbox("Cidade-base a explorar",list(names),
                index=list(names).index(candidate),format_func=lambda x:names[x],
                key="base_explorer_city")
        st.session_state["scenario_base_selected"]=choose_exploratory_base(selected,options)
        status=next(row["research_status"] for row in options if row["id"]==selected)
        st.caption("Cenário exploratório · "+status+
                   " · não modifica a cidade-base aprovada.")
        _nearby(data,selected)
        _choose_base(data,plan,selected)
    elif mode=="Comparar mesmas viagens":
        _comparison(data)
    elif mode=="Uma ou duas bases":
        _split_stay(data,plan,trip_data,finance_live,eurfx)
    else:
        render_expanded_research()
    st.caption("Dados de origem: pesquisa documentada em 15/11/2026. "
               "Pernoites, horários reais de retorno, tarifas normais e aluguel de "
               "curta duração ainda são pendências. Zero nunca significa preço desconhecido.")
