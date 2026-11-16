"""UX 3.7: small contextual next-steps component, with no new top-level tabs."""
import streamlit as st

from ux37_next_actions_model import next_actions
from ux_navigation import set_task
from outing_cost_evidence import load_outing_evidence


def _open_action(area: str, section: str, destination_id: str | None) -> None:
    state = st.session_state
    state["ux37_return_area"] = state.get("ux_area", "Minha viagem")
    state["ux37_return_section"] = state.get("ux_section", "Resumo")
    # Preselect destination only when appropriate; existing editor persists its own draft.
    if destination_id and (area, section) == ("Explorar", "Passeios"):
        state["explore_selected_destination"] = destination_id
    set_task(state, area, section)


def _return_to_summary() -> None:
    set_task(st.session_state, "Minha viagem", "Resumo")


def render_next_actions(plan: dict, catalog: dict) -> None:
    st.markdown("### Próximos passos da nossa viagem")
    st.caption("Sugestões baseadas no roteiro e nas pesquisas registradas; "
               "não são reservas nem confirmação de preços para 2027.")
    try:
        evidence = load_outing_evidence(catalog=catalog)
        actions = next_actions(plan, catalog, evidence, limit=4)
    except (OSError, ValueError, KeyError, TypeError):
        st.warning("Não foi possível conferir as pesquisas agora. "
                   "Seu planejamento não foi alterado.")
        return
    if not actions:
        st.info("Sem próximas ações identificadas nas regras atuais. "
                "Continue revisando pesquisas e reservas manualmente.")
        return
    for action in actions:
        with st.container(border=True):
            st.markdown("**" + action["title"] + "**")
            st.caption(action["status"] + " · " + action["detail"])
            with st.expander("Por que isso importa?"):
                st.write(action["why"])
                if action["source"]:
                    st.markdown("[Fonte da pesquisa](" + action["source"] + ")")
            st.button("Abrir tarefa", key="ux37_open_" + action["id"],
                      on_click=_open_action,
                      args=(action["area"], action["section"], action["destination_id"]))
    st.caption("As ações são informativas: abrir uma pesquisa não altera "
               "a cidade-base, o roteiro ou o orçamento.")


def render_return_to_summary() -> None:
    if (st.session_state.get("ux37_return_area") == "Minha viagem"
            and st.session_state.get("ux37_return_section") == "Resumo"):
        if st.button("Voltar aos próximos passos", key="ux37_return_summary",
                     on_click=_return_to_summary):
            pass
