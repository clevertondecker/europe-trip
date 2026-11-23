"""Source-backed *context*, distinct from REC02/ROUTES7 route evidence.

These notes document attractions and transport networks without changing the
route matrix, historical-time counters, viability, prices or official plan.
"""
from __future__ import annotations

from functools import lru_cache
import json
from pathlib import Path

import streamlit as st

DATA_PATH = Path(__file__).resolve().parent / "data" / "ux105_base_city_context_2026_11.json"
VALID_KINDS = {"urban_access", "service_reference", "operator_caveat"}


@lru_cache(maxsize=1)
def load_city_context() -> dict:
    data=json.loads(DATA_PATH.read_text(encoding="utf-8"))
    if data.get("schema_version") != 1:
        raise ValueError("Contexto UX105 com versão desconhecida")
    rows=data.get("cities")
    if not isinstance(rows,list):
        raise ValueError("Contexto UX105 incompleto")
    by_id={}
    for row in rows:
        city=row["id"]
        if not isinstance(city,str) or city in by_id:
            raise ValueError("Cidade duplicada/inválida no contexto UX105")
        for key in ("mobility","attractions"):
            for item in row[key]:
                if not (item.get("source_url","").startswith("https://") and
                        item.get("detail") and (item.get("name") or item.get("label"))):
                    raise ValueError(f"Referência documental inválida: {city}")
                if key=="mobility" and item.get("kind") not in VALID_KINDS:
                    raise ValueError(f"Categoria de mobilidade inválida: {city}")
        by_id[city]=row
    return by_id


def context_for_base(base_id: str) -> dict | None:
    """Return only exact city-ID documentation; never infer from neighbours."""
    return load_city_context().get(base_id)


def render_base_context_summary(base_id: str) -> None:
    data=context_for_base(base_id)
    if data:
        st.caption(
            f"Pesquisa local: {len(data['mobility'])} referências de mobilidade "
            f"e {len(data['attractions'])} atrações documentadas. "
            "Não aumentam a cobertura dos tempos ferroviários."
        )


def render_base_context_details(base_id: str) -> None:
    data=context_for_base(base_id)
    if not data:
        return
    st.markdown("**Transportes e logística local pesquisados**")
    for index,item in enumerate(data["mobility"]):
        st.write(item["label"]+" — "+item["detail"])
        st.link_button("Fonte de transporte "+str(index+1),
                       item["source_url"],key=f"ux105_transport_{base_id}_{index}")
    st.markdown("**Atrações para investigar**")
    for index,item in enumerate(data["attractions"]):
        st.write(item["name"]+" — "+item["detail"])
        st.link_button("Fonte da atração "+str(index+1),
                       item["source_url"],key=f"ux105_attraction_{base_id}_{index}")
    st.markdown("**Ainda falta validar para 2027**")
    for item in data["gaps"]:
        st.caption("• "+item)
    st.caption("Essas referências não são tempos novos na matriz comparativa, "
               "nem confirmam retorno, tarifa, horários ou disponibilidade em 2027.")
