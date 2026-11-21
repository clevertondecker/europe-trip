"""Guided planning screen: reuse canonical bulk inclusion, editing and private save."""
from __future__ import annotations

import streamlit as st
from itinerary_flow_model import ITALY_STAGE, FRANCE_STAGE, UNASSIGNED
from planning_session import active_plan, commit_undated_destinations
from ux502_destination_interests_model import empty_interests, LABELS
from ux61_destination_board_ui import _discovery
from ux_planning_journey_model import project_planning

VIEW="flow_journey_view"
STAGES=(ITALY_STAGE,FRANCE_STAGE)
LABELS_STAGE={ITALY_STAGE:"Lua de mel na Itália",FRANCE_STAGE:"Temporada europeia"}
LABELS_ACTION={"choose":"Escolher destinos","build":"Montar meu roteiro",
               "organize":"Organizar visitas","review":"Revisar e salvar rascunho"}


def _show(action):
    state=st.session_state
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
    state["flow_journey_intent"]={"action":action,"stage":stage}


def apply_planning_request(state):
    intent=state.pop("flow_journey_intent",None)
    if not isinstance(intent,dict):
        return
    action,stage=intent.get("action"),intent.get("stage")
    if action not in ("build","organize","review") or stage not in (None,*STAGES):
        return
    from ux64_navigation_model import select_public_task
    select_public_task(state,"Planejar","Organizar")
    state[VIEW]=action
    state["flow_journey_identity"]=(state.get("rec03a_identity"),active_plan()["plan_id"])
    state["flow_organize_open"]=action=="organize"
    state["flow_add_open"]=False
    state["flow_save_open"]=False
    state.pop("flow_edit_target",None)
    state["ux_organize_view"]="Por período ou data"
    if stage is not None:
        state["flow_active_stage"]=stage
        state["flow_stage"]=stage


def _choose():
    from rec03a_session import request_navigation
    request_navigation(st.session_state,"wishlist")


def _select_all(key,ids):
    st.session_state[key]=list(ids)


def _selection(key,allowed):
    old=st.session_state.get(key,[])
    clean=list(dict.fromkeys(x for x in old if isinstance(x,str) and x in allowed)) if isinstance(old,list) else []
    if key in st.session_state and clean!=old:
        st.session_state[key]=clean


def render_build(plan, catalog, view):
    st.markdown("#### Montar roteiro a partir da minha lista")
    st.caption("Escolha em lote os lugares de cada etapa. Nenhuma data, atração ou reserva será inventada.")
    for stage in STAGES:
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
                        _show("review")
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


def render_review(plan,catalog,view):
    from continuity_ui import render_primary_private_save,render_continuity_panel
    st.markdown("#### Revisar e salvar meu rascunho")
    st.caption(f'{plan["italy_days"]} dias de lua de mel · {plan["total_days"]-plan["italy_days"]} dias de temporada europeia · Base oficial de referência: {plan["base_city"]}. Nenhuma reserva confirmada.')
    if not view["rows"]:
        st.info("Nenhum destino incluído. Você pode manter sua lista de desejos sem inventar passeios.")
    for stage in STAGES:
        st.markdown("**"+LABELS_STAGE[stage]+"**")
        rows=[r for r in view["rows"] if r["stage"]==stage]
        if rows:
            st.dataframe([{"Destino":r["name"],"Atrações":len(r["attractions"]),
                           "Período":r["period"] if r["period"]!=UNASSIGNED else "A definir",
                           "Datas":", ".join(r["exact_dates"]) or "A definir"}
                          for r in rows],hide_index=True,width="stretch")
        else:
            st.caption("Nenhum destino incluído nesta etapa.")
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
    st.caption("Retornos, reservas, moradia e custos de 2027 ainda precisam de confirmação. "
               "Salvar registra decisões, não confirma reservas.")
    st.button("Organizar períodos e datas (opcional)",key="flow_journey_review_organize",
              on_click=_show,args=("organize",),disabled=not bool(view["rows"]))
    render_primary_private_save(plan,catalog)
    render_continuity_panel(plan,catalog)


def render_planning_journey(plan,catalog,trip_data=None,finance_live=False,eurfx=6.3,chffx=7.1,*,summary_only=False):
    from continuity_ui import private_status_label
    from itinerary_flow_ui import (_render_organize,_render_add,_selected_stage,
                                  _active_stage_changed,_stage_label,_show_add,_compact_budget)
    from ux61_destination_board_ui import render_destination_board
    from ux64_navigation_model import select_public_task
    from rec03a_session import request_navigation
    label,hint=private_status_label(("Rascunho nesta sessão","Salve quando quiser; datas são opcionais."))
    try:
        view=project_planning(plan,st.session_state.get("ux502_interests",empty_interests()),
                              _discovery(),catalog,private_saved=label=="Salvo em espaço privado")
    except (ValueError,KeyError,TypeError):
        st.error("A lista precisa de revisão. Seu roteiro foi preservado.")
        st.button("Abrir minha lista",key="flow_journey_invalid",on_click=_choose)
        return
    st.markdown("## Meu roteiro")
    st.caption(label+" · "+hint)
    counts=view["counts"]
    a,b,c=st.columns(3)
    a.metric("Desejados",counts["wished"])
    b.metric("Incluídos",counts["planned"])
    c.metric("Organizados",counts["organized"])
    state=st.session_state
    # Prevent stale bulk selections when an account or restored plan changes.
    identity=(state.get("rec03a_identity"),plan["plan_id"])
    if state.get("flow_journey_identity")!=identity:
        for key in list(state.keys()):
            if key.startswith("flow_journey_batch_") or key==VIEW:
                state.pop(key,None)
        state["flow_journey_identity"]=identity
    if state.get(VIEW) not in ("build","organize","review"):
        state[VIEW]=None
    # Respect existing explicit edit deep links and the canonical organizer.
    if state.get("flow_edit_target") or state.get("flow_add_open"):
        state[VIEW]="organize"
    if summary_only:
        action=view["next"]
        with st.container(border=True):
            st.markdown("#### Continue de onde parou")
            if action=="build":
                st.write(f'{view["eligible_count"]} destinos elegíveis ainda não incluídos.')
                label="Adicionar destinos pendentes ao roteiro" if counts["planned"] else "Montar roteiro com meus destinos"
            elif action=="review":
                st.write("Confira os destinos incluídos e salve seu rascunho.")
                label="Revisar meu roteiro"
            else:
                st.write("Escolha os destinos que deseja conhecer.")
                label="Escolher destinos"
            st.button(label,key="flow_journey_primary",type="primary",
                      on_click=_choose if action=="choose" else request_planning,
                      args=() if action=="choose" else (state,action))
        st.markdown("#### Etapas da jornada")
        for step,title,status in view["steps"]:
            st.markdown("**"+title+"**")
            st.caption(status)
        with st.expander("Ferramentas complementares"):
            st.button("Encontrar cidades-base",key="flow_journey_suggestions",
                      on_click=request_navigation,args=(state,"suggestions"))
            st.button("Revisar orçamento",key="flow_journey_budget",
                      on_click=select_public_task,args=(state,"Orçamento","Visão financeira"))
            if st.checkbox("Consultar todos os destinos",key="flow_journey_board"):
                render_destination_board(plan,catalog)
        return
    action=state[VIEW] or view["next"]
    with st.container(border=True):
        st.markdown("#### Próxima ação")
        descriptions={"choose":"Escolha os lugares que quer conhecer.",
                      "build":f'{view["eligible_count"]} destino(s) compatíveis ainda podem entrar no roteiro.',
                      "organize":"Defina períodos ou datas se já souber. Você pode salvar sem organizar.",
                      "review":"Confira o que está incluído e salve suas escolhas, mesmo sem datas."}
        st.write(descriptions[action])
        if action=="choose":
            st.button(LABELS_ACTION[action],key="flow_journey_primary",type="primary",on_click=_choose)
        elif action=="review" and state[VIEW]=="review":
            st.caption("A ação de salvamento está na revisão abaixo.")
        elif state[VIEW]=="build":
            st.caption("Confirme os destinos selecionados na montagem abaixo.")
        elif state[VIEW]=="organize":
            st.button("Revisar e salvar rascunho",key="flow_journey_primary",type="primary",on_click=_show,args=("review",))
        else:
            st.button(LABELS_ACTION[action],key="flow_journey_primary",type="primary",
                      on_click=_show,args=(action,))
    st.markdown("#### Etapas da jornada")
    for step,title,status in view["steps"]:
        with st.container():
            left,right=st.columns([3,1],vertical_alignment="center")
            left.markdown("**"+title+"**")
            left.caption(status)
            right.button("Abrir",key="flow_journey_step_"+step,
                         disabled=step=="organize" and not bool(view["rows"]),
                         on_click=_choose if step=="choose" else _show,
                         args=() if step=="choose" else (step,))
    note=state.pop("flow_journey_notice",None) or state.pop("flow_notice",None)
    if note:
        st.success(note)
    if state[VIEW]=="build":
        render_build(plan,catalog,view)
    elif state[VIEW]=="review":
        render_review(plan,catalog,view)
    elif state[VIEW]=="organize":
        st.markdown("#### Organizar visitas")
        if state.get("flow_active_stage") not in STAGES:
            state["flow_active_stage"]=ITALY_STAGE
        stage=st.segmented_control("Etapa da viagem",list(STAGES),key="flow_active_stage",
                                   format_func=_stage_label,on_change=_active_stage_changed,
                                   selection_mode="single")
        if stage not in STAGES:
            stage=ITALY_STAGE
        state["flow_organize_open"]=True
        _render_organize(active_plan(),catalog,stage,show_wishlist=False,review_on_close=True)
        if st.checkbox("Ver calendário e agrupamento de visitas",key="flow_journey_calendar"):
            from ux63_timeline_ui import render_timeline
            render_timeline(active_plan(),catalog,stage)
            if stage==FRANCE_STAGE:
                from ux48_weekend_groups_ui import render_weekend_planner
                render_weekend_planner(active_plan(),catalog)
        st.button("Adicionar passeio ou editar atrações",key="flow_journey_add_outing",on_click=_show_add)
        _render_add(active_plan(),catalog)
        _selected_stage(view["rows"],stage,catalog)
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
