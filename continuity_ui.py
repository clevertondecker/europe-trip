"""UX 3.6 foundation: private manual continuity, honest persistence status.

No cloud synchronization is implied.  An uploaded archive is parsed and
previewed, then passed to app startup for pre-widget confirmed restoration.
"""
from __future__ import annotations

from copy import deepcopy
import streamlit as st

from continuity_archive_model import (
    make_archive,export_archive,import_archive,preview_restore,confirm_restore,
)
from planning_status import save_label
from itinerary_flow_model import selected_rows
from planning_store import sync_legacy_view
from planning_session import bootstrap
from ux_navigation import AREAS,SECTIONS


def _safe_context(plan,catalog)->dict:
    state=st.session_state
    area=state.get("ux_area","Meu roteiro")
    if area not in AREAS:area="Meu roteiro"
    section=state.get("ux_section")
    if section not in SECTIONS[area]:section=SECTIONS[area][0]
    selection={r["id"] for r in selected_rows(plan,catalog)}
    destination=state.get("flow_active_destination")
    context={
        "area":area,"section":section,
        "stage":state.get("flow_active_stage","Itália"),
        "destination_id":destination if destination in selection else None,
        "search":state.get("flow_search_saved",""),
        "organize_view":state.get("ux_organize_view","Por período ou data"),
        "calendar_week":state.get("ux35_week"),
        "calendar_stage":state.get("ux35_stage","Itália"),
    }
    return context


def apply_pending_restore(catalog:dict)->None:
    """Invoke immediately after bootstrap(), BEFORE Streamlit widgets render."""
    state=st.session_state
    pending=state.pop("ux36_pending_restore",None)
    if pending is None:return
    try:
        plan=confirm_restore(bootstrap(),pending["archive"],pending["preview"],
                             catalog,confirmed=True)
        context=pending["archive"]["continuation"]
        state["advisor_plan"]=plan
        state["advisor_saved_snapshot"]=None
        state["advisor_github_sha"]=None
        state["advisor_autosave_pending"]=False
        state["advisor_autosave_optin"]=False
        state["advisor_public_repo_ack"]=False
        state["advisor_local_changed"]=True
        state["ux_area"]=context["area"]
        state["ux_section"]=context["section"]
        state["ux_organize_view"]=context["organize_view"]
        state["flow_stage"]=context["stage"]
        state["flow_active_stage"]=context["stage"]
        state["flow_active_destination"]=context["destination_id"]
        state["flow_search_saved"]=context["search"]
        state["ux35_stage"]=context["calendar_stage"]
        if context["calendar_week"] is not None:
            state["ux35_week"]=context["calendar_week"]
        else:
            state.pop("ux35_week",None)
        # Data from the archive belongs to this locally restored plan.
        # JSON workspaces are still drafts, never changes to the TripPlan.
        state["ux34_drafts"]={d["name"]:deepcopy(d) for d
                             in pending["archive"]["city_studies"]}
        state["ux35_proposals"]=deepcopy(pending["archive"]["calendar_drafts"])
        state.pop("ux35_review_proposal",None)
        state.pop("ux36_review",None)
        sync_legacy_view(plan,state,include_controls=True)
        state["ux36_message"]=(
            "Cópia recuperada nesta sessão. Ainda não está salva online. "
            "Guarde um novo backup local antes de fechar o navegador.")
    except (ValueError,KeyError,TypeError) as exc:
        state["ux36_error"]="A recuperação foi interrompida: "+str(exc)


def render_continuity_panel(plan:dict,catalog:dict)->None:
    with st.expander("Recuperar ou guardar uma cópia privada",expanded=False):
        st.caption("Seus estudos e mudanças ficam nesta sessão até um salvamento "
                   "ou download. Este arquivo é um JSON local **sem criptografia**: "
                   "guarde-o em local privado. Nada é enviado automaticamente "
                   "para o GitHub público.")
        if st.session_state.pop("ux36_message",None):
            st.success("Recuperação local aplicada. Seus dados ainda precisam ser salvos.")
        if st.session_state.pop("ux36_error",None):
            st.error("Recuperação não aplicada. Seu planejamento atual foi preservado.")
        include=st.checkbox("Incluir estudos e propostas desta sessão (quando compatíveis)",
                            key="ux36_include_drafts",value=False)
        city=[];calendars=[]
        if include:
            city=list(st.session_state.get("ux34_drafts",{}).values())
            calendars=list(st.session_state.get("ux35_proposals",[]))
        try:
            archive=make_archive(plan,catalog,_safe_context(plan,catalog),city,calendars)
            raw=export_archive(archive,catalog)
        except (ValueError,TypeError,KeyError) as exc:
            st.warning("Não foi possível incluir esse contexto. "
                       "Desmarque os estudos ou revise o motivo: "+str(exc))
        else:
            st.download_button("Baixar cópia de segurança",
                               data=raw,file_name="nossa-europa-copia-privada.json",
                               mime="application/json",key="ux36_download")
            st.caption("O download não é uma confirmação de sincronização online; "
                       "para recuperar em outro dispositivo, abra este mesmo arquivo lá.")
        uploaded=st.file_uploader("Abrir cópia de segurança (JSON)",
                                  type=["json"],key="ux36_upload")
        if uploaded is not None:
            if st.button("Pré-visualizar recuperação",key="ux36_preview_button"):
                try:
                    imported=import_archive(uploaded.getvalue(),catalog)
                    review=preview_restore(plan,imported,catalog)
                    st.session_state["ux36_review"]={
                        "archive":imported,"preview":review}
                    st.rerun()
                except (ValueError,TypeError,KeyError) as exc:
                    st.error("Arquivo não aceito: "+str(exc))
        pending=st.session_state.get("ux36_review")
        if pending:
            import_archive_document=pending["archive"]
            try:
                current_review=preview_restore(plan,import_archive_document,catalog)
                if (current_review["expected_current_fingerprint"]!=
                    pending["preview"]["expected_current_fingerprint"] or
                    current_review["expected_archive_fingerprint"]!=
                    pending["preview"]["expected_archive_fingerprint"]):
                    raise ValueError("O roteiro foi alterado. Revise o backup novamente")
            except (ValueError,KeyError,TypeError) as exc:
                st.warning(str(exc))
                st.session_state.pop("ux36_review",None)
                return
            summary=pending["preview"]
            st.markdown("#### Antes de recuperar")
            st.caption("Revisão local atual: "+str(summary["current_revision"])+
                       " · Revisão da cópia: "+str(summary["incoming_revision"]))
            st.caption("Lugares selecionados: "+str(summary["places_before"])+
                       " → "+str(summary["places_after"]))
            if summary["changed_fields"]:
                st.caption("Campos que mudam: "+", ".join(summary["changed_fields"]))
            else:
                st.info("Nenhuma diferença nos campos principais.")
            if summary["relation"]=="different_plan":
                st.warning("**Esta cópia pertence a outro planejamento**. "
                           "Confirmar substituirá o plano desta sessão. "
                           "O conteúdo anterior não será excluído do GitHub.")
            elif summary["relation"] in (
                 "same_plan_older","same_plan_same_revision_conflict"):
                st.warning("**Há um conflito ou versão anterior.** "
                           "Comparar e restaurar só depois de baixar uma cópia "
                           "do trabalho atual. Nada será sobrescrito online.")
            st.caption(summary["notice"])
            allow=st.checkbox(
                "Conferi as diferenças e autorizo substituir meu plano nesta sessão",
                key="ux36_restore_ack",value=False)
            a,b=st.columns(2)
            if a.button("Confirmar recuperação local",key="ux36_restore_confirm",
                        type="primary",disabled=not allow):
                st.session_state["ux36_pending_restore"]=pending
                st.rerun()
            if b.button("Cancelar recuperação",key="ux36_restore_cancel"):
                st.session_state.pop("ux36_review",None)
                st.rerun()
        st.caption("**Status:** apenas nesta sessão ou em backup local. "
                   "Sincronização privada automática entre dispositivos "
                   "ainda não está disponível.")
