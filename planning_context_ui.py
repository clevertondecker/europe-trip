"""One progressive configuration screen, one safe comparison workspace.

Reads the canonical TripPlan from planning_session. Shared preference widgets
do not themselves modify the plan. Only approved configuration revisions do.
"""
from __future__ import annotations
from copy import deepcopy
import streamlit as st

from base_scenario_model import base_options
from planning_session import active_plan,update_fields
from planning_workflow_model import (
    BUDGET_LABELS,TRIP_STYLES,settings,preview_settings,
    compare_alternative,resume_target,breadcrumb,
)

def show_settings(*,initial:bool=False)->None:
    st.session_state["workflow_settings_open"]=True
    st.session_state["workflow_compare_open"]=False
    if initial:
        st.session_state["workflow_setup_initial"]=True


def show_alternative()->None:
    st.session_state["workflow_compare_open"]=True
    st.session_state["workflow_settings_open"]=False
    st.session_state["ux_mode_value"]="Simulação"
    st.session_state["ux_pending_mode"]="Simulação"


def open_detailed_impact()->None:
    """Reuse researched route/finance comparison; never edit the official plan."""
    from ux_navigation import set_task
    state=st.session_state
    plan=active_plan()
    base=state.get("workflow_alt_base",plan["base_city"])
    state["scenario_base_selected"]=base
    state["ux_last_candidate"]=base
    state["ux_mode"]="Simulação"
    state["ux_mode_value"]="Simulação"
    state["ux_days_value"]=(
        int(state.get("workflow_alt_total_days",plan["total_days"]))-
        int(state.get("workflow_alt_italy_days",plan["italy_days"])))
    state["ux_days"]=state["ux_days_value"]
    state["unified_stay"]=state["ux_days_value"]
    state["flow_return_stage"]=state.get("flow_active_stage","Itália")
    state["flow_return_destination"]=state.get("flow_active_destination")
    state["flow_return_add_open"]=bool(state.get("flow_add_open",False))
    state["workflow_compare_open"]=False
    set_task(state,"Explorar","Comparar")


def close_overlays()->None:
    st.session_state["workflow_settings_open"]=False
    st.session_state["workflow_compare_open"]=False


def resume_plan()->None:
    from ux_navigation import set_task
    plan=active_plan()
    destination=st.session_state.get("flow_active_destination")
    stage=st.session_state.get("flow_stage")
    if destination is None:
        target=resume_target(plan)
        destination=target["destination_id"]
        stage=target["stage"]
    if stage not in ("Itália","França"):
        stage=resume_target(plan)["stage"]
    st.session_state["flow_stage"]=stage
    st.session_state["flow_active_stage"]=stage
    if destination is not None:
        st.session_state["flow_active_destination"]=destination
    st.session_state["flow_add_open"]=bool(st.session_state.get("flow_add_open"))
    set_task(st.session_state,"Meu roteiro","Meu planejamento")


def return_to_edit()->None:
    """Callback to restore the draft context without resetting search/filters."""
    from ux_navigation import set_task
    state=st.session_state
    state["flow_stage"]=state.get("flow_return_stage","Itália")
    state["flow_active_stage"]=state["flow_stage"]
    if state.get("flow_return_destination"):
        state["flow_active_destination"]=state["flow_return_destination"]
    if state.get("flow_return_add_open"):
        state["flow_add_open"]=True
    set_task(state,"Meu roteiro","Meu planejamento")


def _form_settings(plan:dict)->None:
    names={x["id"]:x["name"] for x in base_options()}
    with st.container(border=True):
        st.markdown("### Configurar minha viagem")
        st.caption("Suas escolhas atuais são a referência. Alterações são revisadas "
                   "e confirmadas antes de atualizar o plano.")
        with st.form("workflow_trip_settings",clear_on_submit=False):
            a,b,c=st.columns(3)
            total=a.number_input("Duração total (dias)",min_value=65,max_value=75,
                                 value=plan["total_days"],step=1)
            italy=b.number_input("Dias na Itália",min_value=8,max_value=12,
                                 value=plan["italy_days"],step=1)
            c.metric("Temporada europeia",str(int(total)-int(italy))+" dias")
            with st.expander("Detalhes de férias e instalação"):
                x,y=st.columns(2)
                vacation=x.number_input("Férias iniciais (dias)",min_value=20,
                                        max_value=30,value=plan["vacation_days"],step=1)
                setup=y.number_input("Instalação (dias)",min_value=1,max_value=5,
                                     value=plan["setup_days"],step=1)
            city=st.selectbox("Cidade-base atual (do plano oficial)",
                              sorted([x for x in names if x in
                                      {"mulhouse","strasbourg","metz","nancy"}]),
                              index=sorted([x for x in names if x in
                                      {"mulhouse","strasbourg","metz","nancy"}]).index(
                                          plan["base_city"]),
                              format_func=lambda k:names[k])
            st.caption("Outras cidades permanecem candidatas: compare antes, "
                       "sem mudar automaticamente a cidade-base oficial.")
            a,b=st.columns(2)
            profile=a.selectbox("Estilo de viagem",list(TRIP_STYLES),
                                index=list(TRIP_STYLES).index(plan["profile"]),
                                format_func=lambda k:TRIP_STYLES[k])
            budget=b.selectbox("Cenário financeiro",list(BUDGET_LABELS),
                               index=list(BUDGET_LABELS).index(plan["budget_scenario"]),
                               format_func=lambda k:BUDGET_LABELS[k])
            from attractions_model import load_attractions
            catalog=load_attractions()
            named={d["id"]:d["name"] for d in catalog["destinations"]}
            for old in (plan.get("mandatory_destinations",[])+
                        plan.get("excluded_destinations",[])):
                named.setdefault(old,old+" (registrado anteriormente)")
            with st.expander("Preferências principais"):
                must=st.multiselect("Destinos que quero priorizar",list(named),
                    default=plan.get("mandatory_destinations",[]),
                    format_func=lambda key:named[key],key="workflow_priority_destinations")
                avoid=st.multiselect("Destinos que quero evitar",list(named),
                    default=plan.get("excluded_destinations",[]),
                    format_func=lambda key:named[key],key="workflow_avoid_destinations")
                st.caption(str(len(plan.get("preferences",{})))+
                    " preferências de atrações já marcadas. "
                    "Preferências específicas continuam editáveis ao escolher passeios.")
            submitted=st.form_submit_button("Revisar as mudanças",type="primary")
        if submitted:
            candidate=dict(total_days=int(total),italy_days=int(italy),
                           vacation_days=int(vacation),setup_days=int(setup),
                           base_city=city,profile=profile,budget_scenario=budget,
                           mandatory_destinations=list(must),
                           excluded_destinations=list(avoid))
            try:
                st.session_state["workflow_settings_preview"]=preview_settings(
                    active_plan(),candidate)
            except (ValueError,TypeError,KeyError) as exc:
                st.session_state.pop("workflow_settings_preview",None)
                st.error("Revise suas premissas: "+str(exc))
        review=st.session_state.get("workflow_settings_preview")
        if review:
            if review["original_revision"]!=active_plan()["revision"]:
                st.warning("O plano foi alterado em outra ação. Revise as mudanças novamente.")
                st.session_state.pop("workflow_settings_preview",None)
            elif review["same_choice"]:
                st.info("As configurações já são iguais às do plano.")
            else:
                st.markdown("**Antes de aplicar**")
                labels={"total_days":"Duração total","italy_days":"Dias na Itália",
                        "vacation_days":"Férias iniciais","setup_days":"Instalação",
                        "base_city":"Base","profile":"Estilo","budget_scenario":"Orçamento",
                        "mandatory_destinations":"Destinos prioritários",
                        "excluded_destinations":"Destinos descartados"}
                for key,change in review["changes"].items():
                    st.caption(labels.get(key,key)+": "+str(change["current"])+
                               " → "+str(change["proposed"]))
                st.warning("Passeios escolhidos, datas, fontes e reservas não "
                           "serão alterados por esta configuração. Revise calendários "
                           "dependentes da duração antes de confirmar.")
                left,right=st.columns(2)
                if left.button("Confirmar mudanças do meu plano",
                               key="workflow_settings_confirm",type="primary"):
                    try:
                        changes={key:delta["proposed"]
                                 for key,delta in review["changes"].items()}
                        if active_plan()["revision"]!=review["original_revision"]:
                            raise ValueError("Plano alterado; revise novamente")
                        update_fields(**changes)
                        st.session_state["workflow_settings_open"]=False
                        st.session_state.pop("workflow_settings_preview",None)
                        st.session_state["workflow_change_notice"]=(
                            "Premissas atualizadas no plano desta sessão. "
                            "Use Salvar planejamento para persistir.")
                        st.rerun()
                    except (ValueError,KeyError,TypeError) as exc:
                        st.error(str(exc))
                if right.button("Cancelar revisão",key="workflow_settings_cancel"):
                    st.session_state.pop("workflow_settings_preview",None)
                    st.rerun()
        with st.expander("Configurações avançadas"):
            st.caption("Câmbio, projeções, otimização e custos pesquisados estão "
                       "disponíveis em Orçamento → Simulações. "
                       "Não é necessário definir taxas para escolher passeios.")
        if st.button("Fechar configurações",key="workflow_settings_close"):
            st.session_state["workflow_settings_open"]=False
            st.session_state.pop("workflow_settings_preview",None)
            st.rerun()


def _form_alternative(plan:dict)->None:
    labels={x["id"]:x["name"] for x in base_options()}
    with st.container(border=True):
        st.markdown("### Comparar alternativa")
        st.caption("Referência: meu plano atual. Nenhuma simulação modifica o TripPlan.")
        st.write("**Meu plano** · "+labels.get(plan["base_city"],plan["base_city"])+
                 " · "+str(plan["total_days"])+" dias · Itália "+
                 str(plan["italy_days"])+" dias · "+TRIP_STYLES[plan["profile"]]+
                 " · "+BUDGET_LABELS[plan["budget_scenario"]])
        a,b=st.columns(2)
        base=a.selectbox("Cidade-base alternativa",list(labels),
                         key="workflow_alt_base",format_func=lambda k:labels[k])
        total=b.number_input("Dias totais da alternativa",min_value=65,max_value=75,
                             value=plan["total_days"],step=1,
                             key="workflow_alt_total_days")
        c,d=st.columns(2)
        italy=c.number_input("Dias na Itália (alternativa)",min_value=8,max_value=12,
                             value=plan["italy_days"],step=1,key="workflow_alt_italy_days")
        budget=d.selectbox("Orçamento da alternativa",list(BUDGET_LABELS),
                           index=list(BUDGET_LABELS).index(plan["budget_scenario"]),
                           format_func=lambda k:BUDGET_LABELS[k],
                           key="workflow_alt_budget")
        profile=st.selectbox("Estilo da alternativa",list(TRIP_STYLES),
                             index=list(TRIP_STYLES).index(plan["profile"]),
                             format_func=lambda k:TRIP_STYLES[k],
                             key="workflow_alt_profile")
        alternative={"base_city":base,"total_days":int(total),
                     "italy_days":int(italy),"budget_scenario":budget,
                     "profile":profile}
        try:
            comparison=compare_alternative(plan,alternative)
        except (ValueError,KeyError,TypeError) as exc:
            st.warning(str(exc))
            comparison=None
        if comparison:
            if not comparison["differences"]:
                st.info("A alternativa é idêntica ao seu plano.")
            else:
                st.markdown("**Impactos desta alternativa**")
                for key,(before,after) in comparison["differences"].items():
                    names={"base_city":"Cidade-base","total_days":"Duração",
                           "italy_days":"Itália","budget_scenario":"Cenário financeiro",
                           "profile":"Estilo"}
                    st.caption(names.get(key,key)+": "+str(before)+" → "+str(after))
            st.caption("**Permanece igual:** "+
                       "; ".join(comparison["unchanged"])+".")
            st.warning("**Não cotado/comparável:** "+
                       "; ".join(comparison["not_quoted"])+
                       ". Uma alternativa não significa economia garantida.")
            if "base_city" in comparison["differences"]:
                st.button("Ver impactos em passeios, rotas e custos",
                          key="workflow_alt_detailed_impact",
                          on_click=open_detailed_impact)
            if not comparison["can_apply_official"]:
                st.info("A candidata tem pesquisa exploratória, mas ainda não integra "
                        "as quatro bases validadas no modelo oficial. Não pode ser "
                        "promovida sem revisão de rotas, custos e regras.")
            elif comparison["differences"]:
                if st.button("Revisar aplicação ao meu plano",
                             key="workflow_alt_review"):
                    changes={key:after for key,(_,after) in
                             comparison["differences"].items()}
                    st.session_state["workflow_alt_preview"]=preview_settings(
                        plan,changes)
                approved=st.session_state.get("workflow_alt_preview")
                if approved:
                    if approved["original_revision"]!=plan["revision"]:
                        st.warning("Seu plano mudou; recalcule esta alternativa.")
                        st.session_state.pop("workflow_alt_preview",None)
                    else:
                        st.warning("A aplicação exige confirmação e poderá alterar "
                                   "dias e premissas, mas não cria reservas.")
                        if st.button("Confirmar aplicação ao plano atual",
                                     key="workflow_alt_confirm"):
                            changes={k:v["proposed"] for k,v in
                                     approved["changes"].items()}
                            update_fields(**changes)
                            st.session_state.pop("workflow_alt_preview",None)
                            st.session_state["workflow_change_notice"]=(
                                "Alternativa aplicada ao plano da sessão; salve sua revisão.")
                            st.rerun()
        if st.button("Fechar comparação",key="workflow_alt_close"):
            st.session_state["workflow_compare_open"]=False
            st.session_state.pop("workflow_alt_preview",None)
            st.rerun()


def return_official_context()->None:
    state=st.session_state
    plan=active_plan()
    selected=state.get("scenario_base_selected",plan["base_city"])
    if selected!=plan["base_city"]:
        state["ux_last_candidate"]=selected
    state["scenario_base_selected"]=plan["base_city"]
    state["scenario_sidebar"]=plan["base_city"]
    state["ux_mode"]="Oficial"
    state["ux_mode_value"]="Oficial"


def render_context(plan:dict,*,area:str)->None:
    """Compact entrypoint, and the *only* comprehensive configuration UI."""
    names={x["id"]:x["name"] for x in base_options()}
    viewing_simulation=st.session_state.get("ux_mode_value")=="Simulação"
    selected=st.session_state.get("scenario_base_selected",plan["base_city"])
    if viewing_simulation:
        st.caption("**Simulação ativa** · "+names.get(selected,selected)+
                   " · "+str(st.session_state.get("ux_days_value",
                   plan["total_days"]-plan["italy_days"]))+
                   " dias de temporada europeia · Plano atual preservado")
        if area=="Minha viagem":
            st.button("Voltar ao oficial",key="ux_return_official",
                      on_click=return_official_context)
    else:
        st.caption("**Roteiro oficial** · "+names.get(plan["base_city"],plan["base_city"])+
                   " · "+str(plan["total_days"]-plan["italy_days"])+
                   " dias de temporada europeia · Reservas não confirmadas")
    display="Meu plano · "+str(plan["total_days"])+" dias · Itália "+str(
        plan["italy_days"])+" dias · "+BUDGET_LABELS[plan["budget_scenario"]]
    if st.session_state.get("workflow_compare_open"):
        display="Comparar alternativa · referência: "+display
    st.caption(display)
    a,b=st.columns([1,1.25])
    a.button("Configurar minha viagem",key="workflow_open_settings",
             on_click=show_settings,width="stretch")
    b.button("Comparar alternativa",key="workflow_open_alternative",
             on_click=show_alternative,width="stretch")
    if st.session_state.pop("workflow_change_notice",None):
        st.success("Plano atualizado nesta sessão. Salve para manter a revisão.")
    if st.session_state.get("workflow_settings_open"):
        _form_settings(active_plan())
    elif st.session_state.get("workflow_compare_open"):
        _form_alternative(active_plan())


def render_breadcrumb(*,stage:str|None=None,city:str|None=None,
                      show_return:bool=False)->None:
    st.caption(" › ".join(breadcrumb(stage,city)))
    if show_return:
        st.button("← Voltar à edição",key="workflow_back_to_edit",
                  on_click=return_to_edit)


def render_home_continue(plan:dict)->None:
    recovery=resume_target(plan)
    has_work=bool(plan.get("packages") or plan.get("flexible_visits"))
    if st.session_state.get("flow_active_destination") or has_work:
        st.caption("Continue de onde o planejamento salvo permite recuperar. "
                   "Filtros não salvos só permanecem durante esta sessão.")
        st.button("Continuar planejando",key="home_continue_planning",
                  on_click=resume_plan,type="primary")
    elif plan["revision"]==0:
        st.caption("Primeiro planejamento? Você pode usar as premissas sugeridas "
                   "e revisá-las depois, sem escolher uma base definitiva.")
        st.button("Configuração inicial (opcional)",key="home_start_setup",
                  on_click=show_settings)
        st.button("Começar pelo roteiro",key="home_start_itinerary",
                  on_click=resume_plan,type="primary")
    else:
        st.button("Continuar planejando",key="home_continue_planning",
                  on_click=resume_plan)
