"""Guided planning screen: reuse canonical bulk inclusion, editing and private save."""
from __future__ import annotations

import streamlit as st
from itinerary_flow_model import ITALY_STAGE, FRANCE_STAGE, UNASSIGNED
from planning_session import active_plan, commit_undated_destinations
from ux502_destination_interests_model import empty_interests, LABELS
from ux61_destination_board_ui import _discovery
from ux_planning_journey_model import project_planning, clear_planning_context
from ux_shared_ui_presentation import section_heading
from ux_planning_journey_presentation import (
    project_visual_state, header_html, metric_html, next_html, step_html,
)

VIEW="flow_journey_view"
STAGES=(ITALY_STAGE,FRANCE_STAGE)
LABELS_STAGE={ITALY_STAGE:"Lua de mel na Itália",FRANCE_STAGE:"Temporada europeia"}
LABELS_ACTION={"choose":"Escolher destinos","build":"Montar meu roteiro",
               "organize":"Organizar visitas","review":"Revisar e salvar rascunho"}


def _show(action, *, navigate=True):
    state=st.session_state
    # UX83: the same canonical flow lives in the public task responsible for it.
    # No separate TripPlan, session copy, or second organizer is introduced.
    if navigate and action in ("build","review","organize"):
        from ux64_navigation_model import select_public_task
        destination="Organizar" if action=="organize" else "Meus destinos"
        select_public_task(state,"Planejar",destination)
    state[VIEW]=action
    state["flow_organize_open"]=action=="organize"
    state["flow_add_open"]=False
    state["flow_save_open"]=False
    if action!="organize":
        state.pop("flow_edit_target",None)


def request_planning(state, action="build", stage=None):
    """Session-only intent shared by wishlist and future REC03B handoffs."""
    if action not in ("build","organize","review") or stage not in (None,*STAGES):
        raise ValueError("Encaminhamento inválido")
    state["flow_journey_intent"]={"action":action,"stage":stage,
                                  "identity":state.get("rec03a_identity"),
                                  "plan_id":state.get("advisor_plan",{}).get("plan_id")}


def apply_planning_request(state):
    intent=state.pop("flow_journey_intent",None)
    if not isinstance(intent,dict):
        return
    if (intent.get("identity")!=state.get("rec03a_identity") or
            intent.get("plan_id")!=state.get("advisor_plan",{}).get("plan_id")):
        return
    action,stage=intent.get("action"),intent.get("stage")
    if action not in ("build","organize","review") or stage not in (None,*STAGES):
        return
    from ux64_navigation_model import select_public_task
    select_public_task(state,"Planejar",
                       "Organizar" if action=="organize" else "Meus destinos")
    identity=(state.get("rec03a_identity"),state["advisor_plan"]["plan_id"])
    if state.get("flow_journey_identity")!=identity:
        clear_planning_context(state)
    state[VIEW]=action
    state["flow_journey_identity"]=(state.get("rec03a_identity"),state["advisor_plan"]["plan_id"])
    state["flow_organize_open"]=action=="organize"
    state["flow_add_open"]=False
    state["flow_save_open"]=False
    state.pop("flow_edit_target",None)
    state["ux_organize_view"]="Por período ou data"
    state["flow_journey_stage_hint"]=stage
    if stage is not None:
        state["flow_active_stage"]=stage
        state["flow_stage"]=stage


def _choose():
    from rec03a_session import request_navigation
    request_navigation(st.session_state,"wishlist")


def _discover():
    from ux504_guided_journey_ui import request_step
    request_step("discover")


def _select_all(key,ids):
    st.session_state[key]=list(ids)


def _selection(key,allowed):
    old=st.session_state.get(key,[])
    clean=list(dict.fromkeys(x for x in old if isinstance(x,str) and x in allowed)) if isinstance(old,list) else []
    if key in st.session_state and clean!=old:
        st.session_state[key]=clean


def _toggle_batch_choice(key, destination_id):
    selected=list(st.session_state.get(key,[]))
    if destination_id in selected:
        selected.remove(destination_id)
    elif len(selected)<50:
        selected.append(destination_id)
    st.session_state[key]=selected


def _workspace_photo(destination_id, name, place):
    """Reuse the licensed local/catalog photo priority, including UX118 Metz."""
    from destination_photo_assets import preferred_destination_photo
    from ux501_destination_photo_service import curated_destination_photo
    from ux47_photo_ui import photo_markup, photo_credit
    photo=preferred_destination_photo({**place,"id":destination_id},
                                      curated_destination_photo(destination_id))
    if photo and photo.get("local_path"):
        st.image(photo["local_path"],width="stretch")
        credit=photo_credit({**photo,"url":photo["source_page"]})
    else:
        st.html(photo_markup(photo,name))
        credit=photo_credit(photo)
    if credit:
        st.caption(credit)


def _render_batch_cards(key, by_id):
    places={r["id"]:r for r in _discovery()["destinations"]}
    search=st.text_input("Buscar na lista",key=key+"_search") if len(by_id)>8 else ""
    visible=[r for r in by_id.values()
             if search.casefold() in (r["name"]+" "+r["country"]).casefold()]
    limit=st.session_state.get(key+"_limit",8)
    selected=st.session_state.get(key,[])
    st.caption(f"{len(selected)} selecionados · até 50 por confirmação")
    for row in visible[:limit]:
        destination_id=row["id"]
        with st.container(border=True):
            image,details,action=st.columns([1,3,2],vertical_alignment="center")
            with image:
                _workspace_photo(destination_id,row["name"],places.get(destination_id,{}))
            with details:
                st.markdown("**"+row["name"]+"**")
                st.caption(row["country"]+" · "+LABELS.get(row["priority"],"Quero conhecer"))
            chosen=destination_id in selected
            action.button("Selecionado · retirar" if chosen else "Selecionar",
                          key=key+"_card_"+destination_id,
                          disabled=not chosen and len(selected)>=50,
                          on_click=_toggle_batch_choice,args=(key,destination_id),width="stretch")
    if len(visible)>limit:
        st.button(f"Mostrar mais {len(visible)-limit} destinos",key=key+"_more",
                  on_click=lambda:st.session_state.update({key+"_limit":limit+8}))
    if not visible:
        st.caption("Nenhum destino encontrado com esse filtro.")


def render_build(plan, catalog, view):
    st.markdown("#### Montar roteiro a partir da minha lista")
    st.caption("Escolha em lote os lugares de cada etapa. Nenhuma data, atração ou reserva será inventada.")
    stage_hint=st.session_state.get("flow_journey_stage_hint")
    stages=tuple(sorted(STAGES,key=lambda stage:stage!=stage_hint))
    for stage in stages:
        eligible=view["batches"][stage]["eligible"]
        with st.container(border=True):
            st.markdown("**"+LABELS_STAGE[stage]+"**")
            included=[row["name"] for row in view["rows"] if row["stage"]==stage]
            if included:
                st.caption("Já no roteiro: "+", ".join(included))
            if not eligible:
                st.caption("Nenhum novo destino compatível nesta etapa.")
                continue
            by_id={r["id"]:r for r in eligible}
            key="flow_journey_batch_"+stage
            _selection(key,by_id)
            a,b=st.columns(2)
            a.button("Selecionar todos",key=key+"_all",on_click=_select_all,
                     args=(key,list(by_id)[:50]))
            b.button("Limpar seleção",key=key+"_clear",on_click=_select_all,args=(key,[]))
            if len(by_id)>50:
                st.caption("Inclua até 50 destinos por confirmação; os demais continuam disponíveis.")
            _render_batch_cards(key,by_id)
            picked=st.multiselect("Destinos para incluir",list(by_id),key=key,
                                  max_selections=50,
                                  format_func=lambda x:by_id[x]["name"]+" · "+LABELS.get(by_id[x]["priority"],""))
            if st.button("Confirmar inclusão · "+LABELS_STAGE[stage],
                         key=key+"_confirm",disabled=not picked):
                try:
                    latest=project_planning(active_plan(),st.session_state.get("ux502_interests",empty_interests()),
                                            _discovery(),catalog)
                    available={r["id"] for r in latest["batches"][stage]["eligible"]}
                    if not set(picked)<=available:
                        raise ValueError("Sua lista mudou. Revise a seleção.")
                    commit_undated_destinations(list(picked),stage,confirmed=True)
                    st.session_state["flow_journey_notice"]=f"{len(picked)} destino(s) incluído(s) sem data."
                    # Review immediately if there is no further eligible batch.
                    after=project_planning(active_plan(),st.session_state.get("ux502_interests",empty_interests()),
                                           _discovery(),catalog)
                    if not after["eligible_count"]:
                        # Already on Planejar > Meus destinos. The public task
                        # widget was rendered earlier in this run, so never
                        # mutate its key while handling an inline confirm.
                        _show("review", navigate=False)
                    st.rerun()
                except (ValueError,KeyError) as exc:
                    st.error(str(exc))
    st.button("Cancelar seleção não confirmada",key="flow_journey_cancel_batch",on_click=_cancel_batch)
    if view["unsupported"]:
        with st.expander("Destinos ainda disponíveis somente para pesquisa"):
            st.write(", ".join(r["name"] for r in view["unsupported"]))
            st.caption("Continuam na wishlist. Você pode revisar e salvar os destinos compatíveis sem esperar novas pesquisas.")
    if view["rows"]:
        st.button("Revisar destinos já incluídos",key="flow_journey_review_after_build",on_click=_show,args=("review",))
    else:
        st.button("Revisar minha lista",key="flow_journey_edit_wishes",on_click=_choose)


def _cancel_batch():
    for key in list(st.session_state.keys()):
        if key.startswith("flow_journey_batch_"):
            st.session_state.pop(key,None)
    _show("review")


def _workspace_cancel_edit():
    state=st.session_state
    old=state.pop("flow_journey_workspace_edit",None)
    if old:
        state.pop("flow_edit_attr_"+old,None)
        state.pop("flow_edit_period_"+old,None)
    state.pop("flow_removing",None)


def _workspace_edit(destination_id):
    _workspace_cancel_edit()
    st.session_state["flow_journey_workspace_edit"]=destination_id


def _workspace_organize(destination_id, stage):
    from itinerary_flow_ui import _organize_destination_changed
    _workspace_cancel_edit()
    _show("organize")
    state=st.session_state
    state["ux_organize_view"]="Por período ou data"
    state["flow_active_stage"]=stage
    state["flow_stage"]=stage
    state["flow_organize_destination"]=destination_id
    _organize_destination_changed()


def _workspace_base(plan):
    from base_scenario_model import base_options
    return next((x["name"] for x in base_options(include_candidates=True)
                 if x["id"]==plan["base_city"]),plan["base_city"])


def _workspace_cards(plan,catalog,view):
    from itinerary_flow_model import get_choice
    from itinerary_flow_ui import _edit_destination, _navigate
    by_id={r["id"]:r for r in view["board"]}
    places={r["id"]:r for r in _discovery()["destinations"]}
    primary_places={r["id"]:r for r in catalog["destinations"]}
    stages=tuple(sorted(STAGES,key=lambda stage:stage!=st.session_state.get("flow_journey_stage_hint")))
    for stage in stages:
        rows=[r for r in view["rows"] if r["stage"]==stage]
        days=plan["italy_days"] if stage==ITALY_STAGE else plan["total_days"]-plan["italy_days"]
        organized=sum(by_id[r["id"]]["organized"] for r in rows)
        st.markdown("##### "+LABELS_STAGE[stage])
        st.caption(f"{days} dias · {len(rows)} incluídos · {organized} organizados"+
                   (" · Base: "+_workspace_base(plan) if stage==FRANCE_STAGE else ""))
        if not rows:
            st.info("Nenhum destino incluído nesta etapa.")
            if stage==ITALY_STAGE:
                st.button("Revisar proposta italiana",key="flow_workspace_italy",
                          on_click=_navigate,args=("Meu roteiro","Itália"))
            else:
                st.button("Explorar destinos",key="flow_workspace_empty_france",on_click=_discover)
        q=st.text_input("Buscar destino nesta etapa",key="flow_journey_workspace_search_"+stage) if len(rows)>8 else ""
        visible=[r for r in rows if q.casefold() in r["name"].casefold()]
        limit=st.session_state.get("flow_journey_workspace_limit_"+stage,8)
        focus=st.session_state.get("flow_journey_workspace_edit")
        visible.sort(key=lambda r:r["id"]!=focus)
        for row in visible[:limit]:
            key=row["id"]
            timing=by_id[key]
            place=places.get(key,{})
            photo_place={**primary_places.get(key,{}),**place}
            if not photo_place.get("photo"):
                photo_place["photo"]=primary_places.get(key,{}).get("photo")
            choice=get_choice(catalog,key)
            names={a["id"]:a["name"] for a in choice["attractions"]}
            with st.container(border=True,key="flow_workspace_card_"+key):
                left,right=st.columns([1,4],gap="small",vertical_alignment="top")
                with left:
                    _workspace_photo(key,row["name"],photo_place)
                with right:
                    st.markdown("**"+row["name"]+"**")
                    st.caption((timing["country"] or ("Itália" if stage==ITALY_STAGE else "País a verificar"))+
                               " · "+("Organizado" if timing["organized"] else "A organizar"))
                    st.write(" · ".join(names.get(a,a) for a in row["attractions"]) or "Atrações a escolher")
                    if timing["individual_period"]:
                        st.caption("Período individual: "+timing["individual_period"])
                    if timing["individual_dates"]:
                        st.caption("Data individual: "+", ".join(timing["individual_dates"]))
                    if timing["group_name"]:
                        st.caption("Viagem: "+timing["group_name"])
                    if timing["group_period"]:
                        st.caption("Período da viagem: "+timing["group_period"])
                    if timing["group_dates"]:
                        dates=timing["group_dates"]
                        st.caption("Intervalo da viagem: "+dates[0]+" a "+dates[-1])
                    if not timing["individual_dates"]:
                        st.caption("Dia individual a definir")
                    a,b=st.columns(2)
                    a.button("Editar passeio",key="flow_workspace_edit_"+key,on_click=_workspace_edit,args=(key,),width="stretch")
                    b.button("Organizar",key="flow_workspace_organize_"+key,on_click=_workspace_organize,args=(key,stage),width="stretch")
                if stage==FRANCE_STAGE and st.checkbox("Consultar logística e custos",key="flow_journey_workspace_logistics_"+key):
                    from attractions_model import load_base_routes
                    from ux47_destination_card_model import destination_card_view
                    try:
                        details=destination_card_view(plan,catalog,load_base_routes(),row)
                        st.caption(details["transport"])
                        st.caption(details["cost"])
                        st.caption(details["data_basis"])
                    except (ValueError,KeyError):
                        st.caption("Referências de logística ou custos ainda indisponíveis.")
                if focus==key:
                    _edit_destination(row,catalog,force_expanded=True)
                    st.button("Cancelar edição",key="flow_workspace_cancel_"+key,on_click=_workspace_cancel_edit)
        if len(visible)>limit:
            st.button(f"Mostrar mais {len(visible)-limit} destinos",key="flow_workspace_more_"+stage,
                      on_click=lambda s=stage:st.session_state.update(
                          {"flow_journey_workspace_limit_"+s:st.session_state.get("flow_journey_workspace_limit_"+s,8)+8}))
        if visible:
            st.caption(f"Exibindo {min(len(visible),limit)} de {len(visible)} destinos")


def render_review(plan,catalog,view):
    from continuity_ui import render_primary_private_save,render_continuity_panel
    st.markdown("#### Revisar e salvar meu rascunho")
    st.caption(f'{plan["italy_days"]} dias de lua de mel · {plan["total_days"]-plan["italy_days"]} dias de temporada europeia · Base oficial de referência: {_workspace_base(plan)}. Nenhuma reserva confirmada.')
    if not view["rows"]:
        st.info("Nenhum destino incluído. Você pode manter sua lista de desejos sem inventar passeios.")
    _workspace_cards(plan,catalog,view)
    if view["pending"]:
        st.info(f'{len(view["pending"])} destino(s) ainda sem período ou data. Isso não impede salvar o rascunho.')
    if view["eligible_count"]:
        st.caption(f'{view["eligible_count"]} desejo(s) compatíveis ainda não incluídos.')
        for stage in STAGES:
            if view["batches"][stage]["eligible"]:
                st.write(LABELS_STAGE[stage]+": "+", ".join(r["name"] for r in view["batches"][stage]["eligible"]))
        st.button("Voltar a incluir destinos",key="flow_journey_review_build",on_click=_show,args=("build",))
    if view["unsupported"]:
        st.caption("Somente pesquisa: "+", ".join(r["name"] for r in view["unsupported"]))
        st.button("Consultar minha lista",key="flow_workspace_research_only",on_click=_choose)
    st.caption("Retornos, reservas, moradia e custos de 2027 ainda precisam de confirmação. "
               "Salvar registra decisões, não confirma reservas.")
    # Finishing a useful draft does not require selecting days or opening
    # research assistants. Keep the canonical cloud save in the primary path.
    render_primary_private_save(plan,catalog)
    st.button("Organizar períodos e datas (opcional)",key="flow_journey_review_organize",
              on_click=_show,args=("organize",),disabled=not bool(view["rows"]))
    # The existing recovery panel is itself an expander. Keep it at the same
    # level as the save action so emergency export is never nested twice.
    render_continuity_panel(plan,catalog)
    with st.expander("Pesquisa complementar · opcional",expanded=False):
        from rec05_priority_research_ui import render_research_from_session
        render_research_from_session(key="rec05_plan")


def render_planning_journey(plan,catalog,trip_data=None,finance_live=False,eurfx=6.3,chffx=7.1,*,summary_only=False,organizer_stage=None):
    from continuity_ui import private_status_label
    from itinerary_flow_ui import (_render_organize,_render_add,_selected_stage,
                                  _active_stage_changed,_stage_label,_show_add,_show_organize,_compact_budget)
    from ux61_destination_board_ui import render_destination_board
    from ux64_navigation_model import select_public_task
    from rec03a_session import request_navigation
    label,hint=private_status_label(("Rascunho nesta sessão","Salve quando quiser; datas são opcionais."), detailed=summary_only)
    try:
        view=project_planning(plan,st.session_state.get("ux502_interests",empty_interests()),
                              _discovery(),catalog,private_saved=label=="Salvo em espaço privado",
                              weekend_groups=st.session_state.get("ux48_weekend_groups"))
    except (ValueError,KeyError,TypeError):
        st.error("A lista precisa de revisão. Seu roteiro foi preservado.")
        st.button("Abrir minha lista",key="flow_journey_invalid",on_click=_choose)
        return
    if summary_only:
        from ux121_overview_ui import render_overview
        render_overview(plan,catalog,view,label,hint,trip_data,finance_live,eurfx,chffx)
        return
    counts=view["counts"]
    state=st.session_state
    # Prevent stale bulk selections when an account or restored plan changes.
    identity=(state.get("rec03a_identity"),plan["plan_id"])
    if state.get("flow_journey_identity")!=identity:
        clear_planning_context(state)
        state["flow_journey_identity"]=identity
    if state.get(VIEW) not in ("build","organize","review"):
        state[VIEW]=None
    if organizer_stage in STAGES:
        state[VIEW]="organize"
    # Respect existing explicit edit deep links and the canonical organizer.
    if state.get("flow_edit_target") or state.get("flow_add_open"):
        state[VIEW]="organize"
    if state.get(VIEW)=="build" and not view["eligible_count"]:
        state[VIEW]="review" if view["rows"] else None
    visual=project_visual_state({**view,"next":view["editor_next"]},label,focused=state[VIEW])
    organizing=(state.get("ux_area"),state.get("ux_section"))==(
        "Meu roteiro","Organizar viagem")
    st.markdown(header_html(
        label,hint,saved=visual["saved"],
        title="Organizar nossa viagem" if organizing else "Meus destinos" if state.get("ux_section")=="Meu planejamento" else "Meu roteiro",
        tag="Visitas por período ou data" if organizing
            else "Gerencie os lugares da sua viagem",
    ),unsafe_allow_html=True)
    with st.container(key="flow_journey_metrics"):
        metric_columns=st.columns(3,gap="small")
        metrics=visual["metrics"]
        if state.get("ux_section")=="Meu planejamento":
            metrics=[
                {"id":"planned","icon":"▣","name":"Incluídos","value":counts["planned"],
                 "hint":"No roteiro","highlight":False},
                {"id":"organized","icon":"▤","name":"Organizados","value":counts["organized"],
                 "hint":"Com período ou data","highlight":False},
                {"id":"pending","icon":"◎","name":"A organizar","value":counts["planned"]-counts["organized"],
                 "hint":"Período ou data opcionais","highlight":bool(view["pending"])},
            ]
        for column,metric in zip(metric_columns,metrics):
            column.markdown(metric_html(metric),unsafe_allow_html=True)
    action=visual["action"]
    with st.container(key="flow_journey_next"):
        st.markdown(next_html(visual),unsafe_allow_html=True)
        if action=="choose":
            st.button(LABELS_ACTION[action],key="flow_journey_primary",
                      type="primary",on_click=_discover)
        elif action=="exploratory":
            st.caption(", ".join(r["name"] for r in view["unsupported"]))
            st.button("Revisar minha lista",key="flow_journey_primary",
                      type="primary",on_click=_choose)
        elif action=="review" and state[VIEW]=="review":
            st.markdown('<a class="journey-next__anchor" href="#journey-review-anchor">'
                        'Ir para a revisão ↓</a>',unsafe_allow_html=True)
        elif action=="build" and state[VIEW]=="build":
            st.markdown('<a class="journey-next__anchor" href="#journey-build-anchor">'
                        'Ir para a seleção de destinos ↓</a>',unsafe_allow_html=True)
        elif action=="organize" and state[VIEW]=="organize":
            st.markdown('<a class="journey-next__anchor" href="#journey-organize-anchor">'
                        'Ir para a organização ↓</a>',unsafe_allow_html=True)
        else:
            st.button(visual["primary_label"] or LABELS_ACTION[action],
                      key="flow_journey_primary",type="primary",
                      on_click=_show,args=(action,))
    # One main next-action button remains above the active editor. Keep
    # legacy step links as a secondary, non-competing escape hatch.
    with st.expander("Acessar outras etapas · opcional",expanded=False):
        st.markdown(section_heading(
            "SEU CAMINHO", "Etapas da jornada",
            "Continue quando quiser. Organizar datas é opcional para salvar um rascunho."
        ), unsafe_allow_html=True)
        for step in visual["steps"]:
            card_key="flow_journey_step_card_"+("active_" if step["active"] else "quiet_")+step["id"]
            with st.container(key=card_key):
                left,right=st.columns([4.5,1.5],vertical_alignment="center")
                left.markdown(step_html(step),unsafe_allow_html=True)
                right.button(step["button"],key="flow_journey_step_"+step["id"],
                             disabled=step["disabled"],use_container_width=True,
                             on_click=_choose if step["id"]=="choose" else _show,
                             args=() if step["id"]=="choose" else (step["id"],))
    note=state.pop("flow_journey_notice",None) or state.pop("flow_notice",None)
    if note:
        st.success(note)
    origin=state.get("ux45_origin")
    if origin and origin.get("destination_id"):
        from itinerary_flow_ui import _ux45_return_to_research
        st.button("Voltar à pesquisa de origem",key="ux45_back_to_origin",on_click=_ux45_return_to_research)
    if state[VIEW]=="build":
        st.markdown('<span id="journey-build-anchor"></span>',unsafe_allow_html=True)
        render_build(plan,catalog,view)
    elif state[VIEW]=="review":
        st.markdown('<span id="journey-review-anchor"></span>',unsafe_allow_html=True)
        render_review(plan,catalog,view)
    elif state[VIEW] is None and state.get("ux_section")=="Meu planejamento" and view["rows"]:
        render_review(plan,catalog,view)
    elif state[VIEW]=="organize":
        st.markdown('<span id="journey-organize-anchor"></span>',unsafe_allow_html=True)
        st.markdown("#### Organizar visitas")
        st.caption("Escolha a etapa: Lua de mel na Itália ou Temporada europeia.")
        if state.get("flow_active_stage") not in STAGES:
            stages={r["stage"] for r in view["rows"]}
            state["flow_active_stage"]=next(iter(stages)) if len(stages)==1 else ITALY_STAGE
        stage=organizer_stage if organizer_stage in STAGES else st.segmented_control(
            "Etapa da viagem",list(STAGES),key="flow_active_stage",
            format_func=_stage_label,on_change=_active_stage_changed,selection_mode="single")
        if stage not in STAGES:
            stage=ITALY_STAGE
        st.markdown("##### "+("Etapa 1 · Lua de mel na Itália" if stage==ITALY_STAGE else "Etapa 2 · Temporada europeia"))
        if state.get("flow_add_open"):
            st.button("Organizar períodos e datas",key="flow_go_calendar",on_click=_show_organize)
            _render_add(active_plan(),catalog)
        else:
            state["flow_organize_open"]=True
            _render_organize(active_plan(),catalog,stage,show_wishlist=False,review_on_close=True,
                             on_close=(lambda:_show("review")) if organizer_stage in STAGES else None)
            st.button("Adicionar passeio ou editar atrações",key="flow_add_open_button",on_click=_show_add)
        if organizer_stage is None and st.checkbox("Ver calendário e agrupamento de visitas",key="flow_journey_calendar"):
            from ux63_timeline_ui import render_timeline
            render_timeline(active_plan(),catalog,stage)
            if stage==FRANCE_STAGE:
                from ux48_weekend_groups_ui import render_weekend_planner
                render_weekend_planner(active_plan(),catalog)
        if organizer_stage is None or state.get("flow_edit_target"):
            _selected_stage(view["rows"],stage,catalog)
        else:
            from ux63_timeline_ui import render_timeline
            def focus_visit(destination_id):
                from itinerary_flow_ui import _organize_destination_changed
                state["flow_organize_destination"]=destination_id
                _organize_destination_changed()
            render_timeline(active_plan(),catalog,stage,on_organize=focus_visit,pending_first=True)
        st.button("Revisar e salvar sem definir outras datas",key="flow_journey_skip_dates",
                  on_click=_show,args=("review",))
    with st.expander("Ferramentas complementares",expanded=False):
        st.button("Encontrar cidades-base",key="flow_journey_suggestions",
                  on_click=request_navigation,args=(state,"suggestions"))
        st.button("Revisar orçamento",key="flow_journey_budget",
                  on_click=select_public_task,args=(state,"Orçamento","Visão financeira"))
        if st.checkbox("Consultar todos os destinos e suas situações",key="flow_journey_board"):
            render_destination_board(plan,catalog)
        if st.checkbox("Ver estimativa financeira",key="flow_journey_cost"):
            _compact_budget(plan,catalog,trip_data,finance_live,eurfx,chffx)
    st.caption("Desejado ≠ incluído ≠ organizado ≠ reservado.")
