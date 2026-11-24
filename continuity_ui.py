"""UX 3.6 foundation: private manual continuity, honest persistence status.

No cloud synchronization is implied.  An uploaded archive is parsed and
previewed, then passed to app startup for pre-widget confirmed restoration.
"""
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
from private_continuity_store import PrivateArchiveStore, StorageConflict, StorageUnavailable
import streamlit as st

from continuity_archive_model import (
    make_archive,export_archive,import_archive,preview_restore,confirm_restore,plan_fingerprint,
    persisted_data_fingerprint,
)
from planning_status import save_label
from itinerary_flow_model import selected_rows
from planning_store import sync_legacy_view
from planning_session import bootstrap
from ux502_destination_interests_model import empty_interests
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
                             catalog,confirmed=True,
                             current_archive=_private_archive(bootstrap(),catalog))
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
        state["ux41_favorites"]=list(pending["archive"].get("city_favorites",[]))
        state["ux502_interests"]=deepcopy(pending["archive"].get("destination_interests",empty_interests()))
        from rec03a_session import clear_recommendation_context
        clear_recommendation_context(state)
        from ux_planning_journey_model import clear_planning_context
        clear_planning_context(state)
        state["ux502_private_saved_revision"]=None
        state["ux48_weekend_groups"]=deepcopy(pending["archive"]["weekend_groups"])
        state.pop("ux35_review_proposal",None)
        state.pop("ux36_review",None)
        sync_legacy_view(plan,state,include_controls=True)
        state["ux36_local_restored"]=True
        state["ux36_cloud_status"]="Backup local recuperado; não salvo na nuvem"
        state["ux36_message"]=(
            "Cópia recuperada nesta sessão. Ainda não está salva online. "
            "Guarde um novo backup local antes de fechar o navegador.")
    except (ValueError,KeyError,TypeError) as exc:
        state["ux36_error"]="A recuperação foi interrompida: "+str(exc)



def _private_store():
    from travel_advisor_ui import _owner_config, _owner_signed_in
    if not _owner_signed_in():
        return None
    try:
        bucket = st.secrets.get("ux36_private_storage", {}).get("bucket")
        if not bucket:
            return None
        return PrivateArchiveStore(bucket, dict(st.secrets["gcp_service_account"]),
                                   _owner_config()["owner_email"])
    except (KeyError, ValueError, TypeError, AttributeError, StorageUnavailable):
        return None


def _archive_fingerprint(archive:dict)->str:
    """Compare content, ignoring the generated export timestamp."""
    value={key:val for key,val in archive.items() if key!="exported_at"}
    raw=json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode("utf-8")
    return sha256(raw).hexdigest()


def _decisions_fingerprint(archive: dict) -> str:
    """The same canonical fingerprint used by archive previews."""
    return persisted_data_fingerprint(archive)


def _current_decisions_fingerprint(plan, catalog) -> str:
    return _decisions_fingerprint(_private_archive(plan, catalog))


def _private_archive(plan, catalog):
    state = st.session_state
    # A fingerprint/archive read must never repair or replace the session sidecar.
    # Canonical plan mutations reconcile before publishing; invalid archives fail.
    weekends=state.get("ux48_weekend_groups")
    return make_archive(plan, catalog, _safe_context(plan, catalog),
                        list(state.get("ux34_drafts", {}).values()),
                        list(state.get("ux35_proposals", [])),
                        city_favorites=list(state.get("ux41_favorites",[])),
                        weekend_groups=weekends,
                        destination_interests=state.get("ux502_interests",empty_interests()))


def restore_private_on_start(catalog):
    """Restore before any widgets, on a fresh owner session only."""
    state = st.session_state
    if state.get("ux36_bootstrapped"):
        return
    if state.get("ux36_local_restored") or state.get("advisor_local_changed"):
        state["ux36_bootstrapped"] = True
        return
    store = _private_store()
    if store is None:
        return
    state["ux36_bootstrapped"] = True
    try:
        loaded = store.load()
        if loaded is None:
            return
        raw, generation = loaded
        archive = import_archive(raw, catalog)
        plan, context = archive["plan"], archive["continuation"]
        state["advisor_plan"] = deepcopy(plan)
        state["advisor_saved_snapshot"] = None  # private != public GitHub
        state["advisor_github_sha"] = None
        state["advisor_autosave_pending"] = False
        state["advisor_autosave_optin"] = False
        state["advisor_public_repo_ack"] = False
        state["advisor_local_changed"] = False
        state["ux36_cloud_generation"] = generation
        state["ux36_cloud_status"] = "Salvo em espaço privado"
        state["ux36_saved_plan_fingerprint"] = plan_fingerprint(plan)
        state["ux36_saved_archive_fingerprint"] = _archive_fingerprint(archive)
        state["ux36_saved_decisions_fingerprint"] = _decisions_fingerprint(archive)
        state["ux36_cloud_dirty"] = False
        for target, source in (
            ("ux_area", "area"), ("ux_section", "section"),
            ("ux_organize_view", "organize_view"),
            ("flow_stage", "stage"), ("flow_active_stage", "stage"),
            ("flow_active_destination", "destination_id"),
            ("flow_search_saved", "search"), ("ux35_stage", "calendar_stage")
        ):
            state[target] = context[source]
        if context["calendar_week"] is not None:
            state["ux35_week"] = context["calendar_week"]
        state["ux34_drafts"] = {d["name"]: deepcopy(d) for d in archive["city_studies"]}
        state["ux35_proposals"] = deepcopy(archive["calendar_drafts"])
        state["ux41_favorites"] = list(archive.get("city_favorites",[]))
        state["ux502_interests"] = deepcopy(archive.get("destination_interests",empty_interests()))
        from rec03a_session import clear_recommendation_context
        clear_recommendation_context(state)
        from ux_planning_journey_model import clear_planning_context
        clear_planning_context(state)
        state["ux502_private_saved_revision"] = state["ux502_interests"]["revision"]
        state["ux48_weekend_groups"] = deepcopy(archive["weekend_groups"])
        sync_legacy_view(plan, state, include_controls=True)
    except (ValueError, KeyError, TypeError, StorageConflict, StorageUnavailable):
        state["ux36_cloud_status"] = "Erro ao recuperar; use um backup local"


def save_private_now(plan, catalog):
    store = _private_store()
    if store is None:
        raise StorageUnavailable("Login ou bucket privado não configurado")
    raw = export_archive(_private_archive(plan, catalog), catalog)
    state = st.session_state
    generation = store.save(raw, state.get("ux36_cloud_generation"))
    state["ux36_cloud_generation"] = generation
    state["ux36_cloud_status"] = "Salvo em espaço privado"
    state["ux36_saved_plan_fingerprint"] = plan_fingerprint(plan)
    confirmed_archive = import_archive(raw, catalog)
    state["ux36_saved_archive_fingerprint"] = _archive_fingerprint(confirmed_archive)
    state["ux36_saved_decisions_fingerprint"] = _decisions_fingerprint(confirmed_archive)
    state["ux36_cloud_dirty"] = False
    state["ux502_private_saved_revision"] = state.get("ux502_interests",empty_interests())["revision"]
    state.pop("ux36_autosave_failed_fingerprint", None)


def autosave_private_if_requested(catalog):
    """Keep pending edits until the remote generation is acknowledged.

    Failed snapshots are not retried on every Streamlit rerun. A changed
    snapshot (or explicit manual retry) is allowed to try again.
    """
    state = st.session_state
    if not state.get("ux36_private_autosave"):
        return
    try:
        pending = _current_decisions_fingerprint(state["advisor_plan"], catalog)
        if pending == state.get("ux36_saved_decisions_fingerprint"):
            return
    except (ValueError, TypeError, KeyError):
        state["ux36_cloud_status"] = "Erro ao preparar; alterações apenas nesta sessão"
        state["ux36_cloud_dirty"] = True
        return
    if state.get("ux36_autosave_failed_fingerprint") == pending:
        return
    try:
        save_private_now(state["advisor_plan"], catalog)
    except StorageConflict:
        state["ux36_cloud_dirty"] = True
        state["ux36_autosave_failed_fingerprint"] = pending
        state["ux36_cloud_status"] = "Conflito de versão; alterações apenas nesta sessão"
    except (ValueError, TypeError, KeyError, StorageUnavailable):
        state["ux36_cloud_dirty"] = True
        state["ux36_autosave_failed_fingerprint"] = pending
        state["ux36_cloud_status"] = "Erro ao salvar; alterações apenas nesta sessão"
    else:
        state.pop("ux36_autosave_failed_fingerprint", None)


def render_private_controls(plan, catalog):
    store = _private_store()
    if store is None:
        st.caption("Nuvem privada indisponível: requer login do proprietário e bucket GCS configurado. Use o backup local.")
        return
    state = st.session_state
    status = state.get("ux36_cloud_status", "Apenas nesta sessão")
    try:
        current = _private_archive(plan, catalog)
        if (state.get("ux36_saved_decisions_fingerprint") != _decisions_fingerprint(current)
                and status == "Salvo em espaço privado"):
            status = "Alterações não salvas"
    except (ValueError, TypeError, KeyError):
        status = "Dados locais precisam de revisão antes de salvar"
    st.caption("**Status privado:** " + status)
    if state.get("ux36_autosave_failed_fingerprint"):
        st.info("O salvamento automático não foi confirmado. Seus dados continuam nesta sessão. "
                "Use Salvar cópia privada agora para tentar novamente, sem substituir conflitos.")
    st.checkbox("Salvar automaticamente minhas alterações do roteiro", key="ux36_private_autosave")
    if st.button("Salvar cópia privada agora", key="ux36_cloud_save"):
        state.pop("ux36_autosave_failed_fingerprint", None)
        try:
            save_private_now(plan, catalog)
            st.success("Cópia privada confirmada. Ela estará disponível na próxima sessão.")
        except StorageConflict:
            state["ux36_cloud_dirty"] = True
            state["ux36_cloud_status"] = "Conflito de versão; alterações apenas nesta sessão"
            st.error("Outra sessão alterou o planejamento. Baixe o backup local, reabra e compare antes de substituir.")
        except (StorageUnavailable, ValueError, KeyError, TypeError):
            state["ux36_cloud_dirty"] = True
            state["ux36_cloud_status"] = "Erro ao salvar; alterações apenas nesta sessão"
            st.error("Falha no armazenamento privado. Baixe uma cópia local.")


def _ux75_private_autosave_changed():
    """Explicit opt-in; never enable background public GitHub writes."""
    st.session_state["ux36_private_autosave"] = bool(
        st.session_state.get("ux75_private_autosave_toggle", False))


def render_primary_private_save(plan, catalog) -> bool:
    """Cloud-first save control; false means private storage is unavailable.

    The GCS archive contains all persisted trip decisions, not only TripPlan.
    This UI never writes to the public GitHub repository.
    """
    store = _private_store()
    if store is None:
        st.warning("Nuvem privada não configurada ou conta não autorizada. "
                   "Nenhum salvamento privado foi realizado. "
                   "Você ainda pode usar as opções avançadas.")
        return False

    state = st.session_state
    try:
        current_fingerprint = _current_decisions_fingerprint(plan, catalog)
    except (ValueError, TypeError, KeyError):
        st.error("Não foi possível validar os dados atuais. "
                 "O planejamento permanece nesta sessão.")
        return True

    saved = state.get("ux36_saved_decisions_fingerprint")
    status = state.get("ux36_cloud_status", "")
    clean = saved is not None and saved == current_fingerprint
    if status.startswith("Conflito"):
        st.error("Outra sessão alterou a cópia privada. "
                 "O planejamento atual foi preservado. "
                 "Não é seguro sobrescrever automaticamente.")
    elif status.startswith("Erro"):
        st.warning("O último salvamento não foi confirmado. "
                   "Suas alterações continuam nesta sessão.")
    elif clean:
        st.success("Salvo na nuvem privada. Suas escolhas estão disponíveis na próxima sessão.")
    else:
        st.info("Alterações ainda não salvas na nuvem privada.")

    if "ux75_private_autosave_toggle" not in state:
        state["ux75_private_autosave_toggle"] = bool(state.get("ux36_private_autosave", False))
    st.checkbox("Salvar automaticamente minhas próximas alterações",
                key="ux75_private_autosave_toggle",
                on_change=_ux75_private_autosave_changed,
                help="Opcional. Usa somente a nuvem privada e mantém o controle de versões.")
    if st.button("Salvar minha viagem", key="ux75_private_save_now",
                 type="primary", disabled=clean and status == "Salvo em espaço privado"):
        # A manual click allows retry even when a previous autosave failed.
        state.pop("ux36_autosave_failed_fingerprint", None)
        try:
            save_private_now(plan, catalog)
        except StorageConflict:
            state["ux36_cloud_dirty"] = True
            state["ux36_cloud_status"] = "Conflito de versão; alterações apenas nesta sessão"
            st.error("Outra sessão salvou uma versão diferente. "
                     "Nada foi sobrescrito; preserve o rascunho e compare as versões.")
        except (StorageUnavailable, ValueError, KeyError, TypeError):
            state["ux36_cloud_dirty"] = True
            state["ux36_cloud_status"] = "Erro ao salvar; alterações apenas nesta sessão"
            st.error("Não foi possível confirmar o salvamento privado. "
                     "Seu planejamento permanece nesta sessão.")
        else:
            st.success("Viagem salva com sucesso na nuvem privada.")
    return True


def render_global_private_save(plan, catalog):
    """One compact, reusable save control; no automatic public GitHub writes."""
    state = st.session_state
    st.markdown("**Minha viagem · salvamento**")
    store = _private_store()
    if store is None:
        st.caption("Somente nesta sessão · use o backup JSON. "
                   "Login e espaço privado são configurações distintas.")
        return
    try:
        dirty = (state.get("ux36_saved_decisions_fingerprint") !=
                 _current_decisions_fingerprint(plan, catalog))
    except (ValueError, TypeError, KeyError):
        st.warning("Dados precisam de revisão antes de salvar.")
        return
    status = state.get("ux36_cloud_status", "")
    if status.startswith("Conflito"):
        st.warning("Outra sessão alterou a cópia privada.")
    elif status.startswith("Erro"):
        st.warning("Último salvamento falhou; alterações só nesta sessão.")
    elif dirty:
        st.caption("Alterações somente nesta sessão.")
    else:
        st.caption("Salvo no espaço privado · confirmado pelo servidor.")
    if st.button("Salvar minha viagem", key="ux65_global_private_save",
                 width="stretch", disabled=not dirty and
                 status=="Salvo em espaço privado"):
        try:
            save_private_now(plan, catalog)
        except StorageConflict:
            state["ux36_cloud_status"] = "Conflito de versão; alterações apenas nesta sessão"
            state["ux36_cloud_dirty"] = True
            st.error("Outra sessão atualizou o arquivo. Exporte um backup antes de reconciliar.")
        except (StorageUnavailable, ValueError, KeyError, TypeError):
            state["ux36_cloud_status"] = "Erro ao salvar; alterações apenas nesta sessão"
            state["ux36_cloud_dirty"] = True
            st.error("Falha ao salvar. Seus dados continuam na sessão; baixe o backup.")
        else:
            st.success("Salvamento privado confirmado.")


def private_status_label(fallback, *, detailed=False):
    """Show private success only after a confirmed remote response."""
    state = st.session_state
    if state.get("ux36_cloud_status") == "Salvo em espaço privado":
        if state.get("ux36_saved_decisions_fingerprint") is None:
            return fallback  # Old session: no complete remote decision hash available.
        try:
            from attractions_model import load_attractions
            if state.get("ux36_saved_decisions_fingerprint") == _current_decisions_fingerprint(
                    bootstrap(), load_attractions()):
                return ("Salvo em espaço privado",
                        "Recuperável após entrar com a conta autorizada")
        except (ValueError, KeyError, TypeError):
            pass
        return ("Alterações apenas nesta sessão", "Salve uma cópia privada ou baixe o backup")
    if state.get("ux36_cloud_status", "").startswith(("Erro","Conflito")):
        hint=("Conflito de versão; revise a cópia antes de salvar" if state["ux36_cloud_status"].startswith("Conflito")
              else "Falha de salvamento; nenhuma gravação confirmada") if detailed else "Salve uma cópia privada ou baixe o backup"
        return ("Alterações apenas nesta sessão", hint)
    return fallback


def render_continuity_panel(plan:dict,catalog:dict)->None:
    with st.expander("Recuperar ou guardar uma cópia privada",expanded=False):
        render_private_controls(plan, catalog)
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
            archive=make_archive(plan,catalog,_safe_context(plan,catalog),city,calendars,
                                 city_favorites=list(st.session_state.get("ux41_favorites",[])),
                                  weekend_groups=st.session_state.get("ux48_weekend_groups"),
                                  destination_interests=st.session_state.get("ux502_interests",empty_interests()))
            raw=export_archive(archive,catalog)
        except (ValueError,TypeError,KeyError) as exc:
            st.warning("Não foi possível incluir esse contexto. "
                       "Desmarque os estudos ou revise o motivo: "+str(exc))
        else:
            st.download_button("Baixar cópia de segurança",
                               data=raw,file_name="nossa-europa-copia-privada.json",
                               mime="application/json",key="ux36_download")
            st.caption("Este download não confirma salvamento na nuvem. "
                       "Para recuperar o arquivo manualmente em outro dispositivo, abra-o lá.")
        uploaded=st.file_uploader("Abrir cópia de segurança (JSON)",
                                  type=["json"],key="ux36_upload")
        if uploaded is not None:
            if st.button("Pré-visualizar recuperação",key="ux36_preview_button"):
                try:
                    imported=import_archive(uploaded.getvalue(),catalog)
                    review=preview_restore(plan,imported,catalog,
                                           current_archive=_private_archive(plan,catalog))
                    st.session_state["ux36_review"]={
                        "archive":imported,"preview":review}
                    st.rerun()
                except (ValueError,TypeError,KeyError) as exc:
                    st.error("Arquivo não aceito: "+str(exc))
        pending=st.session_state.get("ux36_review")
        if pending:
            import_archive_document=pending["archive"]
            try:
                current_review=preview_restore(plan,import_archive_document,catalog,
                                                   current_archive=_private_archive(plan,catalog))
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
                st.caption("Campos do plano que mudam: "+", ".join(summary["changed_fields"]))
            if summary.get("auxiliary_changed_fields"):
                st.caption("Outros dados que mudam: "+
                           ", ".join(summary["auxiliary_changed_fields"]))
            if summary.get("wishlist_changes"):
                differences=summary["wishlist_changes"]
                st.caption("Minha lista: "+str(differences["added"])+" adicionados, "+
                           str(differences["removed"])+" removidos, "+
                           str(differences["priority_changed"])+" prioridades alteradas.")
            if not summary["changed_fields"] and not summary.get("auxiliary_changed_fields"):
                st.info("Nenhuma diferença nos dados persistidos.")
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
        if _private_store() is None:
            st.caption("**Armazenamento:** nesta sessão ou em backup JSON local. "
                       "Sincronização privada requer configuração no Streamlit Cloud.")
        else:
            st.caption("**Armazenamento:** cópia privada disponível para o proprietário autenticado. "
                       "Salvamento automático só funciona após ativação explícita; "
                       "rascunhos e contexto podem exigir salvar manualmente.")
