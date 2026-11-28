"""REC03B presentation for handoffs; existing profile, map and planner."""
from __future__ import annotations

import streamlit as st
from rec03b_handoffs import (
    CHOICE, CONTEXT, ERROR, queue_handoff,
    current_context, contextual_points, planning_handoff_projection,
)
from rec03a_session import request_navigation, SCOPE
from ux502_destination_interests_model import empty_interests
from trip01_supplemental_discovery import build_exploration_discovery
from base_research_expanded_model import load_research


def return_to_suggestions():
    st.session_state.pop(CONTEXT,None)
    st.session_state.pop("rec03a_profile_discovery",None)
    st.session_state.pop("rec03a_profile_map_origin",None)
    request_navigation(st.session_state,"suggestions")


def _discover_from_profile(destination_id=None):
    # Existing REC03B return marker carries an optional canonical destination.
    context,discovery,_=context_for("profile")
    if context is None:
        return
    if destination_id is not None and destination_id not in {d["id"] for d in discovery["destinations"]}:
        return
    st.session_state["rec03a_profile_discovery"]=destination_id or True
    request_navigation(st.session_state,"discovery")

def _map_from_profile(base):
    st.session_state["rec03a_profile_map_origin"]=base
    queue_handoff(st.session_state,"map",[base])

def _return_from_map():
    state=st.session_state
    base=state.pop("rec03a_profile_map_origin",None)
    ctx,_,_=context_for("map")
    if base and ctx and ctx["base_ids"]==[base]:
        queue_handoff(state,"profile",[base])
    else:
        return_to_suggestions()

def render_profile_discovery_return():
    if not st.session_state.get("rec03a_profile_discovery"):
        return
    context,discovery,_=context_for("profile")
    if context is None:
        st.session_state.pop("rec03a_profile_discovery",None)
        return
    target=st.session_state.get("rec03a_profile_discovery")
    def back():
        from ux_navigation import set_task
        st.session_state.pop("rec03a_profile_discovery",None)
        set_task(st.session_state,"Explorar","Cidades-base")
    st.button("Voltar à ficha da cidade",key="rec03a_profile_discovery_back",on_click=back)
    if isinstance(target,str) and target in {d["id"] for d in discovery["destinations"]}:
        def show_all():
            st.session_state["rec03a_profile_discovery"]=True
        st.button("Ver todos os destinos",key="rec03a_profile_discovery_all",on_click=show_all)
        return target

def _compare_profile(base, options):
    state=st.session_state
    selected=selected_card_bases(state,options)
    if base not in selected:
        if len(selected)>=5:
            state[ERROR]="Remova uma cidade da comparação antes de adicionar outra."
            return
        state[CHOICE]=selected+[base]
        state["ux111_last_selection"]=(base,True)
    target="Minha comparação" if len(state.get(CHOICE,[]))>=2 else "Explorar alternativas"
    state["ux112_active_view"]=target
    state["ux112_active_view_shadow"]=target
    return_to_suggestions()

def render_notice():
    message=st.session_state.pop(ERROR,None)
    if message:
        st.warning(message)


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
    before=list(selected)
    wants=state.get("rec03a_pick_"+base,False)
    if wants and base not in selected:
        if len(selected)>=5:
            state["rec03a_pick_"+base]=False
            return
        selected.append(base)
    elif not wants:
        selected=[x for x in selected if x!=base]
    state[CHOICE]=selected
    # Feedback is transient UI metadata; CHOICE remains the only selection.
    if selected != before:
        state["ux111_last_selection"]=(base,base in selected)


def _remove_comparison_base(base,options):
    """Remove from CHOICE; card checkbox is reconciled on the next rerun."""
    state=st.session_state
    selected=selected_card_bases(state,options)
    if base in selected:
        state[CHOICE]=[item for item in selected if item!=base]
        state["ux111_last_selection"]=(base,False)


def _switch_comparison_view(view):
    """Change only presentation mode; CHOICE and TripPlan are untouched."""
    st.session_state["ux112_active_view"]=view
    st.session_state["ux112_active_view_shadow"]=view


def render_selection_toolbar(options,cities,*,navigation=None):
    """Selection feedback adjacent to cards, not another multiselect."""
    selected=selected_card_bases(st.session_state,options)
    with st.container(key="ux111-selection-toolbar",border=True):
        scope=st.session_state.get(SCOPE)
        if isinstance(scope,dict) and isinstance(scope.get("destination_ids"),list):
            from ux96_comparison_visual_ui import selected_context
            st.markdown(selected_context(selected,cities,len(scope["destination_ids"])),
                        unsafe_allow_html=True)
        else:
            st.markdown("**Cidades selecionadas · "+str(len(selected))+" de 5**")
        feedback=st.session_state.get("ux111_last_selection")
        if (isinstance(feedback,tuple) and len(feedback)==2
                and feedback[0] in options
                and (feedback[0] in selected)==feedback[1]):
            st.caption(("✓ "+cities[feedback[0]]["name"]+" adicionada à comparação."
                        if feedback[1] else
                        "✓ "+cities[feedback[0]]["name"]+" removida da comparação."))
        if selected:
            if len(selected)<=5:
                st.caption(str(5-len(selected))+" vaga(s) restantes · pesquisa, não roteiro oficial")
            else:
                st.caption("Seleção antiga acima do limite; remova as excedentes para continuar.")
            # The native remove action is explicit and keyboard accessible.
            columns=st.columns(min(3,len(selected)))
            for i,base in enumerate(selected):
                with columns[i%len(columns)]:
                    st.button("✕ "+cities[base]["name"],
                              key="ux111_remove_"+base,
                              help="Remover "+cities[base]["name"]+" da comparação",
                              on_click=_remove_comparison_base,
                              args=(base,tuple(options)),width="stretch")
        else:
            st.caption("Selecione uma cidade nos cartões para iniciar.")
        if len(selected)>5:
            st.warning("Sua seleção anterior contém mais de cinco cidades. "
                       "Remova as excedentes para comparar; nenhuma foi excluída automaticamente.")
        elif len(selected)<2:
            st.info("Escolha pelo menos duas cidades para ver a comparação.")
        if navigation=="explore":
            if 2<=len(selected)<=5:
                st.button("Ver minha comparação ("+str(len(selected))+")",
                          key="ux112_open_comparison",type="primary",
                          on_click=_switch_comparison_view,args=("Minha comparação",))
        elif navigation=="compare":
            st.button("+ Explorar outras cidades",key="ux112_open_exploration",
                      on_click=_switch_comparison_view,args=("Explorar alternativas",))
        else:
            if 2<=len(selected)<=5:
                st.markdown('<a class="ux111-primary-action" href="#ux111-comparison">'
                            'Ver comparação atualizada ↗</a>',unsafe_allow_html=True)
            st.markdown('<a class="ux111-secondary-action" href="#ux111-picker">'
                        'Adicionar outras cidades</a>',unsafe_allow_html=True)


def render_card_choice(base, options, *, show_selection_hint=True):
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
    feedback=state.get("ux111_last_selection")
    if feedback and feedback[0]==base:
        st.caption(("✓ Adicionada" if feedback[1] else "Removida")+
                   " à comparação · "+str(len(selected))+" de 5 selecionadas")
    elif base in selected:
        st.caption("✓ Nesta comparação · "+str(len(selected))+" de 5 selecionadas")
    if show_selection_hint and base in selected and len(selected)==1:
        st.caption("Selecione mais uma cidade para comparar.")


def render_card_selection_summary(result, cities, *, selection_already_shown=False):
    """Use CHOICE for contextual actions; do not repeat the UX96 selection strip."""
    options=[c["base_id"] for c in result["candidates"]]
    selected=selected_card_bases(st.session_state, options)
    if not selection_already_shown:
        st.markdown("#### Cidades selecionadas")
    if not selected:
        if not selection_already_shown:
            st.caption("Selecione cidades nos cartões. Com duas ou mais, "
                       "a comparação aparece aqui sem outra confirmação.")
        return
    if not selection_already_shown:
        st.write(" · ".join(cities[b]["name"] for b in selected))
        st.caption(f"{len(selected)} de até 5 cidades selecionadas · pesquisa, não decisão oficial.")
    if len(selected)==1:
        if not selection_already_shown:
            st.caption("Você já pode investigar esta cidade sem selecionar outra.")
    elif 2<=len(selected)<=5:
        if not selection_already_shown:
            st.caption("A comparação dos destinos aparece logo abaixo, na mesma página.")
    else:
        st.warning("Revise a seleção para ficar com até cinco cidades.")
        return
    if len(selected)>1:
        key="rec03a_focus_city"
        if st.session_state.get(key) not in selected:
            st.session_state[key]=selected[0]
        focus=st.selectbox(
            "Cidade para investigar individualmente",selected,
            key=key,format_func=lambda city:cities[city]["name"],
            help="Isso não altera as cidades selecionadas para comparar.")
    else:
        focus=selected[0]
    with st.expander("Conhecer cidade, mapa e custos"):
        render_card_actions(focus,"card")


def render_planning_handoff(plan, *, interests, discovery, research):
    from attractions_model import load_attractions
    from rec03b_handoffs import validate_handoff
    from comparison_destinations_model import from_state
    ctx=validate_handoff(st.session_state.get(SCOPE),from_state(st.session_state,discovery),discovery,research,[],"planning")
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


def render_card_actions(base,prefix,*,emphasize_profile=False,compact=False):
    from rec04_candidate_capabilities import capability_for
    from rec04_simulation_handoff import request_simulation
    cap=capability_for(base)
    if compact:
        st.button("Conhecer cidade",key=f"rec03a_handoff_profile_{prefix}_{base}",
                  type="primary" if emphasize_profile else "secondary",
                  on_click=queue_handoff,args=(st.session_state,"profile",[base]),
                  width="stretch")
        return
    a,b,c=st.columns(3)
    a.button("Conhecer cidade",key=f"rec03a_handoff_profile_{prefix}_{base}",
             type="primary" if emphasize_profile else "secondary",
             on_click=queue_handoff,args=(st.session_state,"profile",[base]))
    b.button("Ver no mapa",key=f"rec03a_handoff_map_{prefix}_{base}",
             on_click=queue_handoff,args=(st.session_state,"map",[base]))
    c.button("Simular custo",key=f"rec04_simulate_{prefix}_{base}",
             disabled=not cap["scenario_selectable"],
             on_click=request_simulation,args=(st.session_state,base,"suggestions"))
    if cap["scenario_selectable"]:
        st.caption(cap["budget_note"])
        if not cap["rental_quote_2027_available"]:
            st.caption("Aluguel e caução de 2027 ainda não foram cotados.")
    else:
        st.caption("Ainda não há cenário de custos disponível para esta cidade.")


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
    """A focused single-city research view; no parallel selection or plan edits."""
    from trip_plan_model import BASES
    from rec04_candidate_capabilities import capability_for
    from rec04_simulation_handoff import request_simulation
    from ux41_favorites_model import MAX_FAVORITES

    context,_,research=context_for("profile")
    if context is None:
        return False
    base=context["base_ids"][0]
    city=next(c for c in research["cities"] if c["id"]==base)
    cap=capability_for(base, research=research)

    status=("Base oficial atual" if base==plan["base_city"] else
            "Elegível para o fluxo oficial" if base in BASES else
            "Somente investigação")
    from ux100_base_card_photos import base_card_photo_record,render_base_card_photo
    favorites=st.session_state.get("ux41_favorites",[])
    choices=[c["id"] for c in research["cities"]]
    selected=selected_card_bases(st.session_state,choices)
    with st.container(key="ux124b-profile-header"):
        st.button("← Voltar à comparação",key="rec03a_handoff_back_profile",
                  on_click=return_to_suggestions)
        photo=base_card_photo_record(base)
        if photo:
            heading,visual=st.columns([3,1],gap="small",vertical_alignment="top")
        else:
            heading=st.container()
        with heading:
            st.markdown("## "+city["name"]+" · "+city["country"])
            st.caption(city["corridor"]+" · "+status)
            if base in favorites:
                st.caption("Cidade favorita")
            with st.container(key="ux124b-profile-actions",horizontal=True,gap="small"):
                st.button("Simular orçamento",key="rec04_simulate_profile",
                          type="primary",disabled=not cap["scenario_selectable"],
                          on_click=request_simulation,args=(st.session_state,base,"profile"))
                st.button("Comparar cidade",key="rec03a_profile_compare",
                          disabled=base not in selected and len(selected)>=5,
                          on_click=_compare_profile,args=(base,choices))
                with st.popover("Mais ações"):
                    st.button("Remover favorita" if base in favorites else "Adicionar às favoritas",
                              key="rec03a_handoff_favorite",
                              disabled=base not in favorites and len(favorites)>=MAX_FAVORITES,
                              on_click=_favorite,args=(base,research))
                    if base not in favorites and len(favorites)>=MAX_FAVORITES:
                        st.caption("Limite de favoritas atingido.")
                    st.button("Ver no mapa",key="rec03a_handoff_profile_map",
                              on_click=_map_from_profile,args=(base,))
                    st.button("Consultar destinos em Descobrir",key="rec03a_profile_discover",
                              on_click=_discover_from_profile)
            from ux124b_profile_presentation import simulation_note
            st.caption(simulation_note(cap))
            if base not in selected and len(selected)>=5:
                st.caption("Comparação cheia: remova uma das cinco cidades antes de adicionar outra.")
        if photo:
            with visual:
                with st.container(key="ux109-city-photo"):
                    render_base_card_photo(base,city["name"])
    # Reuse the already loaded public city research. The REC05 queue stays
    # in Pesquisas & decisões rather than duplicating the decision surface.
    from ux124_city_profile_ui import render_city_profile
    render_city_profile(base,research=research,on_discover_destination=_discover_from_profile)
    return True


def render_contextual_map(plan):
    context,discovery,research=context_for("map")
    from_profile=bool(context and st.session_state.get("rec03a_profile_map_origin") in context["base_ids"])
    st.button("Voltar à ficha da cidade" if from_profile else "Voltar às cidades sugeridas",
              key="rec03a_handoff_back_map",on_click=_return_from_map)
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
        from comparison_destinations_model import from_state
        result=recommend_bases(from_state(st.session_state,discovery),
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
