"""Optional draft backup controls for an authenticated-or-local session.

A downloaded JSON file is the only cross-session recovery available here.
No server-side persistence claims, credentials or automatic GitHub writes.
"""
import streamlit as st
from draft_plan_store import export_draft,import_draft,save_draft,get_draft

def render_draft_controls(board:dict,plan:dict,catalog:dict,*,profile:str)->dict|None:
    """Returns restored board when user confirms upload; otherwise None."""
    with st.expander("Guardar ou recuperar esta simulação (backup)",expanded=False):
        st.caption("Rascunhos ainda não aprovados não são gravados automaticamente "
                   "no GitHub público. Baixe um backup para recuperar depois.")
        st.download_button("Baixar backup do rascunho",
            data=export_draft(board),
            file_name=f"nossa-europa-{profile}-rascunho.json",
            mime="application/json",
            key="draft_export_"+profile,use_container_width=True)
        upload=st.file_uploader("Escolher backup do rascunho",type=["json"],
                                key="draft_import_"+profile)
        if upload is not None and st.button("Restaurar backup após validação",
                                             key="draft_confirm_"+profile):
            try:
                restored=import_draft(upload.getvalue().decode("utf-8"),plan,catalog)
                st.success("Rascunho restaurado nesta sessão. Ainda não foi aplicado ao planejamento.")
                return restored
            except (ValueError,UnicodeDecodeError,KeyError,TypeError) as exc:
                st.error("Não foi possível restaurar o rascunho: "+str(exc))
    return None
