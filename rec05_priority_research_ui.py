"""REC05 in-place research summaries; no new main navigation or data writes."""
from __future__ import annotations

import streamlit as st
from rec05_priority_research_model import prioritize_research,export_research_plan


def _show(queue,key):
    if queue["state"]!="ready":
        st.info("Confirme ou atualize o escopo antes de priorizar pesquisas.")
        return
    st.caption(str(queue["total_count"])+" pendências para as bases/destinos selecionados. "
               "Esta é uma ordem de coleta de evidências, NÃO ranking de cidades.")
    st.caption(queue["method"]+" Retorno, última milha e tarifas de 2027 não "
               "são deduzidos a partir do tempo histórico de ida.")
    full=st.checkbox("Ver mais pendências deste escopo",key=key+"_more",value=False)
    subset=queue["tasks"][:50 if full else 8]
    priorities={"must_visit":"Imperdível","interested":"Interesse","maybe":"Talvez",
                "housing":"Moradia"}
    st.dataframe([{
        "Prioridade":priorities[x["priority"]],
        "Trajeto / cidade":x["direction"],
        "Tipo de pesquisa":x["evidence_type"].replace("_"," "),
        "Por que pesquisar":x["reason"],
        "Fonte já registrada":x["source_url"] or "A localizar",
        } for x in subset],hide_index=True,width="stretch")
    if len(subset)<queue["total_count"]:
        st.caption("Mostrando "+str(len(subset))+" de "+str(queue["total_count"])+
                   ". O inventário completo está disponível na exportação.")
    st.download_button("Exportar lista de pesquisas não realizadas (JSON)",
                       data=export_research_plan(queue),
                       file_name="rec05_pesquisas_pendentes.json",
                       mime="application/json",key=key+"_export")
    st.caption("Exportação por ação explícita; contém apenas IDs, prioridades e "
               "fontes de pesquisa, sem usuário, reservas ou plano privado.")


def render_research_result(recommendation, *, key, base_ids=None,readiness=None,
                           capabilities=None):
    with st.expander("Pesquisas prioritárias para esta decisão",expanded=False):
        try:
            queue=prioritize_research(recommendation,base_ids=base_ids,
                                      readiness=readiness,capabilities=capabilities)
            _show(queue,key)
        except (ValueError,KeyError,TypeError):
            st.warning("A pesquisa não está disponível neste escopo. Revise as escolhas.")


def render_research_from_session(*,key,base_ids=None):
    with st.expander("Pesquisa opcional · lacunas mais relevantes",expanded=False):
        enabled=st.checkbox("Calcular pendências para o escopo confirmado",
                            key=key+"_enabled",value=False)
        if not enabled:
            st.caption("O rascunho pode ser montado e salvo sem fazer essa pesquisa.")
            return
        try:
            from rec03a_session import SCOPE
            from ux502_destination_interests_model import empty_interests
            from base_recommendation_model import recommend_bases
            from rec04_candidate_capabilities import candidate_capabilities
            state=st.session_state
            result=recommend_bases(state.get("ux502_interests",empty_interests()),
                                   state.get(SCOPE))
            capabilities=candidate_capabilities()
            queue=prioritize_research(result,base_ids=base_ids,
                                      capabilities=capabilities)
            _show(queue,key)
        except (ValueError,KeyError,TypeError,ImportError,OSError):
            st.warning("O escopo mudou ou a evidência não pôde ser carregada. "
                       "Seu roteiro e suas escolhas foram preservados.")
