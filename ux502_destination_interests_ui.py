"""UX 5.0.2 — wishlist UI; single session authority projected into private archive."""
from __future__ import annotations
import streamlit as st
from hashlib import sha256
from ux502_destination_interests_model import (
    PRIORITIES, LABELS, empty_interests, validate_interests, set_interest,
    remove_interest, ordered_interests, reconcile_transient, export_interests,
    import_interests, selected_destinations_for_comparison,
)
from private_continuity_store import StorageConflict, StorageUnavailable
from ux_shared_ui_presentation import page_header, kpi_cards, next_action


def _current(discovery):
    key = "ux502_interests"
    if key not in st.session_state:
        st.session_state[key] = empty_interests()
    try:
        return validate_interests(st.session_state[key], discovery)
    except ValueError:
        st.error("Lista incompatível; nenhuma preferência foi substituída.")
        return None


def _mark_exported(revision):
    st.session_state["ux502_local_exported_revision"] = revision
    st.session_state["ux502_status"] = "Arquivo local exportado; nuvem não confirmada"


def _change(document):
    st.session_state["ux502_interests"] = document
    st.session_state["ux36_cloud_dirty"] = True
    st.session_state["ux502_local_exported_revision"] = None
    st.session_state["ux502_status"] = "Alterações não salvas"


def add_destination(destination_id, discovery):
    current = _current(discovery)
    if current is not None:
        _change(set_interest(current, destination_id, "interested", discovery))


def _set_priority(destination_id, widget_key, discovery):
    current = _current(discovery)
    if current is not None:
        _change(set_interest(current, destination_id,
                             st.session_state[widget_key], discovery))


def _remove(destination_id, discovery):
    current = _current(discovery)
    if current is not None:
        _change(remove_interest(current, destination_id, discovery))


def render_wishlist(discovery) -> bool:
    """Render controls and return True when 'Minha lista' is the selected view."""
    current = _current(discovery)
    if current is None:
        return False
    by_id = {row["id"]: row for row in discovery["destinations"]}
    def remember_discovery_filters():
        keys = ("ux501_country", "ux501_categories", "ux501_search", "ux501_page")
        # Streamlit removes keys for controls not mounted in the alternate view.
        snapshot = st.session_state.get("ux502_discovery_filters", {}).copy()
        snapshot.update({key: st.session_state[key] for key in keys if key in st.session_state})
        if "ux501_interest_session" in st.session_state:
            st.session_state["ux502_transient_shadow"] = list(st.session_state["ux501_interest_session"])
        st.session_state["ux502_discovery_filters"] = snapshot

    def legacy_view_changed():
        remember_discovery_filters()
        if "ux64_public_task" in st.session_state:
            st.session_state["ux64_public_task"]=(
                "Minha lista" if st.session_state["ux502_view"]=="Minha lista"
                else "Descobrir")
    if "ux64_public_task" in st.session_state:
        # Keep the original widget for existing bookmarks and navigation tests.
        # Public task tabs remain the main way to switch views.
        with st.expander("Visualização anterior · avançado", expanded=False):
            view=st.radio("Visualização", ("Descobrir lugares", "Minha lista"),
                          horizontal=True,key="ux502_view",
                          on_change=legacy_view_changed)
    else:
        view = st.radio("Visualização", ("Descobrir lugares", "Minha lista"),
                        horizontal=True, key="ux502_view",
                        on_change=remember_discovery_filters)
    if view == "Descobrir lugares":
        if "ux501_interest_session" not in st.session_state and "ux502_transient_shadow" in st.session_state:
            st.session_state["ux501_interest_session"] = list(st.session_state["ux502_transient_shadow"])
        for key, value in st.session_state.get("ux502_discovery_filters", {}).items():
            if key not in st.session_state:
                st.session_state[key] = value
    if view == "Minha lista":
        st.markdown(page_header(
            "Minha lista", "NOSSA EUROPA 2027 · EXPLORAR",
            "Classifique os destinos que queremos conhecer e transforme desejos em roteiro.",
            tag="Da descoberta ao planejamento", variant="compact",
        ),unsafe_allow_html=True)
    items = ordered_interests(current, discovery)
    active = [r for r in items if r["priority"] != "discarded"]
    if view == "Minha lista":
        metrics=kpi_cards([
            {"name":"Destinos desejados","value":len(active),"hint":"Na minha lista",
             "icon":"◎","highlight":bool(active)},
            {"name":"Imperdíveis","value":sum(r["priority"] == "must_visit" for r in items),
             "hint":"Maior prioridade","icon":"★"},
            {"name":"Quero conhecer","value":sum(r["priority"] == "interested" for r in items),
             "hint":"Interesses","icon":"◇"},
            {"name":"Talvez","value":sum(r["priority"] == "maybe" for r in items),
             "hint":"Para avaliar","icon":"○"},
        ])
        with st.container(key="ux82_wishlist_metrics"):
            for column,markup in zip(st.columns(4,gap="small"),metrics):
                column.markdown(markup,unsafe_allow_html=True)
        st.caption("São preferências de pesquisa, não passeios, reservas ou trajetos confirmados. "
                   "A cidade-base oficial e o TripPlan não são alterados.")
    transient = st.session_state.get("ux501_interest_session",
                                     st.session_state.get("ux502_transient_shadow", []))
    try:
        _, pending = reconcile_transient(current, transient, discovery)
    except ValueError:
        pending = []
    if pending:
        st.info(f"{len(pending)} interesse(s) da seleção temporária anterior ainda não "
                "foram adicionados à lista salva.")
        if st.button("Trazer seleção temporária para minha lista", key="ux502_migrate"):
            new = current
            for destination in pending:
                new = set_interest(new, destination, "interested", discovery)
            _change(new)
            st.rerun()

    if current["revision"] == st.session_state.get("ux502_private_saved_revision") and not st.session_state.get("ux36_cloud_dirty"):
        st.success("Lista salva no armazenamento privado nesta sessão.")
    elif current["revision"] == st.session_state.get("ux502_local_exported_revision"):
        st.info("Arquivo local preparado para download; não há salvamento em nuvem confirmado.")
    else:
        st.warning(st.session_state.get("ux502_status", "Alterações apenas nesta sessão. Salve ou exporte para recuperá-las."))

    with st.expander("Salvar minha lista", expanded=(view == "Minha lista")):
        from continuity_ui import _private_store, save_private_now
        from attractions_model import load_attractions
        store = _private_store()
        if store is None:
            st.warning("Sem armazenamento privado disponível. Para não perder a lista, "
                       "guarde uma cópia JSON local abaixo.")
        else:
            if st.button("Salvar lista na nuvem privada", key="ux502_cloud_save"):
                try:
                    save_private_now(st.session_state["advisor_plan"], load_attractions())
                except StorageConflict:
                    st.session_state["ux36_cloud_dirty"] = True
                    st.session_state["ux502_status"] = "Conflito de versão; alterações não salvas"
                    st.error("Conflito de versão: outra sessão modificou o arquivo privado. "
                             "Exporte suas alterações e reconcilie antes de salvar.")
                except (StorageUnavailable, ValueError, KeyError, TypeError):
                    st.session_state["ux36_cloud_dirty"] = True
                    st.session_state["ux502_status"] = "Falha de salvamento; alterações não salvas"
                    st.error("Falha de salvamento. Seus interesses continuam nesta sessão.")
                else:
                    st.session_state["ux502_private_saved_revision"] = current["revision"]
                    st.session_state["ux502_status"] = "Salvo no armazenamento privado"
                    st.success("Salvamento privado confirmado pelo servidor.")
            st.caption("Backup ou recuperação de emergência do planejamento completo: "
                       "Planejar → Meus destinos → Recuperar ou guardar uma cópia privada.")
        # Saving to a configured store is not proof of a successful write.
        # Keep a lossless emergency export for confirmed failures/conflicts.
        status = st.session_state.get("ux502_status", "")
        emergency = (store is None or status.startswith(("Conflito", "Falha")))
        if emergency:
            st.warning("Alterações não confirmadas no armazenamento privado. "
                       "Baixe uma cópia local antes de sair desta sessão.")
        raw = export_interests(current, discovery)
        st.download_button("Exportar lista JSON", raw, "nossa-europa-destinos-desejados.json",
                           "application/json", key="ux502_download",
                           on_click=_mark_exported, args=(current["revision"],))
        st.caption("O arquivo exportado não significa que a nuvem foi atualizada.")

        # Standalone wishlist JSON from older releases is not a whole-plan
        # archive. Preserve validated, confirmed imports without showing a
        # routine second save/restore workflow.
        advanced = (store is None or st.checkbox(
            "Recuperar arquivo antigo da lista (avançado)",
            key="ux502_legacy_import_open"))
        if advanced:
        uploaded = st.file_uploader("Importar lista JSON", type=["json"],
                                    key="ux502_upload")
        if uploaded is not None and st.button("Analisar arquivo", key="ux502_import_preview"):
            try:
                incoming = import_interests(uploaded.getvalue(), discovery)
            except ValueError as exc:
                st.error(str(exc))
            else:
                st.session_state["ux502_import_pending"] = incoming
        pending_import = st.session_state.get("ux502_import_pending")
        if pending_import is not None:
            st.warning(f"O arquivo contém {len(pending_import['items'])} preferências. "
                       "Confirmar substituirá a lista atual nesta sessão (não na nuvem).")
            if st.button("Confirmar substituição da lista", key="ux502_import_confirm"):
                # A replaced document is still a local revision, not a remote save.
                restored = validate_interests(pending_import, discovery)
                restored["revision"] = max(current["revision"], restored["revision"]) + 1
                _change(restored)
                from rec03a_session import clear_recommendation_context
                clear_recommendation_context(st.session_state)
                from ux_planning_journey_model import clear_planning_context
                clear_planning_context(st.session_state)
                st.session_state.pop("ux502_import_pending", None)
                st.rerun()


    if view != "Minha lista":
        return False
    if active:
        from rec03a_session import request_navigation
        from ux_planning_journey_ui import request_planning
        from ux_planning_journey_model import project_planning
        from planning_session import active_plan
        from attractions_model import load_attractions
        planning=project_planning(active_plan(),current,discovery,load_attractions())
        # This is presentation of the same authoritative action used by the
        # existing CTA; do not recompute eligibility or introduce another state.
        if planning["eligible_count"]:
            headline="Destinos compatíveis prontos para o roteiro"
            detail=f'{planning["eligible_count"]} destino(s) podem ser incluídos sem definir datas.'
        elif planning["rows"]:
            headline="Seu rascunho está pronto para revisão"
            detail="Confira os destinos incluídos e salve suas escolhas."
        else:
            headline="Continue descobrindo destinos"
            detail="Os desejos atuais ainda estão disponíveis somente para pesquisa."
        st.markdown(next_action(headline,detail,variant="compact"),unsafe_allow_html=True)
        if planning["eligible_count"]:
            st.button("Montar roteiro com meus destinos",key="flow_journey_from_wishlist",type="primary",
                      on_click=request_planning,args=(st.session_state,"build"))
        elif planning["rows"]:
            st.button("Revisar meu roteiro",key="flow_journey_from_wishlist",type="primary",
                      on_click=request_planning,args=(st.session_state,"review"))
        else:
            st.info("Os destinos desejados ainda não têm passeios compatíveis para inclusão. Eles continuam na sua lista.")
            from ux504_guided_journey_ui import request_step
            st.button("Descobrir destinos compatíveis",key="flow_journey_find_compatible",type="primary",
                      on_click=request_step,args=("discover",))
            # Discovery remains accessible in the existing task tabs.
        st.button("Encontrar cidades-base", key="rec03a_open_from_wishlist",
                  on_click=request_navigation,args=(st.session_state,"suggestions"))
        st.button("Comparar cidades-base para nossos destinos",
                  key="ux503_open_from_wishlist",
                  on_click=request_navigation,args=(st.session_state,"manual"))

    if not items:
        st.info("Nenhum destino na lista. Use Descobrir lugares para adicionar.")
    # The widget identity is derived from the canonical document snapshot.
    # Import/restore may replace values even if revision numbers coincide.
    # Never reuse a stale selectbox key from a previous document.
    fingerprint = sha256(export_interests(current, discovery)).hexdigest()[:16]
    for row in items:
        destination_id = row["destination_id"]
        destination = by_id[destination_id]
        with st.container(border=True):
            cols = st.columns([3, 2, 1])
            cols[0].markdown("**" + destination["name"] + "** · " + destination["country"])
            if destination.get("planning_support") == "exploration_only":
                cols[0].caption("Pesquisa e comparação; inclusão no roteiro ainda indisponível.")
            widget_key = "ux502_priority_" + destination_id + "_" + fingerprint
            cols[1].selectbox("Prioridade", PRIORITIES,
                               index=PRIORITIES.index(row["priority"]),
                               format_func=lambda p: LABELS[p], key=widget_key,
                               on_change=_set_priority,
                               args=(destination_id, widget_key, discovery))
            cols[2].button("Remover", key="ux502_remove_" + destination_id,
                           on_click=_remove, args=(destination_id, discovery))
    return True
