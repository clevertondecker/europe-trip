"""Overview of six common criterion weights for all 30 candidate bases.

A weight profile is shared; there is no independent per-city weight. Ranking is
withheld until comparable evidence exists, rather than assigning missing = 0.
"""
from __future__ import annotations
import streamlit as st
from base_research_expanded_model import (
    PRESETS,CRITERIA,load_research,observed_housing,normalized_score
)
from base_scenario_model import base_options

LABELS=("Moradia temporária","Trens e conexões","Passeios viáveis",
        "Custos dos passeios","Vida cotidiana / remoto","Países práticos")
PROFILE_IDS={"Geral":"general","Economia":"economy","Explorador":"explorer"}


def render_weight_coverage()->None:
    st.markdown("### Critérios e pesos das 30 cidades-base")
    st.caption("Os pesos são iguais para todas as cidades dentro de um perfil. "
               "O que muda entre elas são as evidências disponíveis; uma categoria "
               "sem pesquisa não recebe nota zero nem sua importância é redistribuída.")
    profile=st.segmented_control(
        "Perfil de decisão",list(PROFILE_IDS),
        key="ux_30_weight_profile",selection_mode="single")
    profile_id=PROFILE_IDS.get(profile,"general")
    weights=dict(zip(LABELS,PRESETS[profile_id]))
    st.dataframe([{"Critério":label,"Peso (%)":weight}
                  for label,weight in weights.items()],
                 hide_index=True,width="stretch",height=250)
    data=load_research()
    bases={b["id"]:b for b in base_options()}
    rows=[]
    for city in data["cities"]:
        # Historical apartment listings are not eligible 2027 short-stay quotes.
        # No normalized 0-100 criterion exists for any of these candidates yet.
        result=normalized_score({},profile_id)
        housing=observed_housing(city)
        rows.append({
            "Cidade-base":city["name"],
            "País":city["country"],
            "Anúncios históricos":housing["count"],
            "Cotações 2027 completas":city["eligible_2027_quotes"],
            "Rotas pesquisadas":bases[city["id"]]["routes"],
            "Cobertura dos critérios ponderados":f'{result["evidence_weight"]}%',
            "Nota final":"Não calculável",
            "Situação":"Pesquisa em andamento",
        })
    st.markdown("**Cobertura de pesquisa das cidades**")
    st.dataframe(rows,hide_index=True,width="stretch",height=340)
    st.warning("Nenhuma das 30 cidades possui cobertura suficiente para uma "
               "nota final confiável. O quadro acima é de disponibilidade de "
               "evidências, não uma classificação de melhores cidades.")
    st.caption("Quando houver dados comparáveis, cada critério será avaliado na "
               "mesma escala e ponderado sem alterar os pesos faltantes. "
               "Pelo menos três cotações elegíveis de hospedagem em 2027, "
               "rotas completas e condições de trabalho remoto exigem validação.")
