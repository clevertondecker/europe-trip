"""Optional private GCS studies controls embedded in the existing city comparison.

All writes explicit. The authenticated UX3.6 store is reused, but a distinct
owner-scoped object is selected. The official TripPlan is never updated here.
"""
from __future__ import annotations
from copy import deepcopy
import streamlit as st

from private_city_studies import (cloud_load,cloud_commit,add_study,change_study,
                                  validate_collection)
from private_continuity_store import StorageConflict,StorageUnavailable


def _study_store():
    # _private_store enforces owner identity AND verifies configuration.
    from continuity_ui import _private_store
    store=_private_store()
    if store is None:return None
    store.key=store.key.removesuffix("current.json")+"city_studies.json"
    return store


def render_private_studies(comparison:dict,load_draft):
    st.markdown("#### Meus estudos privados")
    st.caption("Estudos separados do roteiro oficial, guardados no mesmo bucket privado. "
               "Toda gravação exige confirmação e geração GCS atual.")
    store=_study_store()
    if store is None:
        st.info("Entre como proprietário e configure a nuvem privada para acessar estudos entre dispositivos.")
        return
    state=st.session_state
    if st.button("Carregar / atualizar estudos da nuvem",key="ux34_cloud_load"):
        try:
            records,generation=cloud_load(store)
            state["ux34_cloud_records"]=records
            state["ux34_cloud_generation"]=generation
            state["ux34_cloud_message"]="Estudos privados atualizados"
        except (ValueError,StorageConflict,StorageUnavailable,KeyError,TypeError):
            st.error("Não foi possível ler os estudos. Seu plano e rascunhos locais foram preservados.")
    records=state.get("ux34_cloud_records")
    if records is None:
        st.caption("Clique em Carregar para consultar a coleção privada. "
                   "Nenhum estudo é enviado automaticamente.")
        return
    if state.pop("ux34_cloud_message",None):
        st.success("Coleção privada carregada e pronta para revisão.")
    studies=records["studies"]
    st.caption(f"{len(studies)} estudos privados nesta versão da coleção.")
    # A new study is derived from the currently visible comparison, never an
    # implicit edit to the approved plan.
    col1,col2=st.columns([2,1])
    fresh_name=col1.text_input("Nome do novo estudo privado",key="ux34_cloud_new_name",
                               value="Comparação "+", ".join(comparison["alternatives"]))
    if col2.button("Salvar novo estudo privado",key="ux34_cloud_create"):
        try:
            from city_decision_store import make_city_draft
            draft=make_city_draft(fresh_name,comparison)
            proposed,_=add_study(records,draft)
            generation=cloud_commit(store,proposed,state.get("ux34_cloud_generation"))
            state["ux34_cloud_records"]=proposed
            state["ux34_cloud_generation"]=generation
            st.success("Estudo criado e confirmado na nuvem privada.")
            st.rerun()
        except StorageConflict:
            st.error("Outra sessão atualizou a coleção. Carregue a versão mais recente e revise novamente.")
        except (ValueError,TypeError,KeyError,StorageUnavailable):
            st.error("Não foi possível salvar. A comparação atual foi preservada nesta sessão.")
    if not studies:return
    names={x["id"]:x["draft"]["name"] for x in studies}
    chosen_id=st.selectbox("Estudo privado",list(names),format_func=lambda x:names[x],
                           key="ux34_cloud_selected")
    selected=next(x for x in studies if x["id"]==chosen_id)
    old=selected["draft"]
    if old["plan_revision_at_creation"]!=comparison["plan_revision"]:
        st.warning("Este estudo foi criado em outra revisão do planejamento. "
                   "Reabrir só restaura as hipóteses e exige recalcular a comparação.")
    st.caption("Pesquisa e preços podem ter sido atualizados desde a criação; "
               "a comparação será recalculada ao reabrir.")
    if st.button("Reabrir estudo privado",key="ux34_cloud_open"):
        load_draft(deepcopy(old))
        st.rerun()
    operation=st.radio("Gerenciar estudo",["Atualizar com comparação atual","Renomear","Duplicar","Excluir"],
                       horizontal=True,key="ux34_cloud_operation")
    new_name=st.text_input("Novo nome",key="ux34_cloud_rename_name",
                            value=old["name"])
    confirmed=st.checkbox("Confirmo a alteração deste estudo privado",
                          key="ux34_cloud_confirm",value=False)
    if st.button("Aplicar ao estudo privado",key="ux34_cloud_apply",disabled=not confirmed):
        try:
            from city_decision_store import make_city_draft
            ops={"Atualizar com comparação atual":"replace",
                 "Renomear":"rename","Duplicar":"duplicate","Excluir":"delete"}
            revision_draft=(make_city_draft(old["name"],comparison,old["notes"])
                            if operation=="Atualizar com comparação atual" else None)
            proposed,_=change_study(records,chosen_id,ops[operation],
                                    name=new_name,draft=revision_draft)
            generation=cloud_commit(store,proposed,state.get("ux34_cloud_generation"))
            state["ux34_cloud_records"]=proposed
            state["ux34_cloud_generation"]=generation
            st.success("Operação confirmada no armazenamento privado.")
            st.rerun()
        except StorageConflict:
            st.error("Conflito: outra sessão mudou a coleção. Recarregue antes de editar.")
        except (ValueError,TypeError,KeyError,StorageUnavailable):
            st.error("Alteração não confirmada. Os estudos originais foram preservados.")
