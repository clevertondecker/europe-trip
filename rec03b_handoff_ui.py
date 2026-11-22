"""REC03B presentation for handoffs; existing profile, map and planner."""
from __future__ import annotations

import streamlit as st
from rec03b_handoffs import (
    CHOICE, CONTEXT, ERROR, PREVIOUS, queue_handoff, queue_restore_manual,
    manual_selection, current_context, contextual_points, planning_handoff_projection,
)
from rec03a_session import request_navigation, SCOPE
from ux502_destination_interests_model import empty_interests
from trip01_supplemental_discovery import build_exploration_discovery
from base_research_expanded_model import load_research


def return_to_suggestions():
    st.session_state.pop(CONTEXT,None)
    request_navigation(st.session_state,"suggestions")


def render_notice():
    message=st.session_state.pop(ERROR,None)
    if message:
        st.warning(message)


def render_compare_selection(result,cities):
    state=st.session_state
    options=[c["base_id"] for c in result["candidates"]]
    st.markdown("#### Escolher alternativas para comparar")
    st.caption("Selecione de 2 a 5 cidades. Nenhuma seleção é oficializada.")
    saved=state.get(CHOICE,[])
    chosen=list(dict.fromkeys(x for x in saved if isinstance(x,str) and x in options)) if isinstance(saved,list) else []
    widget=CHOICE+"_widget"
    if state.get(widget)!=chosen:
        state[widget]=chosen
    def remember():
        state[CHOICE]=list(state[widget])
    selected=st.multiselect("Cidades para a comparação personalizada",options,
                            key=widget,max_selections=5,
                            format_func=lambda b:cities[b]["name"]+" · "+cities[b]["country"],
                            on_change=remember)
    previous=manual_selection(state)
    scope_ids=[x["id"] for x in result["destinations"]]
    if previous:
        st.caption("A ação substituirá os filtros manuais atuais. Você poderá recuperá-los na comparação.")
    st.button(("Substituir filtros e comparar" if previous else "Comparar cidades selecionadas")+
              f" · {len(scope_ids)} destinos",
              key="rec03a_handoff_compare",disabled=not 2<=len(selected)<=5,
              on_click=queue_handoff,args=(state,"manual",list(selected)),type="primary")



def selected_card_bases(state, options):
    """Read-only validated CHOICE projection; do not mutate session on render."""
    allowed=set(options)
    raw=state.get(CHOICE, [])
    return list(dict.fromkeys(x for x in raw if isinstance(x,str) and x in allowed)) \
        if isinstance(raw,list) else []


def _toggle_card_base(base, options):
    """Native checkbox callback: CHOICE is the single ephemeral selection."""
    state=st.session_state
    selected=selected_card_bases(state,options)
    wants=state.get("rec03a_pick_"+base,False)
    if wants and base not in selected:
        if len(selected)>=5:
            state["rec03a_pick_"+base]=False
            return
        selected.append(base)
    elif not wants:
        selected=[x for x in selected if x!=base]
    state[CHOICE]=selected


def render_card_choice(base, options):
    """A single card checkbox; never a parallel multiselect or persisted value."""
    state=st.session_state
    selected=selected_card_bases(state,options)
    key="rec03a_pick_"+base
    if state.get(key)!=(base in selected):
        state[key]=base in selected
    st.checkbox(
        "Selecionar para comparar", key=key,
        disabled=base not in selected and len(selected)>=5,
        on_change=_toggle_card_base,args=(base,tuple(options)),
    )


def render_card_selection_summary(result,cities):
    """Visible selected bases and one temporary, validated UX503 handoff.

    UX87 will replace the CTA with an inline matrix and KEEP CHOICE unchanged.
    """
    options=[c["base_id"] for c in result["candidates"]]
    selected=selected_card_bases(st.session_state,options)
    st.markdown("#### Cidades selecionadas")
    if selected:
        st.write(" · ".join(cities[b]["name"] for b in selected))
        st.caption(f"{len(selected)} de até 5 bases selecionadas · pesquisa, não decisão oficial.")
    else:
        st.caption("Selecione cidades diretamente nos cartões abaixo. Duas bastam para comparar.")
    if len(selected)==1:
        st.caption("Você já pode conhecer ou simular essa cidade sem selecionar uma segunda.")
    elif len(selected)>5:
        st.warning("Há mais de cinco cidades selecionadas; revise para comparar.")
    if 2<=len(selected)<=5:
        previous=manual_selection(st.session_state)
        if previous:
            st.caption("A comparação detalhada usará estes destinos e cidades. "
                       "Filtros manuais anteriores poderão ser recuperados.")
        st.button(
            f"Comparar {len(selected)} cidades com os destinos escolhidos",
            key="rec03a_handoff_compare",type="primary",
            on_click=queue_handoff,args=(st.session_state,"manual",list(selected)),
        )

def render_planning_handoff(plan, *, interests, discovery, research):
    from attractions_model import load_attractions
    from rec03b_handoffs import validate_handoff
    ctx=validate_handoff(st.session_state.get(SCOPE),interests,discovery,research,[],"planning")
    view=planning_handoff_projection(ctx,plan,interests,discovery,load_attractions())
    st.caption(f'{len(view["eligible"])} destinos do escopo podem entrar no roteiro · '
               f'{len(view["included"])} já incluídos · '
               f'{len(view["unsupported"])} somente pesquisa.')
    if view["other_stage"]:
        st.caption("Destinos de outra etapa permanecem disponíveis na lista.")
    labels={"build":"Montar roteiro com meus destinos","review":"Revisar meu roteiro","wishlist":"Revisar minha lista"}
    st.button(labels[view["action"]],key="rec03a_handoff_planning",
              on_click=queue_handoff,args=(st.session_state,"planning",[]))
    st.caption("Abre o planejador existente com a etapa europeia em destaque; "
               "a inclusão depende de sua seleção e confirmação. Nenhuma base é escolhida.")


def render_planning_return():
    context,_,_=context_for("planning")
    if context is not None:
        st.button("Voltar às cidades sugeridas",key="rec03a_handoff_back_planning",
                  on_click=return_to_suggestions)
        st.caption("O escopo das sugestões foi preservado. A lista completa continua disponível no planejador.")


def render_card_actions(base,prefix):
    from rec04_simulation_handoff import request_simulation
    a,b,c=st.columns(3)
    a.button("Conhecer cidade",key=f"rec03a_handoff_profile_{prefix}_{base}",
             on_click=queue_handoff,args=(st.session_state,"profile",[base]))
    b.button("Ver no mapa",key=f"rec03a_handoff_map_{prefix}_{base}",
             on_click=queue_handoff,args=(st.session_state,"map",[base]))
    c.button("Simular esta cidade",key=f"rec04_simulate_{prefix}_{base}",
             on_click=request_simulation,args=(st.session_state,base,"suggestions"))


def render_manual_context(selected=None,visible=None):
    state=st.session_state
    context=state.get(CONTEXT)
    if not isinstance(context,dict) or context.get("kind")!="manual":
        return
    if selected is None:
        valid,_,_=context_for("manual")
        if valid is None:
            state.pop(CONTEXT,None)
            st.caption("O escopo da análise mudou. Os filtros manuais atuais são independentes.")
            return
    if selected is None:
        st.caption("Comparação aberta a partir das sugestões. Os filtros são de pesquisa, não do roteiro.")
        st.button("Voltar às cidades sugeridas",key="rec03a_handoff_back_manual",
                  on_click=return_to_suggestions)
        if PREVIOUS in state:
            st.button("Recuperar comparação anterior",key="rec03a_handoff_restore_manual",
                      on_click=queue_restore_manual,args=(state,))
    elif (set(selected)!=set(context["base_ids"]) or
          set(visible)!=set(context["scope"]["destination_ids"])):
        st.info("Você editou os filtros: esta comparação não representa mais exatamente o escopo das sugestões.")
    else:
        st.caption("Mesmos destinos e células ferroviárias REC01. As contagens desta tela não são os pesos do REC02.")


def context_for(kind):
    from rec03b_handoffs import current_context
    discovery=build_exploration_discovery()
    research=load_research(include_candidates=True)
    interests=st.session_state.get("ux502_interests",empty_interests())
    context=current_context(st.session_state,kind,interests=interests,
                            discovery=discovery,research=research)
    return context,discovery,research


def _favorite(base,research):
    from ux41_favorites_model import set_favorites,MAX_FAVORITES
    state=st.session_state
    old=state.get("ux41_favorites",[])
    chosen=[b for b in old if b!=base] if base in old else old+[base]
    try:
        state["ux41_favorites"]=set_favorites(old,chosen,research)
        state["ux36_cloud_dirty"]=True
        state.pop("ux41_favorites_widget",None)
    except ValueError:
        state[ERROR]="Não foi possível alterar favoritas. Confira o limite e a seleção."


def render_profile_context(plan):
    from trip_plan_model import BASES
    context,_,research=context_for("profile")
    if context is None:
        return False
    base=context["base_ids"][0]
    city=next(c for c in research["cities"] if c["id"]==base)
    st.button("Voltar às cidades sugeridas",key="rec03a_handoff_back_profile",
              on_click=return_to_suggestions)
    st.caption("Cidade em pesquisa: "+city["name"]+
               (" · base oficial atual" if base==plan["base_city"] else
                " · elegível pelo fluxo oficial existente" if base in BASES else
                " · somente exploração, não disponível para oficialização"))
    from ux41_favorites_model import MAX_FAVORITES
    favorites=st.session_state.get("ux41_favorites",[])
    st.button("Remover favorita" if base in favorites else "Adicionar às favoritas",
              key="rec03a_handoff_favorite",disabled=base not in favorites and len(favorites)>=MAX_FAVORITES,
              on_click=_favorite,args=(base,research))
    if base not in favorites and len(favorites)>=MAX_FAVORITES:
        st.caption("Limite de favoritas atingido. Remova uma favorita antes de adicionar outra.")
    from rec04_simulation_handoff import request_simulation
    st.button("Simular esta cidade",key="rec04_simulate_profile",
              on_click=request_simulation,args=(st.session_state,base,"profile"))
    st.button("Ver cidade e destinos no mapa",key="rec03a_handoff_profile_map",
              on_click=queue_handoff,args=(st.session_state,"map",[base]))
    # Reuse the existing full profile renderer, without writing scenario_base_selected.
    from base_research_expanded_ui import render_expanded_research
    render_expanded_research(activity_override="Explorar uma cidade",compact=True,fixed_city=base)
    from rec05_priority_research_ui import render_research_from_session
    render_research_from_session(key="rec05_profile",base_ids=[base])
    return True


def render_contextual_map(plan):
    context,discovery,research=context_for("map")
    st.button("Voltar às cidades sugeridas",key="rec03a_handoff_back_map",
              on_click=return_to_suggestions)
    if context is None:
        st.warning("O contexto mudou; abra o mapa novamente pelas sugestões.")
        return
    from attractions_model import load_attractions
    from base_explorer_model import load_exploration
    from map_presentation_ui import render_map_view
    from base_recommendation_model import recommend_bases
    st.markdown("## Mapa das alternativas e destinos selecionados")
    try:
        points,missing=contextual_points(context,plan,discovery=discovery,research=research,
                                         exploration=load_exploration(),catalog=load_attractions())
        origin=next((p for p in points if p["id"]==context["base_ids"][0]),None)
        render_map_view(points,center=(origin["lat"],origin["lon"]) if origin else None,zoom=4.5)
        if missing:
            st.caption("Sem coordenada no catálogo: "+", ".join(missing))
        st.caption("Marcadores de cidades, não rotas ferroviárias. Nenhum trajeto foi inferido.")
        result=recommend_bases(st.session_state.get("ux502_interests",empty_interests()),
                               context["scope"],discovery=discovery,research=research)
        candidate=next(c for c in result["candidates"] if c["base_id"]==context["base_ids"][0])
        names={x["id"]:x["name"] for x in result["destinations"]}
        st.dataframe([{"Destino":names[d],"Referência de ida":cell["label"]}
                      for d,cell in candidate["evidence"].items()],hide_index=True,width="stretch")
        st.caption(result["limitation"])
        from rec05_priority_research_ui import render_research_result
        render_research_result(result,key="rec05_map",base_ids=[context["base_ids"][0]])
    except (ValueError,ImportError,OSError,KeyError,TypeError):
        import logging
        logging.getLogger(__name__).exception("REC03B contextual map failed")
        st.error("Não foi possível carregar o mapa de pesquisa. O planejamento não mudou.")
