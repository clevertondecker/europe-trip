"""UX 4.1: exploratory favorites, same-basket city matrix, private continuity.

No official plan mutation and no public repository persistence.
"""
from __future__ import annotations
import streamlit as st

from base_research_expanded_model import COUNTRY_FLAGS
from city_profiles_model import load_profiles
from city_research_packs_model import load_city_packs
from ux41_favorites_model import (
    validate_favorites,set_favorites,export_favorites,import_favorites,
    comparative_matrix,comparison_insights,
)


def _remember_favorites(study):
    selected=list(st.session_state["ux41_favorites_widget"])
    st.session_state["ux41_favorites"]=set_favorites(
        st.session_state.get("ux41_favorites",[]),selected,study)
    st.session_state["ux36_cloud_dirty"]=True


def _set_favorites(ids,study):
    st.session_state["ux41_favorites"]=set_favorites(
        st.session_state.get("ux41_favorites",[]),ids,study)
    st.session_state["ux41_favorites_widget"]=list(ids)
    st.session_state["ux36_cloud_dirty"]=True


def _open_favorite_city(city_id):
    st.session_state["ux40_research_activity"]="Explorar uma cidade"
    st.session_state["ux40_selected_city"]=city_id
    st.session_state["expanded_bases_detail_city"]=city_id


def _label(value):
    return "Sem dado comparável" if value is None else str(value)


def _currency(value):
    return "Não pesquisado" if value is None else "€ "+f"{value:,.0f}".replace(",",".")


def _brief_matrix(matrix):
    cities=matrix["cities"]
    if len(cities)<2:
        st.info("Escolha duas ou três favoritas para compará-las lado a lado.")
        return
    headers=[c["name"] for c in cities]
    labels={
        "Anúncios históricos":lambda c:str(c["housing"]["observations_2026"]),
        "Faixa histórica (€/mês)":lambda c:(
            _currency(c["housing"]["min_eur_month"])+" a "+
            _currency(c["housing"]["max_eur_month"]) if
            c["housing"]["min_eur_month"] is not None else "Não pesquisado"),
        "Amostras 30–60 m²":lambda c:str(c["housing"]["size_30_to_60"])+"/"+
            str(c["housing"]["observations_2026"]),
        "Dois adultos documentados":lambda c:str(c["housing"]["two_adults_documented"])+"/"+
            str(c["housing"]["observations_2026"]),
        "Tempos na cesta selecionada":lambda c:
            str(c["documented_shared_basket"])+"/"+
            str(c["selected_destinations_count"]) if c["id"] in
            ("offenburg","trier","mulhouse","strasbourg","lille") else "Sem matriz equivalente",
        "Custo de vida comparável":lambda c:"Ainda não disponível",
        "Coworking pesquisado":lambda c:(
            c["daily"]["coworking_reference"]["name"] if
            c["daily"]["coworking_reference"] else "Não pesquisado"),
        "Bairros com fontes":lambda c:str(len(c["daily"]["neighborhoods"]))+
            " referência(s)" if c["daily"]["neighborhoods"] else "Não pesquisado",
        "Clima histórico set–nov":lambda c:(
            "Estação "+str(c["daily"]["climate_station"]) if
            c["daily"]["climate_months"] else "Não pesquisado"),
        "Estadia 2027":lambda c:"Não confirmada",
        "Retorno ferroviário":lambda c:"Não confirmado",
    }
    table=[]
    for label,fn in labels.items():
        row={"Indicador":label}
        row.update({c["name"]:fn(c) for c in cities})
        table.append(row)
    st.dataframe(table,hide_index=True,width="stretch",
                 height=430)
    st.caption("Faixas de anúncios são amostras pequenas e heterogêneas, não "
               "média do mercado. Mais rotas pesquisadas não significa acesso melhor.")


def _routes(matrix):
    cities=matrix["cities"]
    with st.expander("Passeios desejados: mesma cesta, tempos de ida e lacunas"):
        if not matrix["destinations"]:
            st.info("Escolha ao menos um destino para avaliar viagens.")
            return
        for d in matrix["destinations"]:
            name=next(r["destination_name"] for r in cities[0]["routes"]
                      if r["destination_id"]==d)
            st.markdown("**"+name+"**")
            cols=st.columns(len(cities))
            for col,c in zip(cols,cities):
                route=next(r for r in c["routes"] if r["destination_id"]==d)
                with col:
                    st.caption(c["name"])
                    if route["status"]=="documented_oneway":
                        st.write(str(route["duration_min_oneway"])+" min · ida")
                        if route["regional_min_oneway"] is not None:
                            st.caption("Regional documentado: "+
                                       str(route["regional_min_oneway"])+" min")
                    elif route["status"]=="local":
                        st.caption("Destino na própria cidade; acesso local não validado")
                    else:
                        st.caption("Ainda não pesquisado na mesma matriz")
                    if route["source_url"]:
                        st.markdown("[Fonte ferroviária]("+route["source_url"]+")")
        st.caption("Duração mínima isolada não comprova bate-volta, retorno, "
                   "tarifa válida ou acesso porta a porta.")


def _details(matrix):
    with st.expander("Moradia, infraestrutura, fontes e limitações"):
        for c in matrix["cities"]:
            st.markdown("**"+c["name"]+"**")
            st.caption("Moradia: "+str(c["housing"]["observations_2026"])+
                       " anúncios históricos. Nenhuma cotação para 2027.")
            daily=c["daily"]
            if daily["restaurant_two_eur_2026"] is not None:
                st.markdown("Restaurante para duas pessoas (colaborativo, 2026): "+
                            _currency(daily["restaurant_two_eur_2026"])+
                            " · [Fonte]("+daily["restaurant_source_url"]+")")
            else:
                st.caption("Refeição para duas pessoas: sem referência local comparável.")
            for n in daily["neighborhoods"]:
                st.markdown("• "+n["name"]+" · [Fonte]("+n["source_url"]+")")
            cowork=daily["coworking_reference"]
            if cowork:
                st.caption("Coworking pesquisado: "+cowork["name"]+
                           ". Horários/contrato e internet do imóvel não confirmados.")
                st.markdown("[Fonte do coworking]("+cowork["source_url"]+")")
            st.caption("Lacunas: "+", ".join(c["data_missing"]))
            st.divider()


def _persistence(study):
    with st.expander("Guardar ou recuperar minhas favoritas"):
        selected=st.session_state.get("ux41_favorites",[])
        st.download_button("Baixar favoritas (JSON)",
            data=export_favorites(selected,study),
            file_name="nossa-europa-favoritas.json",
            mime="application/json",key="ux41_favorites_export")
        uploaded=st.file_uploader("Recuperar favoritas de um arquivo",
                                   type=["json"],key="ux41_favorites_import_file")
        if uploaded and st.button("Importar favoritas",key="ux41_favorites_import"):
            try:
                imported=import_favorites(uploaded.getvalue(),study)
                st.session_state["ux41_pending_import"]=imported
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))
        from continuity_ui import _private_store,save_private_now
        from private_continuity_store import StorageUnavailable,StorageConflict
        if _private_store() is None:
            st.caption("Sem login/armazenamento privado configurado, a seleção "
                       "permanece nesta sessão. Baixe o JSON para continuar depois.")
        else:
            if st.button("Salvar favoritas no espaço privado",
                         key="ux41_favorites_cloud_save"):
                try:
                    from planning_session import active_plan
                    from attractions_model import load_attractions
                    save_private_now(active_plan(),load_attractions())
                    st.success("Favoritas incluídas no backup privado confirmado.")
                except StorageConflict:
                    st.error("Conflito entre sessões. Exporte suas favoritas antes de tentar novamente.")
                except (StorageUnavailable,ValueError,TypeError,KeyError):
                    st.error("Não foi possível salvar. Use o arquivo de favoritas.")
            st.caption("O salvamento privado usa a cópia existente do projeto, "
                       "sem mudar a cidade-base aprovada.")


def render_favorite_comparison(study,five):
    st.markdown("#### Minhas cidades favoritas")
    choices={c["id"]:c for c in study["cities"]}
    pending=st.session_state.pop("ux41_pending_import",None)
    if pending is not None:
        _set_favorites(pending,study)
        st.session_state["ux41_import_notice"]=True
    if st.session_state.pop("ux41_import_notice",False):
        st.success("Favoritas recuperadas nesta sessão; salve no espaço privado ou baixe o JSON.")
    saved=validate_favorites(st.session_state.get("ux41_favorites",[]),study)
    # Widget lifetime is shorter than session lifetime when activities change.
    if "ux41_favorites_widget" not in st.session_state:
        st.session_state["ux41_favorites_widget"]=list(saved)
    selected=st.multiselect("Selecione até três cidades para comparar",
        list(choices),max_selections=3,key="ux41_favorites_widget",
        on_change=_remember_favorites,args=(study,),
        format_func=lambda key:COUNTRY_FLAGS.get(choices[key]["country"],"")+
                                " "+choices[key]["name"])
    if list(selected)!=saved:
        st.session_state["ux41_favorites"]=list(selected)
    st.caption(str(len(selected))+"/3 favoritas · seleção exploratória, "
               "sem aprovação de cidade-base ou alteração do roteiro.")
    if not selected:
        st.info("Escolha suas primeiras favoritas. As cinco cidades mais "
                "aprofundadas continuam logo abaixo como referência.")
    else:
        st.markdown("**Selecionadas:** "+", ".join(choices[k]["name"] for k in selected))
    common={d["id"]:d for d in five["common_destinations"]}
    if "ux41_destinations" not in st.session_state:
        stored=st.session_state.get("ux41_saved_destinations")
        st.session_state["ux41_destinations"]=(
            [d for d in stored if d in common] if isinstance(stored,list)
            else list(common))
    dest=st.multiselect("Passeios considerados para todas as favoritas",
        list(common),key="ux41_destinations",
        format_func=lambda key:common[key]["name"],
        on_change=lambda:st.session_state.update({
            "ux41_saved_destinations":list(st.session_state["ux41_destinations"])}))
    if selected:
        matrix=comparative_matrix(study,five,load_profiles(),load_city_packs(),
                                  list(selected),list(dest))
        st.markdown("#### Comparação rápida")
        _brief_matrix(matrix)
        if len(selected)>=2:
            st.markdown("**O que os dados permitem concluir**")
            for insight in comparison_insights(matrix):
                st.caption("• "+insight)
        _routes(matrix)
        _details(matrix)
        st.markdown("**Abrir ficha completa sem perder favoritas**")
        cols=st.columns(min(3,len(selected)))
        for col,key in zip(cols,selected):
            with col:
                st.button("Explorar "+choices[key]["name"],
                    key="ux41_open_"+key,on_click=_open_favorite_city,args=(key,),
                    use_container_width=True)
    _persistence(study)
