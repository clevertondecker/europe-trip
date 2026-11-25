"""Transient visit focus. No persisted state, scheduling or independent writer."""
from datetime import date
import streamlit as st

FOCUS="flow_journey_visit_focus"
DRAFTS="flow_journey_visit_drafts"
PENDING="flow_journey_visit_pending"
ORDER="flow_journey_visit_order"
NOTICE="flow_journey_visit_notice"
WIDGETS=("flow_organize_mode","flow_organize_period",
         "flow_organize_date_Itália","flow_organize_date_França")


def visible_visits(rows,limit,focus=None):
    """Expose a deep-linked visit without silently hiding another visible card."""
    visible=list(rows[:limit])
    if focus and not any(r["id"]==focus for r in visible):
        visible.extend(r for r in rows[limit:] if r["id"]==focus)
    return visible


def stable_visit_order(rows,state,stage,focus):
    """Freeze current order while a card is open, even after its status changes."""
    prior=state.get(ORDER)
    ids=[row["id"] for row in rows]
    if focus and isinstance(prior,tuple) and prior[0]==stage:
        rank={key:i for i,key in enumerate(prior[1])}
        rows=sorted(rows,key=lambda row:rank.get(row["id"],len(rank)))
        ids=[row["id"] for row in rows]
    state[ORDER]=(stage,ids)
    return rows


def _clear_widgets(state):
    for key in WIDGETS:
        state.pop(key,None)


def _remember():
    state=st.session_state
    focus=state.get(FOCUS)
    if not focus:
        return
    drafts=state.setdefault(DRAFTS,{})
    draft=drafts.setdefault(focus,{})
    draft.update({key:state[key] for key in WIDGETS if key in state})


def _dirty(state,row,stage):
    draft=state.get(DRAFTS,{}).get((stage,row["id"]),{})
    period=draft.get("flow_organize_period",row["period"])
    chosen=draft.get("flow_organize_date_"+stage)
    return period!=row["period"] or (
        isinstance(chosen,date) and chosen.isoformat() not in row["exact_dates"]
        and draft.get("date_changed",False))


def _record_date():
    _remember()
    state=st.session_state
    focus=state.get(FOCUS)
    if focus:
        state[DRAFTS][focus]["date_changed"]=True


def _apply(target,stage,*,discard=False):
    from itinerary_flow_ui import _show_organize,_show_add
    state=st.session_state
    old=state.get(FOCUS)
    if old and (discard or old!=(stage,target)):
        state.get(DRAFTS,{}).pop(old,None)
    _clear_widgets(state)
    state.pop(PENDING,None)
    state.pop(NOTICE,None)
    if target=="catalog":
        state.pop(FOCUS,None)
        _show_add()
        return
    if target is None:
        state.pop(FOCUS,None)
        state["flow_organize_open"]=False
        state["flow_add_open"]=False
        state.pop("flow_organize_destination",None)
        return
    _show_organize()
    state[FOCUS]=(stage,target)
    state["flow_organize_destination"]=target


def request_focus(target,stage,rows):
    state=st.session_state
    old=state.get(FOCUS)
    if old==(stage,target) and not state.get("flow_add_open"):
        return
    current=next((r for r in rows if old==(stage,r["id"])),None)
    if current is not None and _dirty(state,current,stage):
        state[PENDING]=(stage,target)
        return
    _apply(target,stage)


def render_pending(rows,stage):
    state=st.session_state
    pending=state.get(PENDING)
    if not pending or pending[0]!=stage:
        return
    target=pending[1]
    if target not in (None,"catalog") and not any(r["id"]==target for r in rows):
        state.pop(PENDING,None)
        return
    st.warning("Há alterações de período ou data ainda não confirmadas.")
    a,b=st.columns(2)
    a.button("Descartar alterações e continuar",key="ux129_discard",on_click=_apply,
             args=(target,stage),kwargs={"discard":True})
    b.button("Continuar editando",key="ux129_keep_editing",
             on_click=lambda:state.pop(PENDING,None))


def render_editor(plan,catalog,stage,row,*,rows=None):
    from itinerary_flow_ui import _render_organize_fields
    state=st.session_state
    focus=(stage,row["id"])
    if state.pop("flow_journey_visit_refresh",None)==focus:
        mode=state.get("flow_organize_mode")
        _clear_widgets(state)
        if mode:
            state["flow_organize_mode"]=mode
    draft=state.get(DRAFTS,{}).get(focus,{})
    for key in WIDGETS:
        if key in draft and key not in state:
            state[key]=draft[key]
    def saved():
        state.get(DRAFTS,{}).pop(focus,None)
        state.pop(PENDING,None)
        state["flow_journey_visit_refresh"]=focus
        message=state.pop("flow_notice",None)
        if message:
            state[NOTICE]=(focus,message)
    st.markdown("##### Organizar visita a "+row["name"])
    st.caption("Período e data são opcionais. Use o botão de gravação para aplicar as alterações.")
    notice=state.pop(NOTICE,None)
    if notice and notice[0]==focus:
        st.success(notice[1])
    _render_organize_fields(plan,catalog,stage,row,on_draft_change=_remember,
                            on_date_change=_record_date,on_saved=saved)
    render_pending(rows if rows is not None else [row],stage)
    a,b=st.columns(2)
    # This key now closes only the focused card; legacy navigation uses
    # flow_journey_skip_dates to return to Meus destinos.
    a.button("Fechar",key="flow_organize_close",
             on_click=request_focus,args=(None,stage,[row]))
    b.button("Cancelar",key="ux129_cancel_visit",on_click=_apply,
             args=(None,stage),kwargs={"discard":True})
