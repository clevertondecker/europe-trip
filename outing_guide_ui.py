"""Reusable, compact travel guide from the canonical catalog and route matrix."""
from __future__ import annotations

import streamlit as st
import pydeck as pdk

from destination_labels import place_label
from outing_guide_model import additional_estimate
from planning_session import select_package


def _money(value:float)->str:
    return "R$ "+f"{value:,.0f}".replace(",",".")


def _currency(eur:float,chf:float)->str:
    return f"€ {eur:.2f} · CHF {chf:.2f}"


def _add_optional(destination_id:str,selected_ids:list[str],optional_id:str)->None:
    """Only explicit user action mutates the official itinerary."""
    select_package(destination_id,selected_ids+[optional_id])


def _render_map(guide:dict)->None:
    base=guide["base_name"]
    destination=guide["destination"]
    # Only the destination's city coordinates are documented; these pins
    # deliberately do not suggest a pedestrian or railway route.
    points=[{"name":destination["name"],"role":"Cidade do passeio",
             "lat":destination["lat"],"lon":destination["lon"],"color":[198,132,58]}]
    if guide["local"]:
        st.caption("A origem e o destino são a mesma cidade. "
                   "Locais exatos das atrações ainda não possuem coordenadas verificadas.")
    else:
        # No second pin: base coords must come from the catalog model, not inference.
        st.caption("Ponto aproximado do centro da cidade de destino; "
                   "não representa rota de trem nem percurso a pé.")
    layer=pdk.Layer("ScatterplotLayer",data=points,get_position="[lon,lat]",
                    get_fill_color="color",get_radius=9000,radius_min_pixels=10,
                    radius_max_pixels=14,pickable=True)
    deck=pdk.Deck(map_style="https://basemaps.cartocdn.com/gl/positron-gl-style/style.json",
                  initial_view_state=pdk.ViewState(latitude=destination["lat"],
                                                   longitude=destination["lon"],zoom=10),
                  layers=[layer],tooltip={"html":"<b>{name}</b><br>{role}"})
    st.pydeck_chart(deck,height=260,width="stretch")


def render_outing_guide(guide:dict,*,key_prefix:str,
                        eurfx:float=6.3,chffx:float=7.1,
                        allow_add_optional:bool=False)->None:
    """One consistent detail block for confirmed, suggested and draft outings.

    Expense what-if inputs live only in widget state: never alter the official
    total or write a guessed price back into the research catalog.
    """
    mins=guide["train_minutes_one_way"]
    route=guide["route"]
    a,b,c=st.columns(3,gap="small")
    a.metric("Trem de ida",str(mins)+" min" if mins is not None else
             ("Local" if guide["local"] else "Não verificado"))
    b.metric("Visita às atrações",str(guide["visit_minutes_editorial"])+" min")
    c.metric("Custos conhecidos (casal)",
             _money(guide["known_cost"]["EUR"]*eurfx+
                    guide["known_cost"]["CHF"]*chffx))
    st.caption("Tempo de visita editorial; trem somente estação a estação. "
               "O subtotal é histórico e incompleto, não preço final de 2027.")
    with st.expander("Ver guia completo: como chegar, atrações e custos",expanded=False):
        st.markdown("#### Como chegar de "+guide["base_name"])
        st.write("**"+("Visita local" if guide["local"] else "Modalidade em pesquisa: trem")+"** · "+
                 guide["feasibility"])
        st.caption("Origem: "+route["departure_point"]+
                   " · Chegada: "+route["arrival_point"])
        if mins is not None:
            st.write(f"Tempo publicado: **{mins} min de ida**; "
                     f"**{guide['roundtrip_train_minutes_station_only']} min** "
                     "de ida + volta apenas no trecho ferroviário.")
        else:
            st.warning("Tempo de viagem não verificado para esta cidade-base. "
                       "Não é possível calcular o deslocamento total.")
        fare=guide["fare_eur_person_oneway"]
        if fare is not None:
            st.write(f"Tarifa histórica: **€ {fare:.2f} por pessoa e trecho**.")
            if guide["fare_type"]=="discount_carte_fluo":
                st.warning("Tarifa condicionada à Carte Fluo; elegibilidade e "
                           "valor do cartão não incluídos. Não equivale à tarifa cheia.")
        elif not guide["local"]:
            st.caption("Tarifa da conexão entre a base e o destino ainda não cotada.")
        st.caption("Distância ferroviária/rodoviária: "+
                   (f"{guide['distance_km_documented']} km documentados" if
                    guide["distance_km_documented"] is not None else "não verificada")+
                   ". Conexões: "+(str(route["transfers"]) if route["transfers"] is not None
                                   else "não verificadas")+
                   ". Tempo estação → atrações: "+
                   (str(route["first_last_mile_minutes"])+" min" if
                    route["first_last_mile_minutes"] is not None else "desconhecido")+".")
        st.caption("Retorno no dia/fim de semana: "+
                   ("documentado" if route["weekend_return_verified"]
                    else "a confirmar em horários oficiais")+
                   " · Pesquisa da rota: "+str(guide["route_checked_at"]))
        st.markdown("[Consultar fonte ferroviária]("+guide["route_source"]+")")

        st.markdown("#### Principais pontos do passeio")
        st.caption("Ordem de apresentação do catálogo, não uma rota a pé otimizada. "
                   "As durações são hipóteses editoriais.")
        for i,attraction in enumerate(guide["selected"],start=1):
            st.markdown(f"**{i}. {attraction['name']}** · {attraction['category']}")
            st.write(attraction["summary"])
            st.caption("Tempo sugerido: "+str(attraction["visit_minutes"])+" min"+
                       (" · Horário de visita não verificado" if
                        attraction["opening_hours"] is None else
                        " · Verificar horário oficial"))
            ticket=attraction["ticket"]
            if ticket["status"]=="operator_published":
                st.caption("Ingresso histórico: "+
                           ticket["currency"]+" "+str(ticket["amount"])+
                           " por "+str(ticket["per"])+
                           " · "+str(ticket.get("validity") or "validade a verificar"))
            elif ticket["status"]=="not_applicable":
                st.caption("Visita externa/espaço público: sem bilhete no subtotal; "
                           "atividades internas podem ser pagas.")
            else:
                st.caption("Ingresso: preço não verificado.")
            if attraction.get("source_urls"):
                st.markdown("[Fonte da atração]("+attraction["source_urls"][0]+")")
        st.caption("Somatório das visitas: "+str(guide["visit_minutes_editorial"])+
                   " min, **sem** almoço, deslocamentos entre atrações, filas, "
                   "acesso à estação ou margem de espera.")

        st.markdown("#### Mais atrações para considerar")
        if not guide["optional"]:
            st.caption("Nenhuma atração adicional disponível no catálogo deste destino.")
        for extra in guide["optional"][:3]:
            st.write("**"+extra["name"]+"** · "+extra["summary"])
            if allow_add_optional and len(guide["selected"])<5:
                st.button("＋ Adicionar "+extra["name"],key=key_prefix+"_add_"+extra["id"],
                          on_click=_add_optional,
                          args=(guide["destination_id"],
                                [a["id"] for a in guide["selected"]],extra["id"]))
            else:
                st.caption("Sugestão opcional: não incluída automaticamente no seu roteiro.")

        st.markdown("#### Custos para duas pessoas")
        st.write("Transporte intermunicipal conhecido: "+
                 _currency(guide["known_transport"]["EUR"],guide["known_transport"]["CHF"]))
        st.write("Ingressos conhecidos: "+
                 _currency(guide["known_admission"]["EUR"],guide["known_admission"]["CHF"]))
        st.write("**Subtotal documentado:** "+
                 _currency(guide["known_cost"]["EUR"],guide["known_cost"]["CHF"]))
        if guide["conditional"]:
            st.caption("Condições tarifárias: "+"; ".join(guide["conditional"]))
        st.markdown("**Ainda precisa pesquisar**")
        for missing in guide["missing"]:
            st.caption("• "+missing)
        st.caption("Alimentação, traslados urbanos, retorno não verificado, bilhetes "
                   "pendentes e possíveis pernoites NÃO estão incluídos no subtotal.")
        if st.checkbox("Simular meus gastos extras (opcional)",
                       key=key_prefix+"_extra_enabled"):
            food=st.number_input("Alimentação por pessoa (€)",min_value=0.,
                    max_value=300.,step=5.,value=25.,
                    key=key_prefix+"_food")
            local=st.number_input("Transporte local por pessoa (€)",min_value=0.,
                    max_value=200.,step=2.,value=5.,
                    key=key_prefix+"_local")
            extras=st.number_input("Outros gastos para o casal (€)",min_value=0.,
                    max_value=1000.,step=5.,value=0.,
                    key=key_prefix+"_extras")
            simulation=additional_estimate(guide,eur_fx=eurfx,chf_fx=chffx,
                dining_per_person_eur=food,local_transport_per_person_eur=local,
                extra_for_couple_eur=extras)
            st.metric("Cenário pessoal (não incorporado ao orçamento)",
                      _money(simulation["scenario_brl"]))
            st.warning("Os valores acima são apenas as hipóteses que você digitou; "
                       "o custo final ainda pode ter passagens e outras despesas pendentes.")
        if st.checkbox("Ver localização aproximada no mapa",
                       key=key_prefix+"_show_map"):
            _render_map(guide)
        st.caption("Catálogo consultado: "+str(guide["catalog_checked_at"])+
                   ". Consulte horários e condições para a data real de 2027.")
