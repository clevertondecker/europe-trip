"""Europa 2027 — Streamlit travel + planning dashboard (read-only MVP)."""
from __future__ import annotations

from html import escape
from pathlib import Path

import streamlit as st

from data_model import STATUS_LABEL, calculate_scenario, get_scenario, load_data, money_brl, select_places
from map_presentation_ui import render_map_view
from drive_sync import load_live_updates, update_map_places
from city_compare import get_preset, initialize_weight_state, load_cities, normalized_weights, rank_cities
from city_research import city_readiness, load_audit
from city_market import load_market, observed_rent_summary, example_train_couple_return
from city_research_round2 import load_round2
from finance_lifestyle import FRENCH_BUDGET, audit_subtotals, lifestyle_outcome
from itinerary_planner import load_itinerary, select_outings, basket_totals, visible_map_places
from italy_honeymoon_ui import render_italy_honeymoon
from catalog import build_catalog, filter_catalog
from unified_budget import resolve_french_budget, scenario_total
from calendar_model import calendar_plan
from route_preview import route_endpoints
from attractions_ui import render_explorer
from ux501_destination_discovery_ui import render_independent_destination_discovery
from rec03a_suggestions_ui import render_recommendation_activity
from rec03a_session import apply_navigation as apply_recommendation_navigation, sync_identity, identity_token, SUGGESTED
from rec03b_handoff_ui import render_notice, render_profile_context, render_contextual_map, render_planning_return
from rec03b_handoffs import CONTEXT
from rec04_simulation_handoff import apply_simulation_request
from rec04_simulation_ui import (render_simulation_context,render_optional_housing_commitments,render_housing_cashflow_note)
from sidebar_account_ui import account_view_state, _logged_in_user
from travel_advisor_ui import _owner_config
from travel_advisor_ui import render_advisor, _recover_saved_plan, _secure_save, _owner_signed_in
from sidebar_account_ui import render_sidebar_account
from ux64_navigation_model import public_area, select_public_area
from ux64_navigation_ui import render_public_task_tabs
from travel_dashboard_ui import render_trip_dashboard
from itinerary_flow_ui import render_itinerary_workbench
from ux_planning_journey_ui import render_planning_journey, apply_planning_request
from smart_calendar_ui import render_smart_calendar
from ux37_next_actions_ui import render_next_actions,render_return_to_summary
from continuity_ui import (apply_pending_restore,render_continuity_panel,
                           restore_private_on_start,autosave_private_if_requested,private_status_label)
from planning_context_ui import (render_context,render_home_continue,
                                 render_breadcrumb,return_to_edit,show_settings)
from base_explorer_ui import render_base_explorer, _comparison as render_route_comparison, _split_stay as render_split_stay
from base_explorer_model import load_exploration
from base_change_ui import render_base_change
from city_decision_ui import render_city_decision
from base_weight_coverage_ui import render_weight_coverage
from budget_sections_ui import render_budget_summary, render_budget_details
from base_scenario_model import base_options, choose_exploratory_base, hypothetical_city_name, expanded_rail_routes
from base_research_expanded_model import load_research, find_city, observed_housing
from base_scenario_ui import render_scenario_impact
from exploratory_selection import sync_city_widget, set_city_from_widget
from ux_navigation import (AREAS as UX_AREAS, SECTIONS as UX_SECTIONS, DESCRIPTIONS as UX_DESCRIPTIONS,
                           LEGACY_PAGES, LEGACY_ITINERARY, RESEARCH_OPTIONS, SUGGESTION_OPTIONS,
                           GUIDES as UX_GUIDES,
                           bootstrap as bootstrap_ux, apply as apply_ux,
                           set_task as set_ux_task, set_area as set_ux_area,
                           set_from_legacy as set_ux_legacy, route as ux_route)
from planning_session import bootstrap as bootstrap_trip, active_plan, update_fields
from planning_store import summary as planning_summary
from ux504_guided_journey_model import apply_navigation_request
from ux504_guided_journey_ui import render_guided_home, render_contextual_shortcuts
from planning_status import save_label
from attractions_model import load_attractions, load_base_routes, places_for_base, excursions_overage_brl, package_cost

st.set_page_config(page_title="Nossa Europa 2027", page_icon="🌍", layout="wide", initial_sidebar_state="expanded")

# Initialize the single plan before any page-specific widgets.
# Authenticated new sessions recover the latest saved GitHub plan.
_recover_saved_plan()
bootstrap_trip()
# Manual recovery is committed before nav/widgets; no automatic cloud writes.
apply_pending_restore(load_attractions())
restore_private_on_start(load_attractions())
restored_mode=st.session_state.pop("ux_pending_mode",None)
if restored_mode in ("Oficial","Simulação"):
    st.session_state["ux_mode"]=restored_mode
    st.session_state["ux_mode_value"]=restored_mode
# Restore saved exploratory durations before any Streamlit widget is rendered.
restored_days=st.session_state.pop("ux_pending_days",None)
if restored_days is not None:
    st.session_state["ux_days"]=max(40,min(80,int(restored_days)))
    st.session_state["unified_stay"]=st.session_state["ux_days"]
bootstrap_ux(st.session_state)
_rec_config = _owner_config()
_rec_user = (_logged_in_user() if _rec_config.get('google_configured') and _rec_config.get('owner_email') else None)
sync_identity(st.session_state, identity_token(account_view_state(_rec_config, _rec_user), _rec_user))
apply_navigation_request(st.session_state)
apply_recommendation_navigation(st.session_state)
apply_planning_request(st.session_state)
apply_simulation_request(st.session_state)
# Legacy outing handoffs must reach the single editor rather than the summary.
if ((st.session_state.get("ux_area"),st.session_state.get("ux_section"))==("Meu roteiro","Meu planejamento")
        and st.session_state.get("ux45_origin") and st.session_state.get("flow_edit_target")):
    set_ux_task(st.session_state,"Meu roteiro","Organizar viagem")
    st.session_state["flow_journey_view"]="organize"
    st.session_state["ux_organize_view"]="Por período ou data"
if st.session_state.pop("ux503_pending_return_to_wishlist", False):
    set_ux_task(st.session_state, "Explorar", "Passeios")
    st.session_state["ux502_view"] = "Minha lista"
# One global exploratory base, separate from the approved TripPlan.
_all_bases=base_options(include_candidates=True)
_base_details={item["id"]:item for item in _all_bases}
_candidate=st.session_state.get("scenario_base_selected",active_plan()["base_city"])
if _candidate not in _base_details:
    _candidate=active_plan()["base_city"]
st.session_state["scenario_base_selected"]=_candidate
st.session_state.setdefault("ux_mode","Oficial")
st.session_state.setdefault("ux_mode_value",st.session_state["ux_mode"])
st.session_state.setdefault("ux_days",active_plan()["total_days"]-active_plan()["italy_days"])
st.session_state.setdefault("ux_days_value",st.session_state["ux_days"])
st.session_state.setdefault("unified_stay",st.session_state["ux_days"])
if st.session_state.get("scenario_sidebar")!=_candidate:
    st.session_state["scenario_sidebar"]=_candidate
# UX75: clear any stale legacy public-autosave intent without publishing.
st.session_state.pop("advisor_autosave_pending", None)
st.session_state["advisor_autosave_optin"] = False
autosave_private_if_requested(load_attractions())
data = load_data()

@st.cache_data(ttl=300, show_spinner=False)
def fetch_live():
    # st.secrets does not exist locally until configured; never log secret contents.
    credentials = dict(st.secrets["gcp_service_account"])
    return load_live_updates(credentials)

sync_status = "snapshot"
sync_time = ""
sync_error = ""
sync_sources = {name: {"status": "snapshot"} for name in ("decisions", "tasks", "finance")}
sync_issues = []
try:
    if "gcp_service_account" in st.secrets:
        live = fetch_live()
        sync_time = live["synced_at"]
        sync_sources.update(live["source_status"])
        sync_issues = live["issues"]
        if sync_sources["decisions"]["status"] == "live":
            data["decisions"] = live["decisions"]
            data["places"] = update_map_places(data["places"], data["decisions"])
        if sync_sources["tasks"]["status"] == "live":
            data["tasks"] = live["tasks"]
        if sync_sources["finance"]["status"] == "live":
            data["budget_scenarios"] = live["budget_scenarios"]
            data["timeline"] = live["timeline"]
            data.update(live["trip_metadata"])
        if all(value["status"] == "live" for value in sync_sources.values()):
            sync_status = "live"
        elif any(value["status"] == "live" for value in sync_sources.values()):
            sync_status = "partial"
except Exception as exc:
    sync_error = type(exc).__name__


st.markdown("<style>" + (Path(__file__).resolve().parent / "assets" / "styles.css").read_text(encoding="utf-8") + "</style>", unsafe_allow_html=True)


def link(label: str, key: str) -> None:
    url = data["sources"].get(key)
    if url:
        st.link_button(label, url, use_container_width=True)


def note(msg: str) -> None:
    st.markdown(f'<div class="note">{escape(msg)}</div>', unsafe_allow_html=True)


def overline(label: str) -> None:
    st.markdown(f'<div class="eyebrow">{escape(label)}</div>', unsafe_allow_html=True)


def section(text: str) -> None:
    st.markdown(f'<div class="section-title">{escape(text)}</div>', unsafe_allow_html=True)


def map_view(places: list[dict], height: int = 430, show_labels: bool = True,
             center: tuple[float, float] | None = None, zoom: float = 4.0) -> None:
    """Backward-compatible app entrypoint forwarding to isolated renderer."""
    render_map_view(places,height=height,show_labels=show_labels,
                    center=center,zoom=zoom)


def show_place(place: dict) -> None:
    role=escape(place["role"])
    st.markdown(f"**{escape(place['name'])} · {escape(place['country'])}**")
    st.caption(f"{STATUS_LABEL[place['status']]} · {role}")
    st.write(place["description"])
    st.write(f"**Duração:** {place['duration']}")
    url=data["sources"].get(place.get("source", ""))
    if url:
        st.link_button("Ver pesquisa ou decisão no Drive", url)


def mini_budget() -> None:
    selected = st.radio("Cenário", ["60k", "70k"], format_func=lambda x:"R$ 60 mil" if x=="60k" else "R$ 70 mil",
                        horizontal=True, key="summary_budget")
    scenario=get_scenario(data,selected)
    calc=calculate_scenario(scenario)
    st.metric("Total histórico simulado", money_brl(calc["base"]))
    st.progress(min(1.0, calc["base"]/scenario["cap_brl"]))
    st.caption(f"Limite {money_brl(scenario['cap_brl'])} · Margem {money_brl(calc['balance'])} · Reserva já incluída")
    if calc["balance"] < 1000:
        st.warning("Margem muito pequena. Não aprovar compras com estes valores sem novas cotações.")
    st.link_button("Abrir planilha original",data["sources"]["spreadsheet"],use_container_width=True)


def bottom_source() -> None:
    status_text = (f"Fontes do Drive verificadas às {escape(sync_time)} (UTC)." if sync_time
                   else f"Snapshot local de {escape(data['snapshot_date'])}.")
    details = " · ".join(f"{name}: {'Drive' if status['status'] == 'live' else 'snapshot'}" for name, status in sync_sources.items())
    st.markdown(f"<div class='source-footer'>{status_text} {escape(details)}. "
                "As finanças são estimativas, não preços cotados nem reservas. "
                "O mapa usa uma base geográfica de referência, não rotas contratadas.</div>", unsafe_allow_html=True)
    with st.expander("Fontes e documentação do projeto"):
        for title,key in [("Pasta do Drive","project_folder"),("Estado atual","decisions"),("Planilha financeira","spreadsheet"),
                           ("Markdown completo","knowledge"),("Pendências","tasks")]:
            st.markdown(f"- [{title}]({data['sources'][key]})")
        st.markdown(f"Crédito da fotografia: [{data['hero_image_credit']}]({data['hero_image_credit_url']}).")

def navigate_page(destination: str) -> None:
    """Navigation from homepage controls, applied before the radio on rerun."""
    st.session_state["main_navigation"] = destination

def navigate_to_base_explorer() -> None:
    """Change navigation in a widget callback, before the sidebar is rendered."""
    st.session_state["main_navigation"] = "Roteiro"
    st.session_state["itinerary_section"] = "Explorar bases"
    st.session_state["base_explorer_mode"] = "Destinos próximos"


def navigate_to_attractions() -> None:
    st.session_state["main_navigation"] = "Roteiro"
    st.session_state["itinerary_section"] = "Guias e pesquisas"
    st.session_state["guide_section"] = "Explorar atrações"

def navigate_to_consultor() -> None:
    st.session_state["main_navigation"] = "Roteiro"
    st.session_state["itinerary_section"] = "Meus passeios"


def simulate_city_in_budget(city_name: str) -> None:
    """Carry a hypothetical base to the finance page, without approving D-004."""
    st.session_state["unified_city"] = city_name
    candidates={x["name"]:x["id"] for x in base_options(include_candidates=True)}
    if city_name in candidates:
        st.session_state["scenario_base_selected"]=candidates[city_name]
    st.session_state["unified_override_rent"] = True
    st.session_state["main_navigation"] = "Orçamento"


def _select_scenario_sidebar() -> None:
    chosen=choose_exploratory_base(st.session_state["scenario_sidebar"],_all_bases)
    st.session_state["scenario_base_selected"]=chosen
    st.session_state["ux_last_candidate"]=chosen
    st.session_state["ux_mode"]="Simulação"
    st.session_state["ux_mode_value"]="Simulação"


def _ux_area_changed() -> None:
    st.session_state.pop("ux45_origin",None)
    st.session_state.pop("flow_edit_target",None)
    set_ux_area(st.session_state,st.session_state["ux_area"])

def _ux64_legacy_sidebar_clicked(area: str) -> None:
    # Original indexed controls remain reachable in advanced navigation.
    st.session_state.pop("ux45_origin", None)
    st.session_state.pop("flow_edit_target", None)
    set_ux_area(st.session_state, area)


def _ux_sidebar_button_clicked(area: str) -> None:
    """Public navigation uses the preexisting legacy router, not a second plan."""
    st.session_state.pop("ux45_origin",None)
    st.session_state.pop("flow_edit_target",None)
    select_public_area(st.session_state,area)


def _ux_section_changed() -> None:
    # A repeated click may yield None in Streamlit. Preserve the return
    # handoff unless the user actually selects a different task.
    requested=st.session_state["ux_section"]
    if requested is not None and requested!=st.session_state.get("_ux_last_section"):
        st.session_state.pop("ux45_origin",None)
        st.session_state.pop("flow_edit_target",None)
    set_ux_task(st.session_state,st.session_state["ux_area"],requested)


def _ux_aux_changed() -> None:
    if st.session_state.get("ux_organize_view")=="Calendário inteligente":
        st.session_state["ux35_stage"]=st.session_state.get("flow_active_stage","Itália")
    apply_ux(st.session_state)


def _ux_legacy_page_changed() -> None:
    set_ux_legacy(st.session_state,st.session_state["main_navigation"],
                  st.session_state.get("itinerary_section"),
                  st.session_state.get("guide_section"))


def _ux_legacy_itinerary_changed() -> None:
    set_ux_legacy(st.session_state,"Roteiro",
                  st.session_state["itinerary_section"],
                  st.session_state.get("guide_section"))


def _ux_legacy_guide_changed() -> None:
    set_ux_legacy(st.session_state,"Roteiro","Guias e pesquisas",
                  st.session_state["guide_section"])


def _ux_days_changed() -> None:
    # Shared duration is a what-if input, never a mutation of TripPlan.
    st.session_state["ux_days_value"]=st.session_state["ux_days"]
    st.session_state["unified_stay"]=st.session_state["ux_days"]


def _ux_budget_days_changed() -> None:
    st.session_state["ux_days"]=st.session_state["unified_stay"]
    st.session_state["ux_days_value"]=st.session_state["unified_stay"]


def _ux_next_task(area:str,task:str) -> None:
    set_ux_task(st.session_state,area,task)


def _ux_mode_changed() -> None:
    st.session_state["ux_mode_value"]=st.session_state["ux_mode"]
    official=active_plan()["base_city"]
    if st.session_state["ux_mode"]=="Oficial":
        previous=st.session_state.get("scenario_base_selected",official)
        if previous!=official:
            st.session_state["ux_last_candidate"]=previous
        st.session_state["scenario_base_selected"]=official
        st.session_state["scenario_sidebar"]=official
    else:
        candidate=st.session_state.get("ux_last_candidate",official)
        if candidate not in _base_details:
            candidate=official
        st.session_state["scenario_base_selected"]=candidate
        st.session_state["scenario_sidebar"]=candidate


def _ux_return_to_official() -> None:
    """Compact home action: return to approved context, not a TripPlan update."""
    st.session_state["ux_mode"]="Oficial"
    _ux_mode_changed()


with st.sidebar:
    if "advisor_autosave_notice" in st.session_state:
        st.success(st.session_state.pop("advisor_autosave_notice"))
    if "advisor_autosave_error" in st.session_state:
        st.warning(st.session_state.pop("advisor_autosave_error"))
    st.markdown("""<div class='sidebar-brand'>
      <small>TRAVEL JOURNAL · 2027</small>
      <strong>✧ Nossa Europa</strong>
      <span>Lua de mel & temporada na França</span></div>""", unsafe_allow_html=True)
    # Native buttons provide real hit targets, icons, keyboard focus and a
    # visible active state without relying on Streamlit radio DOM internals.
    # UX_AREAS and ux_area remain the only navigation source of truth.
    sidebar_items = (
        ("Explorar", "Explorar", ":material/explore:"),
        ("Planejar", "Planejar", ":material/calendar_month:"),
        ("Orçamento", "Orçamento", ":material/account_balance_wallet:"),
    )
    with st.container(gap="xxsmall"):
        for index, (area, label, icon) in enumerate(sidebar_items):
            selected = public_area(st.session_state["ux_area"]) == area
            st.button(label, key=f"ux64_sidebar_nav_{index}",
                      type="primary" if selected else "secondary",
                      icon=icon, width="stretch",
                      help=("Seção atual: " if selected else "Abrir seção: ") + label,
                      on_click=_ux_sidebar_button_clicked, args=(area,))

    # Keep account access visible before expandable Drive/legacy sections.
    st.divider()
    render_sidebar_account()
    # A single private persistence action is available from every area.
    from continuity_ui import render_global_private_save
    render_global_private_save(active_plan(), load_attractions())

    live_count = sum(state["status"] == "live" for state in sync_sources.values())
    if sync_status == "live":
        sync_summary = "Dados sincronizados · 3/3 fontes"
    elif sync_status == "partial":
        sync_summary = f"Sincronização parcial · {live_count}/3 fontes"
    else:
        sync_summary = "Dados locais · nenhuma fonte ativa"
    st.caption(sync_summary)
    # The sync operation time and each source's modified_at are distinct.
    # A successful fetch must never imply every Drive source changed today.
    with st.expander("Google Drive · detalhes", expanded=False):
        if sync_time:
            st.caption(f"Consulta ao Drive: {sync_time} (UTC)")
        else:
            st.caption(f"Snapshot local: {data['snapshot_date']}")
        for source_name, source_label in (
            ("decisions", "Decisões"),
            ("tasks", "Pendências"),
            ("finance", "Financeiro e roteiro"),
        ):
            state = sync_sources[source_name]
            modified_at = state.get("modified_at")
            date_info = f" · fonte: {modified_at[:10]}" if modified_at else " · data não informada"
            label = "sincronizada" if state["status"] == "live" else "snapshot"
            st.caption(f"{'✅' if state['status'] == 'live' else '⚪'} {source_label}: {label}{date_info}")
        if st.button("Atualizar dados do Drive", use_container_width=True):
            fetch_live.clear()
            st.rerun()
        st.link_button("Abrir pasta no Drive", data["sources"]["project_folder"],
                       use_container_width=True)
        if sync_error:
            # Exception class only; never expose keys, tokens or raw API errors.
            st.warning("Sincronização indisponível; exibindo snapshot.")
            diagnosis = {
                "StreamlitSecretNotFoundError": "Secrets ausentes: configure [gcp_service_account] em Settings → Secrets.",
                "KeyError": "O campo [gcp_service_account] ou um campo obrigatório está ausente.",
                "ValueError": "Formato da credencial inválido. Confira especialmente os caracteres de nova linha na chave privada.",
                "MalformedError": "A chave privada não pôde ser interpretada.",
                "RefreshError": "O Google rejeitou a autenticação. Confira se a chave está ativa.",
            }.get(sync_error, "Verifique os logs do aplicativo no Streamlit Cloud.")
            st.error(f"Diagnóstico: {sync_error}. {diagnosis}")
        elif live_count == 0:
            st.caption("Nenhuma fonte ao vivo. Verifique a configuração de sincronização.")
        if sync_issues:
            with st.expander(f"Avisos de sincronização ({len(sync_issues)})"):
                for issue in sync_issues:
                    st.warning(issue)

    # Retain legacy tools for compatibility without competing with main areas.
    with st.expander("Fontes e ferramentas", expanded=False):
        st.radio("Acesso à navegação anterior", list(LEGACY_PAGES),
                 key="main_navigation", on_change=_ux_legacy_page_changed)
        st.caption("Acesso avançado às pesquisas e ferramentas anteriores.")
        # Compatibility: old indexed controls still work, but are not top-level tabs.
        for old_index,old_area in enumerate(("Minha viagem","Explorar",
                                             "Meu roteiro","Orçamento")):
            st.button("Abrir "+old_area,key=f"ux_sidebar_nav_{old_index}",
                      on_click=_ux64_legacy_sidebar_clicked,args=(old_area,))
    st.caption("ⓘ Planejamento em andamento")

# One configuration/comparison entrypoint. The TripPlan is the only official
# state; exploratory controls inside the shared panel are never official edits.
official_id=active_plan()["base_city"]
ux_area=st.session_state["ux_area"]
ux_section=st.session_state["ux_section"]
render_context(active_plan(),area=ux_area)
# Legacy exploratory inputs are only shown on demand; they never change the
# official TripPlan. Keeping them accessible preserves advanced comparisons.
if ux_area=="Explorar":
    with st.expander("Ajustes avançados da simulação",expanded=False):
        st.segmented_control("Visualizar",["Oficial","Simulação"],
                             key="ux_mode",on_change=_ux_mode_changed)
        st.selectbox("Cidade-base da simulação",list(_base_details),
                     key="scenario_sidebar",on_change=_select_scenario_sidebar,
                     disabled=st.session_state["ux_mode_value"]=="Oficial",
                     format_func=lambda key:_base_details[key]["name"]+
                                          " · "+_base_details[key]["country"])
        st.number_input("Dias na França (simulação)",
                        min_value=40,max_value=80,
                        key="ux_days",on_change=_ux_days_changed,
                        disabled=st.session_state["ux_mode_value"]=="Oficial")
        st.caption("Entradas hipotéticas, não alteram o roteiro aprovado. "
                   "Para alterar o plano oficial, use Configurar minha viagem.")
if (ux_area in ("Explorar","Orçamento") and
    st.session_state.get("flow_return_stage")):
    render_breadcrumb(stage=st.session_state.get("flow_return_stage"),
                      city=st.session_state.get("flow_return_city"),
                      show_return=True)

# UX 6.4: three public areas with route IDs retained for saved workspaces.
render_public_task_tabs()
render_notice()
if (st.session_state.get(CONTEXT) or {}).get("kind")=="planning" and (
        ux_area=="Meu roteiro" or (ux_area,ux_section)==("Explorar","Passeios")):
    render_planning_return()
# Preserve the original contract: home has no extra legacy task selector.
if ux_area!="Minha viagem" or ux_section!="Resumo":
    with st.expander("Atividades anteriores · avançado", expanded=False):
        st.segmented_control("Atividade legada",list(UX_SECTIONS[ux_area]),
                             key="ux_section",on_change=_ux_section_changed,
                             selection_mode="single")
if ux_area=="Meu roteiro" and ux_section=="Organizar viagem":
    st.segmented_control("Como organizar?",
                         ["Por período ou data","Calendário inteligente","Calendário completo"],
                         key="ux_organize_view",on_change=_ux_aux_changed)
elif ux_area=="Meu roteiro" and ux_section=="Melhorar meu roteiro":
    st.selectbox("Escolha uma ferramenta de apoio",[
        "Descobrir","Simular roteiros","Itália",
        "Temporada europeia","Calendário completo","Guias especializados"],
        key="ux_improve_view",on_change=_ux_aux_changed)
    if st.session_state.get("ux_improve_view")=="Guias especializados":
        st.selectbox("Qual guia?",list(UX_GUIDES),
                     key="ux_guide_view",on_change=_ux_aux_changed)
elif ux_area=="Orçamento" and ux_section=="Simulações":
    st.segmented_control("Ferramenta de simulação",
                         ["Simulação geral","Consultor de passeios"],
                         key="ux_budget_view",on_change=_ux_aux_changed)
# Initialize the organizer on navigation entry, never on each Streamlit rerun.
_organize_activity=(ux_area,ux_section)==("Meu roteiro","Organizar viagem")
if _organize_activity and not st.session_state.get("_flow_organize_activity",False):
    st.session_state["flow_organize_open"]=True
    # UX83: entering Organizar focuses the canonical organizer; no extra editor.
    st.session_state["flow_journey_view"]="organize"
st.session_state["_flow_organize_activity"]=_organize_activity
page,itinerary_target,guide_target,base_target=ux_route(
    ux_area,ux_section,
    research=("Calendário completo" if
              st.session_state.get("ux_organize_view")=="Calendário completo"
              and (ux_area,ux_section)==("Meu roteiro","Organizar viagem")
              else st.session_state.get("ux_research","Pesquisa ampliada")),
    suggestion=(st.session_state.get("ux_improve_view","Descobrir") if
                (ux_area,ux_section)==("Meu roteiro","Melhorar meu roteiro")
                else st.session_state.get("ux_suggestion","Descobrir")),
    france=st.session_state.get("ux_france_view","Meus passeios"),
    city_view=st.session_state.get("ux_city_view","Visão da cidade"),
    budget_view=st.session_state.get("ux_budget_view","Simulação geral"),
    guide_view=st.session_state.get("ux_guide_view","Itália e Costa Amalfitana"))
if ux_area!="Minha viagem" and (ux_area,ux_section)!=("Explorar","Cidades-base"):
    st.caption(UX_DESCRIPTIONS.get((ux_area,ux_section),"Continue o planejamento."))
if (ux_area=="Meu roteiro" and ux_section=="Melhorar meu roteiro" and
    st.session_state.get("flow_return_stage")):
    render_breadcrumb(stage=st.session_state.get("flow_return_stage"),
                      city=st.session_state.get("flow_return_city"),
                      show_return=True)
if page != "Visão geral":
    render_return_to_summary()
if page == "Visão geral":
    render_planning_journey(active_plan(),load_attractions(),data,
                            sync_sources["finance"]["status"]=="live",
                            st.session_state.get("advisor_eurfx",6.3),
                            st.session_state.get("advisor_chffx",7.1),summary_only=True)
    with st.expander("Painéis anteriores, mapa, fontes e detalhes · avançado", expanded=False):
        st.divider()
        st.markdown("#### Informações e painéis complementares")
        render_home_continue(active_plan())
        render_next_actions(active_plan(),load_attractions())
        if st.session_state.get("flow_journey_view")!="review":
            render_continuity_panel(active_plan(),load_attractions())
        st.markdown("""<div class="home-hero" role="region" aria-label="Apresentação da viagem">
          <div class="home-hero__content"><div class="home-hero__eyebrow">ITÁLIA → FRANÇA · 2027</div>
          <h1>Uma viagem para viver,<br>não só visitar.</h1>
          <p>Uma lua de mel entre cidades históricas, costa italiana e semanas vivendo como moradores na França.</p>
          <div class="home-hero__chips"><span>♡ Dois viajantes</span>
          <span>✧ Sem reservas confirmadas</span><span>◷ Longa temporada em estudo</span></div>
          </div></div>""", unsafe_allow_html=True)

        current_plan=active_plan()
        # Main call to action sits inside the home dashboard, after the hero.
        st.button("Explorar cidades-base →",key="home_continue_bases",
                  on_click=_ux_next_task,args=("Explorar","Cidades-base"))
        status_label,status_hint=private_status_label(save_label(
            current_plan,st.session_state.get("advisor_saved_snapshot"),
            _owner_signed_in()))
        trip_stats=planning_summary(current_plan)
        st.markdown("<div class='page-section'>Continuar nosso planejamento</div>",
                    unsafe_allow_html=True)
        for col,(label,value,hint) in zip(st.columns(3,gap="small"),[
            ("Atrações escolhidas",str(trip_stats["attractions"]),
             "Passeios desejados"),
            ("Dias organizados",str(trip_stats["scheduled_days"]),
             "Sem reservas confirmadas"),
            ("Planejamento",status_label,status_hint)]):
            with col:
                st.markdown("<div class='page-stat page-stat--mint'>"
                            f"<div class='page-stat__label'>{escape(label)}</div>"
                            f"<div class='page-stat__value'>{escape(value)}</div>"
                            f"<div class='page-stat__hint'>{escape(hint)}</div></div>",
                            unsafe_allow_html=True)
        if not trip_stats["attractions"]:
            st.info("Você ainda não escolheu atrações. Explore os destinos para começar a montar o roteiro.")
        else:
            st.caption("O roteiro está em construção. Preços e horários para 2027 precisam de confirmação.")
        b1,b2,b3=st.columns(3,gap="small")
        with b1:
            st.button("Escolher atrações",key="home_choose_attractions",
                      on_click=navigate_to_attractions,use_container_width=True)
        with b2:
            st.button("Melhorar meu roteiro",key="home_open_consultor",
                      on_click=navigate_to_consultor,use_container_width=True)
        with b3:
            st.button("Ver orçamento",key="home_open_budget",
                      on_click=navigate_page,args=("Orçamento",),use_container_width=True)

        from datetime import date
        wedding = date.fromisoformat(data["wedding_date"])
        departure = date.fromisoformat(data["departure_candidate"])
        departure_label = departure.strftime("%d/%m/%Y") if departure > wedding else "A definir"
        cap_values = sorted({int(item["cap_brl"] / 1000) for item in data["budget_scenarios"]})
        cap_label = f"R$ {cap_values[0]} mil / R$ {cap_values[-1]} mil" if len(cap_values) > 1 else f"R$ {cap_values[0]} mil"
        cards = [
            ("Casamento", wedding.strftime("%d/%m/%Y"), "Data fixa do casal", "♡", "wedding"),
            ("Partida em estudo", departure_label, "Hipótese, sem bilhete emitido", "▦", "departure"),
            ("Permanência proposta", f"{data['duration_min_days']}–{data['duration_max_days']} dias", "Para dois viajantes", "✈", "duration"),
            ("Orçamento", cap_label, "Tetos de planejamento, não cotações", "◎", "budget"),
        ]
        for col, (label, value, detail, glyph, tone) in zip(st.columns(4, gap="small"), cards):
            with col:
                st.markdown(f"<div class='home-kpi home-kpi--{tone}'>"
                            f"<span class='home-kpi__icon' aria-hidden='true'>{glyph}</span>"
                            f"<div class='home-kpi__label'>{escape(label)}</div>"
                            f"<div class='home-kpi__value'>{escape(value)}</div>"
                            f"<div class='home-kpi__detail'>{escape(detail)}</div></div>",
                            unsafe_allow_html=True)

        st.markdown("<div class='page-section'>Situação atual do planejamento</div>",unsafe_allow_html=True)
        tasks_done=sum(t.get("status")=="concluído" for t in data["tasks"])
        tasks_total=len(data["tasks"])
        open_decisions=sum(d["status"].casefold() in {"aberta","não decidida","nao decidida"}
                           for d in data["decisions"])
        sources_live=sum(v["status"]=="live" for v in sync_sources.values())
        progress_cards=[
            ("Pesquisas concluídas",f"{tasks_done}/{tasks_total}","Registro de tarefas no Drive"),
            ("Decisões ainda abertas",str(open_decisions),"Aguardando definição"),
            ("Fontes sincronizadas",f"{sources_live}/3","Docs e planilha do Drive"),
            ("Reservas confirmadas","0","Nenhum compromisso registrado")
        ]
        for col,(label,value,detail) in zip(st.columns(4,gap="small"),progress_cards):
            with col:
                st.markdown("<div class='page-stat'>"
                            f"<div class='page-stat__label'>{escape(label)}</div>"
                            f"<div class='page-stat__value'>{escape(value)}</div>"
                            f"<div class='page-stat__hint'>{escape(detail)}</div></div>",
                            unsafe_allow_html=True)
        action1,action2=st.columns(2,gap="medium")
        with action1:
            st.button("Continuar pelo orçamento →",use_container_width=True,
                      key="home_next_budget",on_click=navigate_page,args=("Orçamento",))
        with action2:
            st.button("Ver pesquisas prioritárias →",use_container_width=True,
                      key="home_next_tasks",on_click=navigate_page,args=("Pesquisas & decisões",))

        overview_left, overview_map, overview_budget = st.columns([1.06, 1.42, 1.08], gap="medium")
        with overview_left:
            st.markdown("<div class='home-overview-copy'><div class='home-section-label'>VISÃO DA VIAGEM</div>"
                        "<h2>O que estamos construindo</h2>"
                        "<p>Destinos, orçamento e escolhas do casal em um só lugar. "
                        "Os pontos do mapa são referências, não reservas.</p></div>", unsafe_allow_html=True)
            st.button("Explorar destinos →", use_container_width=True,
                      on_click=navigate_page, args=("Mapa & destinos",), key="home_go_map")

        with overview_map:
            # The map displays real reference coordinates but no invented connecting route.
            map_view([p for p in build_catalog(data["places"],load_itinerary())
                      if p["id"] in {"rome","maiori","mulhouse","strasbourg"}],190)
            st.caption("Mapa de referência · cidades ainda em avaliação")

        with overview_budget:
            selected = st.radio("Cenário em estudo", ["60k", "70k"],
                                format_func=lambda x: f"R$ {x[:-1]} mil",
                                horizontal=True, key="home_budget_choice")
            scenario = get_scenario(data, selected)
            calc = calculate_scenario(scenario)
            used_pct = max(0, min(100, 100 * calc["total"] / scenario["cap_brl"]))
            st.markdown(
                "<div class='home-mini-budget'><div class='home-mini-budget__eyebrow'>◉ Resumo do orçamento</div>"
                f"<div class='home-mini-budget__amount'>{escape(money_brl(calc['total']))}</div>"
                f"<div class='home-mini-budget__track'><div class='home-mini-budget__fill' style='width:{used_pct:.1f}%'></div></div>"
                f"<div class='home-mini-budget__foot'>Margem: {escape(money_brl(calc['balance']))} · {'premissas do Drive' if sync_sources['finance']['status']=='live' else 'snapshot histórico'}</div></div>",
                unsafe_allow_html=True)
            st.button("Ver orçamento completo →", use_container_width=True,
                      on_click=navigate_page, args=("Orçamento",), key="home_go_budget")

        left, right = st.columns([2.3, 1], vertical_alignment="center")
        with left:
            st.markdown("<div class='home-section-label'>DECISÕES EM ABERTO</div>", unsafe_allow_html=True)
        with right:
            st.button("Ver todas as decisões →", use_container_width=True,
                      on_click=navigate_page, args=("Pesquisas & decisões",),
                      key="home_go_decisions")

        outstanding = [d for d in data["decisions"] if d["status"].casefold() in {"aberta", "não decidida", "nao decidida"}]
        if outstanding:
            for col, decision in zip(st.columns(min(3, len(outstanding)), gap="small"), outstanding[:3]):
                with col:
                    detail = decision.get("note", "").strip()
                    if not detail or detail.rstrip(".") == decision["title"].strip().rstrip("."):
                        detail = "Aguardando definição no Drive."
                    st.markdown(
                        f"<div class='home-decision'><strong>{escape(decision['title'])}</strong>"
                        f"<p>{escape(detail)}</p></div>", unsafe_allow_html=True)
        else:
            st.caption("Nenhuma decisão pendente identificada no documento sincronizado.")

        st.markdown("<div class='home-section-label'>TRÊS MOMENTOS</div>", unsafe_allow_html=True)
        st.markdown("<div class='home-section-title'>Da lua de mel à vida francesa</div>", unsafe_allow_html=True)
        stages = [
            ("01 · NOSSA CHEGADA", "Itália",
             f"Cerca de {data['italy_days_approx']} dias entre Roma e uma base a escolher na Costa Amalfitana.",
             "https://images.unsplash.com/photo-1552832230-c0197dd311b5?w=1000&auto=format&fit=crop&q=85", "Roteiro"),
            ("02 · NOSSA BASE", "Instalação",
             "Cerca de 3–5 dias para organizar moradia, internet e rotina na França.",
             "https://images.unsplash.com/photo-1449844908441-8829872d2607?w=1000&auto=format&fit=crop&q=85", "Roteiro"),
            ("03 · NOSSO COTIDIANO", "França",
             f"{data['france_days_estimate']} no total, incluindo férias e trabalho remoto.",
             "https://images.unsplash.com/photo-1502602898657-3e91760cbb34?w=1000&auto=format&fit=crop&q=85", "Roteiro"),
        ]
        for idx, (col, (number, title, description, photo, dest)) in enumerate(zip(st.columns(3, gap="medium"), stages)):
            with col:
                st.markdown(
                    f"<div class='home-stage'><div class='home-stage__image' role='img' aria-label='Imagem ilustrativa: {escape(title)}' "
                    f"style='background-image:url({photo})'></div>"
                    f"<div class='home-stage__inside'><div class='home-stage__no'>{escape(number)}</div>"
                    f"<div class='home-stage__name'>{escape(title)}</div>"
                    f"<div class='home-stage__desc'>{escape(description)}</div></div></div>",
                    unsafe_allow_html=True)
                st.button(f"Ver etapa: {title} →", key=f"home_stage_{idx}", use_container_width=True,
                          on_click=navigate_page, args=(dest,))

        st.markdown("<div class='home-disclaimer'>Planejamento em desenvolvimento: voos, imóveis e passeios ainda não reservados. "
                    "As estimativas históricas não substituem cotações reais. Imagens ilustrativas: Wikimedia Commons e Unsplash.</div>",
                    unsafe_allow_html=True)

elif page == "Mapa & destinos" and (st.session_state.get(CONTEXT) or {}).get("kind")=="map":
    render_contextual_map(active_plan())
    if st.button("Abrir mapa geral", key="rec03a_handoff_general_map"):
        st.session_state.pop(CONTEXT,None)
        st.rerun()

elif page == "Mapa & destinos":
    st.markdown("<div class='page-eyebrow'>EXPLORAR · EUROPA 2027</div>"
                "<div class='page-title'>Mapa & destinos</div>"
                "<div class='page-subtitle'>Explore as cidades do planejamento, compare alternativas e "
                "acompanhe o que foi proposto ou ainda está em avaliação.</div>", unsafe_allow_html=True)
    enriched_catalog = build_catalog(data["places"],load_itinerary(),
                                     load_attractions()["destinations"])
    countries_all = sorted(set(p["country"] for p in enriched_catalog))
    c1, c2, c3 = st.columns(3, gap="small")
    with c1:
        st.markdown(f"<div class='page-stat page-stat--blue'><div class='page-stat__label'>Destinos mapeados</div>"
                    f"<div class='page-stat__value'>{len(enriched_catalog)}</div>"
                    "<div class='page-stat__hint'>Referências geográficas</div></div>", unsafe_allow_html=True)
    with c2:
        st.markdown(f"<div class='page-stat page-stat--mint'><div class='page-stat__label'>Países</div>"
                    f"<div class='page-stat__value'>{len(countries_all)}</div>"
                    "<div class='page-stat__hint'>Candidatos e passeios</div></div>", unsafe_allow_html=True)
    with c3:
        candidates = sum(p["status"] == "candidata" for p in enriched_catalog)
        st.markdown(f"<div class='page-stat page-stat--cream'><div class='page-stat__label'>Alternativas em avaliação</div>"
                    f"<div class='page-stat__value'>{candidates}</div>"
                    "<div class='page-stat__hint'>Sem escolha definitiva</div></div>", unsafe_allow_html=True)

    st.markdown("<div class='page-section'>Filtre os destinos</div>", unsafe_allow_html=True)
    a,b = st.columns([1,1], gap="medium")
    with a:
        countries = st.multiselect("Países", countries_all, default=countries_all, key="map_countries")
    with b:
        statuses = st.multiselect("Etapa de decisão", list(STATUS_LABEL.keys()),
                                  default=list(STATUS_LABEL.keys()), format_func=lambda key: STATUS_LABEL[key],
                                  key="map_statuses")
    current = filter_catalog(enriched_catalog, countries=countries, statuses=statuses)
    st.markdown(f"<div class='page-filter-hint'>{len(current)} destinos encontrados · "
                "Os pontos não representam reservas, trajetos ou disponibilidade.</div>",
                unsafe_allow_html=True)
    if current:
        map_view(current, 460, show_labels=False)
    else:
        st.info("Nenhum ponto atende aos filtros. Reative uma seleção para exibir destinos.")
    st.caption("Passe o cursor sobre um ponto para ver o nome e a classificação. "
               "Os marcadores são referências geográficas, não rotas de transporte.")

    st.markdown("<div class='page-section'>Conheça as opções</div>", unsafe_allow_html=True)
    if current:
        for start_idx in range(0, len(current), 3):
            row = current[start_idx:start_idx+3]
            for column, place in zip(st.columns(3, gap="medium"), row):
                with column:
                    tone = {"roteiro_proposto":"proposed", "candidata":"candidate", "opcional":"optional"}.get(place["status"], "optional")
                    st.markdown(f"<div class='page-panel'>"
                                f"<span class='page-chip page-chip--{tone}'>{escape(STATUS_LABEL[place['status']])}</span>"
                                f"<div class='page-panel__title' style='margin-top:12px'>⌖ {escape(place['name'])}</div>"
                                f"<div class='page-panel__meta'>{escape(place['country'])} · {escape(place['role'])}</div>"
                                f"<p class='page-panel__desc'>{escape(place['description'])}</p>"
                                f"<div class='page-panel__meta'>Duração: {escape(place['duration'])}</div></div>",
                                unsafe_allow_html=True)
                    source_url = data["sources"].get(place.get("source", ""))
                    if place.get("source") in {"itinerary_research_2026",
                                                 "attractions_research_2026"}:
                        source_url = "https://github.com/clevertondecker/europe-trip/blob/main/data/itinerary_options_2027.json"
                    if source_url:
                        st.link_button("Consultar fonte", source_url, use_container_width=True)
    else:
        st.info("Nenhum destino corresponde aos filtros. Selecione mais países ou etapas.")
    st.button("Explorar atrações turísticas por cidade-base →",
              on_click=navigate_to_attractions,use_container_width=True,
              key="map_go_attractions")
    st.markdown("<div class='page-alert page-alert--neutral'>"
                "Cidades e coordenadas vêm do catálogo unificado de pesquisas históricas; a decisão sobre uma cidade-base francesa "
                "pode atualizar o status a partir do documento do Drive. Os demais pontos não são atualizados "
                "automaticamente por cotações ou reservas.</div>", unsafe_allow_html=True)

elif page == "Comparar cidades":
    st.markdown("## Comparar cidades-base")
    _rec_activity = render_recommendation_activity(plan=active_plan())
    render_contextual_shortcuts("comparison")
    with st.expander("Análises antigas de cidades-base · avançado", expanded=False):
        st.caption("Ferramentas anteriores preservadas para consultas adicionais.")
        compare_mode=st.segmented_control(
        "Tipo de análise",["Impacto da troca","Pesos das 30 cidades",
        "Comparar mesmas viagens","Uma ou duas bases","Estudo histórico"],
        key="ux_compare_mode",selection_mode="single")
        if compare_mode in ("Impacto da troca",None):
            render_city_decision(active_plan(),data,
                                 sync_sources["finance"]["status"]=="live",
                                 int(st.session_state.get("ux_days_value",60)))
        elif compare_mode=="Pesos das 30 cidades":
            render_weight_coverage()
        elif compare_mode=="Comparar mesmas viagens":
            render_route_comparison(load_exploration())
        elif compare_mode=="Uma ou duas bases":
            render_split_stay(load_exploration(),active_plan(),data,
                              sync_sources["finance"]["status"]=="live",
                              st.session_state.get("advisor_eurfx",6.3))
        else:

            import pandas as pd
            city_data = load_cities()
            all_exploratory_bases=base_options(include_candidates=True)
            compare_names={item["id"]:item["name"] for item in all_exploratory_bases}
            current_candidate=st.session_state.get("scenario_base_selected",active_plan()["base_city"])
            if current_candidate not in compare_names:
                current_candidate=active_plan()["base_city"]
            sync_city_widget("compare_exploratory_base",list(compare_names))
            selected_candidate=st.selectbox(
                "Cidade-base hipotética compartilhada", list(compare_names),
                index=list(compare_names).index(current_candidate),
                format_func=lambda k:compare_names[k],key="compare_exploratory_base",
                on_change=set_city_from_widget,args=("compare_exploratory_base",))
            st.caption("Seleção exploratória compartilhada com Explorar bases e Orçamento. "
                       "As quatro cidades do comparador histórico continuam com métricas "
                       "mais detalhadas; outras cidades podem não ter cotações equivalentes.")
            st.button("Abrir passeios e rotas desta base",
                      key="compare_open_base",on_click=navigate_to_base_explorer)
            if selected_candidate not in {"mulhouse","strasbourg","metz","nancy"}:
                research=find_city(load_research(),selected_candidate)
                observed=observed_housing(research)
                rails=expanded_rail_routes(selected_candidate)
                with st.expander("Pesquisa da candidata · "+
                                 compare_names[selected_candidate],expanded=True):
                    st.caption("Região: "+research["corridor"]+
                               " · "+str(observed["count"])+" anúncios observados em 2026"
                               " · 0 cotações completas de 2027.")
                    if observed["minimum_eur_month"] is not None:
                        st.caption("Menor anúncio histórico: € "+
                                   f'{observed["minimum_eur_month"]:,.0f}'+
                                   "/mês. Sem contrato e taxas verificados; NÃO é "
                                   "preço para 56–60 noites.")
                    if rails:
                        st.dataframe([{
                            "Destino":line["destination_name"],
                            "Trem mais rápido (min)":line["oneway_minutes"],
                            "Tarifa publicada desde (€ / pessoa / trecho)":
                                line["fare_eur_person_oneway"] if line["fare_eur_person_oneway"]
                                is not None else "Não cotada",
                            "Retorno 2027":"Não verificado",
                        } for line in rails],hide_index=True,width="stretch")
                    else:
                        st.caption("Rotas base → destino ainda não pesquisadas no "
                                   "mesmo padrão do comparador histórico.")
                    st.warning("Esta cidade não possui dados suficientes para o ranking "
                               "histórico das quatro bases. Não comparar totais parciais "
                               "como economias garantidas.")
            city_audit = load_audit()
            market = load_market()
            round2 = load_round2()
            market_by_name = {city["name"]: city for city in market["cities"]}
            audit_by_name = {city["name"]: city for city in city_audit["cities"]}
            criteria_ids = [criterion["id"] for criterion in city_data["criteria"]]

            st.markdown(
                "<div class='page-eyebrow'>PLANEJAMENTO 2027 · FRANÇA</div>"
                "<div class='page-title'>Qual cidade combina mais com a nossa viagem?</div>"
                "<div class='page-subtitle'>Um resumo claro de quatro opções, com moradia, deslocamentos e "
                "preferências separados. Os dados históricos ajudam a pesquisar, mas não autorizam reservas.</div>",
                unsafe_allow_html=True,
            )
            total_observed = sum(len(city["offers"]) for city in market["cities"])
            for col, title, value, info, tone in zip(
                st.columns(4, gap="small"),
                ["Cidades pesquisadas", "Anúncios observados", "Cotações válidas para 2027", "Última coleta"],
                [str(len(market["cities"])), str(total_observed),
                 str(sum(city["rental_quote_eligible_2027"] for city in market["cities"])), "14/11/2026"],
                ["Todas usam o mesmo padrão", "Apenas amostra de catálogo",
                 "Imóvel, datas e contrato não verificados", "Fotografia histórica do mercado"],
                ["blue", "mint", "cream", "blue"],
            ):
                with col:
                    st.markdown(
                        f"<div class='page-stat page-stat--{tone}'>"
                        f"<div class='page-stat__label'>{escape(title)}</div>"
                        f"<div class='page-stat__value'>{escape(value)}</div>"
                        f"<div class='page-stat__hint'>{escape(info)}</div></div>",
                        unsafe_allow_html=True,
                    )
            # Native segmented control has its own selected-state visual; it does not rely
            # on fragile CSS selectors for Streamlit tab internals.
            sections = ["Visão rápida", "Moradia", "Transporte e custos", "Comparar e ajustar"]
            active_section = st.segmented_control(
                "Seção do comparador", sections, default="Visão rápida",
                selection_mode="single", key="city_compare_section",
                label_visibility="collapsed",
                format_func=lambda section: {
                    "Visão rápida": "◉  Visão rápida",
                    "Moradia": "⌂  Moradia",
                    "Transporte e custos": "⇄  Transporte e custos",
                    "Comparar e ajustar": "⚖  Comparar e ajustar",
                }[section],
            )
            if active_section is None:
                active_section = "Visão rápida"

            if active_section == "Visão rápida":
                st.markdown("<div class='page-section'>Quatro cidades, principais indicadores</div>",
                            unsafe_allow_html=True)
                st.caption("Aluguel: mediana de somente três anúncios observados em 2026, não média de mercado "
                           "nem custo para dois meses. Passe: tarifa publicada de 2025–26 por pessoa/mês.")
                # Cards are informative; no rank or “winner” is inferred from a non-representative sample.
                for group_start in range(0, len(market["cities"]), 2):
                    for col, city in zip(st.columns(2, gap="medium"),
                                         market["cities"][group_start:group_start + 2]):
                        summary = observed_rent_summary(city)
                        audit = audit_by_name[city["name"]]
                        risks = audit["risks"]
                        with col:
                            st.markdown(
                                "<div class='city-digest'>"
                                "<div class='city-digest__top'>"
                                f"<span class='city-digest__name'>{escape(city['name'])}</span>"
                                "<span class='city-digest__status'>● 2027 pendente</span></div>"
                                "<div class='city-digest__metrics'>"
                                "<div><div class='city-digest__label'>Mediana de 3 anúncios</div>"
                                f"<div class='city-digest__big'>€ {summary['sample_median_eur_month']:,.0f}"
                                "<small>/mês</small></div></div>"
                                "<div><div class='city-digest__label'>Passe urbano publicado</div>"
                                f"<div class='city-digest__big'>€ {city['urban_pass']['fare_eur_month_person']:.2f}"
                                "<small>/pessoa</small></div></div></div>"
                                "<div class='city-digest__foot'>"
                                f"<span>Faixa da amostra: € {summary['min_eur_month']:,.0f}–"
                                f"{summary['max_eur_month']:,.0f}/mês</span>"
                                f"<span>{len(city['offers'])} anúncios observados</span></div>"
                                f"<div class='city-digest__alert'><strong>A verificar</strong> · "
                                f"{escape(risks[0])}</div></div>",
                                unsafe_allow_html=True,
                            )


                st.markdown("<div class='page-section'>Custos ilustrativos do mesmo estilo de vida</div>",
                            unsafe_allow_html=True)
                st.caption("Cenário de R$70 mil, casal, 60 dias na França, duas saídas de €60 por semana "
                           "e câmbio hipotético R$6,30/€. Substitui apenas o aluguel e a verba de restaurantes "
                           "pelas hipóteses indicadas; não inclui taxas adicionais de locação nem comprova disponibilidade.")
                example_scenario=get_scenario(data,"70k")
                example_split=resolve_french_budget(example_scenario,sync_sources["finance"]["status"]=="live")
                quick=[]
                for city in city_data["cities"]:
                    guess=scenario_total(example_scenario,example_split,french_days=example_split["french_days"],
                            outings_weekly=2,outing_couple_eur=60,fx_brl_per_eur=6.3,
                            rent_override_eur_month=city["reference_rent_eur"])
                    quick.append({"Cidade":city["name"],
                                  "Aluguel hipotético €/mês":city["reference_rent_eur"],
                                  "Viagem simulada (R$)":guess["total"],
                                  "Margem até o teto (R$)":guess["margin"],
                                  "Confiabilidade":"Referência histórica — não cotada"})
                st.dataframe(pd.DataFrame(quick),hide_index=True,use_container_width=True,
                             column_config={
                                "Aluguel hipotético €/mês":st.column_config.NumberColumn(format="€ %.0f"),
                                "Viagem simulada (R$)":st.column_config.NumberColumn(format="R$ %.0f"),
                                "Margem até o teto (R$)":st.column_config.NumberColumn(format="R$ %.0f"),
                             })
                st.caption("Esta comparação é uma análise de sensibilidade, não uma previsão verificável do "
                           "custo completo. O indicador de confiabilidade para reserva continua insuficiente.")

                st.markdown("<div class='page-section'>O que já sabemos — e o que não sabemos</div>",
                            unsafe_allow_html=True)
                known, unknown = st.columns(2, gap="medium")
                with known:
                    st.markdown(
                        "<div class='city-fact city-fact--good'>"
                        "<strong>✓ Evidências já coletadas</strong>"
                        "<p>Três anúncios de catálogo por cidade, exemplos ferroviários e tarifas de "
                        "transporte local publicadas. O ranking editorial histórico permanece disponível.</p>"
                        "</div>", unsafe_allow_html=True)
                with unknown:
                    st.markdown(
                        "<div class='city-fact city-fact--warn'>"
                        "<strong>! Ainda não é uma cotação de viagem</strong>"
                        "<p>Faltam preços totais para 55–65 noites, contas, casal permitido, internet, "
                        "contrato adequado e deslocamentos completos. Nenhuma cidade foi escolhida.</p>"
                        "</div>", unsafe_allow_html=True)
                st.caption("Use Moradia e Transporte para examinar evidências. "
                           "Use Comparar e ajustar para recalcular somente as notas editoriais de 2026.")

            elif active_section == "Moradia":
                st.markdown("<div class='page-section'>Aluguéis observados por cidade</div>",
                            unsafe_allow_html=True)
                st.markdown(
                    "<div class='city-fact city-fact--warn'><strong>! Preço anunciado ≠ cotação elegível</strong>"
                    "<p>Estes 12 registros são observações de catálogos de novembro/2026, não links únicos "
                    "de imóveis confirmados para duas pessoas. Contas variam; nenhuma estadia para "
                    "setembro–novembro/2027 foi confirmada.</p></div>",
                    unsafe_allow_html=True,
                )
                hcity = st.selectbox("Cidade", ["Todas"] + [c["name"] for c in market["cities"]],
                                     key="city_housing_filter")
                housing_rows = []
                for city in market["cities"]:
                    if hcity != "Todas" and city["name"] != hcity:
                        continue
                    for offer in city["offers"]:
                        utilities = {"included": "Incluídas (anúncio)",
                                     "excluded": "Não incluídas",
                                     "partial": "Parciais"}.get(offer["utilities"], "Não informado")
                        housing_rows.append({
                            "Cidade": city["name"], "Local / rua": offer["street"],
                            "Área (m²)": offer["size_m2"], "€/mês": offer["observed_eur_month"],
                            "Contas": utilities, "Fonte": city["housing_catalogue"],
                        })
                st.dataframe(pd.DataFrame(housing_rows), hide_index=True, use_container_width=True,
                             column_config={
                                 "€/mês": st.column_config.NumberColumn(format="€ %.0f"),
                                 "Área (m²)": st.column_config.NumberColumn(format="%d m²"),
                                 "Fonte": st.column_config.LinkColumn("Catálogo", display_text="Abrir"),
                             })
                st.caption("Uma URL de catálogo pode mudar ou deixar de mostrar o anúncio. "
                           "A mediana apresentada na Visão rápida resume apenas os três itens coletados.")
                with st.expander("O que precisamos confirmar em cada imóvel", expanded=False):
                    st.markdown(
                        "Para duas pessoas e 55–65 noites: datas, disponibilidade, preço total, "
                        "taxas, contas, limpeza e caução; ocupação autorizada, modalidade contratual, "
                        "internet e local para home office. O aluguel mensal observado não pode "
                        "ser multiplicado por dois e apresentado como oferta real.")
                with st.expander("Divergências das referências financeiras originais", expanded=False):
                    for audit in city_audit["cities"]:
                        st.markdown(f"**{escape(audit['name'])}**")
                        st.caption(
                            f"Modelo editorial: €{audit['historic_reference_rent_eur']}/mês · "
                            f"Premissa logística: €{audit['alternative_logistics_rent_eur']}/mês. "
                            "São parâmetros diferentes, não duas cotações equivalentes.")

            elif active_section == "Transporte e custos":
                st.markdown("<div class='page-section'>Passes urbanos publicados</div>",
                            unsafe_allow_html=True)
                pass_rows = [
                    {"Cidade": city["name"],
                     "€/pessoa/mês": city["urban_pass"]["fare_eur_month_person"],
                     "Período": city["urban_pass"]["price_period"],
                     "Operadora": city["urban_pass"]["source_url"]}
                    for city in market["cities"]
                ]
                st.dataframe(pd.DataFrame(pass_rows), hide_index=True, use_container_width=True,
                             column_config={
                                 "€/pessoa/mês": st.column_config.NumberColumn(format="€ %.2f"),
                                 "Operadora": st.column_config.LinkColumn("Fonte oficial", display_text="Consultar"),
                             })
                st.caption("Tarifas nominais de 2025–26: verificar requisitos de acesso e quantidade "
                           "de meses cobrados para dois adultos; valores não confirmados para 2027.")
                st.markdown("<div class='page-section'>Trem: duração e tarifa ilustrativa</div>",
                            unsafe_allow_html=True)
                rail_rows = []
                for city in market["cities"]:
                    for route in city["rail"]:
                        rail_rows.append({
                            "Origem": city["name"], "Destino": route["destination"],
                            "Trem (min)": route["train_minutes"],
                            "€/pessoa/trecho*": route["discounted_eur_leg_person"],
                            "Fonte": route["source_url"],
                        })
                st.dataframe(pd.DataFrame(rail_rows), hide_index=True, use_container_width=True,
                             column_config={
                                 "Trem (min)": st.column_config.NumberColumn(format="%d min"),
                                 "€/pessoa/trecho*": st.column_config.NumberColumn(format="€ %.2f"),
                                 "Fonte": st.column_config.LinkColumn("Fonte TER", display_text="Consultar"),
                             })
                st.markdown(
                    "<div class='city-fact city-fact--info'><strong>* Tarifa reduzida Carte Fluo</strong>"
                    "<p>É uma referência de preço por pessoa e por trecho, que pode exigir cartão. "
                    "Os minutos são de estação a estação, sem conexões locais. Faltam horários, "
                    "tarifas e retornos efetivos para a viagem de 2027.</p></div>",
                    unsafe_allow_html=True)
                st.markdown("<div class='page-section'>Supermercado e lazer</div>",
                            unsafe_allow_html=True)
                basket = market["common_costs"]
                st.markdown(
                    "<div class='city-fact city-fact--info'>"
                    "<strong>Hipótese compartilhada para as quatro cidades</strong>"
                    f"<div class='city-cost-highlight'>€ {basket['groceries_eur_week_couple']:.2f}"
                    "<span> / semana para duas pessoas</span></div>"
                    "<p>Cesta histórica ilustrativa do projeto, não quatro pesquisas locais. "
                    "Restaurantes, academia e lazer ainda precisam de levantamento equivalente "
                    "por bairro. Evitar somar essa referência novamente ao orçamento oficial.</p>"
                    "</div>", unsafe_allow_html=True)
                st.link_button("Consultar origem da cesta no Drive", basket["source_url"])

                st.markdown("<div class='page-section'>Novas evidências de custo de vida</div>",unsafe_allow_html=True)
                st.markdown(
                    "<div class='city-fact city-fact--info'><strong>Leitura correta dos preços</strong>"
                    "<p>Os aluguéis abaixo são estimativas de contratos residenciais comuns em €/m²/mês "
                    "(não hospedagem de temporada). O jantar para dois é um dado colaborativo do Numbeo, "
                    "não preço de reserva ou média estatisticamente comprovada.</p></div>",
                    unsafe_allow_html=True)
                economic_rows = []
                for rec in round2["cities"]:
                    economic_rows.append({
                        "Cidade":rec["name"],
                        "Aluguel residencial €/m²/mês":rec["residential_rent_eur_sqm_month"],
                        "Jantar para dois €":rec["restaurant_two_midrange_eur"],
                        "Fonte jantar":rec["restaurant_source_url"]
                    })
                st.dataframe(pd.DataFrame(economic_rows), hide_index=True, use_container_width=True,
                             column_config={
                                 "Aluguel residencial €/m²/mês":st.column_config.NumberColumn(format="€ %.2f"),
                                 "Jantar para dois €":st.column_config.NumberColumn(format="€ %.2f"),
                                 "Fonte jantar":st.column_config.LinkColumn("Numbeo", display_text="Consultar"),
                             })
                st.link_button("Metodologia e dados do aluguel residencial",
                               round2["common_sources"][0]["url"])
                st.caption("Indicador de aluguel do MeilleursAgents em 01/11/2026, apartamento residencial "
                           "comum; o jantar é um item comparável nas páginas consultadas em novembro/2026. "
                           "Metz possui lacunas de amostra em vários produtos. Não converter esses valores "
                           "em custo real da viagem.")

                st.markdown("<div class='page-section'>Plano B para o trabalho remoto</div>",unsafe_allow_html=True)
                st.markdown("<div class='page-subtitle'>Opções de coworking publicadas: preços, modalidades "
                            "e horários não equivalentes. Não garantem videoconferências até o fim "
                            "do expediente brasileiro.</div>", unsafe_allow_html=True)
                coworking_rows = []
                for rec in round2["cities"]:
                    office = rec["coworking"]
                    coworking_rows.append({
                        "Cidade":rec["name"], "Espaço":office["name"],
                        "Preço publicado €":office["price_eur"],
                        "Modalidade":office["price_basis"],
                        "Compatível até 22–23h":("Não" if office["late_work_compatible"] is False else "A confirmar"),
                        "Fonte":office["source_url"]
                    })
                st.dataframe(pd.DataFrame(coworking_rows), hide_index=True, use_container_width=True,
                             column_config={
                                 "Preço publicado €":st.column_config.NumberColumn(format="€ %.2f"),
                                 "Fonte":st.column_config.LinkColumn("Fonte", display_text="Consultar")
                             })
                with st.expander("Horários, disponibilidade e condições de cada coworking"):
                    for rec in round2["cities"]:
                        office = rec["coworking"]
                        st.markdown(f"**{escape(rec['name'])} — {escape(office['name'])}**")
                        st.caption("Horário: " + (office["schedule"] or "não verificado") +
                                   " · " + office["note"])
                st.markdown("<div class='city-fact city-fact--warn'><strong>Alojamento e contrato continuam bloqueantes</strong>"
                            "<p>O bail mobilité francês pode servir para contratos temporários, "
                            "mas depende de uma situação legal qualificadora. Não assumir que "
                            "trabalhar remotamente para uma empresa brasileira seja suficiente. "
                            "Nenhuma oferta foi confirmada para a janela de 2027.</p></div>",
                            unsafe_allow_html=True)
                st.link_button("Ver regras de contrato no Service-Public",
                               round2["common_sources"][1]["url"])


            elif active_section == "Comparar e ajustar":
                st.markdown("<div class='page-section'>Ranking de preferências históricas</div>",
                            unsafe_allow_html=True)
                st.caption("A pontuação de 0 a 5 vem de avaliações editoriais de 2026. "
                           "Não mede disponibilidade de imóveis ou custos de 2027.")
                profile = st.selectbox(
                    "Perfil de comparação", city_data["presets"],
                    format_func=lambda item: item["label"], key="city_compare_profile",
                    help="Pesos extraídos da matriz histórica do projeto.")
                initialize_weight_state(st.session_state, profile["id"],
                                        get_preset(city_data, profile["id"]))
                weights = {}
                for idx, criterion in enumerate(city_data["criteria"]):
                    # Three well-balanced columns instead of a long vertical list.
                    if idx % 3 == 0:
                        slider_cols = st.columns(3, gap="medium")
                    with slider_cols[idx % 3]:
                        weights[criterion["id"]] = st.slider(
                            criterion["label"], min_value=0, max_value=100, step=5,
                            key=f"city_weight_{criterion['id']}", help=criterion["explanation"])
                total_weights = sum(weights.values())
                if total_weights == 0:
                    st.warning("Ajuste pelo menos um critério acima de zero.")
                else:
                    actual_weights = normalized_weights(weights, criteria_ids)
                    st.caption("Pesos normalizados: " + " · ".join(
                        f"{crit['label']}: {actual_weights[crit['id']]*100:.0f}%"
                        for crit in city_data["criteria"]))
                    ranking = rank_cities(city_data["cities"], weights, criteria_ids)
                    for group_start in range(0, len(ranking), 2):
                        for col, (position, result) in zip(
                            st.columns(2, gap="medium"),
                            list(enumerate(ranking, start=1))[group_start:group_start + 2]
                        ):
                            city = result["city"]
                            pct = max(0.0, min(100.0, result["score"] * 20))
                            with col:
                                st.markdown(
                                    "<div class='city-ranking-card'>"
                                    f"<span>#{position} · Preferência simulada</span>"
                                    f"<strong>{escape(city['name'])}</strong>"
                                    f"<div class='city-ranking-number'>{result['score']:.3f}"
                                    "<small> / 5</small></div>"
                                    f"<div class='city-score__bar'><span style='width:{pct:.2f}%'></span></div>"
                                    "</div>", unsafe_allow_html=True)
                    score_rows = [
                        {"Cidade": result["city"]["name"],
                         "Score ponderado": round(result["score"], 3),
                         **{criterion["label"]: result["city"]["scores"][criterion["id"]]
                            for criterion in city_data["criteria"]}}
                        for result in ranking
                    ]
                    with st.expander("Ver notas de cada critério", expanded=False):
                        st.dataframe(pd.DataFrame(score_rows), hide_index=True,
                                     use_container_width=True,
                                     column_config={
                                         "Score ponderado": st.column_config.NumberColumn(format="%.3f")
                                     })
                    st.markdown("<div class='page-section'>Duas cidades, lado a lado</div>",
                                unsafe_allow_html=True)
                    selections = st.multiselect("Escolha até duas cidades",
                                                [c["name"] for c in city_data["cities"]],
                                                default=["Mulhouse", "Strasbourg"],
                                                max_selections=2, key="city_compare_pair")
                    results_by_name = {item["city"]["name"]: item for item in ranking}
                    if not selections:
                        st.info("Escolha uma ou duas cidades para comparar os detalhes.")
                    for col, city_name in zip(st.columns(2, gap="medium"), selections):
                        city = results_by_name[city_name]["city"]
                        market_city = market_by_name[city_name]
                        sample = observed_rent_summary(market_city)
                        with col:
                            st.markdown(
                                "<div class='city-side'>"
                                f"<div class='city-side__name'>{escape(city_name)}</div>"
                                f"<div class='city-side__score'>{results_by_name[city_name]['score']:.3f}/5"
                                " <small>nota editorial</small></div>"
                                f"<div class='city-side__sample'>€ {sample['sample_median_eur_month']:,.0f}"
                                " <small>/mês · mediana de 3 anúncios</small></div>"
                                f"<p>{escape(city['summary'])}</p>"
                                "</div>", unsafe_allow_html=True)
                            st.markdown(
                                "<div class='city-fact city-fact--good'><strong>✓ Pontos favoráveis "
                                "(avaliação histórica)</strong><ul>" +
                                "".join(f"<li>{escape(value)}</li>" for value in city["advantages"]) +
                                "</ul></div>", unsafe_allow_html=True)
                            st.markdown(
                                "<div class='city-fact city-fact--warn'><strong>! Riscos e verificações</strong>"
                                "<ul>" + "".join(f"<li>{escape(value)}</li>" for value in
                                                (city["risks"] + audit_by_name[city_name]["risks"][:1])) +
                                "</ul></div>", unsafe_allow_html=True)
                            st.button(f"Simular {city_name} no orçamento →",key=f"city_budget_{city_name}",
                                      use_container_width=True,on_click=simulate_city_in_budget,
                                      args=(city_name,))
                            with st.expander(f"Exemplos históricos em {city_name}"):
                                for ad in city["sample_ads"]:
                                    st.link_button(ad["label"], ad["url"], use_container_width=True)
                with st.expander("Metodologia, requisitos e documentos", expanded=False):
                    st.markdown("**Amostra observada ≠ preço de mercado ≠ nota editorial ≠ cotação para 2027.**")
                    st.caption("Todos os valores de mercado são registros de novembro de 2026. "
                               "Uma cidade só estará pronta quando houver imóveis elegíveis para as datas "
                               "reais, custo completo e os oito requisitos de auditoria comprovados.")
                    for gate in city_audit["standards"]:
                        st.markdown(f"**{escape(gate['label'])}**")
                        st.caption(gate["gate"])
                    st.link_button("Ver relatório e lacunas", 
                        "https://github.com/clevertondecker/europe-trip/blob/main/RELATORIO_PRIMEIRA_COMPARACAO_REAL.md")
                    st.link_button("Abrir matriz original no Drive", city_data["source"]["url"])
                    st.link_button("Decisão D-004 no Drive", data["sources"]["decisions"])

elif page == "Roteiro":
    itinerary = load_itinerary()
    # The page title follows the current task, rather than showing a giant
    # generic trip dashboard above every single tool.
    task_title={
        "Cidades-base":"Explorar cidades-base",
        "Passeios e destinos":"O que podemos conhecer?",
        "Mais pesquisas":"Detalhes das pesquisas",
        "Meu planejamento":"Meu roteiro",
        "Organizar viagem":"Organizar nossa viagem",
        "Melhorar meu roteiro":"Melhorar nosso roteiro",
    }.get(ux_section,"Meu roteiro")
    if ux_section not in ("Meu planejamento","Organizar viagem"):
        st.markdown("<div class='page-eyebrow'>NOSSA EUROPA · "+escape(ux_area.upper())+"</div>"
                "<div class='page-title'>"+escape(task_title)+"</div>"
                "<div class='page-subtitle'>"+escape(
                    UX_DESCRIPTIONS.get((ux_area,ux_section),"Planeje sua viagem."))+
                "</div>",unsafe_allow_html=True)
    if ux_section not in ("Meu planejamento","Organizar viagem"):
        render_scenario_impact(active_plan(),data,
                               sync_sources["finance"]["status"]=="live")
    # UX 4.8: only task-based navigation is user-visible. Keep legacy routing
    # adapter internally for old deep links and session-state compatibility.
    # The modern task selector resolves guide/research access without a second
    # competing nine-item navigation menu.
    itinerary_section=itinerary_target or st.session_state.get("itinerary_section","Meus passeios")
    if itinerary_section=="Guias e pesquisas":
        itinerary_section=guide_target or st.session_state.get("guide_section","Explorar atrações")
    if itinerary_section=="Calendário de pesquisa":
        itinerary_section="Calendário legado"

    def itinerary_map(phase: str, zoom: float, center: tuple[float,float], height: int=400) -> None:
        # Convert research-place roles into existing project status colors; no fake route lines.
        markers=[]
        for point in visible_map_places(itinerary,phase):
            status=("roteiro_proposto" if point["role"] in
                    ("Cidade principal","Logística","Passeio desejado") else
                    "candidata" if "Base candidata" in point["role"] else "opcional")
            markers.append({**point,"status":status})
        map_view(markers,height=height,show_labels=False,zoom=zoom,center=center)

    if itinerary_section == "Visão geral":
        if (ux_area,ux_section)==("Meu roteiro","Meu planejamento"):
            render_planning_journey(active_plan(),load_attractions(),data,
                                    sync_sources["finance"]["status"]=="live",
                                    st.session_state.get("advisor_eurfx",6.3),
                                    st.session_state.get("advisor_chffx",7.1))
        elif (ux_area,ux_section)==("Meu roteiro","Organizar viagem") and (
            st.session_state.get("ux_organize_view")=="Calendário inteligente"):
            render_smart_calendar(
                active_plan(),load_attractions(),load_base_routes(),data,sync_sources)
        elif (ux_area,ux_section)==("Meu roteiro","Organizar viagem"):
            render_planning_journey(active_plan(),load_attractions(),data,
                                    sync_sources["finance"]["status"]=="live",
                                    st.session_state.get("advisor_eurfx",6.3),
                                    st.session_state.get("advisor_chffx",7.1))
        else:
            render_itinerary_workbench(
                active_plan(),load_attractions(),data,
                sync_sources["finance"]["status"]=="live",
                st.session_state.get("advisor_eurfx",6.3),
                st.session_state.get("advisor_chffx",7.1),
                show_weekend_planner=(ux_area,ux_section)==("Meu roteiro","Organizar viagem"))

    elif itinerary_section == "Itália":
        render_italy_honeymoon()

    elif itinerary_section == "Explorar atrações":
        # UX 5.0.1: destination-first discovery, no base choice required.
        render_independent_destination_discovery()
        if st.session_state.get("ux502_view","Descobrir lugares")=="Descobrir lugares":
            render_contextual_shortcuts("discovery")
        st.divider()
        with st.popover("Pesquisar por cidade-base · opcional", use_container_width=True):
            st.caption("Ferramenta anterior preservada para investigar alternativas de cidade-base.")
            render_explorer(data,sync_sources,map_view)

    elif itinerary_section == "Explorar bases":
        if ((st.session_state.get(CONTEXT) or {}).get("kind")!="profile"
                or not render_profile_context(active_plan())):
            render_base_explorer(active_plan(),data,sync_sources["finance"]["status"]=="live",
                                 st.session_state.get("advisor_eurfx",6.3),
                                 focused=(ux_area=="Explorar" and ux_section=="Cidades-base"))

    elif itinerary_section in ("Meus passeios","Descobrir","Orçamento","Calendário","Simular roteiros"):
        if itinerary_section=="Calendário":
            from itinerary_flow_model import selected_rows,ITALY_STAGE
            italian=[
                {"Data planejada":day,"Lugar":visit["name"],
                 "Etapa":"Lua de mel na Itália"}
                for visit in selected_rows(active_plan(),load_attractions())
                if visit["stage"]==ITALY_STAGE
                for day in visit["exact_dates"]
            ]
            if italian:
                st.markdown("#### Dias definidos na Itália")
                st.dataframe(italian,hide_index=True,width="stretch")
                st.caption("Visitas italianas organizadas pelo novo roteiro, sem "
                           "reserva confirmada. Edite datas em Meu roteiro → Visão geral "
                           "→ Organizar dias.")
        render_advisor(data,sync_sources,workspace_area=itinerary_section)

    elif itinerary_section == "Itália e Costa Amalfitana":
        st.markdown("<div class='page-section'>Roma e Costa Amalfitana</div>",unsafe_allow_html=True)
        itinerary_map("italy",6.5,(40.98,13.7),390)
        st.caption("Roma 3–4 dias; costa 5–6 dias dentro da etapa de aproximadamente 10 dias. "
                   "Portos, ferry e clima exigem confirmação para setembro/2027.")
        coast_base=st.radio("Onde ficar na Costa Amalfitana?",["salerno","maiori"],
                            format_func=lambda x:"Salerno · base prática" if x=="salerno"
                            else "Maiori · base à beira-mar",horizontal=True,key="route_italy_base")
        available=select_outings(itinerary,"italy",coast_base)
        for outing in available:
            fare=(f"€ {outing['price_eur_person_leg'] * outing['legs'] * 2:.2f} / casal"
                  if outing["price_eur_person_leg"] is not None else "A cotar")
            time_info=(f"{outing['duration_minutes_one_way']} min/trecho (sem espera)"
                       if outing["duration_minutes_one_way"] is not None else "Tempo a cotar")
            st.markdown(
                "<div class='page-panel'><div class='page-panel__title'>"
                f"{escape(outing['title'])}</div><div class='page-panel__desc'>"
                f"🚢 {escape(outing['mode'])} · {escape(time_info)} · "
                f"<strong>{escape(fare)}</strong></div>"
                f"<div class='page-panel__meta'>{escape(outing['notes'])}</div></div>",
                unsafe_allow_html=True)
            st.link_button("Consultar operadora / atração",outing["source_url"])
        st.markdown("<div class='city-fact city-fact--warn'><strong>Reservas ainda necessárias</strong>"
                    "<p>Hospedagem e bilhetes para 2027, transporte Roma → costa, deslocamento ao porto, "
                    "Capri, ingressos e bagagens. A tarifa Travelmar é por pessoa em 2026; "
                    "ela não inclui transporte até o ferry nem eventuais mudanças de rota.</p></div>",
                    unsafe_allow_html=True)
        st.link_button("Horários Travelmar 2026",itinerary["sources"]["travelmar_schedule"])
        st.markdown("#### Revisão crítica e alternativas de 10 dias")
        render_italy_honeymoon()

    elif itinerary_section == "França e escapadas":
        st.markdown("<div class='page-section'>Passeios a partir da nossa futura base</div>",
                    unsafe_allow_html=True)
        itinerary_map("france",5.6,(48.05,7.1),390)
        french_base=st.selectbox("Cidade-base para explorar (não é escolha definitiva)",
                                  ["mulhouse","strasbourg","metz","nancy"],
                                  format_func=lambda x:x.capitalize(),
                                  key="route_france_base")
        options=select_outings(itinerary,"france",french_base)
        for outing in options:
            price=outing["price_eur_person_leg"]
            cost=("Sem bilhete cotado" if price is None else
                  f"{outing['currency']} {price*outing['legs']*2:.2f} / casal")
            time=(str(outing["duration_minutes_one_way"])+" min/trecho"
                  if outing["duration_minutes_one_way"] is not None else "Tempo total a verificar")
            st.markdown(
                "<div class='page-panel'><div class='page-panel__title'>"
                f"{escape(outing['title'])}</div>"
                f"<div class='page-panel__desc'>{escape(outing['mode'])} · "
                f"{escape(time)} · <strong>{escape(cost)}</strong></div>"
                f"<div class='page-panel__meta'>{escape(outing['notes'])}</div></div>",
                unsafe_allow_html=True)
            st.link_button("Ver fonte / operador",outing["source_url"])
        st.markdown("<div class='city-fact city-fact--info'><strong>Alpes suíços precisam de planejamento próprio</strong>"
                    "<p>Oeschinensee é uma viagem sazonal e pode exigir pernoite. "
                    "A tarifa do teleférico não inclui trem desde a base francesa. "
                    "Priorizar as montanhas durante as férias e confirmar o clima e a operação em 2027.</p></div>",
                    unsafe_allow_html=True)

    elif itinerary_section == "Transportes e custos":
        st.markdown("<div class='page-section'>Simulador de passeios para o casal</div>",
                    unsafe_allow_html=True)
        a,b=st.columns(2,gap="medium")
        with a:
            phase=st.radio("Etapa",["italy","france"],format_func=lambda x:"Itália" if x=="italy" else "França",
                           horizontal=True,key="route_cost_phase")
        with b:
            choices=["salerno","maiori"] if phase=="italy" else ["mulhouse","strasbourg","metz","nancy"]
            base=st.selectbox("Base de comparação",choices,format_func=lambda x:x.capitalize(),
                              key=f"route_cost_base_{phase}")
        available=select_outings(itinerary,phase,base)
        selected=st.multiselect("Escolha os passeios a incluir",
                                [x["id"] for x in available],
                                format_func=lambda x:next(o["title"] for o in available if o["id"]==x),
                                default=[],key=f"route_cost_options_{phase}_{base}")
        subtotal=basket_totals(available,selected)
        eur=subtotal["known_ticket_subtotals"]["EUR"]
        chf=subtotal["known_ticket_subtotals"]["CHF"]
        p1,p2,p3=st.columns(3,gap="medium")
        for col,(title,value,detail) in zip((p1,p2,p3),[
            ("Bilhetes EUR conhecidos",f"€ {eur:.2f}","Tarifas publicadas, condicionais"),
            ("Bilhetes CHF conhecidos",f"CHF {chf:.2f}","Não convertido em EUR"),
            ("Passeios sem preço",str(len(subtotal["unpriced"])),"Ainda precisam de cotação")
        ]):
            with col:
                st.markdown("<div class='page-stat page-stat--mint'>"
                            f"<div class='page-stat__label'>{escape(title)}</div>"
                            f"<div class='page-stat__value'>{escape(value)}</div>"
                            f"<div class='page-stat__hint'>{escape(detail)}</div></div>",
                            unsafe_allow_html=True)
        known_route_choices=[x for x in available if len(route_endpoints(itinerary,x))==2]
        if known_route_choices:
            st.markdown("<div class='page-section'>Visualizar origem e destino no mapa</div>",
                        unsafe_allow_html=True)
            selected_route=st.selectbox("Deslocamento pesquisado",
                                        known_route_choices,
                                        format_func=lambda item:item["title"],
                                        key=f"route_preview_{phase}_{base}")
            pins=route_endpoints(itinerary,selected_route)
            center=(sum(p["lat"] for p in pins)/2,sum(p["lon"] for p in pins)/2)
            map_view(pins,height=300,show_labels=True,center=center,
                     zoom=7.5 if phase=="italy" else 6.8)
            st.caption("Mapa apenas com pontos de partida e chegada, não o traçado real do "
                       "trem ou do ferry. Tempo publicado, quando existente, é entre "
                       "estações/portos e não porta a porta.")
            st.link_button("Consultar trajeto na fonte original",
                           selected_route["source_url"])
        if subtotal["discount_conditional"]:
            st.warning("Parte das tarifas de trem exige Carte Fluo (não incluída): "
                       + ", ".join(subtotal["discount_conditional"]))
        if subtotal["unpriced"]:
            st.info("Sem preço completo: "+", ".join(subtotal["unpriced"]))
        st.markdown("<div class='city-fact city-fact--warn'><strong>Este não é o orçamento total dos passeios</strong>"
                    "<p>O cálculo soma SOMENTE os bilhetes com tarifa histórica publicada "
                    "para duas pessoas e pernas informadas. Não inclui refeições, hospedagem, "
                    "transfers, ingressos não cotados, impostos ou descontos elegíveis. "
                    "EUR e CHF não são somados entre si. Não adicionar automaticamente ao orçamento "
                    "oficial: a rubrica passeios da França já tem verba prevista.</p></div>",
                    unsafe_allow_html=True)
        with st.expander("Ver tarifas e fontes de cada opção"):
            for entry in available:
                amount=("A cotar" if entry["price_eur_person_leg"] is None
                        else f"{entry['currency']} {entry['price_eur_person_leg']:.2f} / pessoa "
                        f"{'ida e volta' if entry['fare_kind']=='roundtrip_price' else '/ trecho'}")
                st.markdown(f"**{escape(entry['title'])}** · {escape(amount)}")
                st.caption(entry["season"]+" · "+entry["notes"])
                st.link_button("Abrir fonte",entry["source_url"])

    elif itinerary_section == "Calendário legado":
        from datetime import date
        import pandas as pd
        st.markdown("<div class='page-section'>Calendário ilustrativo da viagem</div>",
                    unsafe_allow_html=True)
        st.caption("As etapas são projeções, não compromissos nem bilhetes. "
                   "Altere as premissas para identificar dias disponíveis aos passeios.")
        col1,col2,col3 = st.columns(3,gap="medium")
        with col1:
            depart=st.date_input("Saída candidata",value=date.fromisoformat(data["departure_candidate"]),
                                 min_value=date(2027,9,5),key="itinerary_departure")
        with col2:
            total_days=st.slider("Duração total (dias)",65,75,70,key="itinerary_total_days")
        with col3:
            vacation_days=st.slider("Férias iniciais (dias)",20,30,25,key="itinerary_vacation_days")
        italy_days=st.slider("Etapa italiana (dias)",8,12,int(data["italy_days_approx"]),
                             key="itinerary_italy_days")
        setup_days=st.slider("Instalação na França (dias)",3,5,4,key="itinerary_setup_days")
        fields={"departure_date":depart.isoformat(),"total_days":total_days,
                "italy_days":italy_days,"vacation_days":vacation_days,
                "setup_days":setup_days}
        if any(active_plan()[k]!=v for k,v in fields.items()):
            update_fields(**fields)
        schedule=calendar_plan(depart,total_days,italy_days,vacation_days,setup_days)
        explore_calendar=active_plan()["assignments"]
        destination_names={dest["id"]:dest["name"] for dest in load_attractions()["destinations"]}
        st.dataframe(pd.DataFrame([
            {"Dia":r["day"],"Data":r["date"],"Região":r["stage"],
             "Atividade sugerida":r["activity"],
             "Passeio escolhido":destination_names.get(
                 explore_calendar.get(r["date"],""),
                 explore_calendar.get(r["date"],""))} for r in schedule]),
            hide_index=True,use_container_width=True,height=450)
        if explore_calendar:
            st.caption("Passeios escolhidos aparecem pelo nome. As datas são sugestões de planejamento, "
                       "não reservas, nem confirmação dos horários de 2027.")
        breakdown={}
        for row in schedule:
            breakdown[row["activity"]]=breakdown.get(row["activity"],0)+1
        st.markdown("<div class='page-section'>Distribuição dos dias</div>",unsafe_allow_html=True)
        st.bar_chart(pd.DataFrame([{"Atividade":k,"Dias":v} for k,v in breakdown.items()]),
                     x="Atividade",y="Dias",horizontal=True)
        st.info("Este calendário distribui etapas por regras simples. Não agenda passeios individuais, "
                "não calcula horários locais de trabalho nem confirma operações para os dias específicos.")
        st.link_button("Ver cronograma original no Drive",data["sources"]["spreadsheet"],
                       use_container_width=True)

    elif itinerary_section == "Cronograma oficial":
        finance_live=sync_sources["finance"]["status"]=="live"
        st.markdown("<div class='page-section'>Cronograma do projeto</div>",unsafe_allow_html=True)
        st.caption("Origem: aba 04 do Excel no Drive" if finance_live
                   else "Mostrando snapshot de referência: falha na sincronização do Excel")
        for idx,entry in enumerate(data["timeline"],start=1):
            st.markdown(
                f"<div class='page-timeline'><div class='page-timeline__number'>{idx:02d}</div>"
                "<div class='page-timeline__content'>"
                f"<div class='page-timeline__period'>{escape(entry['period'])} · {escape(entry['status'].upper())}</div>"
                f"<div class='page-timeline__stage'>{escape(entry['stage'])}</div>"
                f"<div class='page-timeline__desc'>{escape(entry['details'])}</div></div></div>",
                unsafe_allow_html=True)
        col1,col2=st.columns(2)
        with col1:
            st.link_button("Documento de decisões no Drive",data["sources"]["decisions"],use_container_width=True)
        with col2:
            st.link_button("Planilha do cronograma no Drive",data["sources"]["spreadsheet"],use_container_width=True)

elif page == "Orçamento":
    if ux_section=="Simulações":
        render_simulation_context(active_plan())
    live_finance=sync_sources["finance"]["status"]=="live"
    if ux_area=="Orçamento" and ux_section=="Resumo financeiro":
        render_budget_summary(data,active_plan(),live_finance)
    elif ux_area=="Orçamento" and ux_section=="Detalhamento":
        render_budget_details(data,active_plan(),live_finance)
    else:

        import pandas as pd
        st.markdown("<div class='page-eyebrow'>PLANEJAMENTO FINANCEIRO · DOIS VIAJANTES</div>"
                    "<div class='page-title'>Orçamento integrado</div>"
                    "<div class='page-subtitle'>Uma única simulação para moradia, duração, restaurantes, "
                    "transporte e passeios. Cada escolha substitui a verba prevista ou adiciona somente a diferença.</div>",
                    unsafe_allow_html=True)
        live_finance = sync_sources["finance"]["status"] == "live"
        if not live_finance:
            st.warning("Financeiro em snapshot histórico. Verifique o Drive antes de decidir uma reserva.")
        else:
            st.caption("Valores das subcategorias são recalculados a partir da planilha sincronizada.")
        if "unified_scenario" not in st.session_state:
            st.session_state["unified_scenario"]=active_plan()["budget_scenario"]
        scenario_id = st.segmented_control(
            "Cenário completo para o casal", ["60k","70k"], default="70k",
            format_func=lambda x:f"R$ {x[:-1]} mil", key="unified_scenario",selection_mode="single")
        scenario_id = scenario_id or "70k"
        if scenario_id!=active_plan()["budget_scenario"]:
            st.info("Teto selecionado apenas para esta simulação. "
                    "O teto do planejamento oficial permanece em R$ "+
                    active_plan()["budget_scenario"][:-1]+" mil.")
            if st.session_state.get("ux_mode")=="Oficial":
                if st.button("Confirmar alteração do teto oficial",key="budget_cap_confirm"):
                    update_fields(budget_scenario=scenario_id)
                    st.rerun()
        scenario = get_scenario(data,scenario_id)
        baseline = calculate_scenario(scenario)
        french = resolve_french_budget(scenario,live_finance)
        st.markdown("<div class='page-section'>Escolha o estilo de viagem</div>",unsafe_allow_html=True)
        preset = st.segmented_control("Estilo",["Econômico","Equilibrado","Mais ativo","Personalizado"],
            default="Equilibrado",key="unified_style",selection_mode="single")
        profiles={"Econômico":(1,35),"Equilibrado":(2,60),"Mais ativo":(4,75)}
        if preset in profiles and st.session_state.get("_unified_previous_style") != preset:
            st.session_state["unified_outings"] = profiles[preset][0]
            st.session_state["unified_outing_cost"] = profiles[preset][1]
        st.session_state["_unified_previous_style"] = preset
        col1,col2,col3 = st.columns(3,gap="medium")
        with col1:
            stay = st.slider("Dias na França",min_value=40,max_value=80,
                             value=french["french_days"],step=1,key="unified_stay",
                             on_change=_ux_budget_days_changed)
        with col2:
            outings = st.slider("Saídas por semana",0,7,value=2,key="unified_outings")
        with col3:
            spend = st.slider("Gasto por saída (€ para o casal)",15,150,value=60,step=5,
                              key="unified_outing_cost")
        col4,col5 = st.columns(2,gap="medium")
        with col4:
            fx = st.number_input("Câmbio simulado (R$/€)",4.0,10.0,6.3,0.05,key="unified_fx")
        with col5:
            exploratory_options=base_options(include_candidates=True)
            city_ids=[item["id"] for item in exploratory_options]
            candidate=st.session_state.get("scenario_base_selected",active_plan()["base_city"])
            if candidate not in city_ids:
                candidate=active_plan()["base_city"]
            selected_base_id=candidate
            selected_city=hypothetical_city_name(selected_base_id,exploratory_options)
            st.markdown("**Cidade-base nesta análise:** "+selected_city)
            st.caption("Use o seletor de cidade no cabeçalho para comparar outra base.")
        st.caption("Esta cidade é uma simulação independente. "
                   "O roteiro oficial permanece em "+active_plan()["base_city"].capitalize()+
                   ". A ausência de aluguel pesquisado não significa custo zero.")
        st.markdown("<div class='page-section'>Moradia e custos adicionais</div>",unsafe_allow_html=True)
        st.caption("O aluguel da cidade é um valor de referência editorial de 2026, NÃO uma oferta para 2027. "
                   "Ao preenchê-lo, ele **substitui** a verba de moradia — não é somado novamente.")
        city_data_budget = load_cities()
        selected_rent = next((float(c["reference_rent_eur"]) for c in
                              city_data_budget["cities"] if c["name"] == selected_city
                              and c.get("reference_rent_eur") is not None),None)
        if selected_rent is None:
            st.info("Aluguel mobiliado desta cidade: não cotado. "
                    "O orçamento abaixo mantém a provisão oficial de hospedagem "
                    "e não a apresenta como preço desta cidade.")
        use_city_rent = st.checkbox("Informar aluguel mensal hipotético para esta cidade",
                                    value=False,key="unified_override_rent")
        quoted_rent = None
        if use_city_rent:
            input_rent=st.number_input(
                "Aluguel hipotético (€ por mês, sem taxas)",
                min_value=0.,max_value=6000.,
                value=selected_rent if selected_rent is not None else 0.,
                step=50.,key="unified_rent_month_"+selected_base_id)
            if input_rent>0:
                quoted_rent=float(input_rent)
                st.caption("Provisão inserida manualmente. Não é uma cotação "
                           "confirmada para setembro–novembro de 2027.")
            else:
                st.warning("Informe um aluguel maior que €0 para substituição. "
                           "Até lá, a verba geral do orçamento permanece como provisão.")
        with st.expander("Alterações adicionais às outras verbas"):
            st.caption("Ajustes negativos representam economia. Nenhuma despesa final "
                       "pode ficar abaixo de zero; os valores continuam hipóteses.")
            flight_budget=next((row["amount"] for row in scenario["components"]
                                if row["name"].startswith("Passagens e deslocamentos aéreos")),0)
            ratio=stay/french["french_days"]
            minimum_rent=(quoted_rent*(stay/30)*fx if quoted_rent is not None
                          else french["amounts"]["rent"]*ratio)
            extra1,extra2,extra3,extra4=st.columns(4,gap="small")
            with extra1:
                flight_delta=st.number_input("Variação em voos (R$)",min_value=-int(flight_budget),
                                             max_value=25000,value=0,step=250,key="unified_flight_extra")
            with extra2:
                excursions_delta=st.number_input("Variação em passeios (R$)",
                                                 min_value=-int(french["amounts"]["excursions"]*ratio),
                                                 max_value=20000,value=0,step=250,key="unified_tour_extra")
            with extra3:
                transit_delta=st.number_input("Variação em transporte (R$)",
                                              min_value=-int(french["amounts"]["transport"]*ratio),
                                              max_value=10000,value=0,step=250,key="unified_transit_extra")
            with extra4:
                rent_delta=st.number_input("Variação em taxas/moradia (R$)",
                                           min_value=-int(minimum_rent),max_value=10000,
                                           value=0,step=250,key="unified_rent_extra")
        housing_terms=render_optional_housing_commitments(fx,selected_base_id)
        # Reference is intentionally only a known ticket subtotal. It must never
        # replace the entire tour allowance nor create a discount for missing quotes.
        catalog_extra=0.0
        attraction_ref=None
        current_plan=active_plan()
        from itinerary_flow_model import selected_rows, FRANCE_STAGE
        official_cities=[row["id"] for row in selected_rows(current_plan,load_attractions())
                         if row["stage"]==FRANCE_STAGE]
        if official_cities:
            known_cost=package_cost(
                load_attractions(),load_base_routes(),current_plan["base_city"],
                [id for items in current_plan["packages"].values() for id in items],
                planned_destination_ids=official_cities)
            attraction_ref={
                "eur":known_cost["known_by_currency"]["EUR"],
                "chf":known_cost["known_by_currency"]["CHF"],
                "fx_eur":fx,
                "fx_chf":st.session_state.get("explore_chf_fx",7.1),
                "base":current_plan["base_city"],
                "incomplete":not known_cost["complete"],
                "destinations":official_cities}
            st.caption("Passeios importados do roteiro oficial. Os custos destas "
                       "atrações ainda não foram recalculados para a base hipotética "
                       "selecionada; compare as rotas em Roteiro → Explorar bases.")

        if attraction_ref:
            st.markdown("<div class='page-section'>Passeios escolhidos no roteiro</div>",
                        unsafe_allow_html=True)
            st.info(
                f"Da base {escape(attraction_ref['base'].capitalize())}: bilhetes conhecidos "
                f"€{attraction_ref['eur']:.2f} + CHF{attraction_ref['chf']:.2f} para dois. "
                "A verba de passeios já está incluída no orçamento base; tarifas "
                "reduzidas e ingressos desconhecidos não estão garantidos para 2027.")
            use_catalog=st.checkbox(
                "Considerar apenas eventual excedente dos bilhetes conhecidos sobre a verba de passeios",
                value=True,key="budget_use_attraction_cost")
            if use_catalog:
                allocated_tours=french["amounts"]["excursions"]*stay/french["french_days"]
                catalog_extra=excursions_overage_brl(
                    attraction_ref["eur"],attraction_ref["chf"],
                    attraction_ref["fx_eur"],attraction_ref["fx_chf"],allocated_tours)
                if attraction_ref["incomplete"]:
                    st.warning("A cesta de passeios tem preços faltantes. A ausência de excedente NÃO "
                               "significa que todos os passeios caibam na verba disponível.")
                st.caption(f"Verba original proporcional de passeios: "
                           f"{money_brl(allocated_tours)}. "
                           f"Excedente conhecido somado uma vez: {money_brl(catalog_extra)}.")
        result=scenario_total(
            scenario,french,french_days=stay,outings_weekly=outings,
            outing_couple_eur=spend,fx_brl_per_eur=fx,
            rent_override_eur_month=quoted_rent,flight_delta_brl=flight_delta,
            excursions_delta_brl=excursions_delta+catalog_extra,local_transport_delta_brl=transit_delta,
            rent_delta_brl=rent_delta+(housing_terms["one_time_fee_expense_brl"] or 0.))
        render_housing_cashflow_note(result,housing_terms)
        stats=[
            ("Total projetado",money_brl(result["total"]),"Viagem completa · estimativa"),
            ("Margem até o teto",money_brl(result["margin"]),"Reserva de emergência já incluída"),
            ("Reserva protegida",money_brl(result["reserve_already_in_total"]),
             "Não utilizar para lazer"),
            ("Uso do teto",f"{result['budget_fraction']*100:.1f}%","Sem preços contratados")
        ]
        for col,(label,value,hint) in zip(st.columns(4,gap="small"),stats):
            with col:
                st.markdown(f"<div class='page-stat page-stat--blue'>"
                            f"<div class='page-stat__label'>{escape(label)}</div>"
                            f"<div class='page-stat__value'>{escape(value)}</div>"
                            f"<div class='page-stat__hint'>{escape(hint)}</div></div>",
                            unsafe_allow_html=True)
        if result["status"]=="acima_do_teto":
            st.error("O cenário ultrapassa o teto. Reduza gastos ou reveja a meta.")
        elif result["status"]=="apertado":
            st.warning("Orçamento apertado: menos de 5% de margem adicional ao valor já reservado "
                       "para emergências. Os preços de 2027 ainda são incertos.")
        else:
            st.success("Há pelo menos 5% de margem adicional à reserva contabilizada, "
                       "mas isso ainda depende de cotações reais.")
        st.markdown("<div class='page-section'>Como as escolhas alteram o orçamento</div>",unsafe_allow_html=True)
        translate={"rent":"Aluguel","groceries":"Supermercado","dining":"Restaurantes e bares",
                   "transport":"Transporte local","excursions":"Passeios"}
        rows=[{"Categoria":translate[k],"Verba original (R$)":round(french["amounts"][k],2),
               "Simulado (R$)":result["new_components"][k],
               "Variação (R$)":result["deltas"][k]} for k in
              ("rent","groceries","dining","transport","excursions")]
        st.dataframe(pd.DataFrame(rows),use_container_width=True,hide_index=True,
                     column_config={k:st.column_config.NumberColumn(format="R$ %.2f")
                        for k in ("Verba original (R$)","Simulado (R$)","Variação (R$)")})
        st.caption("Moradia, compras e transporte ajustados proporcionalmente aos dias; "
                   "passeios ajustados proporcionalmente apenas como hipótese; "
                   "bares/restaurantes substituídos pelo seu padrão de saídas. "
                   "Despesas não incluídas ou de preço desconhecido continuam fora da simulação. "
                   "O câmbio aqui só converte valores inseridos em euros — "
                   "não reprecifica os valores da planilha em reais.")
        st.markdown("<div class='page-section'>Orçamento total de referência</div>",unsafe_allow_html=True)
        st.bar_chart([{"Categoria":part["name"],"Valor (R$)":part["amount"]}
                      for part in scenario["components"]],x="Categoria",y="Valor (R$)",
                     horizontal=True,height=385)
        with st.expander("Conciliação, origem e limitações"):
            st.caption(f"Origem das subcategorias: {'Drive sincronizado' if live_finance else 'snapshot histórico do GitHub'}. "
                       "A reserva emergencial já está dentro do total da planilha. "
                       "Nenhum valor exibido é uma cotação fechada para setembro–novembro/2027.")
            st.write(f"Total de referência: {money_brl(baseline['total'])} · "
                     f"teto: {money_brl(scenario['cap_brl'])} · "
                     f"saldo de referência: {money_brl(baseline['balance'])}")
            if abs(baseline["rounding_difference"]) > .1:
                st.warning("Há divergência entre o subtotal de componentes e o total do modelo. "
                           "Validar a planilha antes de compras.")
            st.link_button("Planilha financeira oficial",data["sources"]["spreadsheet"],
                           use_container_width=True)

elif page == "Pesquisas & decisões":
    st.markdown("<div class='page-eyebrow'>CENTRAL DE PLANEJAMENTO · FONTES DO DRIVE</div>"
                "<div class='page-title'>Pesquisas, decisões & próximos passos</div>"
                "<div class='page-subtitle'>O que falta resolver, por prioridade, e onde estão os "
                "registros oficiais. O painel é somente leitura.</div>",unsafe_allow_html=True)
    tasks=data["tasks"]
    completed=sum(task.get("status")=="concluído" for task in tasks)
    decision_pending=sum(d["status"].casefold() in {"aberta","não decidida","nao decidida"}
                         for d in data["decisions"])
    summaries=[
        ("Pesquisas registradas",str(len(tasks)),"Documento de pendências"),
        ("Por concluir",str(len(tasks)-completed),"Prioridades P0–P3"),
        ("Concluídas",str(completed),"Registradas no Drive"),
        ("Decisões abertas",str(decision_pending),"Sem aprovação automática")
    ]
    for col,(label,value,hint) in zip(st.columns(4,gap="small"),summaries):
        with col:
            st.markdown(f"<div class='page-stat page-stat--blue'>"
                        f"<div class='page-stat__label'>{escape(label)}</div>"
                        f"<div class='page-stat__value'>{escape(value)}</div>"
                        f"<div class='page-stat__hint'>{escape(hint)}</div></div>",
                        unsafe_allow_html=True)
    st.info("As pendências oficiais têm apenas status **pendente** ou **concluído**. "
            "Não inventei uma coluna 'Em andamento': será possível acrescentá-la "
            "quando a fonte registrar esse status.")
    if ux_area=="Minha viagem" and ux_section in ("Pendências","Decisões"):
        view="Fila por prioridade" if ux_section=="Pendências" else "Decisões oficiais"
    else:
        view=st.segmented_control("Navegar por",
            ["Fila por prioridade","Decisões oficiais","Fontes & atualização"],
            default="Fila por prioridade",key="tasks_view",
            selection_mode="single",label_visibility="collapsed")
        if view is None: view="Fila por prioridade"
    if view=="Fila por prioridade":
        filters=st.columns([1,1],gap="medium")
        with filters[0]:
            priority=st.selectbox("Prioridade",["Todas","P0","P1","P2","P3"],
                                  key="tasks_priority_new")
        with filters[1]:
            situation=st.selectbox("Situação",["Pendentes","Todas","Concluídas"],
                                   key="tasks_status_new")
        labels={"P0":"Crítica · documentos e autorização",
                "P1":"Alta · gastos e reservas",
                "P2":"Média · passeios e refinamento",
                "P3":"Organização e evidências"}
        visible=[t for t in tasks
                if (priority=="Todas" or t["priority"]==priority)
                and (situation=="Todas" or
                     (situation=="Pendentes" and t.get("status")!="concluído") or
                     (situation=="Concluídas" and t.get("status")=="concluído"))]
        if not visible:
            st.info("Nenhuma pesquisa corresponde aos filtros escolhidos.")
        for cat in ("P0","P1","P2","P3"):
            grouped=[t for t in visible if t["priority"]==cat]
            if grouped:
                st.markdown(f"<div class='page-section'>{cat} · {escape(labels[cat])}"
                            f" <small style='color:#718796'>({len(grouped)})</small></div>",
                            unsafe_allow_html=True)
                for task in grouped:
                    done=task.get("status")=="concluído"
                    st.markdown(f"<div class='page-task page-task--{cat.lower()} "
                                f"{'page-task--done' if done else ''}'>"
                                f"<div class='page-task__tag'>{cat}</div>"
                                f"<div class='page-task__body'>{escape(task['title'])}</div>"
                                f"<div class='page-task__status'>{'✓ Concluída' if done else '○ Pendente'}"
                                "</div></div>",unsafe_allow_html=True)
        st.link_button("Atualizar pendências no Drive",data["sources"]["tasks"],
                       use_container_width=True)
    elif view=="Decisões oficiais":
        st.markdown("<div class='page-section'>Registro de decisões</div>",unsafe_allow_html=True)
        for decision in data["decisions"]:
            tone=("proposed" if decision["status"].casefold().startswith(("vigente","aprovada"))
                  else "candidate")
            st.markdown(f"<div class='page-panel'>"
                        f"<span class='page-chip page-chip--{tone}'>{escape(decision['status'])}</span>"
                        f"<div class='page-panel__title' style='margin-top:9px'>"
                        f"{escape(decision['id'])} · {escape(decision['title'])}</div>"
                        f"<div class='page-panel__desc'>{escape(decision.get('note',''))}</div>"
                        "</div>",unsafe_allow_html=True)
        st.link_button("Consultar documento de decisões",data["sources"]["decisions"],
                       use_container_width=True)
    else:
        st.markdown("<div class='page-section'>Integridade e origem</div>",unsafe_allow_html=True)
        for key,title in [("decisions","Decisões"),("tasks","Pendências"),("finance","Finanças e cronograma")]:
            src=sync_sources[key]
            st.markdown(f"**{escape(title)}:** {escape(src['status'])}" +
                        (f" · modificado {escape(src['modified_at'][:10])}" if src.get("modified_at") else
                         " · usando snapshot ou sem data verificada"))
        st.warning("Ranking e auditorias de cidades, anúncios, tarifas e roteiros detalhados "
                   "são pesquisas históricas versionadas no GitHub. "
                   "A sincronização do Drive não atualiza essas fontes automaticamente.")
        docs=[
            ("Guia do projeto","guide"),("Decisões e premissas","decisions"),
            ("Proveniência de pesquisas","evidence"),("Pendências","tasks"),
            ("Base de conhecimento","knowledge"),("Modelo financeiro","spreadsheet")]
        for col,(label,key) in zip(st.columns(2,gap="medium"),docs[:2]):
            with col: st.link_button(label,data["sources"][key],use_container_width=True)
        for col,(label,key) in zip(st.columns(2,gap="medium"),docs[2:4]):
            with col: st.link_button(label,data["sources"][key],use_container_width=True)
        for col,(label,key) in zip(st.columns(2,gap="medium"),docs[4:]):
            with col: st.link_button(label,data["sources"][key],use_container_width=True)

bottom_source()