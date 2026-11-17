"""UX 5.0.3 — comparison presentation, always read-only."""
from __future__ import annotations
import streamlit as st
from base_research_expanded_model import load_research
from ux501_destination_discovery_model import build_destination_discovery
from ux502_destination_interests_model import empty_interests
from ux503_destination_base_comparison_model import compare_wishlist_bases


def _return_to_wishlist():
    st.session_state["ux_area"] = "Explorar"
    st.session_state["ux_section"] = "Passeios"
    st.session_state["ux502_view"] = "Minha lista"


def render_wishlist_base_comparison(*, plan, discovery=None, research=None):
    discovery = discovery if discovery is not None else build_destination_discovery()
    research = research if research is not None else load_research()
    st.markdown("### Qual cidade-base facilita conhecer os lugares que escolhemos?")
    st.caption("Comparamos a mesma lista de desejos em todas as bases. "
               "Pesquisa ferroviária histórica não confirma bate-volta em 2027.")
    interests = st.session_state.get("ux502_interests", empty_interests())
    cities = {c["id"]:c for c in research["cities"]}
    official = plan["base_city"]
    favorite = set(st.session_state.get("ux41_favorites", []))
    preferred = [x for x in [official, *sorted(favorite)] if x in cities]
    choices = list(dict.fromkeys([*preferred, *sorted(
        cities, key=lambda x: (cities[x]["name"], x))]))
    defaults = list(dict.fromkeys([x for x in
                [official,"strasbourg","lille","mulhouse"] if x in cities]))[:4]
    if len(defaults) < 2:
        defaults = choices[:2]
    if "ux503_bases" not in st.session_state:
        st.session_state["ux503_bases"] = defaults

    def label(city_id):
        tags = []
        if city_id == official:
            tags.append("referência oficial")
        if city_id in favorite:
            tags.append("favorita")
        suffix = (" · " + ", ".join(tags)) if tags else ""
        return cities[city_id]["name"] + " · " + cities[city_id]["country"] + suffix

    selected = st.multiselect(
        "Cidades-base para comparar (2 a 5)",choices,
        format_func=label,key="ux503_bases",
        help="Seleção apenas para pesquisa; não altera a base oficial.")
    st.caption("Base do roteiro oficial: **" + label(official) + "**. "
               "Removê-la desta comparação não altera a viagem.")
    if st.button("Voltar à minha lista", key="ux503_back_to_wishes"):
        _return_to_wishlist()
        st.rerun()
    if len(selected) < 2 or len(selected) > 5:
        st.warning("Selecione entre duas e cinco cidades-base para comparar.")
        return
    try:
        result = compare_wishlist_bases(interests, list(selected),
                                        discovery=discovery, research=research)
    except ValueError as exc:
        st.error("Não foi possível validar a lista: " + str(exc))
        st.caption("Confira IDs removidos ou renomeados antes de continuar. "
                   "Nenhuma preferência ou base foi alterada.")
        return
    if not result["destinations"]:
        if result["discarded_count"]:
            st.info("Todos os destinos estão descartados. "
                    "Reclassifique um lugar em Minha lista antes de comparar.")
        else:
            st.info("Sua lista está vazia. Adicione destinos em Explorar → Passeios.")
        return
    st.markdown("#### Nossos destinos")
    st.write(" · ".join(x["name"]+" ("+x["priority_label"]+")"
                         for x in result["destinations"]))
    st.caption("Destinos descartados não participam; alterações na lista são "
               "refletidas ao retornar a esta comparação.")
    st.markdown("#### Logística conhecida por destino")
    st.caption("Os tempos são históricos, de ida e entre estações. "
               "Dados ausentes não significam falta de conexão.")
    indexed={(r["base_id"],r["destination_id"]):r for r in result["rows"]}
    # One destination per block: readable on small screens; 2–5 columns when space allows.
    for destination in result["destinations"]:
        with st.container(border=True):
            st.markdown("**"+destination["name"]+"** · "+destination["priority_label"])
            cols=st.columns(len(selected))
            for col,base_id in zip(cols,selected):
                route=indexed[(base_id,destination["id"])]
                with col:
                    st.markdown("**"+cities[base_id]["name"]+"**")
                    minimum=route["minimum_oneway_min"]
                    st.write((str(minimum)+" min · ida histórica") if minimum is not None
                             else route["status"])
                    if route["typical_oneway_min"] is not None:
                        st.caption("Típico observado: "+str(route["typical_oneway_min"])+" min")
                    st.caption("Retorno: não verificado · última milha: pendente")
                    if route["divergent_sources"]:
                        st.warning("Fontes com tempos divergentes")
                    with st.expander("Fontes e detalhes", expanded=False):
                        st.write("Transferências: "+(str(route["transfers"])
                                 if route["transfers"] is not None else "Não pesquisadas"))
                        st.write("Observação: "+str(route["source_date"] or "Data não informada"))
                        if route["source_url"]:
                            st.link_button("Fonte selecionada",route["source_url"])
                        for observation in route["observations"]:
                            source=observation.get("source_url")
                            if source and source != route["source_url"]:
                                st.markdown("[Outra observação]("+source+")")
                        st.caption("Fontes históricas não garantem retorno nem "
                                   "condições equivalentes em 2027.")
    st.markdown("#### O que sabemos — e o que falta pesquisar")
    st.caption("Cobertura de pesquisa não é qualidade logística. "
               "Nenhuma base recebe ranking ou pontuação automática.")
    for summary in result["summaries"]:
        with st.container(border=True):
            st.markdown("**"+summary["base_name"]+"**")
            c1,c2,c3=st.columns(3)
            c1.metric("Idas documentadas",summary["documented_time_count"])
            c2.metric("Sem tempo",summary["missing_time_count"])
            c3.metric("Acesso local",summary["local_count"])
            housing=summary["housing"]
            if housing["count"]:
                st.caption("Moradia: "+str(housing["count"])+" anúncios históricos; "
                           "mediana € "+str(round(housing["median_eur_month"]))+
                           "/mês. Não comparável ou confirmada para 2027.")
            else:
                st.caption("Moradia: sem amostras comparáveis documentadas.")
            st.write("Qualidade logística: **ainda não conclusiva**.")
            with st.expander("Pendências para decidir com segurança"):
                for item in summary["research_gaps"]:
                    st.markdown("- "+item)
    st.info("Próximo passo: conferir retornos aos fins de semana, "
            "acesso local, moradia e custos em condições equivalentes "
            "antes de tomar a decisão de cidade-base.")
