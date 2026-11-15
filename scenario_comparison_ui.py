"""Editorial comparison UI for three real itinerary proposals."""
from __future__ import annotations

from html import escape

import pydeck as pdk
import streamlit as st

from scenario_comparison_model import (scenario_comparison,comparison_table,
                                        PROFILE_WEIGHTS)


def money(value:float)->str:
    return "R$ "+f"{value:,.0f}".replace(",",".")


def _name(key:str,names:dict)->str:
    return names.get(key,key)


def _go_profile(profile:str)->None:
    """Open the selected details immediately, not only an editor far below."""
    opened=st.session_state.get("scenario_open_profile")
    st.session_state["scenario_open_profile"]=None if opened==profile else profile
    if opened!=profile:
        st.session_state["scenario_board_profile"]=profile


def _inline_profile_details(row:dict,option:dict,catalog:dict,plan:dict)->None:
    """Show an actual per-style breakdown directly below its button."""
    destinations={d["id"]:d for d in catalog["destinations"]}
    attractions={a["id"]:a for a in catalog["attractions"]}
    recommendations={r["destination_id"]:r for r in option["new_recommendations"]}
    with st.container(border=True):
        st.markdown("#### Detalhes do "+row["label"])
        st.caption("Esta é uma proposta, não são reservas ou passeios já confirmados.")
        for dest_id,ids in option["proposal_packages"].items():
            dest=destinations.get(dest_id,{"name":dest_id,"country":""})
            official=dest_id in plan["packages"]
            st.markdown("**"+dest["name"]+" · "+dest["country"]+"**")
            st.caption("✓ Já está em Meus passeios" if official else
                       "＋ Pré-selecionado somente nesta simulação")
            for attraction_id in ids:
                attraction=attractions.get(attraction_id)
                if attraction:
                    st.write("• "+attraction["name"])
            rec=recommendations.get(dest_id)
            if rec:
                known=rec["known_costs"]
                st.caption("Bilhetes e transportes históricos conhecidos (casal): "
                           f"€ {known['EUR']:.2f} · CHF {known['CHF']:.2f}")
                if rec["missing"]:
                    st.caption(f"⚠ {len(rec['missing'])} custo(s)/condição(ões) ainda por verificar")
                reasons=rec.get("reasons",[])
                if reasons:
                    st.caption("Motivo: "+reasons[0])
        st.markdown("**Resumo financeiro do estilo**")
        st.write("Custos conhecidos: "+money(row["known_brl"])+
                 " · Projeção global: "+money(row["total_brl"]))
        st.caption("Margem: "+money(row["margin_brl"])+
                   f" · {row['pending_count']} componente(s) sem preço completo")
        st.info("A projeção inclui uma provisão para passeios. A ausência de "
                "custos cotados não significa que um passeio é gratuito.")
        st.caption("Para editar atrações e aplicar este estilo, use a seção "
                   "Personalize uma proposta, logo abaixo do comparador.")


def _cards(model:dict,scenarios:list[dict],catalog:dict,plan:dict)->None:
    st.markdown("#### Escolha o estilo para comparar")
    destination_names={d["id"]:d["name"] for d in catalog["destinations"]}
    attraction_names={a["id"]:a["name"] for a in catalog["attractions"]}
    proposals={option["profile"]:option["proposal_packages"] for option in scenarios}
    cols=st.columns(3,gap="medium")
    for col,row in zip(cols,model["rows"]):
        with col:
            st.markdown(
                "<div class='scenario-style-card'>"
                "<div class='scenario-style-card__eyebrow'>ESTILO DE VIAGEM</div>"
                "<h3>"+escape(row["label"])+"</h3>"
                "<div class='scenario-style-card__count'>"+str(row["destinations"])+" destinos</div>"
                "<p>"+escape(row["explanation"])+"</p></div>",
                unsafe_allow_html=True)
            st.caption(f"{row['new_destinations']} novo(s) · {row['attractions']} atrações "
                       f"· {row['scheduled_days']} dia(s) atribuídos na proposta")
            st.metric("Bilhetes e transportes conhecidos",money(row["known_brl"]))
            st.metric("Projeção global",money(row["total_brl"]))
            st.caption("Margem: "+money(row["margin_brl"])+
                       f" · {row['pending_count']} componente(s) sem custo completo")
            if row["unresolved"]:
                st.caption(f"⚠ {row['unresolved']} passeio(s) sem agenda segura")
            st.markdown("**Passeios pré-selecionados neste estilo**")
            picks=proposals[row["profile"]]
            if not picks:
                st.info("Nenhum passeio sugerido com os filtros atuais.")
            else:
                for destination,attractions in picks.items():
                    official=destination in plan["packages"]
                    st.markdown(("✓ **" if official else "＋ **")+
                                destination_names.get(destination,destination)+"**"+
                                (" · Já está em Meus passeios" if official
                                 else " · Sugestão nova"))
                    st.caption("Atrações: "+(", ".join(attraction_names.get(a,a)
                              for a in attractions) if attractions else "A definir"))
            opened=st.session_state.get("scenario_open_profile")==row["profile"]
            st.button("Fechar detalhes" if opened else "Ver detalhes deste estilo",
                      key="scenario_style_choose_"+row["profile"],
                      on_click=_go_profile,args=(row["profile"],),width="stretch")
            if opened:
                _inline_profile_details(row,next(s for s in scenarios
                                                 if s["profile"]==row["profile"]),
                                        catalog,plan)


def _destinations(model:dict)->None:
    names=model["names"]
    with st.expander("Destinos em comum e exclusivos",expanded=False):
        common=model["shared"]
        st.markdown("**Presentes em mais de um estilo**")
        st.write(", ".join(_name(d,names) for d in common) if common else
                 "Nenhum destino aparece em mais de um cenário.")
        st.markdown("**Exclusivos de cada estilo**")
        for row in model["rows"]:
            places=model["unique_by_profile"][row["profile"]]
            st.write("**"+row["label"]+":** "+
                     (", ".join(_name(d,names) for d in places) if places else
                      "Nenhum destino exclusivo"))
        st.caption("Destinos existentes no seu roteiro são preservados pelos três estilos.")


def _scenario_map(model:dict,catalog:dict,plan:dict)->None:
    show=st.checkbox("Mostrar mapa interativo dos estilos",
                     key="scenario_map_visible",value=False)
    if show:
        options=["Econômico","Equilibrado","Aproveitar ao máximo","União dos estilos"]
        selected=st.selectbox("Mostrar no mapa",options,key="scenario_comparison_map_filter")
        by_label={row["label"]:row for row in model["rows"]}
        ids=(set().union(*(set(r["proposal_destinations"]) for r in model["rows"]))
             if selected=="União dos estilos"
             else set(by_label[selected]["proposal_destinations"]))
        destinations={d["id"]:d for d in catalog["destinations"]}
        points=[]
        base=plan["base_city"]
        if base in destinations:
            d=destinations[base]
            points.append({"name":d["name"],"role":"Base hipotética",
                           "lat":d["lat"],"lon":d["lon"],"color":[35,118,109]})
        for key in sorted(ids):
            if key==base or key not in destinations:continue
            d=destinations[key]
            official=key in plan["packages"]
            points.append({"name":d["name"],"role":"Já no meu roteiro" if official
                           else "Proposta de passeio","lat":d["lat"],"lon":d["lon"],
                           "color":[30,78,111] if official else [194,126,51]})
        if points:
            scatter=pdk.Layer("ScatterplotLayer",data=points,
                get_position="[lon,lat]",get_fill_color="color",get_radius=16000,
                radius_min_pixels=7,radius_max_pixels=16,stroked=True,
                get_line_color=[255,255,255],line_width_min_pixels=2,pickable=True)
            center=destinations[base]
            deck=pdk.Deck(
                map_style="https://basemaps.cartocdn.com/gl/positron-gl-style/style.json",
                initial_view_state=pdk.ViewState(latitude=center["lat"],longitude=center["lon"],
                                                 zoom=5.6),
                layers=[scatter],tooltip={"html":"<b>{name}</b><br/>{role}"})
            st.pydeck_chart(deck,height=340,width="stretch")
        else:
            st.info("Nenhum ponto para exibir.")
        st.caption("Localizações aproximadas do catálogo; o mapa não representa conexões "
                   "reservadas, distâncias rodoviárias ou tempos porta a porta.")


def render_scenario_comparison(plan:dict,scenarios:list[dict],catalog:dict,
                               eurfx:float,chffx:float)->dict:
    names={d["id"]:d["name"] for d in catalog["destinations"]}
    model=scenario_comparison(plan,scenarios,eurfx,chffx,names)
    st.markdown("### Encontre o estilo ideal da nossa viagem")
    st.caption("Compare passeios, experiências e custos. Nenhum cenário modifica "
               "seu roteiro sem sua ação e aprovação.")
    base=names.get(plan["base_city"],plan["base_city"])
    st.caption("Base em estudo: "+base+
               f" · {len(plan['packages'])} passeios escolhidos · teto R$ "+
               plan["budget_scenario"][:-1]+" mil · referências históricas de 2026")
    _cards(model,scenarios,catalog,plan)
    st.markdown("#### O que muda entre os estilos?")
    st.dataframe(comparison_table(model),hide_index=True,width="stretch")
    _destinations(model)
    _scenario_map(model,catalog,plan)
    with st.expander("Como essas sugestões são calculadas?"):
        st.caption("Pontuações editoriais, não cotações reais nem avaliações de qualidade.")
        for row in model["rows"]:
            weights=PROFILE_WEIGHTS[row["profile"]]
            st.write("**"+row["label"]+"** · interesse "+
                     str(weights["interest"])+"%, custo "+str(weights["cost"])+
                     "%, conforto "+str(weights["comfort"])+"%, agenda "+
                     str(weights["schedule"])+"%.")
        st.caption("Cada proposta combina destinos pesquisados e preserva seus passeios "
                   "atuais; cidades não verificadas podem ter custos pendentes.")
    st.caption("A projeção global pode coincidir entre estilos: há uma verba de "
               "excursões já incluída no orçamento. Valores desconhecidos nunca são grátis.")
    return model


def render_financial_breakdown(sim:dict,eurfx:float,chffx:float)->None:
    financial=sim["finance"]
    known=sim["detail"]["total"]["known_by_currency"]
    known_brl=float(known["EUR"])*eurfx+float(known["CHF"])*chffx
    allowance=float(financial["budget_excursions_allowance_brl"])
    st.markdown("#### De onde vêm os valores?")
    col1,col2,col3=st.columns(3)
    col1.metric("Bilhetes e deslocamentos conhecidos",money(known_brl))
    col2.metric("Verba já reservada para passeios",money(allowance))
    col3.metric("Excedente conhecido",money(financial["known_excursions_overage_brl"]))
    if allowance>0:
        st.progress(max(0.,min(1.,known_brl/allowance)))
        st.caption(f"{min(known_brl/allowance*100,100):.0f}% da verba reservada "
                   "representada pelos gastos conhecidos.")
    if known_brl<=allowance:
        st.info("Os custos conhecidos ainda cabem na provisão de passeios. "
                "Isso não significa que todos os gastos estão cotados, "
                "nem que outros estilos custarão o mesmo.")
    if sim["detail"]["total"]["missing"]:
        st.warning(str(len(sim["detail"]["total"]["missing"]))+
                   " componente(s) sem valor completo. Projeção parcial.")
    st.caption("Orçamento do casal: "+money(financial["result"]["total"])+
               " · margem até o teto: "+money(financial["result"]["margin"])+
               ". Os custos acima não são somados novamente à projeção.")


def render_approval_diff(diff:dict,names:dict)->None:
    st.markdown("#### Como ficaria meu roteiro?")
    a,b=st.columns(2)
    a.metric("Atrações atuais",diff["attractions_before"])
    b.metric("Atrações na proposta",diff["attractions_after"],
             delta=diff["attractions_after"]-diff["attractions_before"])
    st.caption("Dias atribuídos: "+str(diff["scheduled_before"])+" → "+
               str(diff["scheduled_after"])+
               " (as novas datas são apenas propostas).")
    st.caption("Bilhetes e transportes conhecidos: "+money(diff["known_before"])+
               " → "+money(diff["known_after"])+".")
    st.caption("Despesas sem valor: "+str(diff["pending_before"])+" → "+
               str(diff["pending_after"])+".")
    st.write("**Passeios que seriam incluídos:** "+
             (", ".join(names.get(k,k) for k in diff["new"]) if diff["new"]
              else "Nenhum novo passeio"))
    st.caption("Projeção global da proposta: "+money(diff["total_after"])+
               " · margem: "+money(diff["margin_after"])+".")
